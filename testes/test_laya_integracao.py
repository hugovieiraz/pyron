"""Testes unitários e de integração para o motor LAYA no Pyron.

Valida as 5 etapas de agregação e decisão calibrada:
1. Motor LAYAHead (atenção multi-camada ViT e atribuição de profundidade);
2. Calibração RLCD / Conformal (Jev confidence, prediction_set, ECE, temperature scaling);
3. Agregação espacial de patches (NOCTIS + LAYA anti-reflexo solar);
4. Fusão multimodal adaptativa (Visual + Geometria 3D + Radiometria IR);
5. Consenso temporal multi-frame em keyframes de vídeo e arbitragem normativa NBR 15866.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from nucleo.classificacao.laya_aggregator import (
    LAYA_PACOTE_DISPONIVEL,
    LAYAHead,
    agregar_keyframes_laya,
    agregar_patches_laya,
    arbitrar_severidade_normativa_laya,
    calibrar_temperatura_laya,
    calcular_ece,
    calcular_entropia_confianca,
    calcular_jev_confidence,
    conjunto_preditivo_conformal,
    fundir_modalidades_laya,
    laya_disponivel,
    resumir_atribuicao_camadas,
)
from nucleo.classificacao.dinov2_engine import DINOv2Classifier
from nucleo.detectores.sam2_dinov2 import fundir_scores_dnoctis
from nucleo.medicao.video_keyframes import agregar_medicoes
from nucleo.analise import analisar_regioes


# ---------------------------------------------------------------- 1. LAYAHead & Atribuição de Profundidade


def test_laya_head_forward_e_normalizacao():
    d_model = 384
    num_layers = 4
    head = LAYAHead(d_model=d_model, num_layers=num_layers, temperatura=1.0)
    head.eval()

    # Teste com batch [2, 4, 384]
    estados = torch.randn(2, num_layers, d_model)
    emb, pesos = head(estados)

    assert emb.shape == (2, d_model)
    assert pesos.shape == (2, num_layers)

    # Verifica norma unitária L2
    normas = torch.norm(emb, p=2, dim=-1)
    assert torch.allclose(normas, torch.ones_like(normas), atol=1e-5)

    # Verifica se os pesos de atenção somam 1.0 por amostra
    soma_pesos = torch.sum(pesos, dim=-1)
    assert torch.allclose(soma_pesos, torch.ones_like(soma_pesos), atol=1e-5)

    # Teste com tensor 2D [4, 384] (amostra única)
    emb_single, pesos_single = head(estados[0])
    assert emb_single.shape == (d_model,)
    assert pesos_single.shape == (num_layers,)
    assert math_close(float(torch.norm(emb_single, p=2).item()), 1.0)
    assert math_close(float(torch.sum(pesos_single).item()), 1.0)


def test_resumir_atribuicao_camadas():
    pesos = [0.10, 0.25, 0.35, 0.30]
    resumo = resumir_atribuicao_camadas(pesos)
    assert "rasas_textura" in resumo
    assert "intermediarias_periodicidade" in resumo
    assert "profundas_semantica" in resumo
    assert resumo["camada_dominante"] == 2
    assert math_close(resumo["rasas_textura"] + resumo["intermediarias_periodicidade"] + resumo["profundas_semantica"], 1.0)


# ---------------------------------------------------------------- 2. Jev Confidence, Conformal Sets & Calibração


def test_calcular_jev_confidence():
    # Caso 1: Certeza absoluta
    p_certo = {"isolador": 1.0, "bucha": 0.0, "transformador": 0.0}
    assert calcular_jev_confidence(p_certo, tipo="choice") == 1.0

    # Caso 2: Totalmente uniforme (n=3, p=0.333...) -> confiança deve ser 0.0
    p_unif = {"isolador": 1.0 / 3, "bucha": 1.0 / 3, "transformador": 1.0 / 3}
    assert math_close(calcular_jev_confidence(p_unif, tipo="choice"), 0.0, atol=1e-3)

    # Caso 3: Alta confiança calibrada
    p_alto = {"bucha": 0.85, "isolador": 0.10, "transformador": 0.05}
    jev = calcular_jev_confidence(p_alto, tipo="choice")
    assert 0.70 <= jev <= 0.85


def test_conjunto_preditivo_conformal_e_roteamento():
    # Caso A: Decisão nítida -> rota "auto", prediction_set com 1 elemento
    p_nitida = {"transformador": 0.92, "tanque": 0.05, "radiador": 0.03}
    dec_a = conjunto_preditivo_conformal(p_nitida, alpha=0.10, limiar_precisao=0.60)
    assert dec_a["choice"] == "transformador"
    assert dec_a["prediction_set"] == ["transformador"]
    assert dec_a["abstain"] is False
    assert dec_a["route"] == "auto"

    # Caso B: Decisão ambígua (zona cinzenta bucha vs para-raio) -> rota "review", prediction_set com 2 elementos
    p_ambigua = {"bucha": 0.48, "para_raio": 0.44, "isolador": 0.08}
    dec_b = conjunto_preditivo_conformal(p_ambigua, alpha=0.10, limiar_precisao=0.60)
    assert len(dec_b["prediction_set"]) >= 2
    assert "bucha" in dec_b["prediction_set"]
    assert "para_raio" in dec_b["prediction_set"]
    assert dec_b["route"] == "review"

    # Caso C: Fora da distribuição (OOD / unbound) -> rota "review"
    dec_c = conjunto_preditivo_conformal(p_nitida, similaridade_max=0.12, limiar_ood=0.22)
    assert dec_c["unbound"] is True
    assert dec_c["route"] == "review"


def test_calibrar_temperatura_laya_reduz_ece():
    np.random.seed(42)
    # Simula logits sobre-confiantes (temperatura verdadeira ~1.8)
    n = 200
    classes = 4
    logits = np.random.randn(n, classes) * 3.5
    exp_z = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probs = exp_z / np.sum(exp_z, axis=1, keepdims=True)
    targets = np.array([np.random.choice(classes, p=p) for p in probs])

    res = calibrar_temperatura_laya(logits, targets, temperatura_inicial=0.25)
    assert res["temperatura_otima"] > 0.5
    assert res["ece_depois"] <= res["ece_antes"] + 1e-4


# ---------------------------------------------------------------- 3. Agregação de Patches Espaciais (NOCTIS + LAYA)


def test_agregar_patches_laya_reflexo_solar():
    nq = 16
    np_patches = 8
    dim = 64
    np.random.seed(123)
    q = np.random.randn(nq, dim).astype(np.float32)
    proto = np.random.randn(np_patches, dim).astype(np.float32)

    # 1. Simula cenário normal sem reflexo solar
    res_normal = agregar_patches_laya(q, proto)
    assert "similaridade" in res_normal
    assert "score_anomalia" in res_normal
    assert res_normal["fator_reflexo_solar"] == 0.0
    assert len(res_normal["pesos_atencao"]) == nq

    # 2. Simula pico de temperatura pontual isolado (artefato/reflexo)
    temperaturas = np.full(nq, 25.0, dtype=np.float32)
    temperaturas[3] = 95.0  # pico isolado no patch 3
    res_reflexo = agregar_patches_laya(q, proto, temperaturas_patches=temperaturas)
    assert res_reflexo["fator_reflexo_solar"] > 0.40
    # O patch com pico de reflexo deve ter peso reduzido na agregação
    assert res_reflexo["pesos_atencao"][3] < res_normal["pesos_atencao"][3]


# ---------------------------------------------------------------- 4. Fusão Multimodal Dinâmica (D-NOCTIS + LAYA)


def test_fundir_modalidades_laya():
    scores_vis = {"bucha": 0.45, "para_raio": 0.40, "isolador": 0.15}
    # Geometria 3D compatível com para-raio (altura esguia)
    scores_geom = {"bucha": 0.30, "para_raio": 0.90, "isolador": 0.20}
    # Assinatura radiométrica com gradiente característico
    termica = {"t_max": 75.0, "t_min": 30.0, "t_desvio": 6.5}

    fusao = fundir_modalidades_laya(
        scores_visuais=scores_vis,
        scores_geometricos=scores_geom,
        estatisticas_termicas=termica,
        tem_telemetria_3d=True,
    )

    assert "classe" in fusao
    assert "pesos_modalidades" in fusao
    assert fusao["pesos_modalidades"]["geometria_3d"] > 0.15
    assert fusao["pesos_modalidades"]["termografia_ir"] > 0.05
    assert "laya" in fusao


def test_fundir_scores_dnoctis_retrocompatibilidade():
    scores_vis = {"isolador": 0.70, "bucha": 0.20, "conexao": 0.10}
    res = fundir_scores_dnoctis(scores_vis, altura_m=0.85, razao_aspecto=2.7, usar_laya=True)

    # Contrato oficial do Pyron preservado
    assert res["classe"] == "isolador"
    assert "confianca" in res
    assert "nome" in res
    assert "scores" in res
    assert "consistencia_geometrica" in res
    # Chaves adicionais do LAYA enriquecidas
    assert "laya" in res
    assert "pesos_modalidades" in res


# ---------------------------------------------------------------- 5. DINOv2Classifier Integrado com LAYA


class MockDINOModelLaya(torch.nn.Module):
    def __init__(self, dim: int = 384):
        super().__init__()
        self.dim = dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.shape[0]
        val = float(x.mean().item())
        v = torch.zeros((b, self.dim), dtype=torch.float32)
        v[:, 0] = val
        v[:, 1] = 1.0 - val
        return v


def test_dinov2_classificar_com_laya():
    DINOv2Classifier._instancia = None
    mock_model = MockDINOModelLaya(dim=384)
    clf = DINOv2Classifier(modelo=mock_model, dispositivo="cpu")

    img_teste = np.full((224, 224, 3), 160, dtype=np.uint8)
    res = clf.classificar(img_teste, usar_laya=True)

    assert "classe" in res
    assert "confianca" in res
    assert "nome" in res
    assert "scores" in res
    assert "laya" in res

    laya_diag = res["laya"]
    assert "prediction_set" in laya_diag
    assert "jev_confidence" in laya_diag
    assert "route" in laya_diag
    assert "atribuicao_camadas" in laya_diag
    assert "rasas_textura" in laya_diag["atribuicao_camadas"]


# ---------------------------------------------------------------- 6. Consenso de Keyframes e Arbitragem Normativa


class MedidaMock:
    def __init__(self, alt: float, nit: float = 80.0, conf: float = 0.90):
        self.altura_cm = alt
        self.comprimento_cm = alt * 1.5
        self.nitidez = nit
        self.confianca = conf


def test_agregar_medicoes_laya_video():
    medidas = [
        MedidaMock(alt=50.2, nit=95.0, conf=0.95),
        MedidaMock(alt=49.8, nit=85.0, conf=0.90),
        MedidaMock(alt=50.0, nit=90.0, conf=0.92),
        MedidaMock(alt=72.0, nit=15.0, conf=0.40),  # Outlier com pose rasante e baixa nitidez
    ]

    consenso = agregar_medicoes(medidas, usar_laya=True)
    assert "altura_cm" in consenso
    alt_info = consenso["altura_cm"]
    assert alt_info["valor"] == 50.1  # mediana padrão
    assert "valor_laya" in alt_info
    # O valor ponderado LAYA deve suprimir o outlier (72.0) e ficar em torno de 50.0 cm
    assert 49.5 <= alt_info["valor_laya"] <= 51.0
    assert "laya" in alt_info


def test_analisar_regioes_arbitragem_laya():
    matriz = np.full((60, 60), 25.0, dtype=np.float32)
    # Simula ponto quente de 85 °C em uma bucha com ambiente a 25 °C e plena carga
    matriz[20:30, 20:30] = 85.0

    regioes = [
        {"classe": "bucha", "caixa": [15.0, 15.0, 35.0, 35.0], "nome": "Bucha Fase B"},
        {"classe": "bucha", "caixa": [38.0, 15.0, 55.0, 35.0], "nome": "Bucha Fase A"},
    ]

    saida, resumo = analisar_regioes(
        matriz,
        regioes,
        ambiente_c=25.0,
        carga_pct=100.0,
    )

    # Verifica integridade da saída
    assert len(saida) == 2
    item_critico = saida[0]
    assert "laya" in item_critico

    laya_item = item_critico["laya"]
    assert "choice" in laya_item
    assert "probabilities" in laya_item
    assert "prediction_set" in laya_item
    assert "prob_reflexo_solar" in laya_item
    assert "route" in laya_item

    # Verifica resumo global LAYA
    assert "laya" in resumo
    assert resumo["laya"]["total_avaliadas"] >= 1


def math_close(a: float, b: float, atol: float = 1e-4) -> bool:
    return abs(float(a) - float(b)) <= atol
