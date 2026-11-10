"""Medição por região e classificação de severidade.

Segue a ABNT NBR 15866: cada anomalia é avaliada contra referências explícitas.

- **Absoluta:** a temperatura projetada para plena carga, T_amb + (T_medida − T_amb)·(100/carga)^n,
  comparada com a máxima temperatura admissível (MTA) do componente (``referencias.py``).
  Informa também quanto de carga cabe até a MTA: sqrt((MTA − T_amb) / (T_medida − T_amb)).
- **Relativa:** ΔT contra o componente semelhante (mesma classe, outras fases), corrigido pela
  carga nas partes resistivas. Para-raios e isoladores têm faixa própria, sem correção de carga.
- **Ar ambiente (opcional, NETA MTS):** ΔT sobre o ambiente.

A severidade final é a pior das avaliações aplicáveis e registra qual critério a disparou. A
comparação com o entorno imediato é mostrada, mas não classifica: não é critério de norma.

Com um modelo de componentes e o detector de pontos quentes juntos, ``relacionar_componentes``
diz em qual peça está cada ponto quente e o ponto mais quente da cena, e compara as peças iguais.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from nucleo import referencias

NIVEIS = {
    "normal": {"ordem": 0, "rotulo": "Normal", "acao": "Nenhuma ação."},
    "atencao": {"ordem": 1, "rotulo": "Atenção", "acao": "Corrigir na próxima manutenção periódica."},
    "programar": {"ordem": 2, "rotulo": "Programar reparo", "acao": "Agendar a correção e reinspecionar."},
    "urgente": {"ordem": 3, "rotulo": "Urgente", "acao": "Corrigir o mais rápido possível."},
    "imediato": {"ordem": 4, "rotulo": "Imediato", "acao": "Corrigir imediatamente."},
    # Para-raio ou isolador sem a peça igual de outra fase na imagem: não há com o que comparar.
    "nao_avaliado": {"ordem": -1, "rotulo": "Não avaliado", "acao": "Fotografar junto a mesma peça das outras fases para comparar."},
    # Sem pixel com temperatura (imagem sem dados radiométricos nem escala): não é "normal".
    "sem_medida": {"ordem": -2, "rotulo": "Sem medida", "acao": "Medir com o JPEG radiométrico ou informar a escala."},
}
SEM_CLASSIFICACAO = ("normal", "sem_medida", "nao_avaliado")  # não são anomalias: não viram pendência nem achado

# Faixas brasileiras (NBR 15866 + Infraspection Institute, conforme prática de concessionárias).
CRITERIOS_PADRAO = {
    "nome": "Brasil: NBR 15866 (MTA e ΔT entre semelhantes)",
    # ΔT contra o semelhante em partes que conduzem corrente (°C; nível vale a partir do limite)
    "similares": [[5.0, "atencao"], [10.1, "programar"], [20.1, "urgente"], [40.1, "imediato"]],
    # ΔT contra o semelhante em para-raios e isoladores (°C)
    "dieletrico": [[2.0, "atencao"], [5.0, "programar"], [10.0, "urgente"]],
    # temperatura projetada em % da MTA
    "mta_faixas": [[60.1, "atencao"], [70.1, "programar"], [80.1, "urgente"], [100.1, "imediato"]],
    # ΔT sobre o ar ambiente (NETA MTS); desligado no modelo brasileiro
    "usar_ambiente": False,
    "ambiente": [[1.0, "atencao"], [11.0, "programar"], [21.0, "urgente"], [40.1, "imediato"]],
    "expoente_carga": 2.0,
    "carga_minima_pct": 40.0,
}

CRITERIOS_NETA = {
    "nome": "NETA MTS (ΔT entre semelhantes e sobre o ambiente)",
    "similares": [[1.0, "atencao"], [4.0, "programar"], [15.1, "imediato"]],
    "dieletrico": [[1.0, "atencao"], [4.0, "programar"], [15.1, "imediato"]],
    "mta_faixas": [[100.1, "imediato"]],
    "usar_ambiente": True,
    "ambiente": [[1.0, "atencao"], [11.0, "programar"], [21.0, "urgente"], [40.1, "imediato"]],
    "expoente_carga": 2.0,
    "carga_minima_pct": 40.0,
}

ROTULOS_CRITERIO = {"semelhantes": "ΔT entre semelhantes", "mta": "% da MTA", "ambiente": "ΔT sobre o ambiente"}


@dataclass
class Medida:
    t_max: float
    t_med: float
    t_min: float
    x_max: int
    y_max: int
    pixels: int


def medir(temperatura: np.ndarray, caixa: list[float]) -> Medida | None:
    """Estatísticas dentro da caixa (x0, y0, x1, y1), em pixels da matriz."""
    h, w = temperatura.shape
    x0, y0, x1, y1 = caixa
    xa, ya = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
    xb, yb = min(w, int(np.ceil(x1))), min(h, int(np.ceil(y1)))
    if xb <= xa or yb <= ya:
        return None
    recorte = temperatura[ya:yb, xa:xb]
    ok = np.isfinite(recorte)
    if not ok.any():
        return None
    iy, ix = np.unravel_index(np.nanargmax(recorte), recorte.shape)
    return Medida(
        t_max=float(np.nanmax(recorte)),
        t_med=float(np.nanmean(recorte)),
        t_min=float(np.nanmin(recorte)),
        x_max=int(xa + ix),
        y_max=int(ya + iy),
        pixels=int(ok.sum()),
    )


def medir_ponto(temperatura: np.ndarray, x: float, y: float) -> dict | None:
    """Temperatura de um pixel da matriz, como o "ponto" (spot) das câmeras."""
    h, w = temperatura.shape
    xi, yi = int(np.clip(np.floor(x), 0, w - 1)), int(np.clip(np.floor(y), 0, h - 1))
    v = temperatura[yi, xi]
    return {"t": round(float(v), 2), "x": xi, "y": yi} if np.isfinite(v) else None


def perfil_linha(temperatura: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> dict | None:
    """Temperaturas ao longo de uma linha, um valor por pixel percorrido (o "perfil" dos softwares)."""
    h, w = temperatura.shape
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    n = max(n, 2)
    xs = np.clip(np.floor(np.linspace(x0, x1, n)).astype(int), 0, w - 1)
    ys = np.clip(np.floor(np.linspace(y0, y1, n)).astype(int), 0, h - 1)
    valores = temperatura[ys, xs].astype(float)
    ok = np.isfinite(valores)
    if not ok.any():
        return None
    i = int(np.nanargmax(valores))
    return {
        "t_max": round(float(np.nanmax(valores)), 2),
        "t_min": round(float(np.nanmin(valores)), 2),
        "t_med": round(float(np.nanmean(valores)), 2),
        "x_max": int(xs[i]),
        "y_max": int(ys[i]),
        "valores": [round(float(v), 2) if np.isfinite(v) else None for v in valores],
    }


def medir_medicoes(temperatura: np.ndarray, medicoes: list[dict]) -> list[dict]:
    """Pontos (P1, P2…) e linhas (L1, L2…) do usuário, com os valores na matriz atual."""
    saida, n = [], {"ponto": 0, "linha": 0}
    for m in medicoes:
        tipo = m.get("tipo")
        if tipo not in n:
            continue
        n[tipo] += 1
        item = {**m, "nome": f"{'P' if tipo == 'ponto' else 'L'}{n[tipo]}"}
        if tipo == "ponto":
            item["valor"] = medir_ponto(temperatura, m["x"], m["y"])
        else:
            item["valor"] = perfil_linha(temperatura, m["x0"], m["y0"], m["x1"], m["y1"])
        saida.append(item)
    return saida


def otsu(valores: np.ndarray, caixas: int = 256) -> float:
    """Limiar que melhor separa dois grupos de valores (fundo frio × objetos)."""
    hist, bordas = np.histogram(valores, bins=caixas)
    centros = (bordas[:-1] + bordas[1:]) / 2
    peso = np.cumsum(hist)
    peso_fim = peso[-1] - peso
    soma = np.cumsum(hist * centros)
    media_ini = soma / np.maximum(peso, 1)
    media_fim = (soma[-1] - soma) / np.maximum(peso_fim, 1)
    variancia = peso * peso_fim * (media_ini - media_fim) ** 2
    return float(centros[int(np.argmax(variancia[:-1]))])


def mascara_objetos(temperatura: np.ndarray) -> np.ndarray:
    """Pixels de equipamento, separados do fundo frio (céu) pelo limiar de Otsu."""
    ok = np.isfinite(temperatura)
    if ok.sum() < 50:
        return ok
    return ok & (np.nan_to_num(temperatura, nan=-1e9) > otsu(temperatura[ok]))


def temperatura_entorno(
    temperatura: np.ndarray, caixa: list[float], largura: int = 4, outras=(), objetos: np.ndarray | None = None
) -> float | None:
    """Mediana de um anel em volta da caixa (só pixels de equipamento, nunca o céu)."""
    h, w = temperatura.shape
    x0, y0, x1, y1 = (int(round(v)) for v in caixa)
    anel = np.zeros((h, w), dtype=bool)
    anel[max(0, y0 - largura) : min(h, y1 + largura), max(0, x0 - largura) : min(w, x1 + largura)] = True
    anel[max(0, y0) : min(h, y1), max(0, x0) : min(w, x1)] = False
    for c in outras:
        a0, b0, a1, b1 = (int(round(v)) for v in c)
        anel[max(0, b0) : min(h, b1), max(0, a0) : min(w, a1)] = False
    base = np.isfinite(temperatura) if objetos is None else objetos
    valores = temperatura[anel & base]
    if valores.size >= 5:
        return float(np.median(valores))
    todos = temperatura[base]
    return float(np.median(todos)) if todos.size >= 5 else None


def nivel_por_limites(valor: float | None, limites: list) -> str:
    nivel = "normal"
    if valor is None:
        return nivel
    for limite, nome in limites:
        if valor >= limite:
            nivel = nome
    return nivel


def pior(niveis) -> str:
    niveis = list(niveis) or ["normal"]
    return max(niveis, key=lambda n: NIVEIS[n]["ordem"])


def _mensagem(sev: str, criticos: list[dict]) -> str:
    """Resumo em uma frase: onde, por qual critério e o que fazer. Com muitas regiões, só a pior."""

    def nome(i: dict) -> str:
        return i.get("nome") or i.get("classe") or "região"

    def quanto(i: dict) -> str:
        if i["niveis"].get("mta") == sev and i.get("pct_mta") is not None:
            return f"{i['pct_mta']:.0f}% da MTA"
        if i["niveis"].get("semelhantes") == sev and i.get("dt_corrigido") is not None:
            return f"ΔT {i['dt_corrigido']:.1f} °C entre fases".replace(".", ",")
        return ""

    n = NIVEIS[sev]
    motivo = " e ".join(sorted({c for i in criticos for c in (i["criterio_disparo"] or [])}))
    if len(criticos) <= 2:
        onde = " e ".join(f"{nome(i)} ({quanto(i)})" if quanto(i) else nome(i) for i in criticos)
        return f"{n['rotulo']} em {onde}, por {motivo}. {n['acao']}"
    piores = max(criticos, key=lambda i: (i.get("pct_mta") or 0.0, i.get("dt_corrigido") or 0.0))
    detalhe = f" ({quanto(piores)})" if quanto(piores) else ""
    return f"{len(criticos)} regiões em nível {n['rotulo'].lower()}, por {motivo}. A mais crítica é {nome(piores)}{detalhe}. {n['acao']}"


def _referencia_semelhantes(itens: list[dict]) -> float:
    maximos = sorted(i["medida"]["t_max"] for i in itens)
    return float(np.median(maximos)) if len(maximos) >= 3 else maximos[0]


# ---------------------------------------------------------------- Pareamento Contextual Trifásico (UniVAD C³ + SAM-LAD)


def calcular_afinidade_contextual(item_a: dict, item_b: dict) -> float:
    """Calcula a afinidade contextual entre dois ativos segundo UniVAD (C³) e SAM-LAD (DCGA).

    Combina:
    1. Similaridade semântica/visual DINOv2 (embeddings ou distribuição de scores);
    2. Consistência de escala geométrica (altura e largura das caixas/máscaras);
    3. Alinhamento espacial de barramento/perspectiva (ordenada vertical similar).
    """
    ca = item_a.get("caixa") or [0.0, 0.0, 10.0, 10.0]
    cb = item_b.get("caixa") or [0.0, 0.0, 10.0, 10.0]

    wa = max(float(ca[2]) - float(ca[0]), 1.0)
    ha = max(float(ca[3]) - float(ca[1]), 1.0)
    wb = max(float(cb[2]) - float(cb[0]), 1.0)
    hb = max(float(cb[3]) - float(cb[1]), 1.0)

    yca = 0.5 * (float(ca[1]) + float(ca[3]))
    ycb = 0.5 * (float(cb[1]) + float(cb[3]))

    # 1. Similaridade visual / semântica
    emb_a = item_a.get("embedding_dinov2")
    emb_b = item_b.get("embedding_dinov2")
    scores_a = (item_a.get("classificacao_dinov2") or {}).get("scores")
    scores_b = (item_b.get("classificacao_dinov2") or {}).get("scores")

    if emb_a is not None and emb_b is not None:
        va = np.asarray(emb_a, dtype=np.float32).ravel()
        vb = np.asarray(emb_b, dtype=np.float32).ravel()
        na = max(float(np.linalg.norm(va)), 1e-12)
        nb = max(float(np.linalg.norm(vb)), 1e-12)
        sim_vis = float(np.clip(np.dot(va / na, vb / nb), 0.0, 1.0))
    elif isinstance(scores_a, dict) and isinstance(scores_b, dict) and scores_a and scores_b:
        chaves = sorted(set(scores_a) | set(scores_b))
        va = np.array([float(scores_a.get(k, 0.0)) for k in chaves], dtype=np.float32)
        vb = np.array([float(scores_b.get(k, 0.0)) for k in chaves], dtype=np.float32)
        na = max(float(np.linalg.norm(va)), 1e-12)
        nb = max(float(np.linalg.norm(vb)), 1e-12)
        sim_vis = float(np.clip(np.dot(va / na, vb / nb), 0.0, 1.0))
    else:
        cls_a = item_a.get("classe")
        cls_b = item_b.get("classe")
        sim_vis = 1.0 if (cls_a and cls_a == cls_b and cls_a != "ponto_quente") else 0.0

    # 2. Consistência de escala (altura e largura)
    sim_h = min(ha, hb) / max(ha, hb)
    sim_w = min(wa, wb) / max(wa, wb)
    sim_escala = 0.65 * sim_h + 0.35 * sim_w

    # 3. Alinhamento espacial (componentes trifásicos costumam estar na mesma bancada/altura)
    desvio_y = abs(yca - ycb) / max(ha, hb, 10.0)
    sim_espacial = math.exp(-desvio_y / 1.5)

    afinidade = 0.50 * sim_vis + 0.30 * sim_escala + 0.20 * sim_espacial
    return float(np.clip(afinidade, 0.0, 1.0))


def agrupar_homologos_trifasicos(
    itens: list[dict],
    limiar_afinidade: float = 0.68,
) -> list[dict[str, Any]]:
    """Agrupa ativos homólogos (ex.: Fases A, B e C) por grafo de afinidade contextual (UniVAD C³ / SAM-LAD).

    Para cada grupo homólogo formado:
    - Ordena os ativos espacialmente da esquerda para a direita (Fase A -> B -> C);
    - Elege automaticamente o componente homólogo mais frio como referência saudável (T_min_homologo)
      e calcula também a mediana normativa (T_ref_mediana);
    - Calcula o score de anomalia lógica térmica/estrutural (SAM-LAD) de cada fase.
    """
    validos = [
        it for it in itens
        if it.get("medida") and it.get("classe") not in (None, "", "ponto_quente")
    ]
    n = len(validos)
    if n < 2:
        return []

    visitados = [False] * n
    grupos_brutos: list[list[dict]] = []

    for i in range(n):
        if visitados[i]:
            continue
        cls_i = validos[i].get("classe")
        tem_dino_i = bool(validos[i].get("embedding_dinov2") or validos[i].get("classificacao_dinov2"))
        # Regiões genéricas "componente" sem DINOv2 não são agrupadas às cegas
        if cls_i == "componente" and not tem_dino_i:
            continue

        grupo_atual = [validos[i]]
        visitados[i] = True

        for j in range(i + 1, n):
            if visitados[j]:
                continue
            cls_j = validos[j].get("classe")
            tem_dino_j = bool(validos[j].get("embedding_dinov2") or validos[j].get("classificacao_dinov2"))
            if cls_j == "componente" and not tem_dino_j:
                continue

            mesma_classe_nomeada = (
                cls_i == cls_j and cls_i not in ("componente", "equipamento")
            )
            afinidade = calcular_afinidade_contextual(validos[i], validos[j])
            if mesma_classe_nomeada or afinidade >= limiar_afinidade:
                grupo_atual.append(validos[j])
                visitados[j] = True

        if len(grupo_atual) >= 2:
            grupos_brutos.append(grupo_atual)

    saida_grupos: list[dict[str, Any]] = []
    rotulos_fases_trio = ("A", "B", "C")

    for idx_g, g in enumerate(grupos_brutos, start=1):
        # Ordena da esquerda para a direita pela coordenada X central
        g_ordenado = sorted(
            g,
            key=lambda item: 0.5 * (float(item["caixa"][0]) + float(item["caixa"][2])),
        )
        # Calcula afinidade média intra-grupo
        pares_af = []
        for a_idx in range(len(g_ordenado)):
            for b_idx in range(a_idx + 1, len(g_ordenado)):
                pares_af.append(calcular_afinidade_contextual(g_ordenado[a_idx], g_ordenado[b_idx]))
        afinidade_media = float(np.mean(pares_af)) if pares_af else 1.0

        mais_frio = min(g_ordenado, key=lambda item: float(item["medida"]["t_max"]))
        t_frio = float(mais_frio["medida"]["t_max"])
        t_mediana = _referencia_semelhantes(g_ordenado)
        t_quente = max(float(item["medida"]["t_max"]) for item in g_ordenado)
        amplitude = round(t_quente - t_frio, 2)

        classe_grupo = g_ordenado[0].get("classe") or "componente"
        id_grupo = f"homologo_{classe_grupo}_{idx_g}"

        membros_resumo = []
        for pos, item in enumerate(g_ordenado):
            if len(g_ordenado) == 3:
                fase = rotulos_fases_trio[pos]
            else:
                fase = str(pos + 1)

            t_item = float(item["medida"]["t_max"])
            dt_frio = round(max(t_item - t_frio, 0.0), 2)
            dt_mediana = round(max(t_item - t_mediana, 0.0), 2)
            # Score de anomalia lógica SAM-LAD (normalizado em [0, 1] para desvios até 25 °C)
            score_logico = round(float(1.0 - math.exp(-dt_frio / 12.0)), 4)

            info_membro = {
                "grupo_id": id_grupo,
                "fase_estimada": fase,
                "referencia_fria_id": mais_frio.get("id") or mais_frio.get("nome"),
                "referencia_fria_nome": mais_frio.get("nome") or mais_frio.get("classe"),
                "t_ref_fria_c": round(t_frio, 2),
                "t_ref_mediana_c": round(t_mediana, 2),
                "dt_contra_fria_c": dt_frio,
                "dt_contra_mediana_c": dt_mediana,
                "afinidade_contextual": round(afinidade_media, 4),
                "score_anomalia_logica": score_logico,
            }
            item["pareamento_homologo"] = info_membro
            membros_resumo.append({
                "id": item.get("id"),
                "nome": item.get("nome") or item.get("classe"),
                "classe": item.get("classe"),
                "fase_estimada": fase,
                "t_max": round(t_item, 2),
                "dt_contra_fria_c": dt_frio,
                "dt_contra_mediana_c": dt_mediana,
                "score_anomalia_logica": score_logico,
            })

        saida_grupos.append({
            "grupo_id": id_grupo,
            "classe": classe_grupo,
            "total_homologos": len(g_ordenado),
            "trifasico": len(g_ordenado) == 3,
            "afinidade_contextual": round(afinidade_media, 4),
            "referencia_fria": {
                "id": mais_frio.get("id"),
                "nome": mais_frio.get("nome") or mais_frio.get("classe"),
                "t_max": round(t_frio, 2),
            },
            "t_ref_mediana_c": round(t_mediana, 2),
            "amplitude_termica_c": amplitude,
            "membros": membros_resumo,
        })

    return saida_grupos


# ---------------------------------------------------------------- componentes × pontos quentes

PONTO_QUENTE = "ponto_quente"
LIMITE_CONFERIR_C = 150.0  # acima disso, pedir para conferir se não é o sol ou um reflexo (só aviso; não muda a severidade)
MARGEM_FORA_C = 1.0  # um ponto fora das peças só é citado se for pelo menos isso mais quente que o das peças


def _contem(caixa: list[float], x: float, y: float) -> bool:
    """O pixel (x, y) da matriz cai dentro da caixa (pelo centro do pixel)."""
    x0, y0, x1, y1 = caixa
    return x0 <= x + 0.5 <= x1 and y0 <= y + 0.5 <= y1


def _area(caixa: list[float]) -> float:
    return max(caixa[2] - caixa[0], 0.0) * max(caixa[3] - caixa[1], 0.0)


def _identidade(item: dict) -> dict:
    return {"id": item.get("id"), "nome": item.get("nome") or item.get("classe"), "classe": item.get("classe")}


def componente_em(componentes: list[dict], x: float, y: float) -> dict | None:
    """O componente mais específico que contém o pixel: a menor caixa (o terminal, e não o para-raio inteiro)."""
    candidatos = [c for c in componentes if _contem(c["caixa"], x, y)]
    return min(candidatos, key=lambda c: _area(c["caixa"])) if candidatos else None


def relacionar_componentes(itens: list[dict]) -> tuple[dict | None, list[dict]]:
    """Junta o que o modelo de componentes achou com os pontos quentes.

    - cada ponto quente ganha ``componente``: a peça onde está o pixel mais quente dele;
    - devolve o **ponto mais quente** da cena (entre os componentes, ou entre todas as regiões se não
      houver componentes) e em qual componente ele está;
    - devolve a **comparação entre componentes** do mesmo tipo: Tmáx de cada um, a diferença para a
      referência dos semelhantes (a mesma do critério) e entre o mais quente e o mais frio.
    """
    medidos = [i for i in itens if i.get("medida")]
    componentes = [i for i in medidos if i.get("classe") != PONTO_QUENTE]
    for i in medidos:
        if componentes and i.get("classe") == PONTO_QUENTE:  # sem peças identificadas, não há a que ligar
            dono = componente_em(componentes, i["medida"]["x_max"], i["medida"]["y_max"])
            i["componente"] = _identidade(dono) if dono else None

    base = componentes or medidos
    ponto = None
    if base:
        topo = max(base, key=lambda i: i["medida"]["t_max"])
        x, y = topo["medida"]["x_max"], topo["medida"]["y_max"]
        dono = componente_em(componentes, x, y)
        mancha = next((i for i in medidos if i.get("classe") == PONTO_QUENTE and _contem(i["caixa"], x, y)), None)
        ponto = {
            "t_max": topo["medida"]["t_max"],
            "x": x,
            "y": y,
            "componente": _identidade(dono) if dono else None,
            "dentro_de": [_identidade(c) for c in componentes if c is not dono and _contem(c["caixa"], x, y)],
            "regiao": _identidade(mancha or dono or topo),
            "severidade": (dono or topo).get("severidade", "normal"),
            "mais_quente_fora": None,
        }
        # Um ponto quente fora das peças identificadas (outro equipamento, estrutura) mais quente que elas.
        fora = [i for i in medidos if i.get("classe") == PONTO_QUENTE and componentes and not i.get("componente")
                and i["medida"]["t_max"] >= ponto["t_max"] + MARGEM_FORA_C]
        if fora:
            maior = max(fora, key=lambda i: i["medida"]["t_max"])
            ponto["mais_quente_fora"] = {"t_max": maior["medida"]["t_max"], "regiao": _identidade(maior)}

    grupos: dict[str, list[dict]] = {}
    for c in componentes:
        grupos.setdefault(c.get("classe") or "componente", []).append(c)
    comparacao = []
    for classe, grupo in grupos.items():
        grupo = sorted(grupo, key=lambda i: -i["medida"]["t_max"])
        referencia = _referencia_semelhantes(grupo) if len(grupo) >= 2 else None
        maximos = [i["medida"]["t_max"] for i in grupo]
        comparacao.append({
            "classe": classe,
            "nome": grupo[0]["referencia"]["nome"],
            "aquecimento": grupo[0]["referencia"]["aquecimento"],
            "referencia_c": referencia,
            "amplitude_c": max(maximos) - min(maximos) if len(grupo) >= 2 else None,
            "itens": [{**_identidade(i), "t_max": i["medida"]["t_max"], "t_med": i["medida"]["t_med"],
                       "dt": i["medida"]["t_max"] - referencia if referencia is not None else None,
                       "severidade": i.get("severidade", "normal")} for i in grupo],
        })
    comparacao.sort(key=lambda g: -(g["amplitude_c"] if g["amplitude_c"] is not None else -1.0))
    return ponto, comparacao


def analisar_regioes(
    temperatura: np.ndarray,
    regioes: list[dict],
    ambiente_c: float | None = None,
    carga_pct: float | None = None,
    criterios: dict | None = None,
    componentes: dict | None = None,
) -> tuple[list[dict], dict]:
    """Mede cada região, avalia contra as referências e classifica.

    Cada região é um dicionário com ao menos ``caixa`` e ``classe``.
    """
    crit = {**CRITERIOS_PADRAO, **(criterios or {})}
    biblioteca = componentes or referencias.componentes()
    avisos: list[str] = []
    carga_conhecida = carga_pct is not None and carga_pct > 0
    fator_carga = (100.0 / carga_pct) ** crit["expoente_carga"] if carga_conhecida and carga_pct < 100 else 1.0
    if carga_conhecida and carga_pct < crit["carga_minima_pct"]:
        avisos.append(
            f"Carga de {carga_pct:.0f}% abaixo de {crit['carga_minima_pct']:.0f}%: a projeção para plena carga é pouco confiável."
        )

    saida = []
    caixas = [r["caixa"] for r in regioes]
    objetos = mascara_objetos(temperatura)
    for i, r in enumerate(regioes):
        m = medir(temperatura, r["caixa"])
        item = dict(r)
        ref = referencias.do_componente(item.get("classe", "componente"), biblioteca)
        item["referencia"] = {"nome": ref["nome"], "aquecimento": ref["aquecimento"], "mta_c": ref["mta_c"], "fonte": ref["fonte"]}
        item["medida"] = asdict(m) if m else None
        outras = [c for j, c in enumerate(caixas) if j != i]
        item["entorno_c"] = temperatura_entorno(temperatura, r["caixa"], outras=outras, objetos=objetos) if m else None
        saida.append(item)

    # Pareamento contextual trifásico (UniVAD C³ + SAM-LAD)
    pareamento_trifasico = agrupar_homologos_trifasicos(saida)

    grupos: dict[str, list[dict]] = {}
    for item in saida:
        if item["medida"] and item.get("classe") not in (None, "", "ponto_quente", "componente"):
            grupos.setdefault(item["classe"], []).append(item)
        elif item["medida"] and item.get("classe") == "componente" and item.get("pareamento_homologo"):
            # Quando componentes genéricos foram agrupados por afinidade visual DINOv2 (UniVAD C³)
            gid = item["pareamento_homologo"]["grupo_id"]
            grupos.setdefault(gid, []).append(item)

    for item in saida:
        m = item["medida"]
        ref = item["referencia"]
        dieletrico = ref["aquecimento"] == "dieletrico"
        item.update(
            dt_ref=None, ref_tipo=None, dt_corrigido=None, dt_ambiente=None, dt_entorno=None,
            t_projetada=None, pct_mta=None, margem_mta_c=None, carga_limite=None, avaliacao_absoluta=None,
            niveis={}, criterio_disparo=None,
        )
        if not m:
            item["severidade"] = "sem_medida"
            continue
        if item["entorno_c"] is not None:
            item["dt_entorno"] = m["t_max"] - item["entorno_c"]

        # Relativa: contra o semelhante (por classe ou por agrupamento homólogo C³)
        chave_grupo = item.get("classe")
        if chave_grupo == "componente" and item.get("pareamento_homologo"):
            chave_grupo = item["pareamento_homologo"]["grupo_id"]
        grupo = grupos.get(chave_grupo, [])
        if len(grupo) >= 2:
            item["dt_ref"], item["ref_tipo"] = m["t_max"] - _referencia_semelhantes(grupo), "semelhantes"
            item["dt_corrigido"] = max(item["dt_ref"], 0.0) * (1.0 if dieletrico else fator_carga)
            faixas = crit["dieletrico"] if dieletrico else crit["similares"]
            item["niveis"]["semelhantes"] = nivel_por_limites(item["dt_corrigido"], faixas)
        elif item["dt_entorno"] is not None:
            item["ref_tipo"] = "entorno"

        # Absoluta: contra a MTA
        mta = ref["mta_c"]
        if mta and not dieletrico:
            if ambiente_c is not None:
                elevacao = max(m["t_max"] - ambiente_c, 0.0)
                item["t_projetada"] = ambiente_c + elevacao * fator_carga
                item["avaliacao_absoluta"] = "completa" if carga_conhecida else "sem_carga"
                if elevacao > 0.5 and mta > ambiente_c:
                    fator_corrente = math.sqrt((mta - ambiente_c) / elevacao)
                    item["carga_limite"] = {
                        "vezes_corrente_atual": round(fator_corrente, 2),
                        "pct_nominal": round(fator_corrente * carga_pct, 0) if carga_conhecida else None,
                    }
            else:
                item["t_projetada"] = m["t_max"]
                item["avaliacao_absoluta"] = "sem_ambiente"
            item["pct_mta"] = 100.0 * item["t_projetada"] / mta
            item["margem_mta_c"] = mta - item["t_projetada"]
            item["niveis"]["mta"] = nivel_por_limites(item["pct_mta"], crit["mta_faixas"])

        # Ar ambiente (NETA), se ligado
        if ambiente_c is not None:
            item["dt_ambiente"] = m["t_max"] - ambiente_c
            if crit.get("usar_ambiente"):
                item["niveis"]["ambiente"] = nivel_por_limites(item["dt_ambiente"], crit["ambiente"])

        if dieletrico and not item["niveis"]:
            # Para-raio e isolador só se comparam com a peça igual: sem ela, nada foi avaliado (não é "normal").
            item["severidade"] = "nao_avaliado"
        else:
            item["severidade"] = pior(item["niveis"].values())
        if item["severidade"] != "normal":
            item["criterio_disparo"] = [ROTULOS_CRITERIO[k] for k, v in item["niveis"].items() if v == item["severidade"]]

    for item in saida:
        n = NIVEIS[item["severidade"]]
        item["severidade_rotulo"], item["acao"] = n["rotulo"], n["acao"]
        # Indicativa: sem semelhante para comparar e sem projeção para plena carga.
        item["indicativa"] = (item["severidade"] not in ("sem_medida", "nao_avaliado") and "semelhantes" not in item.get("niveis", {})
                              and item.get("avaliacao_absoluta") in (None, "sem_ambiente"))

    # Arbitragem diagnóstica normativa System-1 calibrada (LAYA / RLCD Conformal)
    try:
        from nucleo.classificacao.laya_aggregator import arbitrar_severidade_normativa_laya

        for item in saida:
            if item.get("medida"):
                item["laya"] = arbitrar_severidade_normativa_laya(
                    item,
                    ambiente_c=ambiente_c,
                    carga_pct=carga_pct,
                    criterios=crit,
                )
    except Exception:
        pass

    validos = temperatura[np.isfinite(temperatura)]
    if not validos.size:
        return saida, _resumo_sem_temperatura(saida, crit, fator_carga)
    sev = pior(i["severidade"] for i in saida)
    criticos = [i for i in saida if i["severidade"] == sev and sev not in SEM_CLASSIFICACAO]
    if sev == "normal":
        mensagem = "Nenhuma região acima dos limites do critério."
    elif sev == "nao_avaliado":
        mensagem = "Nenhuma peça pôde ser avaliada: falta a peça igual de outra fase para comparar."
    elif sev == "sem_medida":
        mensagem = "As regiões marcadas não têm pixels com temperatura."
    else:
        mensagem = _mensagem(sev, criticos)
    nao_avaliadas = [i["nome"] for i in saida if i["severidade"] == "nao_avaliado"]
    if nao_avaliadas:
        nomes = ", ".join(nao_avaliadas[:4]) + ("…" if len(nao_avaliadas) > 4 else "")
        avisos.append(f"Sem avaliação: {nomes}. Para-raios e isoladores só se comparam com a mesma peça das outras "
                      "fases; fotografe as três juntas.")
    if saida and ambiente_c is None and any(i["referencia"]["mta_c"] and i["referencia"]["aquecimento"] != "dieletrico" for i in saida):
        avisos.append(
            "Sem temperatura ambiente, a comparação com a MTA usa a temperatura medida, sem projeção para plena carga. "
            "Informe ambiente e carga na aba Condições."
        )
    elif saida and not carga_conhecida and ambiente_c is not None:
        avisos.append("Sem a carga do momento, a projeção considera que a medição foi feita em plena carga.")
    if any(i["indicativa"] for i in saida):
        avisos.append(
            "Regiões sem componente semelhante e sem projeção têm classificação indicativa. "
            "Dê a mesma classe às regiões das três fases para comparar semelhantes."
        )
    pcts = [i["pct_mta"] for i in saida if i.get("pct_mta") is not None]
    ponto_mais_quente, comparacao = relacionar_componentes(saida)
    # o ponto mais quente vem da matriz inteira: imagem sem região nenhuma também tem o seu marcador
    finita = np.isfinite(temperatura)
    if finita.any():
        y_max, x_max = np.unravel_index(np.argmax(np.where(finita, temperatura, -np.inf)), temperatura.shape)
        componentes_medidos = [i for i in saida if i.get("medida") and i.get("classe") != PONTO_QUENTE]
        dono = componente_em(componentes_medidos, x_max, y_max)
        mancha = next((i for i in saida if i.get("medida") and i.get("classe") == PONTO_QUENTE
                       and _contem(i["caixa"], x_max, y_max)), None)
        ponto_mais_quente = ponto_mais_quente or {}
        ponto_mais_quente.update(
            t_max=float(temperatura[y_max, x_max]), x=float(x_max), y=float(y_max),
            componente=_identidade(dono) if dono else None,
            dentro_de=[_identidade(c) for c in componentes_medidos if c is not dono and _contem(c["caixa"], x_max, y_max)],
            regiao=_identidade(mancha or dono) if (mancha or dono) else None,
            severidade=(dono or mancha or {}).get("severidade", "normal"),
        )
    if ponto_mais_quente and ponto_mais_quente["t_max"] > LIMITE_CONFERIR_C:
        avisos.append(
            f"O ponto mais quente passa de {LIMITE_CONFERIR_C:.0f} °C ({ponto_mais_quente['t_max']:.0f} °C). "
            "Confira na imagem se não é o sol ou um reflexo dentro da caixa antes de concluir."
        )
    if ponto_mais_quente and ponto_mais_quente.get("mais_quente_fora"):
        fora = ponto_mais_quente["mais_quente_fora"]
        valor = f"{fora['t_max']:.1f}".replace(".", ",")
        avisos.append(f"Há um ponto mais quente fora das peças identificadas: {fora['regiao']['nome']}, {valor} °C.")
    # A severidade vem só de pontos quentes fora das peças que o modelo achou: pode ser defeito num equipamento
    # que o modelo não conhece, ou uma lâmpada, a estrutura, um reflexo. Não some da classificação (deixar
    # passar um defeito é pior), mas pede o olhar de alguém antes de agir.
    decisivas = [i for i in saida if i["severidade"] == sev]
    conferir = (sev not in SEM_CLASSIFICACAO and bool(decisivas)
                and all(i.get("classe") == PONTO_QUENTE and "componente" in i and not i["componente"] for i in decisivas))
    if conferir:
        avisos.insert(0, "Confira antes de agir: a classificação vem de um ponto quente fora das peças identificadas. "
                         "Pode ser defeito em outro equipamento, ou uma lâmpada, a estrutura ou um reflexo.")
    laya_itens = [i.get("laya") for i in saida if i.get("laya")]
    laya_resumo = {
        "total_avaliadas": len(laya_itens),
        "rotas_auto": sum(1 for l in laya_itens if l.get("route") == "auto"),
        "rotas_review": sum(1 for l in laya_itens if l.get("route") == "review"),
        "prob_reflexo_solar_max": max((float(l.get("prob_reflexo_solar", 0.0)) for l in laya_itens), default=0.0),
    } if laya_itens else None

    resumo = {
        "ponto_mais_quente": ponto_mais_quente,
        "comparacao_componentes": comparacao,
        "pareamento_trifasico": pareamento_trifasico,
        "severidade": sev,
        "severidade_rotulo": NIVEIS[sev]["rotulo"],
        "mensagem": mensagem,
        "regioes": len(saida),
        "t_max_cena": float(validos.max()) if validos.size else None,
        "t_min_cena": float(validos.min()) if validos.size else None,
        "maior_pct_mta": max(pcts) if pcts else None,
        "fator_carga": fator_carga,
        "avisos": avisos,
        "criterio": crit["nome"],
        **({"laya": laya_resumo} if laya_resumo else {}),
        **({"conferir": True} if conferir else {}),
        **({"nao_avaliadas": len(nao_avaliadas)} if nao_avaliadas else {}),
    }
    return saida, resumo


def _resumo_sem_temperatura(saida: list[dict], crit: dict, fator_carga: float) -> dict:
    """Resumo de uma imagem sem nenhuma temperatura: os componentes foram achados, a medida não."""
    return {
        "ponto_mais_quente": None,
        "comparacao_componentes": [],
        "pareamento_trifasico": [],
        "severidade": "sem_medida",
        "severidade_rotulo": NIVEIS["sem_medida"]["rotulo"],
        "mensagem": (f"{len(saida)} {'componente identificado' if len(saida) == 1 else 'componentes identificados'}, sem temperatura."
                     if saida else "Nenhum componente identificado e nenhuma temperatura na imagem."),
        "regioes": len(saida),
        "t_max_cena": None,
        "t_min_cena": None,
        "maior_pct_mta": None,
        "fator_carga": fator_carga,
        "avisos": [],
        "criterio": crit["nome"],
        "sem_temperatura": True,
    }
