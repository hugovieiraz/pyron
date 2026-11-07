"""Registro de detectores: tudo que acha regiões numa matriz de temperatura.

Todo detector recebe a matriz de temperatura (°C) e devolve caixas com classe e confiança, em
pixels da matriz. Alguns modelos olham a imagem colorida da câmera em vez da temperatura
(``precisa_imagem``); para eles, a análise passa também essa imagem, no mesmo sentido da matriz.
Há dois tipos:

- **regra**: sem aprendizado, embutido no código (ex.: pontos quentes por limiar adaptativo);
- **aprendizado**: um modelo treinado, instalado como uma pasta em ``modelos/`` com
  ``cartao.json`` (identidade, classes, métricas) e ``modelo.onnx``. Ver ``modelos/LEIA-ME.md``.

O software lista os dois tipos do mesmo jeito; trocar de modelo é escolher outro na lista.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Deteccao:
    classe: str
    caixa: list[float]  # x0, y0, x1, y1 em pixels da matriz
    confianca: float
    grupo: int | None = None  # parte de um para-raio: o índice dele (0, 1, ...) na cena, da esquerda para a direita


@dataclass
class Detector:
    id: str
    nome: str
    tipo: str  # "regra" ou "aprendizado"
    arquitetura: str
    descricao: str
    classes: list[str]
    versao: str = "1.0"
    cartao: dict = field(default_factory=dict)
    nomes: dict = field(default_factory=dict)  # classe -> nome para exibir (ex.: "parte_isoladora" -> "Parte isoladora")
    precisa_imagem: bool = False  # True: o modelo olha a imagem colorida da câmera, não a temperatura

    def detectar(self, temperatura: np.ndarray, imagem: np.ndarray | None = None) -> list[Deteccao]:  # pragma: no cover - interface
        raise NotImplementedError

    def descrever(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "arquitetura": self.arquitetura,
            "descricao": self.descricao,
            "classes": self.classes,
            "versao": self.versao,
            "cartao": self.cartao,
            "nomes": self.nomes,
        }


_CARREGADOS: dict[Path, tuple[float, Detector]] = {}  # modelo já aberto (a sessão ONNX demora a carregar)


def _carregar(cartao: Path) -> Detector:
    from nucleo.detectores.onnx_modelo import DetectorONNX

    marca = max([cartao.stat().st_mtime, *(p.stat().st_mtime for p in cartao.parent.glob("*.onnx"))])
    guardado = _CARREGADOS.get(cartao)
    if guardado and guardado[0] == marca:
        return guardado[1]
    detector = DetectorONNX(cartao.parent)
    _CARREGADOS[cartao] = (marca, detector)
    return detector


def listar(pasta_modelos: Path | None = None) -> list[Detector]:
    """Detectores embutidos, os modelos instalados na pasta e, para cada modelo, ele junto com os pontos quentes.

    Assim dá para escolher um, o outro ou os dois: só as peças (modelo), só o calor (regra) ou as peças
    com os pontos quentes ligados a elas (combinado).
    """
    from nucleo.detectores.pontos_quentes import PontosQuentes, PontosQuentesComSAM2

    pontos = PontosQuentes()
    pontos_sam2 = PontosQuentesComSAM2()
    detectores: list[Detector] = [pontos, pontos_sam2]
    aprendidos: list[Detector] = []
    if pasta_modelos and pasta_modelos.exists():
        for cartao in sorted(pasta_modelos.glob("*/cartao.json")):
            try:
                aprendidos.append(_carregar(cartao))
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as erro:
                detectores.append(Indisponivel(cartao.parent.name, str(erro)))
    return detectores + aprendidos + [Combinado(m, pontos) for m in aprendidos]


def obter(id_: str, pasta_modelos: Path | None = None) -> Detector:
    if id_ == "sam2-dinov2":
        from nucleo.detectores.sam2_dinov2 import SAM2DINOv2Detector
        return SAM2DINOv2Detector()
    for d in listar(pasta_modelos):
        if d.id == id_:
            return d
    raise KeyError(f"modelo '{id_}' não encontrado")


class Combinado(Detector):
    """Um modelo de componentes e o detector de pontos quentes juntos: o que é cada peça e onde está o calor.

    As duas listas de caixas saem juntas; a análise (``nucleo/analise.py``) liga cada ponto quente à
    peça onde ele está, aponta o ponto mais quente da cena e compara as peças iguais.
    """

    def __init__(self, componentes: Detector, pontos: Detector):
        super().__init__(
            id=f"{componentes.id}+{pontos.id}",
            nome=f"{componentes.nome} + pontos quentes",
            tipo="combinado",
            arquitetura=f"{componentes.arquitetura} + regra de contraste térmico",
            descricao="Identifica as peças com o modelo treinado e acha os pontos quentes pela regra de contraste. "
            "A análise diz em qual peça está cada ponto quente, onde está o ponto mais quente e a diferença "
            "de temperatura entre as peças iguais.",
            classes=list(dict.fromkeys(componentes.classes + pontos.classes)),
            versao=componentes.versao,
            cartao={
                "treino": componentes.cartao.get("treino"),
                "metricas": componentes.cartao.get("metricas"),
                "limitacoes": [*componentes.cartao.get("limitacoes", []),
                               "Reflexo do sol pode aparecer como ponto quente dentro da caixa de uma peça; confira valores muito altos."],
            },
            nomes={**pontos.nomes, **componentes.nomes},
            precisa_imagem=componentes.precisa_imagem or pontos.precisa_imagem,
        )
        self.partes = (componentes, pontos)

    def detectar(self, temperatura: np.ndarray, imagem: np.ndarray | None = None) -> list[Deteccao]:
        componentes, pontos = (parte.detectar(temperatura, imagem) for parte in self.partes)
        componentes = organizar_para_raios(componentes)
        return componentes + pontos_fora_das_pecas(pontos, componentes)


# ---------------------------------------------------------------- para-raios e as partes dele

PARA_RAIO = "para_raio"
PARTES_PARA_RAIO = ("terminal_superior", "aletas_isoladoras", "terminal_inferior")  # de cima para baixo
PARTE_DENTRO = 0.5  # fração da caixa da parte que precisa cair no para-raio para ser dele
PARA_RAIO_REPETIDO = 0.6  # dois para-raios que se cobrem nessa fração são o mesmo


def _inter(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _area(c: list[float]) -> float:
    return max(0.0, c[2] - c[0]) * max(0.0, c[3] - c[1])


def _fracao_dentro(a: list[float], b: list[float]) -> float:
    """Quanto da caixa ``a`` cai dentro da ``b`` (0 a 1)."""
    return _inter(a, b) / _area(a) if _area(a) > 0 else 0.0


def organizar_para_raios(deteccoes: list[Deteccao]) -> list[Deteccao]:
    """Arruma as partes de cada para-raio: terminal superior, aletas e terminal inferior viram faixas que não se cobrem.

    O modelo devolve a caixa do para-raio inteiro e a de cada parte, e as caixas se sobrepõem (as aletas costumam
    pegar o para-raio quase todo, os terminais entram nelas). Assim o mesmo pixel quente aparecia em várias regiões.
    Aqui (pedido do Hugo em 03/11/2026):

    - para-raio repetido (caixas que se cobrem) fica um só, o de maior confiança; os para-raios são numerados da
      esquerda para a direita (``grupo``);
    - cada parte vai para o para-raio que a contém e fica cortada na caixa dele; de cada tipo de parte fica uma por
      para-raio (a de maior confiança);
    - num para-raio em pé, as aletas começam onde o terminal superior termina e acabam onde o inferior começa.

    Parte fora de qualquer para-raio e as outras classes passam sem mudança.
    """
    para_raios: list[Deteccao] = []
    for d in sorted((d for d in deteccoes if d.classe == PARA_RAIO), key=lambda d: -d.confianca):
        if all(_fracao_dentro(d.caixa, p.caixa) < PARA_RAIO_REPETIDO and _fracao_dentro(p.caixa, d.caixa) < PARA_RAIO_REPETIDO for p in para_raios):
            para_raios.append(d)
    para_raios.sort(key=lambda d: (d.caixa[0] + d.caixa[2]) / 2)
    saida = [Deteccao(d.classe, list(d.caixa), d.confianca, grupo=i) for i, d in enumerate(para_raios)]

    soltas: list[Deteccao] = []
    por_grupo: dict[int, dict[str, Deteccao]] = {}
    for d in deteccoes:
        if d.classe == PARA_RAIO:
            continue
        if d.classe not in PARTES_PARA_RAIO or not para_raios:
            soltas.append(d)
            continue
        fracoes = [_fracao_dentro(d.caixa, p.caixa) for p in para_raios]
        i = int(np.argmax(fracoes))
        if fracoes[i] < PARTE_DENTRO:
            soltas.append(d)
            continue
        atual = por_grupo.setdefault(i, {}).get(d.classe)
        if atual is None or d.confianca > atual.confianca:
            por_grupo[i][d.classe] = d

    for i, partes in sorted(por_grupo.items()):
        px0, py0, px1, py1 = para_raios[i].caixa
        caixas = {c: [max(d.caixa[0], px0), max(d.caixa[1], py0), min(d.caixa[2], px1), min(d.caixa[3], py1)] for c, d in partes.items()}
        em_pe = (py1 - py0) >= (px1 - px0)
        aletas = caixas.get("aletas_isoladoras")
        if em_pe and aletas:
            if "terminal_superior" in caixas:
                aletas[1] = max(aletas[1], caixas["terminal_superior"][3])
            if "terminal_inferior" in caixas:
                aletas[3] = min(aletas[3], caixas["terminal_inferior"][1])
            if aletas[3] - aletas[1] < 1:  # os terminais cobriram tudo: não sobra faixa de aletas
                del caixas["aletas_isoladoras"]
        for classe in PARTES_PARA_RAIO:
            if classe in caixas and _area(caixas[classe]) > 0:
                saida.append(Deteccao(classe, [round(v, 2) for v in caixas[classe]], partes[classe].confianca, grupo=i))
    return saida + soltas


def pontos_fora_das_pecas(pontos: list[Deteccao], pecas: list[Deteccao]) -> list[Deteccao]:
    """Os pontos quentes que não caem numa peça identificada.

    Dentro de uma peça (para-raio e as partes dele), o ponto mais quente é o da própria peça, que a análise já mede;
    um ponto quente à parte ali repetia a mesma coisa com outra caixa. Fica fora quem tem o centro dentro de uma peça
    ou metade da caixa nela.
    """
    def dentro(d: Deteccao) -> bool:
        cx, cy = (d.caixa[0] + d.caixa[2]) / 2, (d.caixa[1] + d.caixa[3]) / 2
        return any((p.caixa[0] <= cx <= p.caixa[2] and p.caixa[1] <= cy <= p.caixa[3]) or _fracao_dentro(d.caixa, p.caixa) >= PARTE_DENTRO
                   for p in pecas)
    return [d for d in pontos if not dentro(d)]


class Indisponivel(Detector):
    """Modelo instalado com problema (arquivo faltando, cartão inválido): aparece na lista com o erro."""

    def __init__(self, id_: str, erro: str):
        super().__init__(id_, f"{id_} (com erro)", "aprendizado", "-", f"Não foi possível carregar: {erro}", [])

    def detectar(self, temperatura: np.ndarray, imagem: np.ndarray | None = None) -> list[Deteccao]:
        raise ValueError(self.descricao)
