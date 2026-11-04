"""Classificação de ativos elétricos e anomalias com base em representações fundacionais DINOv2.

O DINOv2 (Meta AI) extrai representações visuais ricas sem supervisão através de arquiteturas Vision
Transformer (ViT). O modelo opera com patches de 14x14 pixels e gera vetores semânticos densos e
invariantes a rotações parciais, iluminação e ruído térmico.

Este módulo implementa o classificador zero-shot/few-shot baseado em galeria de protótipos de
embeddings característicos do setor elétrico:
- Isolador (textura periódica de aletas cerâmicas/poliméricas)
- Bucha (corpo alongado vertical com terminal superior e discos)
- Para-raio (coluna esguia de anéis de varistor de óxido de zinco/silicone)
- Conexão (junções aparafusadas metálicas com reflexos especulares)
- Radiador (painéis verticais de aletas de troca térmica)
- Tanque (superfície plana metálica maciça de transformador)
- Cabo (condutor contínuo/trançado cilíndrico)
- Ponto quente (concentração radial de gradiente térmico de alta energia)
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np
import torch

log = logging.getLogger(__name__)

TAMANHO_PATCH = 14
TAMANHO_MINIMO = 224
IMAGENET_MEDIA = (0.485, 0.456, 0.406)
IMAGENET_DESVIO = (0.229, 0.224, 0.225)
COR_FUNDO_NEUTRO = (128, 128, 128)
TEMPERATURA_SOFTMAX_PADRAO = 0.07
CONFIANCA_MINIMA_AJUSTE = 0.60
LIMIAR_CICLICO_NOCTIS_PADRAO = 0.65
PASTA_PROTOTIPOS_PADRAO = Path(__file__).resolve().parents[2] / "modelos" / "dinov2" / "prototipos_subestacao.npz"

CLASSES_PYRON: tuple[str, ...] = (
    "isolador",
    "bucha",
    "para_raio",
    "conexao",
    "radiador",
    "tanque",
    "transformador",
    "cabo",
    "estrutura",
)

NOMES_CLASSES: dict[str, str] = {
    "isolador": "Isolador",
    "bucha": "Bucha",
    "para_raio": "Para-raio",
    "conexao": "Conexão",
    "radiador": "Radiador",
    "tanque": "Tanque",
    "transformador": "Transformador",
    "cabo": "Cabo",
    "estrutura": "Estrutura",
}


def escolher_dispositivo(preferido: str | torch.device | None = None) -> torch.device:
    """Seleciona GPU CUDA se disponível, senão fallback automático para CPU."""
    if preferido:
        return torch.device(preferido)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def recortar_e_mascarar(
    imagem_rgb: np.ndarray,
    bbox: Sequence[float] | None = None,
    mascara: np.ndarray | None = None,
) -> np.ndarray:
    """Recorta a região de interesse (caixa delimitadora) e aplica máscara com fundo neutro se fornecida."""
    img = np.asarray(imagem_rgb)
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"Imagem RGB deve possuir formato H x W x 3; recebido {img.shape}")

    altura, largura = img.shape[:2]

    if bbox is not None:
        caixa = [float(v) for v in bbox]
        if len(caixa) != 4:
            raise ValueError(f"Caixa deve possuir 4 valores [x0, y0, x1, y1]; recebido {bbox!r}")
        x0 = max(0, min(int(round(caixa[0])), largura - 1))
        y0 = max(0, min(int(round(caixa[1])), altura - 1))
        x1 = max(x0 + 1, min(int(round(caixa[2])), largura))
        y1 = max(y0 + 1, min(int(round(caixa[3])), altura))
        recorte = img[y0:y1, x0:x1].copy()

        if mascara is not None:
            m = np.asarray(mascara)
            if m.shape == (altura, largura):
                m_recorte = m[y0:y1, x0:x1]
            elif m.shape == recorte.shape[:2]:
                m_recorte = m
            else:
                m_recorte = cv2.resize(m.astype(np.uint8), (recorte.shape[1], recorte.shape[0]), interpolation=cv2.INTER_NEAREST)
            fundo_neutro = np.full_like(recorte, COR_FUNDO_NEUTRO, dtype=np.uint8)
            fora = (m_recorte <= 0)
            recorte[fora] = fundo_neutro[fora]
        return recorte

    if mascara is not None:
        m = np.asarray(mascara)
        if m.shape[:2] != (altura, largura):
            m = cv2.resize(m.astype(np.uint8), (largura, altura), interpolation=cv2.INTER_NEAREST)
        recorte = img.copy()
        fundo_neutro = np.full_like(recorte, COR_FUNDO_NEUTRO, dtype=np.uint8)
        fora = (m <= 0)
        recorte[fora] = fundo_neutro[fora]
        return recorte

    return img.copy()


def ajustar_resolucao_vit(imagem_rgb: np.ndarray) -> np.ndarray:
    """Ajusta a imagem para que dimensões sejam estritamente divisíveis por 14 px e no mínimo 224x224."""
    altura, largura = imagem_rgb.shape[:2]
    # Mínimo absoluto de 224 pixels (16 * 14)
    h_alvo = max(TAMANHO_MINIMO, (altura // TAMANHO_PATCH) * TAMANHO_PATCH)
    w_alvo = max(TAMANHO_MINIMO, (largura // TAMANHO_PATCH) * TAMANHO_PATCH)

    # Garantia estrita de divisibilidade pelo patch size de 14 px
    if h_alvo % TAMANHO_PATCH != 0:
        h_alvo = ((h_alvo + TAMANHO_PATCH - 1) // TAMANHO_PATCH) * TAMANHO_PATCH
    if w_alvo % TAMANHO_PATCH != 0:
        w_alvo = ((w_alvo + TAMANHO_PATCH - 1) // TAMANHO_PATCH) * TAMANHO_PATCH

    if (altura, largura) != (h_alvo, w_alvo):
        return cv2.resize(imagem_rgb, (w_alvo, h_alvo), interpolation=cv2.INTER_CUBIC)
    return imagem_rgb


def normalizar_tensor_imagenet(imagem_rgb: np.ndarray, dispositivo: torch.device) -> torch.Tensor:
    """Converte array numpy RGB para tensor float32 normalizado segundo padrões ImageNet (média e desvio)."""
    # Converte para float32 [0.0, 1.0]
    arr = imagem_rgb.astype(np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(dispositivo)

    media = torch.tensor(IMAGENET_MEDIA, dtype=torch.float32, device=dispositivo).view(1, 3, 1, 1)
    desvio = torch.tensor(IMAGENET_DESVIO, dtype=torch.float32, device=dispositivo).view(1, 3, 1, 1)
    return (tensor - media) / desvio


def _normalizar_linhas_l2(matriz: np.ndarray) -> np.ndarray:
    """Garante vetores L2-normalizados ao longo da última dimensão."""
    arr = np.asarray(matriz, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[None, :]
    normas = np.linalg.norm(arr, axis=-1, keepdims=True)
    return arr / np.maximum(normas, 1e-12)


def similaridade_noctis(
    patches_consulta: np.ndarray,
    patches_prototipo: np.ndarray,
    limiar_ciclico: float = LIMIAR_CICLICO_NOCTIS_PADRAO,
) -> float:
    """Calcula similaridade entre bancos de patches via Cyclic Thresholding (NOCTIS, Gandyra et al. 2025).

    Em estruturas repetitivas (aletas de buchas, isoladores e para-raios), o casamento simples (max-pooling)
    colapsa múltiplos patches para o mesmo disco. O Cyclic Thresholding (CT) exige reciprocidade cíclica
    (i -> j* -> i*) ou proximidade espacial recíproca combinada ao limiar mínimo de similaridade.
    """
    q = _normalizar_linhas_l2(patches_consulta)
    p = _normalizar_linhas_l2(patches_prototipo)
    if q.size == 0 or p.size == 0:
        return 0.0

    # Matriz de similaridade cruzada (N_q x N_p)
    sim_matrix = np.matmul(q, p.T)
    nq = sim_matrix.shape[0]

    # Ida: para cada patch de consulta i, melhor patch de protótipo j*
    j_melhor = np.argmax(sim_matrix, axis=1)
    sim_ida = sim_matrix[np.arange(nq), j_melhor]

    # Volta (ciclo): para cada j*, qual o melhor patch de consulta i*
    i_melhor_por_p = np.argmax(sim_matrix, axis=0)
    i_retorno = i_melhor_por_p[j_melhor]

    # Distância cíclica normalizada no espaço de índices dos patches
    if nq > 1:
        dist_ciclica = np.abs(np.arange(nq, dtype=np.float32) - i_retorno.astype(np.float32)) / float(nq - 1)
    else:
        dist_ciclica = np.zeros(nq, dtype=np.float32)

    tolerancia_ciclo = max(1.0 - float(limiar_ciclico), 0.10)
    consistentes = (dist_ciclica <= tolerancia_ciclo) & (sim_ida >= float(limiar_ciclico))

    if np.any(consistentes):
        pesos_ciclo = 1.0 - 0.5 * (dist_ciclica[consistentes] / max(tolerancia_ciclo, 1e-6))
        return float(np.clip(np.average(sim_ida[consistentes], weights=pesos_ciclo), -1.0, 1.0))

    # Fallback suave: média dos top-25% patches mais similares ponderada pela consistência cíclica
    k_top = max(1, nq // 4)
    idx_top = np.argsort(sim_ida)[-k_top:]
    fator_ciclo = np.clip(1.0 - 0.35 * dist_ciclica[idx_top], 0.5, 1.0)
    return float(np.clip(np.mean(sim_ida[idx_top] * fator_ciclo), -1.0, 1.0))


def calcular_anomalia_patches(
    patches_consulta: np.ndarray,
    patches_referencia: np.ndarray,
    k: int = 3,
) -> dict[str, Any]:
    """Calcula anomalia estrutural zero/few-shot baseada em k-NN de patches (AnomalyDINO, 2025).

    Para cada patch da consulta, mede a distância de cosseno (1 - similaridade) para os k patches
    mais próximos na galeria de referência saudável.
    """
    q = _normalizar_linhas_l2(patches_consulta)
    ref = _normalizar_linhas_l2(patches_referencia)
    if q.size == 0 or ref.size == 0:
        return {"score_anomalia": 0.0, "mapa_anomalia": [], "patch_mais_anomalo": 0}

    sim_matrix = np.matmul(q, ref.T)
    k_efetivo = max(1, min(int(k), ref.shape[0]))
    # Maiores similaridades por patch de consulta
    part = np.sort(sim_matrix, axis=1)[:, -k_efetivo:]
    sim_knn = np.mean(part, axis=1)
    distancias = np.clip(1.0 - sim_knn, 0.0, 1.0)  # distância de cosseno normalizada em [0, 1]

    # Score global AnomalyDINO: média do top-2% (mínimo 1 patch) para capturar defeitos pontuais
    n_cauda = max(1, int(distancias.size * 0.02))
    score_global = float(np.mean(np.sort(distancias)[-n_cauda:]))
    patch_max = int(np.argmax(distancias))

    return {
        "score_anomalia": round(score_global, 4),
        "mapa_anomalia": [round(float(v), 4) for v in distancias],
        "patch_mais_anomalo": patch_max,
    }


def gerar_padrao_sintetico(classe: str) -> np.ndarray:
    """Gera padrão visual sintético determinístico representativo da classe para a galeria de protótipos."""
    tam = TAMANHO_MINIMO

    if classe == "isolador":
        img = np.full((tam, tam, 3), 160, dtype=np.uint8)
        for y in range(14, 210, 28):
            cv2.rectangle(img, (40, y), (184, y + 10), (90, 80, 70), -1)
            cv2.rectangle(img, (28, y + 10), (196, y + 16), (210, 200, 190), -1)
            cv2.rectangle(img, (98, y + 16), (126, y + 28), (110, 100, 90), -1)
        return img

    if classe == "bucha":
        img = np.full((tam, tam, 3), 140, dtype=np.uint8)
        cv2.rectangle(img, (98, 14), (126, 42), (200, 200, 210), -1)
        pts = np.array([[70, 210], [154, 210], [130, 42], [94, 42]], np.int32)
        cv2.fillPoly(img, [pts], (120, 115, 110))
        for y in range(56, 196, 20):
            cv2.ellipse(img, (112, y), (35, 6), 0, 0, 360, (70, 65, 60), 2)
        return img

    if classe == "para_raio":
        img = np.full((tam, tam, 3), 150, dtype=np.uint8)
        cv2.rectangle(img, (90, 14), (134, 210), (130, 125, 120), -1)
        for y in range(20, 205, 14):
            cv2.rectangle(img, (75, y), (149, y + 5), (60, 60, 65), -1)
            cv2.rectangle(img, (70, y + 5), (154, y + 8), (220, 215, 210), -1)
        return img

    if classe == "conexao":
        img = np.full((tam, tam, 3), 120, dtype=np.uint8)
        cv2.rectangle(img, (42, 60), (182, 164), (190, 175, 140), -1)
        for cx, cy in [(75, 90), (149, 90), (75, 134), (149, 134)]:
            cv2.circle(img, (cx, cy), 16, (80, 80, 85), -1)
            cv2.circle(img, (cx, cy), 10, (230, 230, 240), -1)
        return img

    if classe == "radiador":
        img = np.full((tam, tam, 3), 130, dtype=np.uint8)
        for x in range(28, 200, 14):
            cv2.rectangle(img, (x, 28), (x + 6, 196), (70, 75, 80), -1)
            cv2.rectangle(img, (x + 6, 28), (x + 10, 196), (190, 195, 200), -1)
        return img

    if classe == "transformador":
        img = np.full((tam, tam, 3), 105, dtype=np.uint8)
        cv2.rectangle(img, (40, 60), (184, 200), (130, 135, 130), -1)
        cv2.rectangle(img, (40, 60), (184, 200), (70, 75, 70), 3)
        for bx in (70, 112, 154):
            cv2.rectangle(img, (bx - 6, 25), (bx + 6, 60), (190, 185, 180), -1)
            cv2.ellipse(img, (bx, 25), (8, 4), 0, 0, 360, (220, 220, 230), -1)
        for rx in (20, 28, 196, 204):
            cv2.rectangle(img, (rx - 3, 75), (rx + 3, 185), (85, 90, 95), -1)
        return img

    if classe == "tanque":
        img = np.full((tam, tam, 3), 110, dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (204, 204), (135, 140, 135), -1)
        cv2.rectangle(img, (20, 20), (204, 204), (70, 75, 70), 4)
        for bx in range(35, 195, 30):
            cv2.circle(img, (bx, 28), 5, (50, 50, 50), -1)
            cv2.circle(img, (bx, 196), 5, (50, 50, 50), -1)
        return img

    if classe == "cabo":
        img = np.full((tam, tam, 3), 160, dtype=np.uint8)
        cv2.line(img, (14, 180), (210, 44), (40, 40, 40), 24)
        cv2.line(img, (14, 180), (210, 44), (170, 170, 175), 14)
        cv2.line(img, (14, 180), (210, 44), (230, 230, 235), 4)
        return img

    if classe == "estrutura":
        img = np.full((tam, tam, 3), 60, dtype=np.uint8)
        cv2.line(img, (20, 20), (204, 204), (190, 195, 200), 6)
        cv2.line(img, (204, 20), (20, 204), (190, 195, 200), 6)
        cv2.line(img, (20, 20), (20, 204), (160, 165, 170), 8)
        cv2.line(img, (204, 20), (204, 204), (160, 165, 170), 8)
        return img

    return np.full((tam, tam, 3), 128, dtype=np.uint8)


class DINOv2Classifier:
    """Classificador de alta precisão baseado em embeddings DINOv2 e galeria prototípica.

    Implementado sob padrão Singleton thread-safe com lazy loading dos pesos da rede.
    Suporta tokens globais [CLS] e tokens espaciais de patches para correspondência NOCTIS
    e detecção de anomalias estruturais AnomalyDINO.
    """

    _instancia: DINOv2Classifier | None = None
    _trava_singleton: threading.Lock = threading.Lock()

    @classmethod
    def obter_instancia(
        cls,
        modelo: Any | None = None,
        dispositivo: str | torch.device | None = None,
        prototipos: dict[str, np.ndarray] | None = None,
        temperatura: float = TEMPERATURA_SOFTMAX_PADRAO,
    ) -> DINOv2Classifier:
        """Garante acesso à instância global única do classificador de maneira thread-safe."""
        if cls._instancia is None:
            with cls._trava_singleton:
                if cls._instancia is None:
                    cls._instancia = cls(
                        modelo=modelo,
                        dispositivo=dispositivo,
                        prototipos=prototipos,
                        temperatura=temperatura,
                    )
        return cls._instancia

    def __init__(
        self,
        modelo: Any | None = None,
        dispositivo: str | torch.device | None = None,
        prototipos: dict[str, np.ndarray] | None = None,
        temperatura: float = TEMPERATURA_SOFTMAX_PADRAO,
        prototipos_patches: dict[str, np.ndarray] | None = None,
    ) -> None:
        self.dispositivo = escolher_dispositivo(dispositivo)
        self.temperatura = float(temperatura)
        self._trava_operacao = threading.Lock()
        self._modelo = modelo
        self._prototipos: dict[str, np.ndarray] = dict(prototipos) if prototipos is not None else {}
        self._prototipos_patches: dict[str, np.ndarray] = (
            {k: _normalizar_linhas_l2(v) for k, v in prototipos_patches.items()}
            if prototipos_patches is not None
            else {}
        )

        if self._modelo is not None and not self._prototipos:
            self._inicializar_prototipos()

    def _garantir_modelo(self) -> Any:
        """Carrega o modelo DINOv2 via torch.hub sob demanda (lazy loading) e inicializa protótipos."""
        if self._modelo is not None:
            return self._modelo

        with self._trava_operacao:
            if self._modelo is not None:
                return self._modelo

            log.info("Carregando modelo DINOv2 (dinov2_vits14) no dispositivo %s...", self.dispositivo)
            try:
                # Carrega o modelo ViT-S/14 oficial do repositório da Meta
                modelo_carregado = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14")
                modelo_carregado.to(self.dispositivo)
                modelo_carregado.eval()
                self._modelo = modelo_carregado
            except Exception as erro:
                raise RuntimeError(f"Falha ao carregar pesos do DINOv2: {erro}") from erro

            if not self._prototipos:
                self._inicializar_prototipos()

            return self._modelo

    def _inicializar_prototipos(self) -> None:
        """Carrega galeria persistida em .npz se existir; caso contrário, gera protótipos base."""
        if PASTA_PROTOTIPOS_PADRAO.is_file():
            if self.carregar_galeria(PASTA_PROTOTIPOS_PADRAO):
                return

        for classe in CLASSES_PYRON:
            padrao = gerar_padrao_sintetico(classe)
            emb_cls, emb_patches, _ = self._inferir_features_brutas(padrao)
            self._prototipos[classe] = emb_cls
            self._prototipos_patches[classe] = emb_patches

    def _inferir_features_brutas(self, imagem_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
        """Extrai simultaneamente o token global [CLS] e os patch tokens densos L2-normalizados."""
        ajustada = ajustar_resolucao_vit(imagem_rgb)
        h_aj, w_aj = ajustada.shape[:2]
        grid_size = (h_aj // TAMANHO_PATCH, w_aj // TAMANHO_PATCH)
        tensor = normalizar_tensor_imagenet(ajustada, self.dispositivo)
        modelo = self._modelo if self._modelo is not None else self._garantir_modelo()

        with torch.no_grad():
            if hasattr(modelo, "forward_features") and callable(getattr(modelo, "forward_features")):
                feats = modelo.forward_features(tensor)
                if isinstance(feats, dict) and "x_norm_clstoken" in feats and "x_norm_patchtokens" in feats:
                    cls_t = feats["x_norm_clstoken"]
                    patches_t = feats["x_norm_patchtokens"]
                    cls_norm = torch.norm(cls_t, p=2, dim=-1, keepdim=True)
                    cls_l2 = (cls_t / torch.clamp(cls_norm, min=1e-12)).squeeze(0).detach().cpu().numpy().astype(np.float32)

                    p_norm = torch.norm(patches_t, p=2, dim=-1, keepdim=True)
                    patches_l2 = (patches_t / torch.clamp(p_norm, min=1e-12)).squeeze(0).detach().cpu().numpy().astype(np.float32)
                    return cls_l2, patches_l2, grid_size

            saida = modelo(tensor)
            if hasattr(saida, "shape") and len(saida.shape) > 2:
                cls_t = saida[:, 0]
                patches_t = saida[:, 1:] if saida.shape[1] > 1 else saida
            else:
                cls_t = saida
                # Fallback determinístico para mocks simples que só retornam [B, D]
                num_patches = max(1, grid_size[0] * grid_size[1])
                patches_t = cls_t.unsqueeze(1).repeat(1, min(num_patches, 16), 1)

            norm = torch.norm(cls_t, p=2, dim=-1, keepdim=True)
            cls_l2 = (cls_t / torch.clamp(norm, min=1e-12)).squeeze(0).detach().cpu().numpy().astype(np.float32)

            p_norm = torch.norm(patches_t, p=2, dim=-1, keepdim=True)
            patches_l2 = (patches_t / torch.clamp(p_norm, min=1e-12)).squeeze(0).detach().cpu().numpy().astype(np.float32)

        return cls_l2, patches_l2, grid_size

    def _inferir_embedding_bruto(self, imagem_rgb: np.ndarray) -> np.ndarray:
        """Processa imagem pré-formatada pelo ViT e extrai embedding com L2 norm."""
        cls_l2, _, _ = self._inferir_features_brutas(imagem_rgb)
        return cls_l2

    def extrair_embedding(
        self,
        imagem_rgb: np.ndarray,
        bbox: Sequence[float] | None = None,
        mascara: np.ndarray | None = None,
    ) -> np.ndarray:
        """Recorta, aplica máscara se presente e extrai o embedding unitário (L2 norm) via DINOv2."""
        self._garantir_modelo()
        recorte = recortar_e_mascarar(imagem_rgb, bbox=bbox, mascara=mascara)
        return self._inferir_embedding_bruto(recorte)

    def extrair_features_completas(
        self,
        imagem_rgb: np.ndarray,
        bbox: Sequence[float] | None = None,
        mascara: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Extrai o token [CLS], os patch tokens espaciais e a grade ViT (H_p, W_p)."""
        self._garantir_modelo()
        recorte = recortar_e_mascarar(imagem_rgb, bbox=bbox, mascara=mascara)
        cls_l2, patches_l2, grid_size = self._inferir_features_brutas(recorte)
        return {
            "cls": cls_l2,
            "patches": patches_l2,
            "grid_size": grid_size,
        }

    def registrar_prototipo(
        self,
        classe: str,
        embedding: np.ndarray,
        peso: float = 1.0,
        patches: np.ndarray | None = None,
    ) -> None:
        """Atualiza a galeria de protótipos incorporando novo vetor por média móvel L2-normalizada."""
        vetor = np.asarray(embedding, dtype=np.float32).ravel()
        norm = np.linalg.norm(vetor)
        if norm > 0:
            vetor = vetor / norm

        with self._trava_operacao:
            if classe in self._prototipos:
                atual = self._prototipos[classe]
                novo_centro = atual + float(peso) * vetor
                self._prototipos[classe] = novo_centro / max(np.linalg.norm(novo_centro), 1e-12)
            else:
                self._prototipos[classe] = vetor

            if patches is not None:
                self._atualizar_banco_patches_interno(classe, patches)

    def _atualizar_banco_patches_interno(self, classe: str, patches: np.ndarray, max_patches: int = 256) -> None:
        p_norm = _normalizar_linhas_l2(patches)
        if classe in self._prototipos_patches and self._prototipos_patches[classe].size > 0:
            combinado = np.vstack([self._prototipos_patches[classe], p_norm])
            if combinado.shape[0] > max_patches:
                passo = max(1, combinado.shape[0] // max_patches)
                combinado = combinado[::passo][:max_patches]
            self._prototipos_patches[classe] = combinado
        else:
            if p_norm.shape[0] > max_patches:
                passo = max(1, p_norm.shape[0] // max_patches)
                p_norm = p_norm[::passo][:max_patches]
            self._prototipos_patches[classe] = p_norm

    def salvar_galeria(self, caminho: Path | str | None = None) -> Path:
        """Salva os protótipos [CLS] e bancos de patches em arquivo .npz comprimido."""
        self._garantir_modelo()
        destino = Path(caminho) if caminho is not None else PASTA_PROTOTIPOS_PADRAO
        destino.parent.mkdir(parents=True, exist_ok=True)
        pacote: dict[str, np.ndarray] = {}
        with self._trava_operacao:
            for c, emb in self._prototipos.items():
                pacote[f"cls_{c}"] = np.asarray(emb, dtype=np.float32)
            for c, p in self._prototipos_patches.items():
                pacote[f"patches_{c}"] = np.asarray(p, dtype=np.float32)
        np.savez_compressed(destino, **pacote)
        return destino

    def carregar_galeria(self, caminho: Path | str | None = None) -> bool:
        """Carrega protótipos reais persistidos em .npz."""
        origem = Path(caminho) if caminho is not None else PASTA_PROTOTIPOS_PADRAO
        if not origem.is_file():
            return False
        try:
            with np.load(origem) as dados:
                novos_cls: dict[str, np.ndarray] = {}
                novos_patches: dict[str, np.ndarray] = {}
                for chave in dados.files:
                    if chave.startswith("cls_"):
                        novos_cls[chave[4:]] = np.asarray(dados[chave], dtype=np.float32)
                    elif chave.startswith("patches_"):
                        novos_patches[chave[8:]] = _normalizar_linhas_l2(dados[chave])
            if not novos_cls:
                return False
            with self._trava_operacao:
                self._prototipos.update(novos_cls)
                self._prototipos_patches.update(novos_patches)
            return True
        except Exception as erro:
            log.warning("Não foi possível carregar galeria DINOv2 de %s: %s", origem, erro)
            return False

    @property
    def prototipos(self) -> dict[str, np.ndarray]:
        """Dicionário imutável de leitura dos protótipos cadastrados."""
        self._garantir_modelo()
        return dict(self._prototipos)

    @property
    def prototipos_patches(self) -> dict[str, np.ndarray]:
        """Dicionário de bancos de patch tokens por classe."""
        self._garantir_modelo()
        return dict(self._prototipos_patches)

    def avaliar_anomalia_estrutural(
        self,
        imagem_rgb: np.ndarray,
        classe: str | None = None,
        bbox: Sequence[float] | None = None,
        mascara: np.ndarray | None = None,
        k: int = 3,
    ) -> dict[str, Any]:
        """Avalia anomalia estrutural na peça via k-NN de patch tokens (AnomalyDINO)."""
        feats = self.extrair_features_completas(imagem_rgb, bbox=bbox, mascara=mascara)
        classe_alvo = classe
        if not classe_alvo:
            res_cls = self.classificar(imagem_rgb, bbox=bbox, mascara=mascara)
            classe_alvo = res_cls["classe"]

        ref_patches = self._prototipos_patches.get(classe_alvo)
        if ref_patches is None or ref_patches.size == 0:
            proto_cls = self._prototipos.get(classe_alvo)
            ref_patches = proto_cls[None, :] if proto_cls is not None else feats["patches"]

        resultado = calcular_anomalia_patches(feats["patches"], ref_patches, k=k)
        resultado["classe_referencia"] = classe_alvo
        resultado["grid_size"] = list(feats["grid_size"])
        return resultado

    def classificar(
        self,
        imagem_rgb: np.ndarray,
        bbox: Sequence[float] | None = None,
        mascara: np.ndarray | None = None,
        usar_noctis: bool = False,
        peso_noctis: float = 0.30,
        limiar_ciclico: float = LIMIAR_CICLICO_NOCTIS_PADRAO,
    ) -> dict:
        """Classifica a região calculando similaridade de cosseno contra os protótipos e softmax calibrado.

        Quando ``usar_noctis=True`` e há banco de patches para as classes, combina a similaridade
        global [CLS] com a similaridade de patches filtrada por Cyclic Thresholding (NOCTIS).

        Retorna:
            dict com formato {"classe": str, "confianca": float, "nome": str, "scores": dict[str, float]}
        """
        self._garantir_modelo()
        recorte = recortar_e_mascarar(imagem_rgb, bbox=bbox, mascara=mascara)
        embedding, patches_consulta, _ = self._inferir_features_brutas(recorte)

        peso_ct = float(np.clip(peso_noctis, 0.0, 1.0)) if usar_noctis else 0.0

        # Similaridade de cosseno entre vetores L2-normalizados (+ NOCTIS opcional)
        scores_cosseno: dict[str, float] = {}
        for classe, proto in self._prototipos.items():
            sim_cls = float(np.dot(embedding, proto))
            if peso_ct > 0.0 and classe in self._prototipos_patches:
                sim_ct = similaridade_noctis(
                    patches_consulta,
                    self._prototipos_patches[classe],
                    limiar_ciclico=limiar_ciclico,
                )
                scores_cosseno[classe] = (1.0 - peso_ct) * sim_cls + peso_ct * sim_ct
            else:
                scores_cosseno[classe] = sim_cls

        classes = list(scores_cosseno.keys())
        sims = np.array([scores_cosseno[c] for c in classes], dtype=np.float64)

        # Softmax calibrado com temperatura Boltzmann
        temperatura = max(self.temperatura, 1e-4)
        logits = sims / temperatura
        logits_estabilizados = logits - np.max(logits)
        exp_logits = np.exp(logits_estabilizados)
        probabilidades = exp_logits / np.sum(exp_logits)

        scores_calibrados = {c: float(round(p, 4)) for c, p in zip(classes, probabilidades)}

        melhor_idx = int(np.argmax(probabilidades))
        melhor_classe = classes[melhor_idx]
        melhor_confianca = float(round(probabilidades[melhor_idx], 4))
        nome_legivel = NOMES_CLASSES.get(melhor_classe, melhor_classe)

        return {
            "classe": melhor_classe,
            "confianca": melhor_confianca,
            "nome": nome_legivel,
            "scores": scores_calibrados,
        }
