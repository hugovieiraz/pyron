"""Detector automático de ativos elétricos com modelos fundacionais (Grounding DINO + SAM 2 + DINOv2 + Criminisi).

Pipeline:
1. Grounding DINO (Open-Vocabulary) / SAM 2 (AutomaticMaskGenerator): descobre propostas de regiões e máscaras de ativos.
2. DINOv2 (ViT) + NOCTIS (Cyclic Thresholding): classifica cada ativo com correspondência global e de patches.
3. Geometria Projetiva (Criminisi / Telemetria) + D-NOCTIS: calcula altura H, diâmetro e pondera score geométrico 3D.
4. Termografia Isolada + DefectSAM: extrai Tmáx, Tmed e isola a sub-máscara e área exata (cm²) de hotspots.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np
import torch

from nucleo.detectores import Deteccao, Detector
from nucleo.detectores.pontos_quentes import PontosQuentes

log = logging.getLogger(__name__)

CLASSES_ATIVOS = [
    "bucha",
    "isolador",
    "para_raio",
    "transformador",
    "conexao",
    "radiador",
    "cabo",
]

NOMES_ATIVOS = {
    "bucha": "Bucha",
    "isolador": "Isolador",
    "para_raio": "Para-raio",
    "transformador": "Transformador",
    "conexao": "Conexão",
    "radiador": "Radiador",
    "cabo": "Condutor/Cabo",
    "tanque": "Tanque",
    "estrutura": "Estrutura",
    "ponto_quente": "Ponto quente",
}

PADROES_ALTURA = {
    "isolador": 0.80,
    "bucha": 1.25,
    "para_raio": 1.20,
    "transformador": 1.60,
    "conexao": 0.50,
    "radiador": 1.20,
    "cabo": 1.00,
    "tanque": 1.60,
    "estrutura": 2.50,
}

PADROES_RAZAO_ASPECTO = {
    "isolador": 2.8,
    "bucha": 3.5,
    "para_raio": 4.2,
    "transformador": 1.1,
    "conexao": 1.2,
    "radiador": 2.2,
    "cabo": 5.5,
    "tanque": 1.1,
    "estrutura": 3.0,
}

PROMPTS_GROUNDING_DINO: dict[str, str] = {
    "electrical bushing": "bucha",
    "ceramic insulator": "isolador",
    "surge arrester": "para_raio",
    "power transformer": "transformador",
    "metal clamp connector": "conexao",
    "cooling radiator": "radiador",
    "overhead power cable": "cabo",
}


def calcular_iou_boxes(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    """Calcula sobreposição máxima (IoU ou contenção) entre duas caixas [x0, y0, x1, y1]."""
    x_esq = max(box_a[0], box_b[0])
    y_topo = max(box_a[1], box_b[1])
    x_dir = min(box_a[2], box_b[2])
    y_fundo = min(box_a[3], box_b[3])

    if x_dir <= x_esq or y_fundo <= y_topo:
        return 0.0

    intersecao = (x_dir - x_esq) * (y_fundo - y_topo)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    uniao = area_a + area_b - intersecao
    iou = intersecao / max(uniao, 1e-6)
    contencao = intersecao / max(min(area_a, area_b), 1e-6)
    return max(iou, contencao)


def simplificar_contorno_binario(mascara: np.ndarray, epsilon: float = 1.0) -> list[list[float]]:
    """Extrai contorno vetorial simplificado para renderização SVG com fechamento morfológico anti-ruído."""
    binaria = (np.asarray(mascara) > 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
    contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return []
    maior = max(contornos, key=cv2.contourArea)
    aproximado = cv2.approxPolyDP(maior, epsilon=epsilon, closed=True)
    return [[float(p[0][0]), float(p[0][1])] for p in aproximado]


def calcular_consistencia_geometrica(
    altura_m: float | None,
    razao_aspecto: float | None,
    classe: str,
    sigma_h: float = 0.65,
    sigma_ar: float = 1.8,
) -> float:
    """Calcula o score de consistência geométrica 3D/métrica segundo D-NOCTIS (BMVC 2025).

    Compara a altura física medida (H_medido em metros) e a razão de aspecto (H/W) com o
    gabarito dimensional canônico da classe elétrica candidata.
    """
    h_ref = PADROES_ALTURA.get(classe, 1.0)
    ar_ref = PADROES_RAZAO_ASPECTO.get(classe, 2.0)

    penalidade = 0.0
    peso_total = 0.0

    if altura_m is not None and float(altura_m) > 0:
        erro_rel_h = abs(float(altura_m) - h_ref) / max(sigma_h * max(h_ref, 0.30), 1e-4)
        penalidade += 0.65 * erro_rel_h
        peso_total += 0.65

    if razao_aspecto is not None and float(razao_aspecto) > 0:
        ar_val = max(float(razao_aspecto), 0.1)
        erro_log_ar = abs(math.log(ar_val / max(ar_ref, 0.1))) / max(sigma_ar, 1e-4)
        penalidade += 0.35 * erro_log_ar
        peso_total += 0.35

    if peso_total <= 0.0:
        return 1.0

    penalidade_norm = penalidade / peso_total
    return float(np.clip(math.exp(-penalidade_norm), 0.01, 1.0))


def fundir_scores_dnoctis(
    scores_visuais: dict[str, float],
    altura_m: float | None = None,
    razao_aspecto: float | None = None,
    peso_geometrico: float = 0.30,
    estatisticas_termicas: Any | None = None,
    usar_laya: bool = True,
) -> dict[str, Any]:
    """Funde as probabilidades visuais DINOv2 com o score de consistência geométrica 3D (D-NOCTIS) e LAYA.

    Permite desambiguar componentes com textura semelhante mas escalas métricas distintas
    (ex.: conector de 0,50 m vs. bucha de 1,25 m vs. transformador de 1,60 m).
    Quando ``usar_laya=True`` (padrão), utiliza o motor adaptativo ``fundir_modalidades_laya``.
    """
    if not scores_visuais:
        return {
            "classe": "isolador",
            "confianca": 0.0,
            "nome": "Isolador",
            "scores": {},
            "consistencia_geometrica": {},
        }

    scores_geom: dict[str, float] = {}
    for c in scores_visuais:
        s_g = calcular_consistencia_geometrica(altura_m, razao_aspecto, c)
        scores_geom[c] = round(s_g, 4)

    if usar_laya:
        try:
            from nucleo.classificacao.laya_aggregator import fundir_modalidades_laya

            res_laya = fundir_modalidades_laya(
                scores_visuais=scores_visuais,
                scores_geometricos=scores_geom if (altura_m is not None or razao_aspecto is not None) else None,
                estatisticas_termicas=estatisticas_termicas,
                tem_telemetria_3d=bool(altura_m is not None and float(altura_m) > 0),
            )
            cls_final = res_laya["classe"]
            return {
                "classe": cls_final,
                "confianca": round(float(res_laya["confianca"]), 4),
                "nome": NOMES_ATIVOS.get(cls_final, cls_final.capitalize()),
                "scores": res_laya["scores"],
                "consistencia_geometrica": scores_geom,
                "pesos_modalidades": res_laya.get("pesos_modalidades", {}),
                "laya": res_laya.get("laya", {}),
            }
        except Exception as erro:
            log.debug("Fallback de fundir_modalidades_laya para fusao linear dnoctis: %s", erro)

    lam = float(np.clip(peso_geometrico, 0.0, 0.85))
    if altura_m is None and razao_aspecto is None:
        lam = 0.0

    scores_combinados: dict[str, float] = {}
    for c, s_vis in scores_visuais.items():
        s_g = scores_geom[c]
        scores_combinados[c] = (1.0 - lam) * float(s_vis) + lam * s_g

    soma = sum(scores_combinados.values())
    if soma > 0:
        scores_norm = {c: round(v / soma, 4) for c, v in scores_combinados.items()}
    else:
        scores_norm = {c: round(float(v), 4) for c, v in scores_visuais.items()}

    melhor_classe = max(scores_norm, key=lambda k: scores_norm[k])
    melhor_conf = float(scores_norm[melhor_classe])

    return {
        "classe": melhor_classe,
        "confianca": round(melhor_conf, 4),
        "nome": NOMES_ATIVOS.get(melhor_classe, melhor_classe.capitalize()),
        "scores": scores_norm,
        "consistencia_geometrica": scores_geom,
    }


def propor_caixas_grounding_dino(
    imagem_rgb: np.ndarray,
    limiar_caixa: float = 0.25,
    limiar_texto: float = 0.20,
    modelo_id: str = "IDEA-Research/grounding-dino-tiny",
    dispositivo: str | None = None,
    detector_injetado: Any | None = None,
) -> list[dict[str, Any]]:
    """Gera propostas de caixas delimitadoras guiadas por texto via Grounding DINO (Apache 2.0).

    Se ``detector_injetado`` for fornecido (ex.: em testes unitários), delega diretamente a ele.
    Caso o modelo ``IDEA-Research/grounding-dino-tiny`` não esteja disponível localmente no cache
    do ``transformers``, retorna lista vazia de forma silenciosa para acionar o fallback SAM 2.
    """
    rgb = np.asarray(imagem_rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return []

    if detector_injetado is not None:
        return list(detector_injetado(rgb, limiar_caixa=limiar_caixa, limiar_texto=limiar_texto))

    try:
        from PIL import Image
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        dev = dispositivo or ("cuda" if torch.cuda.is_available() else "cpu")
        processor = AutoProcessor.from_pretrained(modelo_id, local_files_only=True)
        model = AutoModelForZeroShotObjectDetection.from_pretrained(modelo_id, local_files_only=True).to(dev)
        model.eval()

        texto_prompt = ". ".join(PROMPTS_GROUNDING_DINO.keys()) + "."
        pil_img = Image.fromarray(rgb)
        inputs = processor(images=pil_img, text=texto_prompt, return_tensors="pt").to(dev)

        with torch.no_grad():
            outputs = model(**inputs)

        resultados = processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=limiar_caixa,
            text_threshold=limiar_texto,
            target_sizes=[pil_img.size[::-1]],
        )[0]

        propostas: list[dict[str, Any]] = []
        boxes = resultados["boxes"].detach().cpu().numpy()
        scores = resultados["scores"].detach().cpu().numpy()
        labels = resultados.get("text_labels") or resultados.get("labels") or []

        for box, score, label in zip(boxes, scores, labels):
            rotulo_str = str(label).strip().lower()
            classe_sugerida = "isolador"
            for chave_prompt, cls_pyron in PROMPTS_GROUNDING_DINO.items():
                if chave_prompt in rotulo_str or rotulo_str in chave_prompt:
                    classe_sugerida = cls_pyron
                    break
            propostas.append({
                "caixa": [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                "score_dino": float(score),
                "prompt": rotulo_str,
                "classe_sugerida": classe_sugerida,
            })
        return propostas
    except Exception as e:
        log.debug("Grounding DINO local indisponível (%s); usando fallback AutomaticMaskGenerator.", e)
        return []


class SAM2DINOv2Detector(Detector):
    """Detector fundacional automático: Grounding DINO + SAM 2 + DINOv2 (NOCTIS / D-NOCTIS) + DefectSAM."""

    def __init__(
        self,
        caminho_pesos_sam2: Path | str | None = None,
        conf_minima: float = 0.40,
        iou_nms: float = 0.45,
        usar_grounding_dino: bool = True,
        usar_noctis: bool = True,
        usar_dnoctis: bool = True,
        usar_defectsam: bool = True,
        usar_laya: bool = True,
        grounding_detector: Any | None = None,
        segmentador_sam2: Any | None = None,
    ) -> None:
        self.id = "sam2-dinov2"
        self.nome = "SAM 2 + DINOv2 (Identificação e Metrologia Automática)"
        self.tipo = "aprendizado"
        self.arquitetura = "Grounded-SAM 2 (Hiera) + DINOv2 (NOCTIS/D-NOCTIS) + Criminisi Metrology"
        self.descricao = (
            "Descobre e segmenta os ativos elétricos da subestação automaticamente com Grounded-SAM 2, "
            "classifica com DINOv2 (NOCTIS/D-NOCTIS) e calcula dimensões físicas reais e pureza térmica."
        )
        self.classes = CLASSES_ATIVOS + ["ponto_quente"]
        self.nomes = NOMES_ATIVOS
        self.precisa_imagem = True
        self.conf_minima = conf_minima
        self.iou_nms = iou_nms
        self.usar_grounding_dino = usar_grounding_dino
        self.usar_noctis = usar_noctis
        self.usar_dnoctis = usar_dnoctis
        self.usar_defectsam = usar_defectsam
        self.usar_laya = usar_laya
        self._grounding_detector = grounding_detector
        self._segmentador_sam2 = segmentador_sam2
        self._caminho_pesos = Path(caminho_pesos_sam2) if caminho_pesos_sam2 else Path("modelos/sam2/sam2.1_hiera_small.pt")
        self._mask_generator = None
        self.cartao = {
            "treino": "Grounding DINO + SAM 2 (Meta AI) + DINOv2 ViT (Meta AI) em escala fundacional",
            "parametros": {
                "conf_minima": conf_minima,
                "iou_nms": iou_nms,
                "usar_grounding_dino": usar_grounding_dino,
                "usar_noctis": usar_noctis,
                "usar_dnoctis": usar_dnoctis,
                "usar_defectsam": usar_defectsam,
            },
            "vantagens": [
                "Identificação e segmentação de ativos inteiros sem depender de caixa manual.",
                "Classificação zero-shot/few-shot com representações DINOv2 + NOCTIS Cyclic Thresholding.",
                "Desambiguação métrica 3D via D-NOCTIS e isolamento de área de hotspot via DefectSAM.",
            ],
            "limitacoes": [
                "Demanda GPU CUDA para inferência ágil (segundos por imagem).",
            ],
        }

    def _obter_generator(self):
        if self._mask_generator is not None:
            return self._mask_generator

        from sam2.build_sam import build_sam2
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

        dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        cfg = "configs/sam2.1/sam2.1_hiera_s.yaml"
        sam2 = build_sam2(cfg, str(self._caminho_pesos), device=dispositivo)
        self._mask_generator = SAM2AutomaticMaskGenerator(
            sam2,
            points_per_side=16,
            pred_iou_thresh=0.75,
            stability_score_thresh=0.85,
            min_mask_region_area=3500,
        )
        return self._mask_generator

    def _obter_segmentador_caixa(self):
        if self._segmentador_sam2 is not None:
            return self._segmentador_sam2
        from nucleo.segmentacao.sam2_engine import SAM2Segmentor

        self._segmentador_sam2 = SAM2Segmentor(checkpoint=self._caminho_pesos)
        return self._segmentador_sam2

    def _gerar_mascaras_candidatas(self, rgb: np.ndarray) -> list[dict[str, Any]]:
        """Tenta propostas guiadas por texto via Grounding DINO + SAM2Segmentor; fallback para AutomaticMaskGenerator."""
        if self.usar_grounding_dino:
            propostas = propor_caixas_grounding_dino(
                rgb,
                detector_injetado=self._grounding_detector,
            )
            if propostas:
                try:
                    seg = self._obter_segmentador_caixa()
                    seg.set_frame(rgb)
                    mascaras_guiadas: list[dict[str, Any]] = []
                    for prop in propostas:
                        cx = prop["caixa"]
                        res_seg = seg.segmentar(cx)
                        x0, y0, x1, y1 = res_seg.caixa
                        mascaras_guiadas.append({
                            "segmentation": res_seg.mascara,
                            "area": int(res_seg.mascara.sum()),
                            "bbox": [x0, y0, x1 - x0, y1 - y0],
                            "predicted_iou": float(res_seg.score),
                            "proposta_grounding": prop,
                        })
                    if mascaras_guiadas:
                        return mascaras_guiadas
                except Exception as e:
                    log.warning("Fallback de Grounding DINO + SAM2Segmentor para AutomaticMaskGenerator: %s", e)

        generator = self._obter_generator()
        try:
            return generator.generate(rgb)
        except Exception as e:
            log.warning("Falha no SAM2AutomaticMaskGenerator: %s. Utilizando fallback.", e)
            return []

    def detectar(
        self,
        temperatura: np.ndarray,
        imagem: np.ndarray | None = None,
        metadados: dict | None = None,
    ) -> list[Deteccao]:
        """Detecta ativos elétricos na imagem e retorna caixas com classes e metadados completos."""
        regioes = self.detectar_com_metrologia(temperatura, imagem, metadados=metadados)
        return [Deteccao(classe=r["classe"], caixa=r["caixa"], confianca=r["confianca"]) for r in regioes]

    def detectar_com_metrologia(
        self,
        temperatura: np.ndarray,
        imagem: np.ndarray | None = None,
        metadados: dict | None = None,
    ) -> list[dict]:
        """Executa a detecção completa com máscaras SAM 2, classificações DINOv2 e metrologia projetiva."""
        from nucleo.classificacao.dinov2_engine import DINOv2Classifier
        from nucleo.metrologia.vanishing_points import VanishingGeometryEstimator
        from nucleo.metrologia.criminisi_metrology import ProjectiveMetrologyEngine
        from nucleo.pipeline.pyron_pipeline import estatisticas_termicas, isolar_hotspot_defectsam

        if imagem is None:
            from nucleo import render

            imagem = render.colorir(temperatura, nome="ferro")

        rgb = np.asarray(imagem)
        matriz = np.asarray(temperatura)
        h_rgb, w_rgb = rgb.shape[:2]
        h_mat, w_mat = matriz.shape[:2]
        area_total = h_rgb * w_rgb

        # 1. Geração de propostas de máscaras (Grounding DINO + SAM 2 ou AutomaticMaskGenerator)
        raw_masks = self._gerar_mascaras_candidatas(rgb)

        clf = DINOv2Classifier.obter_instancia()
        p_engine = ProjectiveMetrologyEngine(default_unit="m")

        # Geometria projetiva da cena (pontos de fuga e horizonte)
        try:
            vp_est = VanishingGeometryEstimator()
            geom_res = vp_est.estimate(rgb)
            hz_y = geom_res["horizon_y_center"]
            vz = geom_res["vanishing_point_z"]
        except Exception:
            hz_y = float(h_rgb * 2.0)
            vz = (float(w_rgb / 2.0), -10000.0)

        # 2. Filtragem, classificação DINOv2 (+ NOCTIS) e medição dos ativos candidatos
        candidatos = []
        for m_item in raw_masks:
            mask = m_item["segmentation"].astype(np.uint8)
            area = int(m_item["area"])
            bbox_xywh = [int(v) for v in m_item["bbox"]]
            x0, y0, w, h = bbox_xywh
            x1, y1 = x0 + w, y0 + h
            caixa_rgb = [float(x0), float(y0), float(x1), float(y1)]

            # Descarta máscaras que cobrem quase toda a imagem ou ruídos desproporcionais (sensibilidade adaptativa)
            area_min = max(80, int(area_total * 0.002))
            area_max = int(area_total * 0.88)
            if area > area_max or area < area_min:
                continue

            # Classificação DINOv2 com máscara e NOCTIS Cyclic Thresholding opcional
            try:
                res_dino = clf.classificar(rgb, bbox=caixa_rgb, mascara=mask, usar_noctis=self.usar_noctis)
            except TypeError:
                res_dino = clf.classificar(rgb, bbox=caixa_rgb, mascara=mask)

            classe = res_dino["classe"]
            conf = float(res_dino["confianca"])

            # Descarta ruídos de baixa confiança ou falsos pontos quentes
            if conf < self.conf_minima or classe in ("ponto_quente", "fundo"):
                continue

            candidatos.append({
                "mask_rgb": mask,
                "caixa_rgb": caixa_rgb,
                "area_px": area,
                "classe": classe,
                "nome_classe": res_dino["nome"],
                "confianca": conf,
                "scores": res_dino.get("scores", {}),
                "score_sam2": float(m_item.get("predicted_iou", 0.95)),
                "proposta_grounding": m_item.get("proposta_grounding"),
            })

        # 3. Non-Maximum Suppression (NMS) baseado em IoU e confiança
        candidatos.sort(key=lambda x: (x["confianca"] * ((x["caixa_rgb"][3] - x["caixa_rgb"][1]) / max(x["caixa_rgb"][2] - x["caixa_rgb"][0], 1))), reverse=True)
        selecionados = []
        for cand in candidatos:
            sobreposto = False
            for sel in selecionados:
                iou = calcular_iou_boxes(cand["caixa_rgb"], sel["caixa_rgb"])
                if iou > self.iou_nms:
                    sobreposto = True
                    break
            if not sobreposto:
                selecionados.append(cand)

        # 4. Enriquecimento de cada ativo com contorno SVG, metrologia, D-NOCTIS e DefectSAM
        sx = w_mat / w_rgb
        sy = h_mat / h_rgb
        regioes_finais = []
        contagem: dict[str, int] = {}

        dist_m = None
        if metadados:
            try:
                d = metadados.get("distancia_m")
                if d is not None and float(d) > 0:
                    dist_m = float(d)
            except (ValueError, TypeError):
                dist_m = None

        for sel in selecionados:
            classe = sel["classe"]
            mask_rgb = sel["mask_rgb"]
            h_ref = PADROES_ALTURA.get(classe, 1.0)

            ys, _ = np.nonzero(mask_rgb)
            pts_y = (float(ys.max()), float(ys.min())) if len(ys) else (sel["caixa_rgb"][3], sel["caixa_rgb"][1])

            # Metrologia Inteligente (Método 1: Telemetria Óptica prioritária; Método 2: Geometria Projetiva)
            if dist_m:
                dim_res = p_engine.compute_dimensions_from_telemetry(
                    mask=mask_rgb,
                    distance_m=dist_m,
                    camera_model=metadados.get("camera") if metadados else None,
                    image_width=w_rgb,
                )
            else:
                dim_res = p_engine.compute_real_dimensions(
                    mask=mask_rgb,
                    horizon_y=hz_y,
                    vz=vz,
                    ref_height_meters=h_ref,
                    ref_points_y=pts_y,
                )

            # Redimensiona máscara e caixa para coordenadas da matriz térmica
            if (w_mat, h_mat) != (w_rgb, h_rgb):
                mask_mat = cv2.resize(mask_rgb, (w_mat, h_mat), interpolation=cv2.INTER_NEAREST)
                caixa_mat = [
                    round(sel["caixa_rgb"][0] * sx, 2),
                    round(sel["caixa_rgb"][1] * sy, 2),
                    round(sel["caixa_rgb"][2] * sx, 2),
                    round(sel["caixa_rgb"][3] * sy, 2),
                ]
            else:
                mask_mat = mask_rgb
                caixa_mat = [round(v, 2) for v in sel["caixa_rgb"]]

            # Pureza térmica dentro do ativo
            stat_termica = estatisticas_termicas(matriz, mask_mat)

            # Fusão D-NOCTIS e LAYA Multimodal (Visual + Consistência Geométrica 3D + Térmica)
            consistencia_geom = {}
            fusao_laya_diag = {}
            fusao_pesos_mod = {}
            if self.usar_dnoctis and sel.get("scores"):
                altura_independente = float(dim_res["height_meters"]) if dist_m else None
                ar_medido = float(dim_res.get("aspect_ratio", 0.0)) or None
                fusao = fundir_scores_dnoctis(
                    sel["scores"],
                    altura_m=altura_independente,
                    razao_aspecto=ar_medido,
                    peso_geometrico=0.30 if dist_m else 0.15,
                    estatisticas_termicas=stat_termica,
                    usar_laya=self.usar_laya,
                )
                classe = fusao["classe"]
                sel["classe"] = classe
                sel["nome_classe"] = fusao["nome"]
                sel["confianca"] = fusao["confianca"]
                sel["scores"] = fusao["scores"]
                consistencia_geom = fusao.get("consistencia_geometrica", {})
                fusao_laya_diag = fusao.get("laya", {})
                fusao_pesos_mod = fusao.get("pesos_modalidades", {})
                h_ref = PADROES_ALTURA.get(classe, h_ref)

            contagem[classe] = contagem.get(classe, 0) + 1

            # Contorno SVG no espaço da matriz
            contorno = simplificar_contorno_binario(mask_mat, epsilon=1.0)

            # DefectSAM: sub-segmentação da mancha térmica (hotspot) dentro do ativo
            hotspot_info = None
            if self.usar_defectsam and stat_termica is not None:
                hs_bruto = isolar_hotspot_defectsam(
                    matriz,
                    mask_mat,
                    segmentador=self._segmentador_sam2,
                    metric_ratio_m_por_px=dim_res.get("scale_y_m_per_px"),
                    caixa_rgb=sel["caixa_rgb"],
                    forma_rgb=(h_rgb, w_rgb),
                )
                if hs_bruto is not None:
                    hotspot_info = {k: v for k, v in hs_bruto.items() if k != "mascara_hotspot"}

            geometria = {
                "unit": "m",
                "metodo_metrologia": dim_res.get("metodo_metrologia", "telemetria_optica" if dist_m else "geometria_projetiva_criminisi"),
                "detalhes_metrologia": dim_res.get("detalhes_metrologia", f"Referência projetiva: {h_ref:.2f}m"),
                "height_meters": dim_res["height_meters"],
                "mean_width_meters": dim_res["mean_width_meters"],
                "max_diameter_meters": dim_res["max_diameter_meters"],
                "min_diameter_meters": dim_res["min_diameter_meters"],
                "projected_area_m2": dim_res["projected_area_m2"],
                "aspect_ratio": dim_res["aspect_ratio"],
                "scale_y_m_per_px": dim_res["scale_y_m_per_px"],
                "ref_height_meters": h_ref,
                "distancia_m": dist_m,
                "length_metric": dim_res["height_meters"],
                "width_metric": dim_res["max_diameter_meters"],
                "mean_width_metric": dim_res["mean_width_meters"],
                "area_metric": dim_res["projected_area_m2"],
                "metric_ratio": dim_res["scale_y_m_per_px"],
                "diameter_profile": dim_res.get("diameter_profile"),
                "area_px": float(mask_mat.sum()),
                "length_px": float(ys.max() - ys.min() + 1) * sy if len(ys) else 0.0,
            }

            regioes_finais.append({
                "id": None,
                "nome": f"{sel['nome_classe']} {contagem[classe]}",
                "classe": classe,
                "caixa": caixa_mat,
                "confianca": round(sel["confianca"], 4),
                "origem": "detector:sam2_dinov2",
                "segmentacao": {
                    "score": round(sel["score_sam2"], 4),
                    "geometria": geometria,
                    "termica_isolada": asdict(stat_termica) if stat_termica else None,
                    "hotspot_defectsam": hotspot_info,
                    "contorno": contorno,
                },
                "classificacao_dinov2": {
                    "classe": classe,
                    "confianca": round(sel["confianca"], 4),
                    "nome": sel["nome_classe"],
                    "scores": sel["scores"],
                    "consistencia_geometrica": consistencia_geom,
                    "pesos_modalidades": fusao_pesos_mod,
                    "laya": fusao_laya_diag,
                },
            })

        # 5. Adiciona pontos quentes pontuais encontrados pela regra térmica (se não contidos em ativo)
        det_termico = PontosQuentes()
        pontos_quentes = det_termico.detectar(matriz, imagem)
        for pq in pontos_quentes:
            cx = (pq.caixa[0] + pq.caixa[2]) / 2.0
            cy = (pq.caixa[1] + pq.caixa[3]) / 2.0

            # Verifica se já está coberto por algum ativo detectado
            contido = False
            for reg in regioes_finais:
                bx = reg["caixa"]
                if bx[0] <= cx <= bx[2] and bx[1] <= cy <= bx[3]:
                    contido = True
                    break

            if not contido:
                regioes_finais.append({
                    "id": None,
                    "nome": f"Ponto quente {len(regioes_finais) + 1}",
                    "classe": "ponto_quente",
                    "caixa": [round(v, 2) for v in pq.caixa],
                    "confianca": round(pq.confianca, 2),
                    "origem": "modelo:pontos-quentes",
                })

        return regioes_finais
