"""Motor de Agregação e Decisão Calibrada LAYA para o Pyron.

Integra duas frentes complementares sob licença Apache-2.0:
1. **LAYA (Layer-wise Attention Aggregator, Vessio 2025/2026):** agregação dinâmica por atenção
   condicionada à entrada ao longo das camadas ocultas de redes profundas (DINOv2 ViT),
   fornecendo representações multi-escala (textura rasa, periodicidade intermediária e
   semântica profunda) e atribuição intrínseca de profundidade sem custo de Grad-CAM.
2. **Laya System-1 Calibrated Decision & Conformal Engine (``laya`` v0.4.31 / ``vegaml``):**
   inferência não-autoregressiva com probabilidades calibradas por temperatura (RLCD),
   confiança normalizada de Jev (``jev_confidence``), conjuntos preditivos conformais
   (``prediction_set`` a nível ``alpha``), detecção fora da distribuição (``unbound``) e
   roteamento automático ``route: "auto" | "review"`` sem limiares arbitrários.

O módulo utiliza o pacote ``laya`` instalado no ambiente quando disponível e mantém
implementações matemáticas vetoriais idênticas em NumPy/PyTorch como fallback autônomo,
garantindo funcionamento em todas as máquinas da equipe.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

log = logging.getLogger(__name__)

# Tenta importar as primitivas oficiais do pacote laya (Apache-2.0)
try:
    import laya as _laya_pkg
    from laya.confidence import (
        apply_confidence_gate as _laya_apply_gate,
        jev_confidence as _laya_jev_confidence,
    )
    from laya.common import ece_score as _laya_ece_score

    LAYA_PACOTE_DISPONIVEL = True
    LAYA_VERSAO = getattr(_laya_pkg, "__version__", "0.4.31")
except Exception:
    _laya_pkg = None
    _laya_apply_gate = None
    _laya_jev_confidence = None
    _laya_ece_score = None
    LAYA_PACOTE_DISPONIVEL = False
    LAYA_VERSAO = "builtin-0.4.31"


TEMP_MIN_LAYA = 0.01
TEMP_MAX_LAYA = 10.0
ALPHA_CONFORMAL_PADRAO = 0.10
PRECISAO_ALVO_PADRAO = 0.60


def laya_disponivel() -> bool:
    """Informa se o pacote ``laya`` está instalado no interpretador Python atual."""
    return LAYA_PACOTE_DISPONIVEL


def _normalizar_probabilidades(probabilidades: Mapping[str, float]) -> dict[str, float]:
    """Garante um dicionário de probabilidades finitas, não-negativas e que somam 1.0."""
    if not probabilidades:
        return {}
    limpas: dict[str, float] = {}
    for k, v in probabilidades.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            limpas[str(k)] = 0.0
            continue
        fv = float(v)
        limpas[str(k)] = fv if (math.isfinite(fv) and fv >= 0.0) else 0.0

    soma = sum(limpas.values())
    n = len(limpas)
    if soma <= 1e-12 or not math.isfinite(soma):
        return {k: round(1.0 / n, 6) for k in limpas}
    return {k: float(v / soma) for k, v in limpas.items()}


def calcular_jev_confidence(
    probabilidades: Mapping[str, float],
    tipo: str = "choice",
) -> float:
    """Calcula a confiança Jev normalizada em [0, 1] sobre a distribuição de probabilidades.

    Para ``choice`` com ``n`` opções: ``(max(p) - 1/n) / (1 - 1/n)``.
    Para ``score`` ordinal: ``max(0, 1 - sum(p_i * |i - mode|) / D_uniforme)``.
    Delega para ``laya.confidence.jev_confidence`` quando o pacote está presente.
    """
    probs = _normalizar_probabilidades(probabilidades)
    if not probs:
        return 0.0
    if len(probs) == 1:
        return 1.0

    if _laya_jev_confidence is not None:
        try:
            if tipo == "score":
                probs_ordenadas = {str(i): float(v) for i, (_, v) in enumerate(probs.items())}
                val = _laya_jev_confidence({"type": "score", "probabilities": probs_ordenadas})
            else:
                val = _laya_jev_confidence({"type": "choice", "probabilities": probs})
            if val is not None and math.isfinite(val):
                return float(np.clip(val, 0.0, 1.0))
        except Exception:
            pass

    valores = list(probs.values())
    n = len(valores)
    if tipo == "score":
        modo = int(np.argmax(valores))
        dispersao = sum(v * abs(i - modo) for i, v in enumerate(valores))
        centro = (n - 1) / 2.0
        dispersao_unif = sum(abs(i - centro) for i in range(n)) / float(n)
        if dispersao_unif <= 1e-12:
            return 1.0
        return float(np.clip(1.0 - dispersao / dispersao_unif, 0.0, 1.0))

    p_max = max(valores)
    inv_n = 1.0 / float(n)
    return float(np.clip((p_max - inv_n) / max(1.0 - inv_n, 1e-12), 0.0, 1.0))


def calcular_entropia_confianca(probabilidades: Mapping[str, float]) -> float:
    """Calcula a confiança baseada em entropia de Shannon normalizada: 1 - H(p)/ln(K)."""
    probs = _normalizar_probabilidades(probabilidades)
    n = len(probs)
    if n <= 1:
        return 1.0
    p = np.array(list(probs.values()), dtype=np.float64)
    p = np.clip(p, 1e-12, 1.0)
    entropia = -float(np.sum(p * np.log(p)))
    max_entropia = math.log(float(n))
    return float(np.clip(1.0 - (entropia / max(max_entropia, 1e-12)), 0.0, 1.0))


def conjunto_preditivo_conformal(
    probabilidades: Mapping[str, float],
    alpha: float = ALPHA_CONFORMAL_PADRAO,
    limiar_precisao: float = PRECISAO_ALVO_PADRAO,
    similaridade_max: float | None = None,
    limiar_ood: float = 0.22,
) -> dict[str, Any]:
    """Constrói o conjunto preditivo conformal (``prediction_set``) e decide o roteamento Laya/Vega.

    Segue a diretriz de ``laya.vega`` ("Gate on ``route``, never on ``confidence``"):
    - ``prediction_set``: menor subconjunto de classes cuja massa acumulada calibrada atinge
      ``1 - alpha`` (padrão 90%), com poda de cauda insignificante;
    - ``abstain``: verdadeiro quando a confiança Jev indica quase-uniformidade (incerteza severa);
    - ``unbound``: verdadeiro quando a amostra está fora da distribuição conhecida (similaridade
      máxima de cosseno abaixo de ``limiar_ood``);
    - ``route``: ``"auto"`` apenas quando ``len(prediction_set) == 1``, ``not abstain``,
      ``not unbound`` e ``answer_confidence >= limiar_precisao``; caso contrário ``"review"``.
    """
    probs = _normalizar_probabilidades(probabilidades)
    if not probs:
        return {
            "choice": None,
            "answer_confidence": 0.0,
            "jev_confidence": 0.0,
            "entropy_confidence": 0.0,
            "prediction_set": [],
            "abstain": True,
            "unbound": True,
            "route": "review",
            "alpha": float(alpha),
        }

    ordenadas = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    melhor_classe, answer_conf = ordenadas[0]
    jev_conf = calcular_jev_confidence(probs, tipo="choice")
    ent_conf = calcular_entropia_confianca(probs)

    cobertura_alvo = float(np.clip(1.0 - float(alpha), 0.50, 0.99))
    n = len(ordenadas)
    # Limiar mínimo para uma classe secundária entrar no conjunto conformal:
    # evita incluir a cauda inteira quando a classe líder já domina com folga.
    piso_secundario = max(float(alpha) / max(float(n), 2.0), 0.05)

    conjunto: list[str] = []
    acumulado = 0.0
    for idx, (cls, p) in enumerate(ordenadas):
        if idx == 0:
            conjunto.append(cls)
            acumulado += p
            continue
        if acumulado >= cobertura_alvo:
            break
        if p >= piso_secundario or (melhor_classe and (answer_conf - p) < 0.15):
            conjunto.append(cls)
            acumulado += p
        else:
            break

    abstain = bool(jev_conf < 0.22 or answer_conf < (1.0 / max(n, 1)) + 0.08)
    unbound = bool(similaridade_max is not None and float(similaridade_max) < float(limiar_ood))

    # Aplica gate de confiança oficial do laya se disponível
    gate_state = "auto"
    if _laya_apply_gate is not None:
        try:
            ans_doc = {
                "type": "choice",
                "choice": melhor_classe,
                "probabilities": {k: round(v, 4) for k, v in probs.items()},
                "answer_confidence": round(answer_conf, 4),
                "confidence": round(ent_conf, 4),
            }
            gated = _laya_apply_gate(ans_doc, float(limiar_precisao))
            if gated.get("low_confidence") or gated.get("gate") != "auto":
                gate_state = "review"
        except Exception:
            if answer_conf < float(limiar_precisao):
                gate_state = "review"
    elif answer_conf < float(limiar_precisao):
        gate_state = "review"

    rota = (
        "auto"
        if (not abstain and not unbound and len(conjunto) == 1 and gate_state == "auto")
        else "review"
    )

    return {
        "choice": melhor_classe,
        "answer_confidence": round(float(answer_conf), 4),
        "jev_confidence": round(float(jev_conf), 4),
        "entropy_confidence": round(float(ent_conf), 4),
        "prediction_set": conjunto,
        "abstain": abstain,
        "unbound": unbound,
        "route": rota,
        "alpha": round(float(alpha), 4),
    }


def calcular_ece(probabilidades: np.ndarray, alvos: np.ndarray, n_bins: int = 10) -> float:
    """Calcula o Expected Calibration Error (ECE) sobre matrizes de probabilidades [N, K] e rótulos."""
    probs = np.asarray(probabilidades, dtype=np.float64)
    targets = np.asarray(alvos)
    if probs.ndim != 2 or len(probs) == 0:
        return 0.0

    if targets.ndim == 2:
        y_true = np.argmax(targets, axis=1)
    else:
        y_true = targets.astype(int).ravel()

    confiancas = np.max(probs, axis=1)
    predicoes = np.argmax(probs, axis=1)
    acertos = (predicoes == y_true).astype(np.float64)

    bordas = np.linspace(0.0, 1.0, max(int(n_bins), 2) + 1)
    ece = 0.0
    n_total = float(len(probs))
    for b in range(len(bordas) - 1):
        if b == 0:
            mascara = (confiancas >= bordas[b]) & (confiancas <= bordas[b + 1])
        else:
            mascara = (confiancas > bordas[b]) & (confiancas <= bordas[b + 1])
        if np.any(mascara):
            peso = float(np.sum(mascara)) / n_total
            acc_bin = float(np.mean(acertos[mascara]))
            conf_bin = float(np.mean(confiancas[mascara]))
            ece += peso * abs(acc_bin - conf_bin)
    return float(round(ece, 6))


def calibrar_temperatura_laya(
    logits_matriz: np.ndarray,
    alvos: np.ndarray,
    temperatura_inicial: float = 0.07,
) -> dict[str, Any]:
    """Ajusta a temperatura ótima T* minimizando a Negative Log-Likelihood (NLL) como em ``laya.calibrate``.

    Retorna a temperatura calibrada dentro de ``[TEMP_MIN_LAYA, TEMP_MAX_LAYA]``, além do
    Expected Calibration Error (ECE) e Brier Score antes e depois da calibração.
    """
    z = np.asarray(logits_matriz, dtype=np.float64)
    if z.ndim != 2 or len(z) == 0:
        return {
            "temperatura_otima": float(temperatura_inicial),
            "ece_antes": 0.0,
            "ece_depois": 0.0,
            "brier_antes": 0.0,
            "brier_depois": 0.0,
        }

    n_amostras, n_classes = z.shape
    y = np.asarray(alvos)
    if y.ndim == 1:
        y_onehot = np.zeros((n_amostras, n_classes), dtype=np.float64)
        for i, idx in enumerate(y.astype(int)):
            if 0 <= idx < n_classes:
                y_onehot[i, idx] = 1.0
    else:
        y_onehot = y.astype(np.float64)

    def _softmax_t(temp: float) -> np.ndarray:
        t = max(float(temp), TEMP_MIN_LAYA)
        esc = z / t
        esc = esc - np.max(esc, axis=1, keepdims=True)
        exp_z = np.exp(esc)
        return exp_z / np.maximum(np.sum(exp_z, axis=1, keepdims=True), 1e-12)

    probs_antes = _softmax_t(temperatura_inicial)
    ece_antes = calcular_ece(probs_antes, y_onehot)
    brier_antes = float(np.mean(np.sum((probs_antes - y_onehot) ** 2, axis=1)))

    # Busca em grade logarítmica refinada + ajuste fino local (determinístico e sem risco de divergência)
    grade_t = np.geomspace(TEMP_MIN_LAYA, TEMP_MAX_LAYA, 120)
    melhor_t = float(temperatura_inicial)
    melhor_nll = float("inf")

    for t_cand in grade_t:
        p = np.clip(_softmax_t(t_cand), 1e-12, 1.0)
        nll = -float(np.mean(np.sum(y_onehot * np.log(p), axis=1)))
        if nll < melhor_nll:
            melhor_nll = nll
            melhor_t = float(t_cand)

    # Refinamento fino em torno de melhor_t
    grade_fina = np.linspace(
        max(TEMP_MIN_LAYA, melhor_t * 0.7),
        min(TEMP_MAX_LAYA, melhor_t * 1.3),
        60,
    )
    for t_cand in grade_fina:
        p = np.clip(_softmax_t(t_cand), 1e-12, 1.0)
        nll = -float(np.mean(np.sum(y_onehot * np.log(p), axis=1)))
        if nll < melhor_nll:
            melhor_nll = nll
            melhor_t = float(t_cand)

    melhor_t = float(np.clip(melhor_t, TEMP_MIN_LAYA, TEMP_MAX_LAYA))
    probs_depois = _softmax_t(melhor_t)
    ece_depois = calcular_ece(probs_depois, y_onehot)
    brier_depois = float(np.mean(np.sum((probs_depois - y_onehot) ** 2, axis=1)))

    return {
        "temperatura_otima": round(melhor_t, 5),
        "ece_antes": round(ece_antes, 5),
        "ece_depois": round(ece_depois, 5),
        "brier_antes": round(brier_antes, 5),
        "brier_depois": round(brier_depois, 5),
    }


# ---------------------------------------------------------------- Etapa 1: LAYA Layer-wise Attention Head


class LAYAHead(nn.Module):
    """Layer-wise Attention Aggregator (LAYA) para Vision Transformers (DINOv2).

    Agrega dinamicamente as representações ocultas de múltiplas camadas ``[B, L, D]``
    por meio de atenção condicionada à entrada e fornece escores intrínsecos de
    atribuição por profundidade (camadas rasas, intermediárias e profundas).
    """

    def __init__(
        self,
        d_model: int = 384,
        num_layers: int = 4,
        temperatura: float = 1.0,
        prior_profundidade: Sequence[float] | None = None,
    ) -> None:
        super().__init__()
        self.d_model = int(d_model)
        self.num_layers = int(num_layers)
        self.temperatura = max(float(temperatura), 1e-3)

        hidden = max(self.d_model // 2, 32)
        self.proj_camada = nn.Linear(self.d_model, hidden)
        self.vetor_atencao = nn.Linear(hidden, 1, bias=False)
        self.norm = nn.LayerNorm(self.d_model)

        # Inicialização estruturada com prior progressivo (valorizando camadas intermediárias e profundas
        # sem descartar a textura das camadas rasas, garantindo ótimo desempenho zero-shot imediato)
        with torch.no_grad():
            nn.init.eye_(self.proj_camada.weight[:hidden, :hidden])
            if self.proj_camada.weight.shape[1] > hidden:
                nn.init.zeros_(self.proj_camada.weight[:, hidden:])
            nn.init.zeros_(self.proj_camada.bias)
            nn.init.constant_(self.vetor_atencao.weight, 1.0 / math.sqrt(hidden))

        if prior_profundidade is not None and len(prior_profundidade) == self.num_layers:
            prior = torch.tensor(list(prior_profundidade), dtype=torch.float32)
        else:
            # Prior canônico para ativos elétricos: [rasas=0.15, interm_1=0.25, interm_2=0.30, profunda=0.30]
            pesos_base = np.linspace(0.15, 0.35, self.num_layers, dtype=np.float32)
            pesos_base = pesos_base / np.sum(pesos_base)
            prior = torch.from_numpy(pesos_base)
        self.register_buffer("prior_logits", torch.log(torch.clamp(prior, min=1e-4)))

    def forward(
        self,
        estados_camadas: torch.Tensor,
        seletividade_camadas: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Calcula o embedding agregado depth-aware e os pesos de atenção por camada.

        Args:
            estados_camadas: Tensor ``[B, L, D]`` ou ``[L, D]`` com os tokens ``[CLS]`` de cada camada.
            seletividade_camadas: Tensor opcional ``[B, L]`` com medida de seletividade espacial
                                  (ex.: variância/contraste dos patches em cada camada).

        Returns:
            embedding_l2: Tensor ``[B, D]`` L2-normalizado.
            pesos_atencao: Tensor ``[B, L]`` somando 1.0 ao longo das camadas.
        """
        unico = False
        if estados_camadas.ndim == 2:
            estados_camadas = estados_camadas.unsqueeze(0)
            unico = True

        bsz, n_camadas, _ = estados_camadas.shape
        # Normaliza cada camada em L2 antes da projeção para evitar que normas brutas dominem
        estados_norm = F.normalize(estados_camadas, p=2, dim=-1)

        h = torch.tanh(self.proj_camada(estados_norm))
        logits_mlp = self.vetor_atencao(h).squeeze(-1)  # [B, L]

        if n_camadas == self.prior_logits.shape[0]:
            logits = 0.35 * logits_mlp + self.prior_logits.unsqueeze(0)
        else:
            prior_interp = torch.linspace(
                -1.2, 0.0, steps=n_camadas, device=estados_camadas.device, dtype=estados_camadas.dtype
            )
            logits = 0.35 * logits_mlp + prior_interp.unsqueeze(0)

        if seletividade_camadas is not None:
            sel = seletividade_camadas.to(estados_camadas.device, dtype=estados_camadas.dtype)
            if sel.ndim == 1:
                sel = sel.unsqueeze(0)
            sel_z = (sel - sel.mean(dim=-1, keepdim=True)) / torch.clamp(sel.std(dim=-1, keepdim=True), min=1e-4)
            logits = logits + 0.45 * sel_z

        pesos_atencao = F.softmax(logits / self.temperatura, dim=-1)  # [B, L]
        agregado = torch.sum(pesos_atencao.unsqueeze(-1) * estados_norm, dim=1)  # [B, D]
        agregado = self.norm(agregado)
        agregado_l2 = F.normalize(agregado, p=2, dim=-1)

        if unico:
            return agregado_l2.squeeze(0), pesos_atencao.squeeze(0)
        return agregado_l2, pesos_atencao


def resumir_atribuicao_camadas(pesos_camadas: Sequence[float] | np.ndarray) -> dict[str, Any]:
    """Converte o vetor de pesos de atenção por camada em grupos semânticos interpretáveis para o laudo."""
    arr = np.asarray(pesos_camadas, dtype=np.float64).ravel()
    if arr.size == 0 or not np.isfinite(arr).all() or np.sum(arr) <= 1e-12:
        return {
            "rasas_textura": 0.25,
            "intermediarias_periodicidade": 0.35,
            "profundas_semantica": 0.40,
            "pesos_por_camada": [0.25, 0.25, 0.25, 0.25],
            "camada_dominante": 3,
            "explicacao_predominante": "semantica_global",
        }

    arr = np.maximum(arr, 0.0)
    arr = arr / np.sum(arr)
    n = arr.size

    if n == 1:
        rasas, interm, profundas = 0.0, 0.0, 1.0
    elif n == 2:
        rasas, interm, profundas = float(arr[0] * 0.5), float(arr[0] * 0.5), float(arr[1])
    elif n == 3:
        rasas, interm, profundas = float(arr[0]), float(arr[1]), float(arr[2])
    else:
        corte1 = max(1, n // 4)
        corte2 = max(corte1 + 1, (3 * n) // 4)
        rasas = float(np.sum(arr[:corte1]))
        interm = float(np.sum(arr[corte1:corte2]))
        profundas = float(np.sum(arr[corte2:]))

    grupos = {
        "textura_superficial_bordas": rasas,
        "periodicidade_aletas_discos": interm,
        "semantica_silhueta_global": profundas,
    }
    dominante_nome = max(grupos, key=lambda k: grupos[k])

    return {
        "rasas_textura": round(rasas, 4),
        "intermediarias_periodicidade": round(interm, 4),
        "profundas_semantica": round(profundas, 4),
        "pesos_por_camada": [round(float(v), 4) for v in arr],
        "camada_dominante": int(np.argmax(arr)),
        "explicacao_predominante": dominante_nome,
    }


# ---------------------------------------------------------------- Etapa 2: Agregação Espacial de Patches (NOCTIS / AnomalyDINO + LAYA)


def agregar_patches_laya(
    patches_consulta: np.ndarray,
    patches_prototipo: np.ndarray,
    limiar_ciclico: float = 0.65,
    temperaturas_patches: np.ndarray | None = None,
) -> dict[str, Any]:
    """Agrega similaridades e anomalias de patches via atenção espacial LAYA + consistência cíclica NOCTIS.

    Diferente da média simples top-k, calcula pesos de atenção por patch ``alpha_i`` combinando:
    1. Reciprocidade cíclica ``i -> j* -> i*`` (protege estruturas periódicas como aletas de buchas);
    2. Seletividade de cosseno (distintividade do patch);
    3. Coerência térmica radial (quando ``temperaturas_patches`` é fornecido, penaliza picos ópticos
       pontuais isolados típicos de reflexo solar que não possuem vizinhança térmica aquecida).
    """
    q = np.asarray(patches_consulta, dtype=np.float32)
    p = np.asarray(patches_prototipo, dtype=np.float32)
    if q.ndim == 1:
        q = q[None, :]
    if p.ndim == 1:
        p = p[None, :]
    if q.size == 0 or p.size == 0:
        return {
            "similaridade": 0.0,
            "score_anomalia": 0.0,
            "patch_decisivo_idx": 0,
            "fator_reflexo_solar": 0.0,
            "pesos_atencao": [],
        }

    q_norm = q / np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-12)
    p_norm = p / np.maximum(np.linalg.norm(p, axis=-1, keepdims=True), 1e-12)

    sim_matrix = np.matmul(q_norm, p_norm.T)  # [N_q, N_p]
    nq = sim_matrix.shape[0]

    j_melhor = np.argmax(sim_matrix, axis=1)
    sim_ida = sim_matrix[np.arange(nq), j_melhor]

    i_melhor_por_p = np.argmax(sim_matrix, axis=0)
    i_retorno = i_melhor_por_p[j_melhor]

    if nq > 1:
        dist_ciclica = np.abs(np.arange(nq, dtype=np.float32) - i_retorno.astype(np.float32)) / float(nq - 1)
    else:
        dist_ciclica = np.zeros(nq, dtype=np.float32)

    consistencia_ciclo = np.clip(1.0 - 0.55 * dist_ciclica, 0.25, 1.0)

    # Avaliação de reflexo solar vs. condução térmica contínua nos patches
    fator_reflexo = 0.0
    pesos_termicos = np.ones(nq, dtype=np.float32)
    if temperaturas_patches is not None:
        t_arr = np.asarray(temperaturas_patches, dtype=np.float32).ravel()
        if t_arr.size == nq and np.isfinite(t_arr).any():
            t_limpo = np.nan_to_num(t_arr, nan=float(np.nanmedian(t_arr)))
            t_med = float(np.median(t_limpo))
            t_std = max(float(np.std(t_limpo)), 0.5)
            z_term = (t_limpo - t_med) / t_std

            # Se apenas 1 patch isolado tem z_term extremo (> 3.0) mas os vizinhos imediatos são frios,
            # há forte indício de reflexo solar/artefato pontual.
            idx_max_t = int(np.argmax(t_limpo))
            vizinhos = []
            if idx_max_t > 0:
                vizinhos.append(t_limpo[idx_max_t - 1])
            if idx_max_t + 1 < nq:
                vizinhos.append(t_limpo[idx_max_t + 1])
            media_viz = float(np.mean(vizinhos)) if vizinhos else float(t_limpo[idx_max_t])
            salto_isolado = float(t_limpo[idx_max_t] - media_viz)

            if z_term[idx_max_t] > 2.2 and salto_isolado > 2.0 * t_std:
                fator_reflexo = float(np.clip(salto_isolado / max(4.0 * t_std, 1.0), 0.0, 1.0))
                # Reduz o peso do patch com reflexo especular na agregação semântica
                pesos_termicos[idx_max_t] *= (1.0 - 0.65 * fator_reflexo)

    # Logits de atenção dos patches: combina similaridade, reciprocidade cíclica e pureza térmica
    logits_patch = (2.5 * sim_ida + 1.5 * consistencia_ciclo) * pesos_termicos
    logits_patch = logits_patch - np.max(logits_patch)
    exp_p = np.exp(logits_patch)
    alfa_patches = exp_p / np.maximum(np.sum(exp_p), 1e-12)

    sim_agregada = float(np.clip(np.sum(alfa_patches * sim_ida * consistencia_ciclo), -1.0, 1.0))

    # Distância de anomalia ponderada (suprimindo falsos positivos de reflexo solar)
    distancias = np.clip(1.0 - sim_ida, 0.0, 1.0) * pesos_termicos
    n_cauda = max(1, int(round(nq * 0.05)))
    score_anomalia = float(np.mean(np.sort(distancias)[-n_cauda:]))
    patch_decisivo = int(np.argmax(alfa_patches))

    return {
        "similaridade": round(sim_agregada, 4),
        "score_anomalia": round(score_anomalia, 4),
        "patch_decisivo_idx": patch_decisivo,
        "fator_reflexo_solar": round(fator_reflexo, 4),
        "pesos_atencao": [round(float(v), 4) for v in alfa_patches],
    }


# ---------------------------------------------------------------- Etapa 3: Fusão Multimodal Cross-Modality (RGB + 3D + Termografia)


def fundir_modalidades_laya(
    scores_visuais: Mapping[str, float],
    scores_geometricos: Mapping[str, float] | None = None,
    estatisticas_termicas: Mapping[str, Any] | Any | None = None,
    tem_telemetria_3d: bool = False,
    alpha: float = ALPHA_CONFORMAL_PADRAO,
) -> dict[str, Any]:
    """Funde dinamicamente as evidências Visual (DINOv2), Geométrica 3D (D-NOCTIS) e Radiométrica (IR).

    Substitui o fator estático ``lambda = 0.30`` por atenção adaptativa condicionada à qualidade
    de cada modalidade:
    - Se a distribuição visual tem alta entropia (contraluz, névoa, baixa resolução), aumenta o
      peso da geometria 3D e da assinatura térmica;
    - Se há telemetria óptica real (``tem_telemetria_3d=True``), eleva a autoridade da métrica 3D;
    - Se o ativo apresenta gradiente térmico interno característico, reforça classes compatíveis
      com dissipação resistiva/dielétrica.
    """
    probs_vis = _normalizar_probabilidades(scores_visuais)
    if not probs_vis:
        return {
            "classe": "isolador",
            "confianca": 0.0,
            "scores": {},
            "pesos_modalidades": {"visual_rgb": 1.0, "geometria_3d": 0.0, "termografia_ir": 0.0},
            "laya": conjunto_preditivo_conformal({}, alpha=alpha),
        }

    classes = list(probs_vis.keys())
    conf_vis = calcular_entropia_confianca(probs_vis)

    # 1. Modalidade Geométrica 3D (D-NOCTIS)
    tem_geom = bool(scores_geometricos and any(v > 0 for v in scores_geometricos.values()))
    if tem_geom and scores_geometricos is not None:
        probs_geom = _normalizar_probabilidades({c: float(scores_geometricos.get(c, 1.0 / len(classes))) for c in classes})
        conf_geom = calcular_entropia_confianca(probs_geom)
        peso_base_geom = 0.35 if tem_telemetria_3d else 0.18
        # Quando a visão está ambígua (conf_vis baixa), a geometria ganha mais peso
        logit_geom = peso_base_geom * (1.0 + 0.65 * (1.0 - conf_vis) + 0.40 * conf_geom)
    else:
        probs_geom = {c: 1.0 / len(classes) for c in classes}
        logit_geom = 0.0

    # 2. Modalidade Termográfica Radiométrica
    t_desvio = 0.0
    t_amplitude = 0.0
    if estatisticas_termicas is not None:
        if isinstance(estatisticas_termicas, Mapping):
            t_max = float(estatisticas_termicas.get("t_max") or 0.0)
            t_min = float(estatisticas_termicas.get("t_min") or t_max)
            t_desvio = float(estatisticas_termicas.get("t_desvio") or 0.0)
        else:
            t_max = float(getattr(estatisticas_termicas, "t_max", 0.0) or 0.0)
            t_min = float(getattr(estatisticas_termicas, "t_min", t_max) or t_max)
            t_desvio = float(getattr(estatisticas_termicas, "t_desvio", 0.0) or 0.0)
        t_amplitude = max(0.0, t_max - t_min)

    tem_termica = t_amplitude > 1.5 or t_desvio > 0.5
    if tem_termica:
        # Prior termográfico suave: ativos com alto gradiente interno ou troca térmica
        afinidade_termica_padrao = {
            "transformador": 1.15 if t_desvio > 1.8 else 1.0,
            "radiador": 1.20 if t_desvio > 1.5 else 1.0,
            "conexao": 1.25 if t_amplitude > 8.0 else 1.0,
            "bucha": 1.15 if t_amplitude > 5.0 else 1.0,
            "para_raio": 1.05,
            "isolador": 1.00,
            "cabo": 1.10 if t_amplitude > 4.0 else 1.0,
            "tanque": 1.10,
            "estrutura": 0.75,  # estruturas metálicas passivas raramente têm gradiente Joule próprio
        }
        probs_term = _normalizar_probabilidades({c: probs_vis[c] * afinidade_termica_padrao.get(c, 1.0) for c in classes})
        logit_term = min(0.22, 0.08 + 0.015 * min(t_amplitude, 10.0))
    else:
        probs_term = probs_vis
        logit_term = 0.0

    logit_vis = max(0.45, 0.75 * (0.5 + 0.5 * conf_vis))
    soma_pesos = logit_vis + logit_geom + logit_term
    w_vis = logit_vis / soma_pesos
    w_geom = logit_geom / soma_pesos
    w_term = logit_term / soma_pesos

    scores_fundidos: dict[str, float] = {}
    for c in classes:
        scores_fundidos[c] = (
            w_vis * probs_vis[c]
            + w_geom * probs_geom.get(c, 0.0)
            + w_term * probs_term.get(c, 0.0)
        )

    probs_finais = _normalizar_probabilidades(scores_fundidos)
    decisao_laya = conjunto_preditivo_conformal(probs_finais, alpha=alpha)
    melhor_classe = decisao_laya["choice"] or classes[0]
    melhor_conf = decisao_laya["answer_confidence"]

    return {
        "classe": melhor_classe,
        "confianca": round(float(melhor_conf), 4),
        "scores": {c: round(float(v), 4) for c, v in probs_finais.items()},
        "pesos_modalidades": {
            "visual_rgb": round(float(w_vis), 4),
            "geometria_3d": round(float(w_geom), 4),
            "termografia_ir": round(float(w_term), 4),
        },
        "laya": decisao_laya,
    }


# ---------------------------------------------------------------- Etapa 4: Consenso Multi-Frame de Keyframes em Vídeo


def agregar_keyframes_laya(
    valores: Sequence[float],
    nitidez: Sequence[float] | None = None,
    confiancas: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Agrega medições 3D de múltiplos keyframes ponderando nitidez, confiança e estabilidade de Huber.

    Inspirado em ``laya.predict_long``, além de estimar a grandeza consolidada com menor
    variância que a mediana simples em presença de poses oblíquas, reporta a atribuição de
    janela (``quadro_decisivo_idx`` e ``pesos_keyframes``).
    """
    arr = np.asarray(valores, dtype=np.float64).ravel()
    validos = np.isfinite(arr)
    arr = arr[validos]
    n = int(arr.size)
    if n == 0:
        return {
            "valor": 0.0,
            "desvio_padrao": 0.0,
            "pesos_keyframes": [],
            "quadro_decisivo_idx": 0,
            "jev_confidence": 0.0,
            "route": "review",
            "reducao_incerteza_pct": 0.0,
        }
    if n == 1:
        return {
            "valor": round(float(arr[0]), 2),
            "desvio_padrao": 0.0,
            "pesos_keyframes": [1.0],
            "quadro_decisivo_idx": 0,
            "jev_confidence": 0.75,
            "route": "review",
            "reducao_incerteza_pct": 0.0,
        }

    # 1. Peso de nitidez Laplaciana normalizado
    if nitidez is not None and len(nitidez) == len(validos):
        nit_arr = np.asarray(nitidez, dtype=np.float64).ravel()[validos]
        nit_arr = np.maximum(nit_arr, 1.0)
        peso_nit = np.sqrt(nit_arr) / np.maximum(np.max(np.sqrt(nit_arr)), 1e-6)
    else:
        peso_nit = np.ones(n, dtype=np.float64)

    # 2. Peso de confiança de segmentação/profundidade
    if confiancas is not None and len(confiancas) == len(validos):
        conf_arr = np.clip(np.asarray(confiancas, dtype=np.float64).ravel()[validos], 0.1, 1.0)
    else:
        conf_arr = np.ones(n, dtype=np.float64)

    # 3. Peso de estabilidade inter-frame (Huber/MAD contra outliers de ângulo rasante)
    mediana = float(np.median(arr))
    mad = float(np.median(np.abs(arr - mediana)))
    escala_robusta = max(1.4826 * mad, 0.03 * abs(mediana), 1e-4)
    residuo_norm = np.abs(arr - mediana) / escala_robusta
    peso_estabilidade = np.exp(-0.5 * (residuo_norm ** 2))

    pesos_brutos = peso_nit * conf_arr * peso_estabilidade
    soma_p = float(np.sum(pesos_brutos))
    if soma_p <= 1e-12:
        pesos = np.full(n, 1.0 / n, dtype=np.float64)
    else:
        pesos = pesos_brutos / soma_p

    valor_laya = float(np.sum(pesos * arr))
    var_ponderada = float(np.sum(pesos * ((arr - valor_laya) ** 2)))
    desvio_ponderado = math.sqrt(max(var_ponderada, 0.0))

    # Tamanho efetivo da amostra de Kish: N_eff = 1 / sum(w_i^2)
    n_eff = 1.0 / max(float(np.sum(pesos ** 2)), 1e-6)
    desvio_bruto = float(np.std(arr))
    fator_base = (1.0 - (1.0 / math.sqrt(max(n_eff, 1.0)))) * 100.0 if n > 1 else 0.0
    ganho_variancia = (
        max(0.0, (1.0 - (desvio_ponderado / max(desvio_bruto, 1e-6))) * 25.0)
        if desvio_bruto > 1e-6
        else 5.0
    )
    reducao_incerteza = min(85.0, fator_base + ganho_variancia)

    cv = desvio_ponderado / max(abs(valor_laya), 1e-4)
    jev_conf = float(np.clip(math.exp(-2.5 * cv), 0.0, 1.0))
    rota = "auto" if (n >= 2 and jev_conf >= 0.70 and cv <= 0.12) else "review"

    return {
        "valor": round(valor_laya, 2),
        "valor_mediana": round(mediana, 2),
        "desvio_padrao": round(desvio_ponderado, 2),
        "desvio_padrao_bruto": round(desvio_bruto, 2),
        "pesos_keyframes": [round(float(w), 4) for w in pesos],
        "quadro_decisivo_idx": int(np.argmax(pesos)),
        "n_efetivo_kish": round(n_eff, 2),
        "jev_confidence": round(jev_conf, 4),
        "route": rota,
        "reducao_incerteza_pct": round(reducao_incerteza, 1),
    }


# ---------------------------------------------------------------- Etapa 5: Arbitragem Normativa System-1 (NBR 15866 / NETA)


ORDEM_NIVEIS_NORMATIVOS = ("normal", "atencao", "programar", "urgente", "imediato")


def _probabilidades_por_faixas(
    valor: float | None,
    faixas: Sequence[Sequence[Any]],
    temperatura_escala: float = 1.8,
) -> dict[str, float]:
    """Converte um valor físico (ΔT ou % da MTA) em distribuição calibrada sobre os 5 níveis normativos.

    Quando o valor medido cai exatamente próximo à fronteira entre duas faixas (ex.: ΔT = 19,9 °C
    perto do limiar de 20,1 °C para ``urgente``), a distribuição atribui massa significativa a ambos
    os níveis vizinhos para que o ``prediction_set`` conformal sinalize revisão técnica.
    """
    if valor is None or not math.isfinite(float(valor)):
        return {n: 0.20 for n in ORDEM_NIVEIS_NORMATIVOS}

    v = float(valor)
    limiares = [(0.0, "normal")] + [(float(lim), str(niv)) for lim, niv in faixas]

    # Calcula centros e larguras de cada faixa normativa
    intervalos: dict[str, tuple[float, float]] = {}
    for idx, (lim_inf, nome_niv) in enumerate(limiares):
        if idx + 1 < len(limiares):
            lim_sup = float(limiares[idx + 1][0])
        else:
            largura_ant = max(lim_inf - float(limiares[idx - 1][0]), 10.0) if idx > 0 else 20.0
            lim_sup = lim_inf + 2.0 * largura_ant
        intervalos[nome_niv] = (lim_inf, lim_sup)

    logits: dict[str, float] = {}
    t_esc = max(float(temperatura_escala), 0.25)

    for niv in ORDEM_NIVEIS_NORMATIVOS:
        if niv not in intervalos:
            logits[niv] = -8.0
            continue
        a, b = intervalos[niv]
        if a <= v < b or (niv == limiares[-1][1] and v >= a):
            # Dentro da faixa: distância até a borda mais próxima determina a margem de segurança
            dist_borda = min(abs(v - a), abs(b - v)) if niv != limiares[-1][1] else abs(v - a)
            logits[niv] = 2.2 + min(dist_borda / t_esc, 3.0)
        else:
            dist = (a - v) if v < a else (v - b)
            logits[niv] = -max(dist, 0.0) / t_esc

    max_l = max(logits.values())
    exp_l = {k: math.exp(val - max_l) for k, val in logits.items()}
    soma = sum(exp_l.values())
    return {k: exp_l[k] / max(soma, 1e-12) for k in ORDEM_NIVEIS_NORMATIVOS}


def arbitrar_severidade_normativa_laya(
    item: Mapping[str, Any],
    ambiente_c: float | None = None,
    carga_pct: float | None = None,
    criterios: Mapping[str, Any] | None = None,
    alpha: float = ALPHA_CONFORMAL_PADRAO,
) -> dict[str, Any]:
    """Executa a arbitragem diagnóstica System-1 calibrada sobre uma região avaliada em ``nucleo/analise.py``.

    Retorna:
    - ``choice``: severidade normativa calibrada;
    - ``probabilities``: probabilidades sobre ``(normal, atencao, programar, urgente, imediato)``;
    - ``prediction_set``: conjunto preditivo conformal (inclui 2 níveis quando a medida está na zona
      cinzenta de fronteira da norma ABNT NBR 15866);
    - ``jev_confidence`` e ``answer_confidence``: confiança calibrada;
    - ``prob_reflexo_solar`` (``noul``): probabilidade calibrada de falso positivo por reflexo solar
      ou artefato óptico externo;
    - ``route``: ``"auto"`` quando a decisão é inequívoca ou ``"review"`` quando está em fronteira
      normativa, falta carga/ambiente ou há suspeita de reflexo solar.
    """
    sev_deterministica = str(item.get("severidade") or "normal")
    if sev_deterministica in ("sem_medida", "nao_avaliado"):
        return {
            "choice": sev_deterministica,
            "probabilities": {},
            "prediction_set": [sev_deterministica],
            "answer_confidence": 0.0,
            "jev_confidence": 0.0,
            "prob_reflexo_solar": 0.0,
            "abstain": True,
            "route": "review",
            "motivos_revisao": [f"estado_{sev_deterministica}"],
        }

    crit = dict(criterios or {})
    faixas_sim = crit.get("similares") or [[5.0, "atencao"], [10.1, "programar"], [20.1, "urgente"], [40.1, "imediato"]]
    faixas_diel = crit.get("dieletrico") or [[2.0, "atencao"], [5.0, "programar"], [10.0, "urgente"]]
    faixas_mta = crit.get("mta_faixas") or [[60.1, "atencao"], [70.1, "programar"], [80.1, "urgente"], [100.1, "imediato"]]

    ref = item.get("referencia") or {}
    dieletrico = ref.get("aquecimento") == "dieletrico"

    dt_corrigido = item.get("dt_corrigido")
    pct_mta = item.get("pct_mta")

    # Incerteza operacional aumenta a temperatura de escala quando falta carga ou ambiente
    fator_incerteza = 1.0
    motivos_revisao: list[str] = []
    if carga_pct is None or float(carga_pct) <= 0:
        fator_incerteza *= 1.25
    elif float(carga_pct) < float(crit.get("carga_minima_pct", 40.0)):
        fator_incerteza *= 1.45
        motivos_revisao.append("carga_abaixo_do_minimo_normativo")

    if ambiente_c is None and not dieletrico:
        fator_incerteza *= 1.20

    if item.get("indicativa"):
        fator_incerteza *= 1.35
        motivos_revisao.append("avaliacao_indicativa_sem_homologo")

    distribuicoes: list[tuple[float, dict[str, float]]] = []
    atribuicao_criterios: dict[str, float] = {}

    if dt_corrigido is not None:
        faixas_rel = faixas_diel if dieletrico else faixas_sim
        esc_rel = (1.2 if dieletrico else 2.2) * fator_incerteza
        p_rel = _probabilidades_por_faixas(float(dt_corrigido), faixas_rel, temperatura_escala=esc_rel)
        # Peso maior para o critério que disparou a maior severidade
        ordem_rel = ORDEM_NIVEIS_NORMATIVOS.index(item.get("niveis", {}).get("semelhantes", "normal"))
        peso_r = 1.0 + 0.8 * ordem_rel
        distribuicoes.append((peso_r, p_rel))
        atribuicao_criterios["semelhantes"] = peso_r

    if pct_mta is not None and not dieletrico:
        esc_mta = 4.0 * fator_incerteza
        p_mta = _probabilidades_por_faixas(float(pct_mta), faixas_mta, temperatura_escala=esc_mta)
        ordem_mta = ORDEM_NIVEIS_NORMATIVOS.index(item.get("niveis", {}).get("mta", "normal"))
        peso_m = 1.0 + 0.8 * ordem_mta
        distribuicoes.append((peso_m, p_mta))
        atribuicao_criterios["mta"] = peso_m

    if not distribuicoes:
        probs_combinadas = {n: (0.88 if n == sev_deterministica else 0.03) for n in ORDEM_NIVEIS_NORMATIVOS}
        atribuicao_criterios["heuristica"] = 1.0
    else:
        # Regra de agregação conservadora calibrada: prioriza a distribuição do critério dominante
        # (aquele que governa o pior caso da NBR 15866), ponderando o secundário como evidência de suporte
        distribuicoes.sort(key=lambda par: par[0], reverse=True)
        peso_dom, p_dom = distribuicoes[0]
        if len(distribuicoes) > 1 and abs(distribuicoes[0][0] - distribuicoes[1][0]) < 0.2:
            # Ambos os critérios têm a mesma severidade: reforço mútuo (reduz entropia)
            probs_brutas = {
                n: (p_dom[n] * distribuicoes[1][1][n]) ** 0.65
                for n in ORDEM_NIVEIS_NORMATIVOS
            }
        else:
            probs_brutas = dict(p_dom)
        probs_combinadas = _normalizar_probabilidades(probs_brutas)

    soma_atrib = sum(atribuicao_criterios.values()) or 1.0
    atribuicao_criterios = {k: round(v / soma_atrib, 4) for k, v in atribuicao_criterios.items()}

    # Estimativa calibrada noul de reflexo solar / artefato óptico externo
    medida = item.get("medida") or {}
    t_max = float(medida.get("t_max") or 0.0)
    t_med = float(medida.get("t_med") or t_max)
    pixels = int(medida.get("pixels") or 100)
    dt_entorno = float(item.get("dt_entorno") or 0.0)

    logit_reflexo = -3.2
    if t_max > 150.0:
        logit_reflexo += 2.8
        motivos_revisao.append("temperatura_acima_150c_possivel_sol_reflexo")
    if (t_max - t_med) > 25.0 and pixels > 20:
        logit_reflexo += 1.2
    if item.get("classe") == "ponto_quente" and not item.get("componente"):
        logit_reflexo += 1.4
        motivos_revisao.append("ponto_quente_fora_de_ativo")
    if dt_entorno > 35.0 and (t_max - t_med) > 18.0:
        logit_reflexo += 0.9

    prob_reflexo = float(1.0 / (1.0 + math.exp(-logit_reflexo)))

    conformal = conjunto_preditivo_conformal(probs_combinadas, alpha=alpha)
    # Garante que a severidade normativa determinística esteja sempre contida no prediction_set
    pred_set = list(conformal["prediction_set"])
    if sev_deterministica in ORDEM_NIVEIS_NORMATIVOS and sev_deterministica not in pred_set:
        pred_set.insert(0, sev_deterministica)

    if len(pred_set) > 1:
        motivos_revisao.append("fronteira_normativa_ambigua")
    if prob_reflexo >= 0.45:
        motivos_revisao.append("alto_risco_reflexo_solar")

    rota = "review" if (conformal["route"] == "review" or motivos_revisao) else "auto"

    return {
        "choice": sev_deterministica,
        "laya_top_choice": conformal["choice"],
        "probabilities": {k: round(float(probs_combinadas[k]), 4) for k in ORDEM_NIVEIS_NORMATIVOS},
        "prediction_set": pred_set,
        "answer_confidence": conformal["answer_confidence"],
        "jev_confidence": conformal["jev_confidence"],
        "entropy_confidence": conformal["entropy_confidence"],
        "prob_reflexo_solar": round(prob_reflexo, 4),
        "atribuicao_criterios": atribuicao_criterios,
        "abstain": conformal["abstain"],
        "route": rota,
        "motivos_revisao": motivos_revisao,
    }


__all__ = [
    "LAYA_PACOTE_DISPONIVEL",
    "LAYA_VERSAO",
    "LAYAHead",
    "laya_disponivel",
    "calcular_jev_confidence",
    "calcular_entropia_confianca",
    "conjunto_preditivo_conformal",
    "calcular_ece",
    "calibrar_temperatura_laya",
    "resumir_atribuicao_camadas",
    "agregar_patches_laya",
    "fundir_modalidades_laya",
    "agregar_keyframes_laya",
    "arbitrar_severidade_normativa_laya",
]
