"""Testes unitários para o pipeline Grounded-SAM 2 + DINOv2 (NOCTIS, D-NOCTIS, DefectSAM, UniVAD C³ e SAM-LAD)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from nucleo import analise
from nucleo.classificacao.dinov2_engine import (
    DINOv2Classifier,
    calcular_anomalia_patches,
    similaridade_noctis,
)
from nucleo.detectores.sam2_dinov2 import (
    SAM2DINOv2Detector,
    calcular_consistencia_geometrica,
    fundir_scores_dnoctis,
    propor_caixas_grounding_dino,
)
from nucleo.pipeline.pyron_pipeline import isolar_hotspot_defectsam
from nucleo.segmentacao.sam2_engine import SAM2Segmentor


# ---------------------------------------------------------------- Fase 1: NOCTIS & AnomalyDINO


def test_similaridade_noctis_cyclic_thresholding():
    """Verifica que correspondências cíclicas consistentes têm score maior que colapsos repetitivos."""
    rng = np.random.default_rng(42)
    base = rng.normal(size=(16, 64)).astype(np.float32)
    base /= np.linalg.norm(base, axis=1, keepdims=True)

    # Caso 1: correspondência bijetora (1-para-1 com ruído leve)
    ruido = rng.normal(scale=0.03, size=base.shape).astype(np.float32)
    consulta_fiel = base + ruido
    score_fiel = similaridade_noctis(consulta_fiel, base, limiar_ciclico=0.65)
    assert score_fiel > 0.90

    # Caso 2: vetores ortogonais/aleatórios
    outro = rng.normal(size=(16, 64)).astype(np.float32)
    score_outro = similaridade_noctis(consulta_fiel, outro, limiar_ciclico=0.65)
    assert score_fiel > score_outro + 0.40


def test_anomalydino_knn_patches():
    """Verifica que patches anômalos elevam o score k-NN (AnomalyDINO) e localizam o patch defeituoso."""
    ref = np.zeros((32, 32), dtype=np.float32)
    for i in range(32):
        ref[i, i % 8] = 1.0

    # Peça saudável
    saudavel = ref.copy()
    res_ok = calcular_anomalia_patches(saudavel, ref, k=3)
    assert res_ok["score_anomalia"] == pytest.approx(0.0, abs=1e-4)

    # Peça com defeito estrutural severo no patch 19
    defeituosa = ref.copy()
    defeituosa[19] = 0.0
    defeituosa[19, 31] = -1.0
    res_def = calcular_anomalia_patches(defeituosa, ref, k=3)
    assert res_def["score_anomalia"] > 0.15
    assert res_def["patch_mais_anomalo"] == 19


def test_persistencia_galeria_npz_e_features_completas(tmp_path):
    """Testa extrair_features_completas, salvar_galeria e carregar_galeria em arquivo .npz."""

    class ModeloDINOComForwardFeatures(torch.nn.Module):
        def forward_features(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
            b = x.shape[0]
            h_p = x.shape[2] // 14
            w_p = x.shape[3] // 14
            n_p = h_p * w_p
            media = float(x.mean().item())
            cls_tok = torch.full((b, 384), media + 0.5, dtype=torch.float32)
            cls_tok[:, 0] = 1.0
            patches = torch.ones((b, n_p, 384), dtype=torch.float32) * 0.1
            patches[:, :, 0] = media + 1.0
            return {
                "x_norm_clstoken": cls_tok,
                "x_norm_patchtokens": patches,
            }

    clf = DINOv2Classifier(modelo=ModeloDINOComForwardFeatures(), dispositivo="cpu")
    img = np.full((224, 224, 3), 140, dtype=np.uint8)
    feats = clf.extrair_features_completas(img)
    assert feats["cls"].shape == (384,)
    assert feats["patches"].shape == (256, 384)
    assert feats["grid_size"] == (16, 16)

    arq_npz = tmp_path / "galeria_teste.npz"
    caminho_salvo = clf.salvar_galeria(arq_npz)
    assert caminho_salvo.is_file()

    clf2 = DINOv2Classifier(
        modelo=ModeloDINOComForwardFeatures(),
        dispositivo="cpu",
        prototipos={"isolador": np.ones(384, dtype=np.float32)},
    )
    assert clf2.carregar_galeria(arq_npz) is True
    assert "bucha" in clf2.prototipos
    assert "bucha" in clf2.prototipos_patches

    res_noctis = clf2.classificar(img, usar_noctis=True, peso_noctis=0.35)
    assert "classe" in res_noctis and "confianca" in res_noctis

    anom = clf2.avaliar_anomalia_estrutural(img, classe="isolador")
    assert "score_anomalia" in anom
    assert anom["grid_size"] == [16, 16]


# ---------------------------------------------------------------- Fase 2: D-NOCTIS (Consistência Geométrica 3D)


def test_dnoctis_desambigua_classes_por_geometria_3d():
    """Quando bucha e conexão têm scores visuais próximos, a altura métrica 3D desambigua."""
    scores_ambiguos = {
        "conexao": 0.42,
        "bucha": 0.40,
        "transformador": 0.18,
    }

    # Medição real indica peça esguia de 1,26 m de altura e razão de aspecto 3,6 (típica de bucha)
    res_bucha = fundir_scores_dnoctis(
        scores_ambiguos,
        altura_m=1.26,
        razao_aspecto=3.6,
        peso_geometrico=0.35,
    )
    assert res_bucha["classe"] == "bucha"
    assert res_bucha["consistencia_geometrica"]["bucha"] > res_bucha["consistencia_geometrica"]["conexao"]

    # Medição real indica peça compacta de 0,48 m e razão de aspecto 1,2 (típica de conexão)
    res_con = fundir_scores_dnoctis(
        scores_ambiguos,
        altura_m=0.48,
        razao_aspecto=1.2,
        peso_geometrico=0.35,
    )
    assert res_con["classe"] == "conexao"
    assert res_con["consistencia_geometrica"]["conexao"] > res_con["consistencia_geometrica"]["bucha"]


# ---------------------------------------------------------------- Fase 3: Grounding DINO + DefectSAM


class PreditorComPontosMock:
    """Preditor SAM 2 simulado que responde a prompts de caixa e de pontos (DefectSAM)."""

    def __init__(self):
        self.imagem = None
        self.chamadas_pontos = 0

    def set_image(self, image: np.ndarray) -> None:
        self.imagem = image

    def predict(self, *, point_coords=None, point_labels=None, box=None, multimask_output=False):
        h, w = self.imagem.shape[:2]
        mascara = np.zeros((h, w), dtype=np.float32)
        if point_coords is not None:
            self.chamadas_pontos += 1
            pts = np.asarray(point_coords)
            lbls = np.asarray(point_labels)
            pos = pts[lbls > 0]
            cx, cy = int(round(pos[0, 0])), int(round(pos[0, 1]))
            # Gera sub-máscara circular ao redor do ponto positivo (hotspot)
            yy, xx = np.ogrid[:h, :w]
            dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
            mascara[dist2 <= 6**2] = 1.0
            return np.stack([mascara]), np.array([0.94], dtype=np.float32), None

        x1, y1, x2, y2 = (int(round(v)) for v in box)
        mascara[max(0, y1):min(h, y2), max(0, x1):min(w, x2)] = 1.0
        return np.stack([mascara]), np.array([0.96], dtype=np.float32), None


def test_defectsam_isola_submascara_e_area_cm2():
    """Verifica que isolar_hotspot_defectsam extrai a mancha quente e calcula sua área em cm²."""
    h, w = 100, 100
    matriz = np.full((h, w), 30.0, dtype=np.float32)
    mascara_ativo = np.zeros((h, w), dtype=np.uint8)
    mascara_ativo[20:80, 30:70] = 1  # ativo de 60x40 = 2400 px
    # Hotspot concentrado em (50, 45)
    matriz[42:49, 47:54] = 85.0
    matriz[45, 50] = 92.0

    pred = PreditorComPontosMock()
    seg = SAM2Segmentor(preditor=pred)
    seg.set_frame(np.full((h, w, 3), 120, dtype=np.uint8))

    # Escala: 0,01 m/px = 1 cm/px -> cada pixel tem 1 cm²
    hs = isolar_hotspot_defectsam(
        matriz,
        mascara_ativo,
        segmentador=seg,
        metric_ratio_m_por_px=0.01,
        caixa_rgb=[30, 20, 70, 80],
    )
    assert hs is not None
    assert pred.chamadas_pontos == 1
    assert hs["x_max"] == 50 and hs["y_max"] == 45
    assert hs["t_max_hotspot"] == pytest.approx(92.0)
    assert 5 <= hs["area_hotspot_px"] <= 60
    assert hs["area_hotspot_cm2"] == pytest.approx(float(hs["area_hotspot_px"]), abs=0.1)
    assert 0.0 < hs["fracao_area_ativo"] < 0.05


def test_grounding_dino_propostas_e_detector_integrado(monkeypatch):
    """Testa propostas guiadas por texto no SAM2DINOv2Detector sem carregar pesos pesados."""
    img = np.full((120, 160, 3), 100, dtype=np.uint8)
    temp = np.full((120, 160), 28.0, dtype=np.float32)
    temp[20:100, 40:80] = 35.0
    temp[35:42, 55:62] = 72.0

    def _grounding_falso(rgb, limiar_caixa=0.25, limiar_texto=0.20):
        return [
            {
                "caixa": [40.0, 20.0, 80.0, 100.0],
                "score_dino": 0.89,
                "prompt": "electrical bushing",
                "classe_sugerida": "bucha",
            }
        ]

    propostas = propor_caixas_grounding_dino(img, detector_injetado=_grounding_falso)
    assert len(propostas) == 1
    assert propostas[0]["classe_sugerida"] == "bucha"

    class ClfMock:
        def classificar(self, rgb, bbox=None, mascara=None, usar_noctis=True):
            return {
                "classe": "bucha",
                "confianca": 0.91,
                "nome": "Bucha",
                "scores": {"bucha": 0.91, "isolador": 0.09},
            }

    monkeypatch.setattr(DINOv2Classifier, "obter_instancia", classmethod(lambda cls: ClfMock()))

    seg_mock = SAM2Segmentor(preditor=PreditorComPontosMock())
    det = SAM2DINOv2Detector(
        usar_grounding_dino=True,
        usar_noctis=True,
        usar_dnoctis=True,
        usar_defectsam=True,
        grounding_detector=_grounding_falso,
        segmentador_sam2=seg_mock,
    )
    regioes = det.detectar_com_metrologia(temp, img, metadados={"distancia_m": 5.0})
    assert len(regioes) >= 1
    bucha = regioes[0]
    assert bucha["classe"] == "bucha"
    assert "hotspot_defectsam" in bucha["segmentacao"]
    assert bucha["segmentacao"]["hotspot_defectsam"]["t_max_hotspot"] == pytest.approx(72.0)
    assert "consistencia_geometrica" in bucha["classificacao_dinov2"]


# ---------------------------------------------------------------- Fase 4: UniVAD C³ & SAM-LAD (Pareamento Trifásico)


def test_univad_samlad_agrupamento_trifasico_automatico():
    """Três buchas alinhadas têm as fases A, B, C atribuídas e a mais fria eleita como referência."""
    t = np.full((120, 180), 20.0, dtype=np.float32)
    # Fase A (esquerda): 32 °C | Fase B (meio, mais fria): 30 °C | Fase C (direita, defeito): 48 °C
    t[20:90, 20:40] = 32.0
    t[20:90, 80:100] = 30.0
    t[20:90, 140:160] = 48.0

    # Mesmo marcadas como classe genérica 'componente', possuem embeddings DINOv2 semelhantes
    emb_bucha = [1.0, 0.0, 0.0, 0.0]
    regioes = [
        {"id": "r_dir", "nome": "Bucha Dir", "classe": "componente", "caixa": [140, 20, 160, 90], "embedding_dinov2": emb_bucha},
        {"id": "r_esq", "nome": "Bucha Esq", "classe": "componente", "caixa": [20, 20, 40, 90], "embedding_dinov2": emb_bucha},
        {"id": "r_meio", "nome": "Bucha Meio", "classe": "componente", "caixa": [80, 20, 100, 90], "embedding_dinov2": emb_bucha},
    ]

    saida, resumo = analise.analisar_regioes(t, regioes)
    assert "pareamento_trifasico" in resumo
    assert len(resumo["pareamento_trifasico"]) == 1

    grupo = resumo["pareamento_trifasico"][0]
    assert grupo["trifasico"] is True
    assert grupo["referencia_fria"]["id"] == "r_meio"
    assert grupo["referencia_fria"]["t_max"] == pytest.approx(30.0)
    assert grupo["amplitude_termica_c"] == pytest.approx(18.0)

    # Ordenação espacial esquerda -> direita: r_esq (A), r_meio (B), r_dir (C)
    fases = {m["id"]: m["fase_estimada"] for m in grupo["membros"]}
    assert fases == {"r_esq": "A", "r_meio": "B", "r_dir": "C"}

    # Verifica que r_dir recebeu avaliação relativa por semelhantes graças ao agrupamento C³
    por_id = {r["id"]: r for r in saida}
    assert por_id["r_dir"]["ref_tipo"] == "semelhantes"
    assert por_id["r_dir"]["dt_corrigido"] == pytest.approx(16.0, abs=0.01)  # 48 - mediana(30, 32, 48)=32
    assert por_id["r_dir"]["severidade"] == "programar"
    assert por_id["r_dir"]["pareamento_homologo"]["dt_contra_fria_c"] == pytest.approx(18.0)
    assert por_id["r_dir"]["pareamento_homologo"]["score_anomalia_logica"] > 0.70
