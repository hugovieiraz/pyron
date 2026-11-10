"""Classificação de ativos elétricos e anomalias com modelos fundacionais (DINOv2 + LAYA)."""

from nucleo.classificacao.dinov2_engine import DINOv2Classifier
from nucleo.classificacao.laya_aggregator import (
    LAYAHead,
    agregar_keyframes_laya,
    agregar_patches_laya,
    arbitrar_severidade_normativa_laya,
    calibrar_temperatura_laya,
    calcular_jev_confidence,
    conjunto_preditivo_conformal,
    fundir_modalidades_laya,
    laya_disponivel,
)

__all__ = [
    "DINOv2Classifier",
    "LAYAHead",
    "agregar_keyframes_laya",
    "agregar_patches_laya",
    "arbitrar_severidade_normativa_laya",
    "calibrar_temperatura_laya",
    "calcular_jev_confidence",
    "conjunto_preditivo_conformal",
    "fundir_modalidades_laya",
    "laya_disponivel",
]
