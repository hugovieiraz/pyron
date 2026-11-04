"""Pipeline ponta a ponta: caixa → máscara SAM 2 → medidas geométricas → temperaturas só da peça.

A caixa do detector pega também o fundo (céu, estrutura, outra fase). Medindo a temperatura na
caixa inteira (``nucleo.analise.medir``), o fundo frio puxa a média e o desvio para baixo e um
objeto quente vizinho pode virar o T_max. Com a máscara, as estatísticas ficam estritamente no
corpo do equipamento: ``matriz_termica[mascara == 1]``.

**Registro entre imagem e matriz.** A caixa e a máscara estão nos pixels da imagem passada ao
SAM 2. Se a matriz de temperatura tem outra resolução, a máscara é redimensionada (vizinho mais
próximo) para a forma da matriz, o que só é correto quando as duas cobrem o **mesmo campo de visão**
(ex.: ``ImagemTermica.exibida_rgb`` e ``ImagemTermica.temperatura_c`` do ``nucleo.entrada``). A foto
visível da FLIR tem outro campo de visão e paralaxe: precisa ser registrada antes (fora deste módulo).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from nucleo.metrologia.dimension_estimator import DimensionEstimator
from nucleo.segmentacao.sam2_engine import SAM2Segmentor, registrar

BRANCO = 255


@dataclass(frozen=True)
class EstatisticasTermicas:
    t_max: float
    t_med: float
    t_min: float
    t_desvio: float
    x_max: int  # pixel mais quente, em coordenadas da matriz
    y_max: int
    pixels: int  # pixels da peça com temperatura válida (NaN fica de fora)


@dataclass
class ResultadoAtivo:
    mascara: np.ndarray  # uint8, forma da imagem
    mascara_termica: np.ndarray  # uint8, forma da matriz de temperatura
    score: float
    geometria: dict
    termica: EstatisticasTermicas | None  # None: nenhum pixel da peça com temperatura
    tempos_ms: dict = field(default_factory=dict)

    def resumo(self) -> dict:
        """Tudo menos as máscaras (para JSON, laudo ou banco)."""
        return {
            "score": self.score,
            "geometria": self.geometria,
            "termica": asdict(self.termica) if self.termica else None,
            "tempos_ms": self.tempos_ms,
        }


def ajustar_mascara(mascara: np.ndarray, forma: tuple[int, int]) -> np.ndarray:
    """Leva a máscara para a forma (H, W) da matriz térmica sem criar valores intermediários."""
    mascara = (np.asarray(mascara) > 0).astype(np.uint8)
    if mascara.shape == tuple(forma):
        return mascara
    import cv2

    altura, largura = forma
    return cv2.resize(mascara, (largura, altura), interpolation=cv2.INTER_NEAREST)


def estatisticas_termicas(matriz_termica: np.ndarray, mascara: np.ndarray) -> EstatisticasTermicas | None:
    """T_max, T_média, T_min e desvio padrão só nos pixels da máscara, ignorando NaN."""
    temperatura = np.asarray(matriz_termica, dtype=np.float32)
    if temperatura.ndim != 2:
        raise ValueError(f"matriz térmica deve ser H x W; veio {temperatura.shape}")
    mascara = ajustar_mascara(mascara, temperatura.shape)
    dentro = (mascara == 1) & np.isfinite(temperatura)
    if not dentro.any():
        return None
    active_thermal_data = temperatura[dentro]
    linhas, colunas = np.nonzero(dentro)
    quente = int(np.argmax(active_thermal_data))
    return EstatisticasTermicas(
        t_max=float(active_thermal_data[quente]),
        t_med=float(active_thermal_data.mean()),
        t_min=float(active_thermal_data.min()),
        t_desvio=float(active_thermal_data.std()),
        x_max=int(colunas[quente]),
        y_max=int(linhas[quente]),
        pixels=int(active_thermal_data.size),
    )


def isolar_hotspot_defectsam(
    matriz_termica: np.ndarray,
    mascara_ativo: np.ndarray,
    segmentador: SAM2Segmentor | None = None,
    metric_ratio_m_por_px: float | None = None,
    caixa_rgb: Sequence[float] | None = None,
    forma_rgb: tuple[int, int] | None = None,
) -> dict[str, Any] | None:
    """Isola a sub-máscara exata do hotspot térmico dentro do ativo (DefectSAM).

    Combina prompts espaciais de pontos no SAM 2 (pico térmico como positivo label=1 e ponto frio do
    corpo como negativo label=0) com validação radiométrica de núcleo quente, estimando a área real
    da anomalia em pixels e em cm².
    """
    temperatura = np.asarray(matriz_termica, dtype=np.float32)
    if temperatura.ndim != 2:
        return None

    h_mat, w_mat = temperatura.shape
    mask_mat = ajustar_mascara(mascara_ativo, (h_mat, w_mat))
    dentro = (mask_mat == 1) & np.isfinite(temperatura)
    if not dentro.any():
        return None

    valores = temperatura[dentro]
    linhas, colunas = np.nonzero(dentro)
    idx_quente = int(np.argmax(valores))
    idx_frio = int(np.argmin(valores))

    t_max = float(valores[idx_quente])
    t_med = float(valores.mean())
    t_min = float(valores[idx_frio])
    t_std = float(valores.std())

    x_quente, y_quente = int(colunas[idx_quente]), int(linhas[idx_quente])
    x_frio, y_frio = int(colunas[idx_frio]), int(linhas[idx_frio])

    # Núcleo radiométrico adaptativo dentro do corpo da peça
    amplitude = max(t_max - t_med, 0.0)
    if amplitude <= 0.2:
        # Corpo termicamente uniforme: apenas o pixel de pico
        nucleo_termico = np.zeros((h_mat, w_mat), dtype=np.uint8)
        nucleo_termico[y_quente, x_quente] = 1
    else:
        limiar_quente = t_med + max(0.45 * amplitude, 1.2 * t_std)
        limiar_quente = min(limiar_quente, t_max - 1e-4)
        nucleo_termico = (dentro & (temperatura >= limiar_quente)).astype(np.uint8)

    mascara_sam_mat = None
    score_sam = 1.0
    if segmentador is not None and getattr(segmentador, "_forma_quadro", None) is not None:
        try:
            h_rgb, w_rgb = forma_rgb or segmentador._forma_quadro
            sx = w_rgb / max(w_mat, 1)
            sy = h_rgb / max(h_mat, 1)
            pontos = [
                [float(x_quente * sx), float(y_quente * sy)],
                [float(x_frio * sx), float(y_frio * sy)],
            ]
            rotulos = [1, 0]
            seg_hs = segmentador.segmentar_com_pontos(pontos, rotulos, bbox_xyxy=caixa_rgb)
            mascara_sam_mat = ajustar_mascara(seg_hs.mascara, (h_mat, w_mat))
            score_sam = float(seg_hs.score)
        except Exception:
            mascara_sam_mat = None

    if mascara_sam_mat is not None and np.any(mascara_sam_mat & nucleo_termico):
        mascara_hotspot = (mascara_sam_mat & nucleo_termico & mask_mat).astype(np.uint8)
    else:
        mascara_hotspot = (nucleo_termico & mask_mat).astype(np.uint8)

    if not np.any(mascara_hotspot):
        mascara_hotspot[y_quente, x_quente] = 1

    # Mantém a componente conexa que contém o pico térmico (x_quente, y_quente)
    import cv2

    num_labels, labels = cv2.connectedComponents(mascara_hotspot)
    rotulo_pico = int(labels[y_quente, x_quente])
    if rotulo_pico > 0:
        mascara_hotspot = (labels == rotulo_pico).astype(np.uint8)

    pixels_hs = int(mascara_hotspot.sum())
    pixels_ativo = max(int(dentro.sum()), 1)
    fracao = float(pixels_hs / pixels_ativo)
    t_med_hs = float(temperatura[mascara_hotspot == 1].mean())

    area_cm2 = None
    if metric_ratio_m_por_px is not None and float(metric_ratio_m_por_px) > 0:
        escala_cm = float(metric_ratio_m_por_px) * 100.0
        area_cm2 = round(float(pixels_hs * (escala_cm**2)), 2)

    ys_hs, xs_hs = np.nonzero(mascara_hotspot)
    caixa_hotspot = [
        int(xs_hs.min()),
        int(ys_hs.min()),
        int(xs_hs.max() + 1),
        int(ys_hs.max() + 1),
    ]

    return {
        "mascara_hotspot": mascara_hotspot,
        "caixa_hotspot": caixa_hotspot,
        "area_hotspot_px": pixels_hs,
        "area_hotspot_cm2": area_cm2,
        "fracao_area_ativo": round(fracao, 4),
        "t_max_hotspot": round(t_max, 2),
        "t_med_hotspot": round(t_med_hs, 2),
        "elevacao_sobre_ativo_c": round(t_max - t_med, 2),
        "x_max": x_quente,
        "y_max": y_quente,
        "score_defectsam": round(score_sam, 4),
    }


def exportar_mascara(mascara: np.ndarray, caminho: str | Path) -> Path:
    """Grava a máscara como PNG preto e branco (0/255), legível em qualquer visualizador."""
    import cv2

    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    ok, png = cv2.imencode(".png", (np.asarray(mascara) > 0).astype(np.uint8) * BRANCO)
    if not ok:
        raise OSError(f"não foi possível codificar a máscara para {caminho}")
    caminho.write_bytes(png.tobytes())  # write_bytes: aceita caminhos com acento no Windows
    return caminho


def analisar_ativo(
    segmentador: SAM2Segmentor,
    imagem_rgb: np.ndarray,
    matriz_termica: np.ndarray,
    bbox_xyxy: Sequence[float] | np.ndarray,
    metric_ratio: float | None = None,
    ref_height_meters: float | None = None,
    metadados_camera: dict | None = None,
    forcar_ref_height: bool = False,
    estimador: DimensionEstimator | None = None,
    reutilizar_quadro: bool = False,
) -> ResultadoAtivo:
    """Segmenta o ativo na caixa, mede a geometria e extrai as temperaturas só do corpo dele.

    ``reutilizar_quadro=True`` pula o ``set_frame`` quando a mesma imagem já foi carregada
    (várias peças na mesma foto: o codificador roda uma vez só).
    """
    estimador = estimador or DimensionEstimator()
    tempos: dict[str, float] = {}

    inicio = time.perf_counter()
    if not reutilizar_quadro:
        segmentador.set_frame(imagem_rgb)
    tempos["embeddings"] = (time.perf_counter() - inicio) * 1000

    segmentacao = segmentador.segmentar(bbox_xyxy)
    tempos["mascara"] = segmentacao.tempo_ms

    inicio = time.perf_counter()
    geometria = estimador.analyze_contour(segmentacao.mascara, metric_ratio=metric_ratio)

    # Metrologia Inteligente: Método 1 (Telemetria Óptica/FLIR) prioritário; Método 2 (Criminisi) secundário
    try:
        from nucleo.metrologia.vanishing_points import VanishingGeometryEstimator
        from nucleo.metrologia.criminisi_metrology import ProjectiveMetrologyEngine

        p_engine = ProjectiveMetrologyEngine(default_unit="m")

        dist_m = None
        if metadados_camera:
            try:
                d = metadados_camera.get("distancia_m")
                if d is not None and float(d) > 0:
                    dist_m = float(d)
            except (ValueError, TypeError):
                dist_m = None

        if dist_m and metric_ratio is None and not forcar_ref_height:
            # MÉTODO 1: Telemetria Óptica da Câmera (Distância real + Lente sem fixar Href)
            dim_res = p_engine.compute_dimensions_from_telemetry(
                mask=segmentacao.mascara,
                distance_m=dist_m,
                camera_model=metadados_camera.get("camera"),
                image_width=imagem_rgb.shape[1],
            )
            geometria["unit"] = "m"
            geometria["metodo_metrologia"] = dim_res["metodo_metrologia"]
            geometria["detalhes_metrologia"] = dim_res["detalhes_metrologia"]
            geometria["height_meters"] = dim_res["height_meters"]
            geometria["mean_width_meters"] = dim_res["mean_width_meters"]
            geometria["max_diameter_meters"] = dim_res["max_diameter_meters"]
            geometria["min_diameter_meters"] = dim_res["min_diameter_meters"]
            geometria["projected_area_m2"] = dim_res["projected_area_m2"]
            geometria["aspect_ratio"] = dim_res["aspect_ratio"]
            geometria["scale_y_m_per_px"] = dim_res["scale_y_m_per_px"]
            geometria["length_metric"] = dim_res["height_meters"]
            geometria["width_metric"] = dim_res["max_diameter_meters"]
            geometria["mean_width_metric"] = dim_res["mean_width_meters"]
            geometria["area_metric"] = dim_res["projected_area_m2"]
            geometria["metric_ratio"] = dim_res["scale_y_m_per_px"]
            geometria["diameter_profile"] = dim_res["diameter_profile"]
            geometria["distancia_m"] = dist_m
        elif ref_height_meters is not None or metric_ratio is None:
            # MÉTODO 2: Geometria de Transferência Criminisi (ou calibração informada)
            h_ref = float(ref_height_meters) if ref_height_meters is not None else 1.0
            estimator_vp = VanishingGeometryEstimator()
            geom_res = estimator_vp.estimate(imagem_rgb)
            hz_y = geom_res["horizon_y_center"]
            vz = geom_res["vanishing_point_z"]

            ys_peca, _ = np.nonzero(segmentacao.mascara)
            if len(ys_peca):
                pts_y = (float(ys_peca.max()), float(ys_peca.min()))
            else:
                pts_y = (float(bbox_xyxy[3]), float(bbox_xyxy[1]))

            dim_res = p_engine.compute_real_dimensions(
                mask=segmentacao.mascara,
                horizon_y=hz_y,
                vz=vz,
                ref_height_meters=h_ref,
                ref_points_y=pts_y,
            )
            geometria["unit"] = "m"
            geometria["metodo_metrologia"] = dim_res.get("metodo_metrologia", "geometria_projetiva_criminisi")
            geometria["detalhes_metrologia"] = dim_res.get("detalhes_metrologia", f"Referência projetiva: {h_ref:.2f}m")
            geometria["height_meters"] = dim_res["height_meters"]
            geometria["mean_width_meters"] = dim_res["mean_width_meters"]
            geometria["max_diameter_meters"] = dim_res["max_diameter_meters"]
            geometria["min_diameter_meters"] = dim_res["min_diameter_meters"]
            geometria["projected_area_m2"] = dim_res["projected_area_m2"]
            geometria["aspect_ratio"] = dim_res["aspect_ratio"]
            geometria["scale_y_m_per_px"] = dim_res["scale_y_m_per_px"]
            geometria["horizon_y"] = hz_y
            geometria["ref_height_meters"] = h_ref
            geometria["length_metric"] = dim_res["height_meters"]
            geometria["width_metric"] = dim_res["max_diameter_meters"]
            geometria["mean_width_metric"] = dim_res["mean_width_meters"]
            geometria["area_metric"] = dim_res["projected_area_m2"]
            geometria["metric_ratio"] = dim_res["scale_y_m_per_px"]
            geometria["diameter_profile"] = dim_res["diameter_profile"]
        else:
            # Proporção métrica uniforme explícita (sem ref_height_meters)
            mr = float(metric_ratio)
            h_metric = float(geometria.get("length_metric", geometria["length_px"] * mr))
            w_max = float(geometria["width_px"]) * mr
            area_m2 = float(geometria["pixel_count"]) * (mr ** 2)
            mean_w = area_m2 / max(h_metric, 1e-6)
            geometria["height_meters"] = round(h_metric, 4)
            geometria["mean_width_meters"] = round(mean_w, 4)
            geometria["max_diameter_meters"] = round(w_max, 4)
            geometria["projected_area_m2"] = round(area_m2, 4)
            geometria["aspect_ratio"] = round(h_metric / max(mean_w, 1e-6), 2)
            geometria["scale_y_m_per_px"] = mr
    except Exception as e:
        registrar("pyron.metrologia_monocular_aviso", erro=str(e))

    tempos["geometria"] = (time.perf_counter() - inicio) * 1000

    inicio = time.perf_counter()
    mascara_termica = ajustar_mascara(segmentacao.mascara, np.asarray(matriz_termica).shape[:2])
    termica = estatisticas_termicas(matriz_termica, mascara_termica)
    tempos["termica"] = (time.perf_counter() - inicio) * 1000

    tempos = {k: round(v, 2) for k, v in tempos.items()}
    registrar(
        "pyron.ativo_analisado",
        score=round(segmentacao.score, 4),
        area_px=round(geometria["area_px"], 1),
        comprimento_px=round(geometria["length_px"], 1),
        t_max=round(termica.t_max, 2) if termica else None,
        tempos_ms=tempos,
    )
    return ResultadoAtivo(
        mascara=segmentacao.mascara,
        mascara_termica=mascara_termica,
        score=segmentacao.score,
        geometria=geometria,
        termica=termica,
        tempos_ms=tempos,
    )
