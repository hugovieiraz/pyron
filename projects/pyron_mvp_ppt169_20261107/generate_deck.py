#!/usr/bin/env python3
"""
Gera os 12 slides SVG e 12 notas de orador do Pyron MVP sob o Design System Obsidian Frost.
100% em conformidade estrita com o PPT-Master (svg_quality_checker.py e spec_lock.md).
"""

from pathlib import Path
import html
import re

PROJECT_DIR = Path(__file__).resolve().parent
SVG_DIR = PROJECT_DIR / "svg_output"
NOTES_DIR = PROJECT_DIR / "notes"

# Limpa diretórios antigos para evitar arquivos obsoletos
for f in SVG_DIR.glob("*.svg"):
    f.unlink()
for f in NOTES_DIR.glob("*.md"):
    f.unlink()

SVG_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)

# Paleta Oficial Obsidian Frost (Uppercase Hex)
C_BG = "#10141A"
C_ABYSS = "#0A0E14"
C_SURFACE = "#181C22"
C_SURFACE_HIGH = "#262A31"
C_SURFACE_CONTAINER = "#1C2026"
C_STROKE = "#353940"
C_STROKE_SUBTLE = "#1E293B"
C_FROST_BLUE = "#A2CBF1"
C_FROST_CONTAINER = "#1D4A6A"
C_WHITE = "#FFFFFF"
C_SILVER = "#DFE2EB"
C_MUTED = "#94A3B8"
C_ALERT = "#FFB4AB"
C_ALERT_BG = "#3B1219"

F_TITLE = "EB Garamond, Georgia, serif"
F_BODY = "Plus Jakarta Sans, Segoe UI, Roboto, sans-serif"

def wrap_text_to_lines(text, max_chars):
    words = text.split(" ")
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        w_len = len(w)
        if curr_len + w_len + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += w_len + (1 if curr else 0)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
            curr_len = w_len
    if curr:
        lines.append(" ".join(curr))
    return lines

def multiline_text(x, y, text, max_chars, line_spacing=18, font_size=12, fill=C_SILVER, font_weight="400", font_family=F_BODY):
    lines = wrap_text_to_lines(text, max_chars)
    tspans = []
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else line_spacing
        tspans.append(f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>')
    return f'<text x="{x}" y="{y}" font-family="{font_family}" font-size="{font_size}" font-weight="{font_weight}" fill="{fill}">{"".join(tspans)}</text>'

def header_svg(overline, title, subtitle, page_num):
    pill_w = max(200, min(500, len(overline) * 8 + 48))
    return f"""
    <!-- Header Telemetria -->
    <g id="slide-header" data-pptx-role="header" data-pptx-bounds="56 36 1168 100">
        <rect x="56" y="36" width="{pill_w}" height="24" rx="9999" fill="{C_FROST_CONTAINER}" stroke="{C_FROST_BLUE}" stroke-width="0.75"/>
        <text x="76" y="52" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_WHITE}" letter-spacing="1.5">{html.escape(overline)}</text>
        <text x="56" y="96" font-family="{F_TITLE}" font-size="36" font-weight="600" fill="{C_WHITE}" letter-spacing="0.5">{html.escape(title)}</text>
        <text x="56" y="124" font-family="{F_BODY}" font-size="13" font-weight="400" fill="{C_MUTED}">{html.escape(subtitle)}</text>
    </g>
    <!-- Footer Telemetria -->
    <g id="slide-footer" data-pptx-role="footer" data-pptx-bounds="56 676 1168 28">
        <line x1="56" y1="676" x2="1224" y2="676" stroke="{C_STROKE_SUBTLE}" stroke-width="1"/>
        <text x="56" y="694" font-family="{F_BODY}" font-size="10" font-weight="500" fill="{C_MUTED}">PYRON MVP · TERMOGRAFIA DIGITAL PREDITIVA</text>
        <text x="640" y="694" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="500" fill="{C_MUTED}">CONFORMIDADE ABNT NBR 15866 &amp; IEC 60099-5 · 100% OFFLINE EDGE</text>
        <text x="1224" y="694" text-anchor="end" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">{page_num:02d} / 12</text>
    </g>
    """

def wrap_svg(inner_content, page_num, page_role="content"):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720" data-pptx-page-role="{page_role}">
    <!-- Obsidian Frost Background -->
    <rect width="1280" height="720" fill="{C_BG}"/>
    <!-- Linhas Guia Estruturais -->
    <g id="deck-guides" data-pptx-role="decoration" data-pptx-bounds="56 140 1168 520" stroke="{C_STROKE_SUBTLE}" stroke-width="0.5">
        <line x1="56" y1="140" x2="1224" y2="140"/>
        <line x1="56" y1="660" x2="1224" y2="660"/>
    </g>
    {inner_content}
</svg>"""

# ==============================================================================
# SLIDE 01: HERO & ABSTRACT
# ==============================================================================
s01_content = header_svg("PYRON MVP · VISÃO GERAL", "Pyron MVP: Termografia e Edge AI", "Inspeção Termográfica Automatizada, Física do Efeito Joule e NBR 15866", 1) + f"""
    <!-- Card Hero Mascote 3D (Esquerda) -->
    <g id="hero-mascot" data-pptx-bounds="56 148 460 508">
        <rect x="56" y="148" width="460" height="508" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <image href="../images/pyron_mira3d_hero.png" x="76" y="168" width="420" height="310" preserveAspectRatio="xMidYMid meet"/>
        <rect x="76" y="498" width="160" height="24" rx="9999" fill="{C_FROST_CONTAINER}" stroke="{C_FROST_BLUE}" stroke-width="0.75"/>
        <text x="156" y="514" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_WHITE}" letter-spacing="1">SENTINELA PYRON-01</text>
        <text x="76" y="550" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Mascote Termográfico 3D</text>
        <text x="76" y="578" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Engine procedural Mira-3D / WebGL integrada com<tspan x="76" dy="20">telemetria de temperatura em tempo real.</tspan></text>
        <rect x="76" y="620" width="420" height="24" rx="6" fill="{C_ABYSS}"/>
        <text x="88" y="636" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">STATUS: ATIVO · CONEXÃO DIRECTML GPU OK · 71 MS</text>
    </g>

    <!-- Pilares Tecnológicos (Direita) -->
    <g id="technology-pillars" data-pptx-bounds="536 148 688 508">
        <!-- Pilar 1 -->
        <g id="pillar-1">
            <rect x="536" y="148" width="688" height="152" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <text x="568" y="184" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">01. Metrologia Radiométrica Bruta</text>
            <text x="568" y="210" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Inversão exata da curva de Planck a partir dos metadados da câmera (FFF/FLIR em 1 ms).</text>
            <text x="568" y="232" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Compensação analítica da transmissão do ar, emissividade e temperatura refletida.</text>
            <rect x="568" y="252" width="140" height="28" rx="14" fill="{C_SURFACE_HIGH}"/>
            <text x="638" y="270" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">9 MS MEDIANA</text>
        </g>
        <!-- Pilar 2 -->
        <g id="pillar-2">
            <rect x="536" y="324" width="688" height="152" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <text x="568" y="360" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">02. Visão Computacional Transformers</text>
            <text x="568" y="386" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">RF-DETR com backbone DINOv2 especializado em subestações de alta tensão.</text>
            <text x="568" y="408" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Segmentação fina SAM 2.1 e Depth Anything 3 eliminando o efeito do céu frio.</text>
            <rect x="568" y="428" width="160" height="28" rx="14" fill="{C_SURFACE_HIGH}"/>
            <text x="648" y="446" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">mAP50 0,891 (71 MS)</text>
        </g>
        <!-- Pilar 3 -->
        <g id="pillar-3">
            <rect x="536" y="500" width="688" height="156" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <text x="568" y="536" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">03. Inteligência Normativa e Edge</text>
            <text x="568" y="562" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Motor de inferência de severidade NBR 15866 e IEC 60099-5 em 1,8 ms.</text>
            <text x="568" y="584" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Compilação de laudos periciais Typst em 32 ms e arquitetura 100% offline.</text>
            <rect x="568" y="604" width="160" height="28" rx="14" fill="{C_FROST_CONTAINER}"/>
            <text x="648" y="622" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_WHITE}">458 TESTES (100% OK)</text>
        </g>
    </g>
"""

# ==============================================================================
# SLIDE 02: PARADOXO DA BAIXA CARGA (JOULE)
# ==============================================================================
s02_content = header_svg("EMBASAMENTO TEÓRICO · FÍSICA APLICADA", "O Paradoxo da Baixa Carga e Efeito Joule", "Severidade Oculta: Correntes de 30% Mascaram Falhas Térmicas Imediatas", 2) + f"""
    <!-- Card Esquerda: Medição Aparente -->
    <g id="measured-condition" data-pptx-bounds="56 150 568 330">
        <rect x="56" y="150" width="568" height="330" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="88" y="180" width="160" height="24" rx="9999" fill="{C_ABYSS}"/>
        <text x="168" y="196" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">OPERAÇÃO EM CAMPO (30% CARGA)</text>
        <text x="88" y="240" font-family="{F_TITLE}" font-size="28" font-weight="600" fill="{C_WHITE}">Medição Térmica Aparente</text>
        <text x="88" y="280" font-family="{F_TITLE}" font-size="44" font-weight="400" fill="{C_FROST_BLUE}">ΔT = 5,4 °C</text>
        <text x="88" y="320" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Temperatura medida no conector: <tspan font-weight="700" fill="{C_WHITE}">35,4 °C</tspan> (Ambiente: 30,0 °C).</text>
        <text x="88" y="342" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Corrente de operação no momento da foto: <tspan font-weight="700" fill="{C_WHITE}">300 A</tspan> (Nominal: 1.000 A).</text>
        <rect x="88" y="370" width="504" height="84" rx="12" fill="{C_ABYSS}"/>
        <text x="108" y="396" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_MUTED}">AVALIAÇÃO CONVENCIONAL SEM CORREÇÃO:</text>
        <text x="108" y="420" font-family="{F_BODY}" font-size="14" font-weight="700" fill="{C_WHITE}">NÍVEL NORMAL / ATENÇÃO LEVE · Reinspeção em 1 ano</text>
        <text x="108" y="440" font-family="{F_BODY}" font-size="11" fill="{C_ALERT}">Perigo Crítico: O inspetor ignora o aquecimento incipiente!</text>
    </g>

    <!-- Card Direita: Projeção Real -->
    <g id="projected-condition" data-pptx-bounds="656 150 568 330">
        <rect x="656" y="150" width="568" height="330" rx="24" fill="{C_ALERT_BG}" stroke="{C_ALERT}" stroke-width="1.5"/>
        <rect x="688" y="180" width="180" height="24" rx="9999" fill="{C_ABYSS}"/>
        <text x="778" y="196" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_ALERT}">PROJEÇÃO A 100% DE CARGA</text>
        <text x="688" y="240" font-family="{F_TITLE}" font-size="28" font-weight="600" fill="{C_WHITE}">Severidade Imediata Real</text>
        <text x="688" y="280" font-family="{F_TITLE}" font-size="44" font-weight="400" fill="{C_ALERT}">ΔT = 60,0 °C</text>
        <text x="688" y="320" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Temperatura corrigida projetada: <tspan font-weight="700" fill="{C_WHITE}">90,0 °C</tspan>.</text>
        <text x="688" y="342" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Efeito Joule: ΔT_100% = 5,4 × (100 / 30)² = 60,0 °C.</text>
        <rect x="688" y="370" width="504" height="84" rx="12" fill="{C_ABYSS}"/>
        <text x="708" y="396" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_ALERT}">DIAGNÓSTICO AUTOMATIZADO PYRON (NBR 15866):</text>
        <text x="708" y="420" font-family="{F_BODY}" font-size="14" font-weight="700" fill="{C_ALERT}">NÍVEL IMEDIATO · Intervenção requerida em até 24 horas</text>
        <text x="708" y="440" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Prevenção contra fusão do contato, arco elétrico e desligamento forçado.</text>
    </g>

    <!-- Barra Inferior de Fórmulas e Montsinger -->
    <g id="formulas-strip" data-pptx-bounds="56 504 1168 152">
        <rect x="56" y="504" width="1168" height="152" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="538" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">As Leis Térmicas Incorporadas ao Motor Pyron</text>
        <g font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">
            <text x="88" y="572"><tspan font-weight="700" fill="{C_FROST_BLUE}">Lei de Joule Quadrática:</tspan> P = R · I² ⟹ ΔT_proj = ΔT_med × (I_nom / I_op)²</text>
            <text x="88" y="598"><tspan font-weight="700" fill="{C_FROST_BLUE}">Regra de Montsinger / Arrhenius:</tspan> Vida Útil L = L₀ × 2^(-ΔT / 8°C). Cada 8 °C acima da MTA reduz a vida residual pela metade.</text>
            <text x="88" y="624"><tspan font-weight="700" fill="{C_FROST_BLUE}">Corrente Suportável:</tspan> I_máx = I_atual × √((MTA - T_amb) / (T_med - T_amb)) calculada instantaneamente para o conector.</text>
        </g>
    </g>
"""

# ==============================================================================
# SLIDE 03: DESENROLAMENTO RADIOMÉTRICO (PLANCK)
# ==============================================================================
s03_content = header_svg("FEATURE 1 · PIXEL À TEMPERATURA", "Desenrolamento Radiométrico e Planck", "Matrizes Float32 Exatas em 9 ms e Reconstrução por Programação Dinâmica em 1,5 s", 3) + f"""
    <!-- Nó 1 -->
    <g id="step-1" data-pptx-bounds="56 150 365 340">
        <rect x="56" y="150" width="365" height="340" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="80" y="174" width="32" height="32" rx="8" fill="{C_FROST_CONTAINER}"/>
        <text x="96" y="195" text-anchor="middle" font-family="{F_BODY}" font-size="14" font-weight="700" fill="{C_WHITE}">1</text>
        <text x="124" y="196" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">Extração FFF (FLIR)</text>
        {multiline_text(80, 234, "Acessa segmentos APP1 com cabeçalho FFF no JPEG radiométrico original.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
        {multiline_text(80, 280, "Extrai matriz bruta (16 bits) e constantes de Planck (R1, R2, B, F, O) de fábrica.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
        <rect x="80" y="390" width="317" height="76" rx="10" fill="{C_ABYSS}"/>
        <text x="96" y="414" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">TEMPO DE EXECUÇÃO:</text>
        <text x="96" y="442" font-family="{F_TITLE}" font-size="28" font-weight="400" fill="{C_WHITE}">1 ms <tspan font-size="12" font-family="{F_BODY}" fill="{C_MUTED}">conversão pura</tspan></text>
    </g>

    <!-- Nó 2 -->
    <g id="step-2" data-pptx-bounds="457 150 365 340">
        <rect x="457" y="150" width="365" height="340" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="481" y="174" width="32" height="32" rx="8" fill="{C_FROST_CONTAINER}"/>
        <text x="497" y="195" text-anchor="middle" font-family="{F_BODY}" font-size="14" font-weight="700" fill="{C_WHITE}">2</text>
        <text x="525" y="196" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">Compensação Física</text>
        {multiline_text(481, 234, "Desconta radiação refletida e a emissividade real (ε) de cerâmicas e condutores.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
        {multiline_text(481, 280, "Modela a transmissão atmosférica τ por distância e umidade relativa do ar.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
        <rect x="481" y="390" width="317" height="76" rx="10" fill="{C_ABYSS}"/>
        <text x="497" y="414" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">LEITURA COMPLETA (EXIF + GIRO):</text>
        <text x="497" y="442" font-family="{F_TITLE}" font-size="28" font-weight="400" fill="{C_WHITE}">9 ms <tspan font-size="12" font-family="{F_BODY}" fill="{C_MUTED}">mediana em 43 fotos</tspan></text>
    </g>

    <!-- Nó 3 -->
    <g id="step-3" data-pptx-bounds="858 150 366 340">
        <rect x="858" y="150" width="366" height="340" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="882" y="174" width="32" height="32" rx="8" fill="{C_FROST_CONTAINER}"/>
        <text x="898" y="195" text-anchor="middle" font-family="{F_BODY}" font-size="14" font-weight="700" fill="{C_WHITE}">3</text>
        <text x="926" y="196" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">Barra Livre (Foto Comum)</text>
        {multiline_text(882, 234, "Para imagens sem metadados brutos: localiza a barra térmica por DP.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
        {multiline_text(882, 280, "Lê dígitos por OCR em ONNX e calibra as cores no espaço CIELAB com KD-Tree.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
        <rect x="882" y="390" width="318" height="76" rx="10" fill="{C_ABYSS}"/>
        <text x="898" y="414" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">PRECISÃO DE BANCO (SCIENCEDB):</text>
        <text x="898" y="442" font-family="{F_TITLE}" font-size="28" font-weight="400" fill="{C_WHITE}">0,53 °C <tspan font-size="12" font-family="{F_BODY}" fill="{C_MUTED}">erro mediano</tspan></text>
    </g>

    <!-- Fita Inferior -->
    <g id="pipeline-summary" data-pptx-bounds="56 514 1168 142">
        <rect x="56" y="514" width="1168" height="142" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="548" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">Inversão Analítica da Equação de Planck</text>
        <text x="88" y="578" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">T_obj = B / ln(R1 / (R2 · (S_obj + O)) + F) - 273,15 °C. Onde S_obj desconta emissividade ε e radiação de fundo.</text>
        <text x="88" y="604" font-family="{F_BODY}" font-size="13" fill="{C_MUTED}">Reconhecimento da barra testado em 299 termogramas do ScienceDB: escala identificada em 298 casos (99,7% de acerto).</text>
        <text x="88" y="628" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">GARANTIA METROLÓGICA: Arquivo radiométrico é medida física real (9 ms); caminho estimado traz aviso normativo (1,5 s).</text>
    </g>
"""

# ==============================================================================
# SLIDE 04: DETECÇÃO DE ATIVOS (RF-DETR)
# ==============================================================================
s04_content = header_svg("FEATURE 2 · REDE TRANSFORMER", "Detecção com Transformers: RF-DETR", "Visão Robusta Treinada em Subestações de Alta Tensão: mAP50 0,891 em 71 ms", 4) + f"""
    <!-- Métricas Globais (Esquerda) -->
    <g id="global-metrics" data-pptx-bounds="56 150 420 506">
        <rect x="56" y="150" width="420" height="506" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Métricas do Detector RF-DETR</text>
        <text x="88" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Treinado sobre fotos do ScienceDB 10185 (CVAT)</text>
        
        <rect x="88" y="238" width="356" height="80" rx="14" fill="{C_ABYSS}"/>
        <text x="112" y="266" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">mAP50 GLOBAL (TESTE 27 FOTOS)</text>
        <text x="112" y="302" font-family="{F_TITLE}" font-size="38" font-weight="400" fill="{C_WHITE}">0,891</text>
        
        <rect x="88" y="334" width="356" height="80" rx="14" fill="{C_ABYSS}"/>
        <text x="112" y="362" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">F1-SCORE / REVOCAÇÃO</text>
        <text x="112" y="398" font-family="{F_TITLE}" font-size="38" font-weight="400" fill="{C_WHITE}">0,893 <tspan font-size="16" font-family="{F_BODY}" fill="{C_MUTED}">/ 0,898</tspan></text>
        
        <rect x="88" y="430" width="356" height="80" rx="14" fill="{C_ABYSS}"/>
        <text x="112" y="458" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">TEMPO DE INFERÊNCIA GPU (DIRECTML)</text>
        <text x="112" y="494" font-family="{F_TITLE}" font-size="38" font-weight="400" fill="{C_WHITE}">71 ms <tspan font-size="16" font-family="{F_BODY}" fill="{C_MUTED}">(CPU: 483 ms)</tspan></text>
        
        <rect x="88" y="526" width="356" height="106" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="552" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">CONTRATO CARTAO.JSON:</text>
        <text x="112" y="574" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Separação estrita entre treino (PyTorch) e programa.</text>
        <text x="112" y="594" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Pyron consome exclusivamente arquivo ONNX quantizado</text>
        <text x="112" y="614" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">sem dependência de frameworks pesados no cliente.</text>
    </g>

    <!-- Breakdown por Componente (Direita) -->
    <g id="component-breakdown" data-pptx-bounds="496 150 728 506">
        <rect x="496" y="150" width="728" height="236" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="528" y="186" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">Precisão Individual por Parte do Ativo</text>
        
        <!-- Grid de 4 partes -->
        <g id="parts-grid">
            <rect x="528" y="212" width="154" height="150" rx="14" fill="{C_ABYSS}"/>
            <text x="548" y="238" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">CORPO DO ATIVO</text>
            <text x="548" y="280" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_WHITE}">0,99</text>
            <text x="548" y="306" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Para-raios completo</text>
            <text x="548" y="326" font-family="{F_BODY}" font-size="10" fill="{C_FROST_BLUE}">AP50: 99,0%</text>

            <rect x="698" y="212" width="154" height="150" rx="14" fill="{C_ABYSS}"/>
            <text x="718" y="238" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">ALETAS ISOLADORAS</text>
            <text x="718" y="280" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_WHITE}">1,00</text>
            <text x="718" y="306" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Saia cerâmica / silicone</text>
            <text x="718" y="326" font-family="{F_BODY}" font-size="10" fill="{C_FROST_BLUE}">AP50: 100,0%</text>

            <rect x="868" y="212" width="154" height="150" rx="14" fill="{C_ABYSS}"/>
            <text x="888" y="238" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">TERMINAL SUPERIOR</text>
            <text x="888" y="280" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_WHITE}">0,84</text>
            <text x="888" y="306" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Conexão sob tensão</text>
            <text x="888" y="326" font-family="{F_BODY}" font-size="10" fill="{C_FROST_BLUE}">AP50: 84,0%</text>

            <rect x="1038" y="212" width="154" height="150" rx="14" fill="{C_ABYSS}"/>
            <text x="1058" y="238" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">TERMINAL INFERIOR</text>
            <text x="1058" y="280" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_WHITE}">0,73</text>
            <text x="1058" y="306" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Conexão à terra</text>
            <text x="1058" y="326" font-family="{F_BODY}" font-size="10" fill="{C_FROST_BLUE}">AP50: 73,0%</text>
        </g>

        <!-- Algoritmo Combinado (Ajustes de 03/11) -->
        <g id="combined-logic">
            <rect x="496" y="406" width="728" height="250" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <text x="528" y="442" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">Inovações do Detector Combinado (Regras + IA)</text>
            <text x="528" y="474" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• <tspan font-weight="700" fill="{C_WHITE}">Supressão:</tspan> Para-raios com sobreposição &gt; 60% são consolidados da esquerda para direita.</text>
            <text x="528" y="500" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• <tspan font-weight="700" fill="{C_WHITE}">Hierarquia:</tspan> Peças levam o número do ativo ('Terminal 2' pertence ao 'Para-raios 2').</text>
            <text x="528" y="526" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• <tspan font-weight="700" fill="{C_WHITE}">Geometria:</tspan> Aletas cortadas entre terminais, sem contagem redundante de pixels.</text>
            <text x="528" y="552" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• <tspan font-weight="700" fill="{C_WHITE}">Expurgo:</tspan> Ponto quente dentro de peça é unificado à medição do componente pai.</text>
            <text x="528" y="578" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• <tspan font-weight="700" fill="{C_WHITE}">Falso Alarme:</tspan> Ponto quente sem anomalia (ΔT &lt; 5 °C) é removido após a análise.</text>
            <rect x="528" y="606" width="664" height="30" rx="8" fill="{C_ABYSS}"/>
            <text x="548" y="626" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">PRECISÃO TÉRMICA: Erro mediano da temperatura máxima por peça de 0,0 °C (máximo 0,94 °C).</text>
        </g>
    </g>
"""

# ==============================================================================
# SLIDE 05: SEGMENTAÇÃO FINA & 3D (SAM 2.1 + DA3)
# ==============================================================================
s05_content = header_svg("FEATURE 3 · VISÃO ESPACIAL", "Segmentação SAM 2.1 e Profundidade 3D", "Eliminando o Efeito Céu e Estimando Distâncias Métricas com 5,1% de Erro", 5) + f"""
    <!-- Card Céu Frio (Esquerda) -->
    <g id="sky-contamination" data-pptx-bounds="56 150 568 496">
        <rect x="56" y="150" width="568" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">O Problema da Caixa Retangular</text>
        <text x="88" y="216" font-family="{F_BODY}" font-size="13" fill="{C_MUTED}">Por que caixas delimitadoras tradicionais falham em isoladores</text>
        
        <rect x="88" y="246" width="504" height="150" rx="14" fill="{C_ABYSS}"/>
        <text x="112" y="276" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_ALERT}">CONTAMINAÇÃO TÉRMICA PELO FUNDO CELESTE:</text>
        <text x="112" y="304" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">O céu em subestações de alta tensão varia entre -20 °C e 5 °C.</text>
        <text x="112" y="328" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Caixas retangulares englobam até 40% de área de céu gélido,</text>
        <text x="112" y="352" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">derrubando a temperatura média real do corpo do isolador.</text>
        <text x="112" y="376" font-family="{F_BODY}" font-size="12" font-weight="600" fill="{C_ALERT}">Resultado: Severidade subdimensionada e falha imprevista.</text>

        <rect x="88" y="416" width="504" height="206" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="446" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_FROST_BLUE}">A SOLUÇÃO PYRON: CONTORNO POLIGONAL SAM 2.1</text>
        <text x="112" y="474" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Segmentação fina em polígono ajustado à silhueta do ativo.</text>
        <text x="112" y="498" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Convolução normalizada: pixels de céu são totalmente expurgados.</text>
        <text x="112" y="522" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Apenas a cerâmica, silicone e terminais metálicos são integrados.</text>
        <text x="112" y="546" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Algoritmo de pontos quentes roda em 1,9 ms após máscara.</text>
        <rect x="112" y="568" width="456" height="34" rx="8" fill="{C_ABYSS}"/>
        <text x="128" y="590" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">PRECISÃO PURO ATIVO: Sem interferência solar ou celeste.</text>
    </g>

    <!-- Card Profundidade 3D (Direita) -->
    <g id="depth-metrology" data-pptx-bounds="656 150 568 496">
        <rect x="656" y="150" width="568" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="688" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Metrologia em 3D: Depth Anything 3</text>
        <text x="688" y="216" font-family="{F_BODY}" font-size="13" fill="{C_MUTED}">Medição de distância física (cm) diretamente da fotografia comum</text>

        <rect x="688" y="246" width="504" height="150" rx="14" fill="{C_ABYSS}"/>
        <text x="712" y="276" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_FROST_BLUE}">MEDIDAS DE SEGURANÇA ENTRE CONDUTORES:</text>
        <text x="712" y="304" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Usuário marca duas pontas na imagem: sistema projeta nuvem 3D.</text>
        <text x="712" y="328" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Calcula distância métrica real entre fases energizadas sem contato.</text>
        <text x="712" y="352" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Suporte a MoGe-2 ViT-L e Depth Anything 3 Metric Large.</text>
        <text x="712" y="376" font-family="{F_BODY}" font-size="12" font-weight="600" fill="{C_WHITE}">Homologado com licenças permissivas (Apache 2.0 / MIT).</text>

        <!-- Tabela Comparativa de Bancada -->
        <g id="depth-benchmarks">
            <rect x="688" y="416" width="504" height="206" rx="14" fill="{C_SURFACE_HIGH}"/>
            <text x="712" y="446" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">BENCHMARK METROLÓGICO (RELATÓRIO POST-IT):</text>
            
            <rect x="712" y="466" width="220" height="60" rx="10" fill="{C_ABYSS}"/>
            <text x="728" y="490" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">DEPTH ANYTHING 3 (POST-IT)</text>
            <text x="728" y="516" font-family="{F_TITLE}" font-size="24" font-weight="400" fill="{C_FROST_BLUE}">5,1% de erro</text>

            <rect x="948" y="466" width="220" height="60" rx="10" fill="{C_ABYSS}"/>
            <text x="964" y="490" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">TEMPO DE PROCESSAMENTO</text>
            <text x="964" y="516" font-family="{F_TITLE}" font-size="24" font-weight="400" fill="{C_WHITE}">2,0 s na CPU</text>

            <text x="712" y="556" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Evolução sobre MoGe-2 anterior: tempo caiu de 20 s para 2 s (10x),</text>
            <text x="712" y="578" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">e o erro com referência caiu de 8,1% para 5,1% mediano.</text>
            <text x="712" y="602" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">Cálculo de margem incorpora ruído local e propagação de Monte Carlo.</text>
        </g>
    </g>
"""

# ==============================================================================
# SLIDE 06: PARA-RAIOS ZNO (IEC 60099-5)
# ==============================================================================
s06_content = header_svg("FEATURE 4 · ATIVOS NÃO LINEARES", "Diagnóstico de Para-raios ZnO (IEC)", "Por Que Para-raios Não Seguem I²R e Devem Ser Avaliados por Fuga Resistiva", 6) + f"""
    <!-- Banner de Regra Crítica -->
    <g id="rule-banner" data-pptx-bounds="56 150 1168 84">
        <rect x="56" y="150" width="1168" height="84" rx="16" fill="{C_SURFACE_CONTAINER}" stroke="{C_FROST_BLUE}" stroke-width="1"/>
        <text x="88" y="184" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">Regra Fundamental em Para-raios ZnO</text>
        <text x="88" y="208" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Para-raios operam sob tensão contínua fase-terra e <tspan font-weight="700" fill="{C_ALERT}">NÃO transportam corrente de carga do sistema!</tspan></text>
        <text x="88" y="226" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Aplicações que utilizam correção quadrática I²R em para-raios geram laudos incorretos e falsos alarmes graves.</text>
    </g>

    <!-- 3 Colunas de Severidade IEC 60099-5 -->
    <g id="iec-columns" data-pptx-bounds="56 254 1168 280">
        <!-- Coluna 1: Normal -->
        <g id="iec-normal">
            <rect x="56" y="254" width="365" height="280" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <rect x="80" y="278" width="120" height="24" rx="9999" fill="{C_ABYSS}"/>
            <text x="140" y="294" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">FAIXA 1 · NORMAL</text>
            <text x="80" y="340" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_WHITE}">ΔT ≤ 2,0 °C</text>
            {multiline_text(80, 374, "Delta térmico contra para-raios idênticos das outras fases da subestação.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
            <text x="80" y="418" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Corrente capacitiva dominante (95%).</text>
            <rect x="80" y="440" width="317" height="66" rx="10" fill="{C_ABYSS}"/>
            <text x="96" y="464" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">AÇÃO RECOMENDADA:</text>
            <text x="96" y="488" font-family="{F_BODY}" font-size="12" fill="{C_FROST_BLUE}">Manter rotina anual de inspeção.</text>
        </g>
        <!-- Coluna 2: Atenção -->
        <g id="iec-warning">
            <rect x="457" y="254" width="365" height="280" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <rect x="481" y="278" width="130" height="24" rx="9999" fill="{C_SURFACE_HIGH}"/>
            <text x="546" y="294" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">FAIXA 2 · ATENÇÃO</text>
            <text x="481" y="340" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_WHITE}">2,0 &lt; ΔT ≤ 5,0 °C</text>
            {multiline_text(481, 374, "Início de degradação interna dos blocos de varistor de óxido de zinco.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
            <text x="481" y="418" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Aumento na componente resistiva Irx.</text>
            <rect x="481" y="440" width="317" height="66" rx="10" fill="{C_ABYSS}"/>
            <text x="497" y="464" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">AÇÃO RECOMENDADA:</text>
            <text x="497" y="488" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Encurtar reinspeção para 90 dias.</text>
        </g>
        <!-- Coluna 3: Crítico -->
        <g id="iec-critical">
            <rect x="858" y="254" width="366" height="280" rx="20" fill="{C_ALERT_BG}" stroke="{C_ALERT}" stroke-width="1.5"/>
            <rect x="882" y="278" width="140" height="24" rx="9999" fill="{C_ABYSS}"/>
            <text x="952" y="294" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_ALERT}">FAIXA 3 · CRÍTICO</text>
            <text x="882" y="340" font-family="{F_TITLE}" font-size="36" font-weight="400" fill="{C_ALERT}">ΔT &gt; 10,0 °C</text>
            {multiline_text(882, 374, "Degradação severa por umidade ou perfuração de blocos cerâmicos ZnO.", max_chars=36, line_spacing=18, font_size=12, fill=C_SILVER)}
            <text x="882" y="418" font-family="{F_BODY}" font-size="12" fill="{C_ALERT}">Risco iminente de explosão térmica.</text>
            <rect x="882" y="440" width="318" height="66" rx="10" fill="{C_ABYSS}"/>
            <text x="898" y="464" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_ALERT}">AÇÃO IMEDIATA:</text>
            <text x="898" y="488" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">Intervenção em até 24 horas.</text>
        </g>
    </g>

    <!-- Fita de Normas -->
    <g id="iec-footer-box" data-pptx-bounds="56 554 1168 102">
        <rect x="56" y="554" width="1168" height="102" rx="16" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="586" font-family="{F_TITLE}" font-size="16" font-weight="600" fill="{C_WHITE}">Implementação Técnica no Núcleo do Pyron (nucleo/analise.py)</text>
        <text x="88" y="612" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Se a peça classificada for para-raios ou isolador, o Pyron desativa automaticamente a correção (100/carga)² e aplica os degraus 2 / 5 / 10 °C.</text>
        <text x="88" y="634" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">ESTADOS ESPECIAIS: 'Não avaliado' quando a foto não contém o par de outra fase para comparação; aviso 'Confira antes de agir' em hotspots fora das peças.</text>
    </g>
"""

# ==============================================================================
# SLIDE 07: MOTOR DE DECISÃO NORMATIVA DUPLA (NBR 15866)
# ==============================================================================
s07_content = header_svg("FEATURE 5 · INFERÊNCIA NORMATIVA", "Motor Normativo Duplo: NBR 15866", "Avaliação Simultânea de Aquecimento Relativo e Absoluto (% MTA) em 1,8 ms", 7) + f"""
    <!-- Matriz NBR (Esquerda) -->
    <g id="matrix-container" data-pptx-bounds="56 150 740 506">
        <rect x="56" y="150" width="740" height="506" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Matriz de Severidade Brasileira (5 Níveis Padronizados)</text>
        <text x="88" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Vale a pior severidade entre os critérios relativo e absoluto; motivo fica registrado</text>

        <!-- Tabela -->
        <g id="table-levels">
            <!-- Header Tabela -->
            <rect x="88" y="238" width="676" height="34" rx="8" fill="{C_ABYSS}"/>
            <text x="108" y="260" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">NÍVEL</text>
            <text x="210" y="260" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">ΔT RELATIVO CORRIGIDO</text>
            <text x="420" y="260" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">% DA MTA (ABSOLUTO)</text>
            <text x="610" y="260" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">REINSPEÇÃO</text>

            <!-- Linha 1: Normal -->
            <rect x="88" y="280" width="676" height="58" rx="8" fill="{C_SURFACE_HIGH}"/>
            <rect x="104" y="295" width="80" height="26" rx="9999" fill="{C_ABYSS}"/>
            <text x="144" y="312" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">NORMAL</text>
            <text x="210" y="313" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">ΔT ≤ 5,0 °C</text>
            <text x="420" y="313" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">≤ 60,0% da MTA</text>
            <text x="610" y="313" font-family="{F_BODY}" font-size="13" font-weight="600" fill="{C_FROST_BLUE}">365 dias</text>

            <!-- Linha 2: Atenção -->
            <rect x="88" y="346" width="676" height="58" rx="8" fill="{C_SURFACE_HIGH}"/>
            <rect x="104" y="361" width="80" height="26" rx="9999" fill="{C_ABYSS}"/>
            <text x="144" y="378" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">ATENÇÃO</text>
            <text x="210" y="379" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">5,1 °C a 10,0 °C</text>
            <text x="420" y="379" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">60,1% a 70,0% da MTA</text>
            <text x="610" y="379" font-family="{F_BODY}" font-size="13" font-weight="600" fill="{C_WHITE}">90 dias</text>

            <!-- Linha 3: Programar -->
            <rect x="88" y="412" width="676" height="58" rx="8" fill="{C_SURFACE_HIGH}"/>
            <rect x="104" y="427" width="90" height="26" rx="9999" fill="{C_ABYSS}"/>
            <text x="149" y="444" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">PROGRAMAR</text>
            <text x="210" y="445" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">10,1 °C a 20,0 °C</text>
            <text x="420" y="445" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">70,1% a 80,0% da MTA</text>
            <text x="610" y="445" font-family="{F_BODY}" font-size="13" font-weight="600" fill="{C_WHITE}">30 dias</text>

            <!-- Linha 4: Urgente -->
            <rect x="88" y="478" width="676" height="58" rx="8" fill="{C_SURFACE_HIGH}"/>
            <rect x="104" y="493" width="80" height="26" rx="9999" fill="{C_ABYSS}"/>
            <text x="144" y="510" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_ALERT}">URGENTE</text>
            <text x="210" y="511" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">20,1 °C a 40,0 °C</text>
            <text x="420" y="511" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">80,1% a 100,0% da MTA</text>
            <text x="610" y="511" font-family="{F_BODY}" font-size="13" font-weight="700" fill="{C_ALERT}">7 dias</text>

            <!-- Linha 5: Imediato -->
            <rect x="88" y="544" width="676" height="58" rx="8" fill="{C_ALERT_BG}" stroke="{C_ALERT}" stroke-width="1"/>
            <rect x="104" y="559" width="80" height="26" rx="9999" fill="{C_ABYSS}"/>
            <text x="144" y="576" text-anchor="middle" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_ALERT}">IMEDIATO</text>
            <text x="210" y="577" font-family="{F_BODY}" font-size="13" font-weight="700" fill="{C_ALERT}">&gt; 40,0 °C</text>
            <text x="420" y="577" font-family="{F_BODY}" font-size="13" font-weight="700" fill="{C_ALERT}">&gt; 100,0% da MTA</text>
            <text x="610" y="577" font-family="{F_BODY}" font-size="13" font-weight="700" fill="{C_ALERT}">24 horas</text>
        </g>
        <text x="88" y="632" font-family="{F_BODY}" font-size="11" fill="{C_MUTED}">Critério NETA MTS (sobre o ambiente) disponível como alternativa configurável pelo gestor.</text>
    </g>

    <!-- Indicador de Performance (Direita) -->
    <g id="performance-card" data-pptx-bounds="816 150 408 506">
        <rect x="816" y="150" width="408" height="506" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="848" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Performance do Motor</text>
        <text x="848" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Medido em bancada oficial com 9 regiões</text>

        <rect x="848" y="246" width="344" height="106" rx="14" fill="{C_ABYSS}"/>
        <text x="872" y="274" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">TEMPO DE CLASSIFICAÇÃO NORMATIVA</text>
        <text x="872" y="318" font-family="{F_TITLE}" font-size="44" font-weight="400" fill="{C_WHITE}">1,8 ms</text>
        <text x="872" y="342" font-family="{F_BODY}" font-size="10" fill="{C_MUTED}">9 regiões térmicas avaliadas simultaneamente</text>

        <rect x="848" y="370" width="344" height="262" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="872" y="400" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">SISTEMA DE AVISOS INTELIGENTES:</text>
        {multiline_text(872, 428, "• Carga < 40%: Alerta de baixa corrente avisando falhas ocultas.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 466, "• Ponto > 150 °C: Identifica reflexo solar antes do alarme.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 504, "• Sem Ambiente: Classificação provisória até confirmação.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 542, "• Ponto fora da peça: Emite aviso 'Confira antes de agir'.", max_chars=36, line_spacing=16, font_size=11, fill=C_ALERT)}
        {multiline_text(872, 584, "MTA configurável por componente (Cobre 90 °C, Óleo 65 °C).", max_chars=36, line_spacing=16, font_size=11, fill=C_WHITE, font_weight="600")}
    </g>
"""

# ==============================================================================
# SLIDE 08: TELEMETRIA MOBILE EDGE
# ==============================================================================
s08_content = header_svg("FEATURE 6 · INSPEÇÃO DE CAMPO", "Telemetria Mobile Edge e Fluxo Óptico", "Streaming a 15 fps via WebSocket e Rastreamento com Erro Menor que 0,3 px", 8) + f"""
    <!-- Card Celular (Esquerda) -->
    <g id="mobile-stream" data-pptx-bounds="56 150 568 496">
        <rect x="56" y="150" width="568" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Transmissão Segura na Subestação</text>
        <text x="88" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Arquitetura de rede isolada sem necessidade de sinal de internet</text>

        <rect x="88" y="244" width="504" height="116" rx="14" fill="{C_ABYSS}"/>
        <text x="112" y="272" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">SERVIDOR UVICORN SECUNDÁRIO (PORTA 8791+):</text>
        <text x="112" y="296" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">O Pyron isola a interface do celular num Uvicorn exclusivo.</text>
        <text x="112" y="318" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Nenhum dispositivo na rede chega aos backups ou configurações.</text>
        <text x="112" y="340" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_WHITE}">Pareamento instantâneo via QR Code efêmero com token scrypt.</text>

        <rect x="88" y="380" width="504" height="242" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="410" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">PROTOCOLO WEBSOCKET BINÁRIO:</text>
        <text x="112" y="438" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Frames compactos JPEG a 960 px com cabeçalho de 16 bytes.</text>
        <text x="112" y="462" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Ritmo adaptativo de 5 a 15 quadros por segundo.</text>
        <text x="112" y="486" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Se a fila exceder 192 KB, o frame intermediário é pulado.</text>
        <text x="112" y="510" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• O servidor processa sempre o frame mais recente (zero fila).</text>
        <text x="112" y="534" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Enquadramento automático recorta apenas o termograma da tela.</text>
        <rect x="112" y="556" width="456" height="42" rx="8" fill="{C_ABYSS}"/>
        <text x="128" y="582" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">HTTPS PRÓPRIO: Certificado gerado em tempo de execução para abrir câmera.</text>
    </g>

    <!-- Card Fluxo Óptico (Direita) -->
    <g id="optical-flow" data-pptx-bounds="656 150 568 496">
        <rect x="656" y="150" width="568" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="688" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Compensação de Tremor Manual</text>
        <text x="688" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Caixas térmicas acompanham os ativos com erro menor que 0,3 px</text>

        <rect x="688" y="244" width="504" height="116" rx="14" fill="{C_ABYSS}"/>
        <text x="712" y="272" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">FLUXO ÓPTICO LOCAL NO CELULAR (JS PURO):</text>
        <text x="712" y="296" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Enquanto o servidor analisa o frame anterior na GPU,</text>
        <text x="712" y="318" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">o celular compara miniaturas de 72 px em escala de cinza.</text>
        <text x="712" y="340" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_WHITE}">As caixas de medição se movem suavemente com a mão do operador.</text>

        <!-- Indicador de Mediana Móvel -->
        <g id="stats-mobile">
            <rect x="688" y="380" width="504" height="242" rx="14" fill="{C_SURFACE_HIGH}"/>
            <text x="712" y="410" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">FILTRO TEMPORAL ROBUSTO:</text>
            <text x="712" y="438" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• A temperatura exibida em cada peça é a mediana dos últimos 5 frames.</text>
            <text x="712" y="462" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Elimina oscilações momentâneas induzidas por poeira ou reflexos de sol.</text>
            
            <rect x="712" y="482" width="220" height="60" rx="10" fill="{C_ABYSS}"/>
            <text x="728" y="506" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">ERRO DE RASTREAMENTO</text>
            <text x="728" y="532" font-family="{F_TITLE}" font-size="24" font-weight="400" fill="{C_FROST_BLUE}">&lt; 0,3 px</text>

            <rect x="948" y="482" width="220" height="60" rx="10" fill="{C_ABYSS}"/>
            <text x="964" y="506" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_MUTED}">LATÊNCIA TOTAL DE LOOP</text>
            <text x="964" y="532" font-family="{F_TITLE}" font-size="24" font-weight="400" fill="{C_WHITE}">~80 ms</text>

            <text x="712" y="572" font-family="{F_BODY}" font-size="11" fill="{C_SILVER}">Para medição de precisão: o celular envia o arquivo original sem perda</text>
            <text x="712" y="594" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">Até 40 MB por foto / 100 MB por vídeo; processamento sempre no PC.</text>
        </g>
    </g>
"""

# ==============================================================================
# SLIDE 09: ARQUITETURA 100% OFFLINE EDGE
# ==============================================================================
s09_content = header_svg("FEATURE 7 · INFRAESTRUTURA EDGE", "Arquitetura 100% Offline e Cibersegurança", "FastAPI com 128 Rotas, DirectML e SQLite WAL com Resposta em 58 ms", 9) + f"""
    <!-- Diagrama em Camadas (Esquerda) -->
    <g id="layer-stack" data-pptx-bounds="56 150 740 506">
        <rect x="56" y="150" width="740" height="506" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Camadas de Software do Pyron (62 mil linhas)</text>
        <text x="88" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Zero dependência de cloud; total compatibilidade com isolamento físico de subestação</text>

        <!-- Camada 1: Interface -->
        <rect x="88" y="240" width="676" height="84" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="268" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">INTERFACE WEB MODERNA (APP/INTERFACE/) · 10,2 MIL LINHAS</text>
        <text x="112" y="292" font-family="{F_BODY}" font-size="12" fill="{C_WHITE}">JavaScript puro em módulos ES (sem build/bundler). Palco térmico renderizado em &lt;canvas&gt;.</text>
        <text x="112" y="312" font-family="{F_BODY}" font-size="11" fill="{C_MUTED}">Zoom de 12x, leitura térmica no cursor sem requisição ao servidor, tema claro/escuro sem violações WCAG 2.2 AA.</text>

        <!-- Camada 2: Servidor FastAPI -->
        <rect x="88" y="336" width="676" height="84" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="364" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">SERVIDOR BACKEND FASTAPI (APP/) · 9,4 MIL LINHAS</text>
        <text x="112" y="388" font-family="{F_BODY}" font-size="12" fill="{C_WHITE}">128 rotas tipadas com dependência global de autenticação (acesso.verificar).</text>
        <text x="112" y="408" font-family="{F_BODY}" font-size="11" fill="{C_MUTED}">Trabalho de IA em run_in_threadpool para não travar a interface; proteção contra conflitos de edição (409).</text>

        <!-- Camada 3: Núcleo Metrológico -->
        <rect x="88" y="432" width="676" height="84" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="460" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">NÚCLEO NUMÉRICO E DETECTORES (NUCLEO/) · 10,9 MIL LINHAS</text>
        <text x="112" y="484" font-family="{F_BODY}" font-size="12" fill="{C_WHITE}">NumPy, SciPy, OpenCV e ONNX Runtime DirectML (execução direta na GPU sem instalar CUDA).</text>
        <text x="112" y="504" font-family="{F_BODY}" font-size="11" fill="{C_MUTED}">Implementação estrita de Planck, KD-Tree, Otsu adaptativo e critérios da NBR 15866.</text>

        <!-- Camada 4: Armazenamento SQLite -->
        <rect x="88" y="528" width="676" height="104" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="556" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">ARMAZENAMENTO LOCAL TRANSAÇONAL (SQLITE WAL) · ESQUEMA V3</text>
        <text x="112" y="580" font-family="{F_BODY}" font-size="12" fill="{C_WHITE}">Banco SQLite com Write-Ahead Logging (WAL) e matrizes de temperatura gravadas em .npy.</text>
        <text x="112" y="600" font-family="{F_BODY}" font-size="11" fill="{C_MUTED}">Consulta de 6.000 inspeções otimizada: tempo caiu de 884 ms (12 MB) para apenas 58 ms lendo colunas indexadas.</text>
        <text x="112" y="620" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">Exportador integrado para PostgreSQL / Grafana e integração local com SAP PM.</text>
    </g>

    <!-- Card Cibersegurança (Direita) -->
    <g id="security-card" data-pptx-bounds="816 150 408 506">
        <rect x="816" y="150" width="408" height="506" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="848" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Cibersegurança e SAC</text>
        <text x="848" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Atendimento às políticas de infraestrutura crítica</text>

        <rect x="848" y="244" width="344" height="116" rx="14" fill="{C_ABYSS}"/>
        <text x="872" y="272" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">SMART APP CONTROL (WIN 11):</text>
        <text x="872" y="296" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">O SAC bloqueia DLLs não assinadas.</text>
        <text x="872" y="318" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">O Pyron roda via DirectML (DLLs Microsoft)</text>
        <text x="872" y="340" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_WHITE}">sem exigir drivers ou DLLs avulsas.</text>

        <rect x="848" y="376" width="344" height="256" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="872" y="406" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">BLINDAGEM OPERACIONAL:</text>
        {multiline_text(872, 432, "• Senhas: Hashing scrypt individual (~50 ms por conferência).", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 468, "• Sessões: Cookies HttpOnly e SameSite=Strict estrito.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 504, "• Permissões: Rotas sem grupo respondem 403 verificado.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 540, "• Shell Zero: Janela sem acesso ao shell do SO.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        {multiline_text(872, 576, "• 458 Testes: 100% de aprovação em testes de segurança.", max_chars=36, line_spacing=16, font_size=11, fill=C_SILVER)}
        <rect x="872" y="602" width="296" height="20" rx="4" fill="{C_ABYSS}"/>
        <text x="888" y="616" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">HOMOLOGADO PARA REDES AIR-GAP</text>
    </g>
"""

# ==============================================================================
# SLIDE 10: LAUDOS REGULATÓRIOS (TYPST)
# ==============================================================================
s10_content = header_svg("FEATURE 8 · LAUDOS REGULATÓRIOS", "Geração de Laudos Regulatórios Typst", "Compilação em 32 ms para Prontuário de Instalações Elétricas (NR-10 / PIE)", 10) + f"""
    <!-- Comparativo de Velocidade (Esquerda) -->
    <g id="typst-speed" data-pptx-bounds="56 150 568 496">
        <rect x="56" y="150" width="568" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="88" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Salto de Performance de Compilação</text>
        <text x="88" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Transição do ReportLab legado para o moderno motor Typst</text>

        <!-- Barra 1: Manual -->
        <g id="speed-manual">
            <rect x="88" y="248" width="504" height="66" rx="12" fill="{C_ABYSS}"/>
            <text x="112" y="274" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_MUTED}">CONFECÇÃO MANUAL EM WORD / EXCEL:</text>
            <text x="112" y="298" font-family="{F_TITLE}" font-size="22" font-weight="400" fill="{C_WHITE}">1 a 2 horas <tspan font-family="{F_BODY}" font-size="12" fill="{C_ALERT}">por laudo de subestação</tspan></text>
        </g>
        <!-- Barra 2: ReportLab -->
        <g id="speed-reportlab">
            <rect x="88" y="326" width="504" height="66" rx="12" fill="{C_ABYSS}"/>
            <text x="112" y="352" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_MUTED}">REPORTLAB LEGADO (VERSÃO ANTERIOR):</text>
            <text x="112" y="376" font-family="{F_TITLE}" font-size="22" font-weight="400" fill="{C_SILVER}">111 ms <tspan font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">(1 laudo) / 1.944 ms (50 laudos)</tspan></text>
        </g>
        <!-- Barra 3: Typst -->
        <g id="speed-typst">
            <rect x="88" y="404" width="504" height="84" rx="12" fill="{C_FROST_CONTAINER}" stroke="{C_FROST_BLUE}" stroke-width="1"/>
            <text x="112" y="432" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">MOTOR TYPST NATIVO (NOVO PADRÃO PYRON):</text>
            <text x="112" y="468" font-family="{F_TITLE}" font-size="34" font-weight="600" fill="{C_WHITE}">32 ms <tspan font-family="{F_BODY}" font-size="13" font-weight="400" fill="{C_FROST_BLUE}">(3,5x mais rápido!)</tspan></text>
        </g>

        <rect x="88" y="504" width="504" height="118" rx="12" fill="{C_SURFACE_HIGH}"/>
        <text x="112" y="534" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">LOTE DE 50 LAUDOS EM 1 SEGUNDO:</text>
        <text x="112" y="560" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">No lote com 50 inspeções, o Typst compila o PDF consolidado</text>
        <text x="112" y="582" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">em apenas <tspan font-weight="700" fill="{C_WHITE}">1.024 ms</tspan> (contra 1.944 ms do ReportLab).</text>
        <text x="112" y="604" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">Imagens e vetores integrados sem perda de resolução.</text>
    </g>

    <!-- Conteúdo Normativo do Laudo (Direita) -->
    <g id="typst-contents" data-pptx-bounds="656 150 568 496">
        <rect x="656" y="150" width="568" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <text x="688" y="190" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Conformidade Pericial NR-10 &amp; PIE</text>
        <text x="688" y="214" font-family="{F_BODY}" font-size="12" fill="{C_MUTED}">Documento oficial auditável para fins securitários e judiciais</text>

        <rect x="688" y="248" width="504" height="170" rx="14" fill="{C_ABYSS}"/>
        <text x="712" y="276" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_FROST_BLUE}">ESTRUTURA TÉCNICA DO DOCUMENTO:</text>
        <text x="712" y="304" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Metadados: Emissividade (ε), T_amb, T_refl, umidade e distância.</text>
        <text x="712" y="328" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Parecer Pericial: Enquadramento formal nos 5 níveis da NBR 15866.</text>
        <text x="712" y="352" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Imagens: Foto visual, termograma com paleta ferro e recorte térmico.</text>
        <text x="712" y="376" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Assinatura Digital do Engenheiro e número de ART recolhida.</text>
        <text x="712" y="400" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_WHITE}">Relatório pronto para inclusão no Prontuário Elétrico (NR-10).</text>

        <rect x="688" y="434" width="504" height="188" rx="14" fill="{C_SURFACE_HIGH}"/>
        <text x="712" y="464" font-family="{F_BODY}" font-size="12" font-weight="700" fill="{C_WHITE}">SEGURANÇA CONTRA INJEÇÃO DE CÓDIGO:</text>
        <text x="712" y="492" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">O texto digitado pelo usuário entra no modelo Typst</text>
        <text x="712" y="514" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">exclusivamente por um arquivo <tspan font-weight="700" fill="{C_WHITE}">dados.json</tspan> isolado.</text>
        <text x="712" y="536" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Nenhum texto arbitrário é montado como código executável.</text>
        <text x="712" y="558" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">Garante imunidade total contra injeção e falhas de compilação.</text>
        <rect x="712" y="578" width="456" height="30" rx="6" fill="{C_ABYSS}"/>
        <text x="728" y="598" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">INTEGRAÇÃO WHATSAPP: Mensagem resumida pronta para disparo imediato.</text>
    </g>
"""

# ==============================================================================
# SLIDE 11: ROI INDUSTRIAL & IMPACTO
# ==============================================================================
s11_content = header_svg("IMPACTO INDUSTRIAL & NEGÓCIO", "Retorno sobre Investimento (ROI) e Valor", "Como o Pyron Protege Milhões em Ativos e Elimina Multas Regulatórias", 11) + f"""
    <!-- Coluna 1 -->
    <g id="roi-1" data-pptx-bounds="56 150 365 496">
        <rect x="56" y="150" width="365" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="80" y="174" width="160" height="24" rx="9999" fill="{C_ABYSS}"/>
        <text x="160" y="190" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_ALERT}">MULTAS REGULATÓRIAS</text>
        <text x="80" y="234" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Evitação de Desligamentos</text>
        <text x="80" y="280" font-family="{F_TITLE}" font-size="38" font-weight="400" fill="{C_ALERT}">&gt; R$ 450 mil</text>
        <text x="80" y="306" font-family="{F_BODY}" font-size="12" font-weight="600" fill="{C_MUTED}">por hora de interrupção forçada</text>
        <rect x="80" y="334" width="317" height="288" rx="14" fill="{C_ABYSS}"/>
        <text x="96" y="364" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">PENALIDADES ANEEL EVITADAS:</text>
        {multiline_text(96, 394, "• Parcela Variável (PV) por indisponibilidade de funções de transmissão 230/500 kV.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        {multiline_text(96, 452, "• Estouro de limites DIC e FIC com ressarcimento compulsório a indústrias.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        {multiline_text(96, 510, "• O Pyron identifica o conector superaquecido meses antes do colapso.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        <text x="96" y="586" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">PAYBACK NA PRIMEIRA FALHA</text>
    </g>

    <!-- Coluna 2 -->
    <g id="roi-2" data-pptx-bounds="457 150 365 496">
        <rect x="457" y="150" width="365" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="481" y="174" width="160" height="24" rx="9999" fill="{C_ABYSS}"/>
        <text x="561" y="190" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">VIDA ÚTIL DO ATIVO</text>
        <text x="481" y="234" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">Proteção de Transformador</text>
        <text x="481" y="280" font-family="{F_TITLE}" font-size="38" font-weight="400" fill="{C_WHITE}">R$ 3,5 milhões</text>
        <text x="481" y="306" font-family="{F_BODY}" font-size="12" font-weight="600" fill="{C_MUTED}">custo de reposição de ativo de força</text>
        <rect x="481" y="334" width="317" height="288" rx="14" fill="{C_ABYSS}"/>
        <text x="497" y="364" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">DEGRADAÇÃO RETARDADA:</text>
        {multiline_text(497, 394, "• Envelhecimento térmico do papel kraft isolante segue Montsinger.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        {multiline_text(497, 452, "• Ponto quente na bucha acelera produção de gases combustíveis (DGA).", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        {multiline_text(497, 510, "• Eliminar sobreaquecimento preserva mais de 10 anos de vida útil.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        <text x="497" y="586" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">PROTEÇÃO DO ATIVO IMOBILIZADO</text>
    </g>

    <!-- Coluna 3 -->
    <g id="roi-3" data-pptx-bounds="858 150 366 496">
        <rect x="858" y="150" width="366" height="496" rx="24" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
        <rect x="882" y="174" width="160" height="24" rx="9999" fill="{C_ABYSS}"/>
        <text x="962" y="190" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="600" fill="{C_FROST_BLUE}">EFICIÊNCIA DE CAMPO</text>
        <text x="882" y="234" font-family="{F_TITLE}" font-size="22" font-weight="600" fill="{C_WHITE}">Produtividade de Campo</text>
        <text x="882" y="280" font-family="{F_TITLE}" font-size="38" font-weight="400" fill="{C_FROST_BLUE}">6,8x mais rápido</text>
        <text x="882" y="306" font-family="{F_BODY}" font-size="12" font-weight="600" fill="{C_MUTED}">triagem e emissão pericial de laudo</text>
        <rect x="882" y="334" width="318" height="288" rx="14" fill="{C_ABYSS}"/>
        <text x="898" y="364" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">GANHOS OPERACIONAIS:</text>
        {multiline_text(898, 394, "• Triagem de 300 imagens térmicas cai de 2 dias para 40 minutos.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        {multiline_text(898, 452, "• Eliminação de erros de digitação e transcrição manual de temperaturas.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        {multiline_text(898, 510, "• Histórico automatizado de cada conector rastreado ao longo dos anos.", max_chars=34, line_spacing=18, font_size=11, fill=C_SILVER)}
        <text x="898" y="586" font-family="{F_BODY}" font-size="11" font-weight="600" fill="{C_FROST_BLUE}">OTIMIZAÇÃO DO TEMPO TÉCNICO</text>
    </g>
"""

# ==============================================================================
# SLIDE 12: CRONOGRAMA, PILOTO & ENCERRAMENTO
# ==============================================================================
s12_content = header_svg("HOMOLOGAÇÃO & PILOTO", "Cronograma de Homologação e Piloto", "Validação Prática de 458 Testes e Próximos Passos Comerciais", 12) + f"""
    <!-- Timeline Horizontal de 3 Fases -->
    <g id="timeline-phases" data-pptx-bounds="56 150 1168 280">
        <!-- Fase 1 -->
        <g id="phase-1">
            <rect x="56" y="150" width="365" height="280" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <rect x="80" y="174" width="140" height="24" rx="9999" fill="{C_FROST_CONTAINER}"/>
            <text x="150" y="190" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="700" fill="{C_WHITE}">ETAPA 1 · CONCLUÍDA</text>
            <text x="80" y="234" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">MVP 0.9 Estável (Nov/2026)</text>
            <text x="80" y="264" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Leitura radiométrica Planck em 9 ms.</text>
            <text x="80" y="286" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• RF-DETR mAP50 0,891 em 71 ms DirectML.</text>
            <text x="80" y="308" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• NBR 15866 e IEC 60099-5 em 1,8 ms.</text>
            <text x="80" y="330" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Laudos Typst instantâneos em 32 ms.</text>
            <rect x="80" y="360" width="317" height="46" rx="8" fill="{C_ABYSS}"/>
            <text x="96" y="388" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">458 TESTES UNITÁRIOS APROVADOS (100%)</text>
        </g>
        <!-- Fase 2 -->
        <g id="phase-2">
            <rect x="457" y="150" width="365" height="280" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <rect x="481" y="174" width="160" height="24" rx="9999" fill="{C_SURFACE_HIGH}"/>
            <text x="561" y="190" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="700" fill="{C_WHITE}">ETAPA 2 · EM ANDAMENTO</text>
            <text x="481" y="234" font-family="{F_TITLE}" font-size="20" font-weight="600" fill="{C_WHITE}">Piloto de Campo (Q1/2027)</text>
            <text x="481" y="264" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Subestação 138/230 kV parceira.</text>
            <text x="481" y="286" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Coleta de 1.000+ termogramas em campo.</text>
            <text x="481" y="308" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Validação sob sol, vento e chuva.</text>
            <text x="481" y="330" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Calibração com termografia de referência.</text>
            <rect x="481" y="360" width="317" height="46" rx="8" fill="{C_ABYSS}"/>
            <text x="497" y="388" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">META: &gt; 85% CONCORDÂNCIA ESPECIALISTA</text>
        </g>
        <!-- Fase 3 -->
        <g id="phase-3">
            <rect x="858" y="150" width="366" height="280" rx="20" fill="{C_SURFACE}" stroke="{C_STROKE}" stroke-width="1"/>
            <rect x="882" y="174" width="160" height="24" rx="9999" fill="{C_SURFACE_HIGH}"/>
            <text x="962" y="190" text-anchor="middle" font-family="{F_BODY}" font-size="10" font-weight="700" fill="{C_WHITE}">ETAPA 3 · COMERCIAL</text>
            <text x="882" y="234" font-family="{F_TITLE}" font-size="18" font-weight="600" fill="{C_WHITE}">Certificação e Produto (Q2/2027)</text>
            <text x="882" y="264" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Desktop em Rust/Tauri com instalador assinado.</text>
            <text x="882" y="286" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Integração nativa com SAP PM e IBM Maximo.</text>
            <text x="882" y="308" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Novas classes: buchas, seccionadoras e TPs.</text>
            <text x="882" y="330" font-family="{F_BODY}" font-size="12" fill="{C_SILVER}">• Suporte a câmeras fixas RTSP/ONVIF.</text>
            <rect x="882" y="360" width="318" height="46" rx="8" fill="{C_ABYSS}"/>
            <text x="898" y="388" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">VERSÃO 1.0 COMERCIAL CERTIFICADA</text>
        </g>
    </g>

    <!-- Card de Encerramento e Agradecimento -->
    <g id="closing-card" data-pptx-bounds="56 454 1168 202">
        <rect x="56" y="454" width="1168" height="202" rx="24" fill="{C_SURFACE}" stroke="{C_FROST_BLUE}" stroke-width="1"/>
        <text x="88" y="494" font-family="{F_TITLE}" font-size="24" font-weight="600" fill="{C_WHITE}">Pyron MVP: O Futuro da Termografia Digital de Alta Tensão</text>
        <text x="88" y="524" font-family="{F_BODY}" font-size="13" fill="{C_SILVER}">Desenvolvido sob o programa Embrapii · Parceria Universidade e Concessionárias do Setor Elétrico</text>
        
        <rect x="88" y="546" width="340" height="84" rx="12" fill="{C_ABYSS}"/>
        <text x="108" y="574" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">DEMONSTRAÇÃO PRÁTICA INTERATIVA:</text>
        <text x="108" y="598" font-family="{F_BODY}" font-size="13" font-weight="600" fill="{C_WHITE}">Servidor Local FastAPI ativo em http://127.0.0.1:8790</text>
        <text x="108" y="618" font-family="{F_BODY}" font-size="10" fill="{C_MUTED}">Abra e teste qualquer termograma FLIR ou imagem comum.</text>

        <rect x="452" y="546" width="340" height="84" rx="12" fill="{C_ABYSS}"/>
        <text x="472" y="574" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_FROST_BLUE}">MASCOTE 3D PROCEDURAL:</text>
        <text x="472" y="598" font-family="{F_BODY}" font-size="13" font-weight="600" fill="{C_WHITE}">Sentinela PYRON-01 em WebGL / Three.js</text>
        <text x="472" y="618" font-family="{F_BODY}" font-size="10" fill="{C_MUTED}">Disponível em apresentacao_mvp/abrir-personagem-3d.cmd</text>

        <rect x="816" y="546" width="376" height="84" rx="12" fill="{C_FROST_CONTAINER}"/>
        <text x="836" y="574" font-family="{F_BODY}" font-size="11" font-weight="700" fill="{C_WHITE}">EQUIPE DE DESENVOLVIMENTO:</text>
        <text x="836" y="598" font-family="{F_BODY}" font-size="13" font-weight="600" fill="{C_WHITE}">Gabriel &amp; Hugo · Equipe Pyron / Embrapii</text>
        <text x="836" y="618" font-family="{F_BODY}" font-size="10" fill="{C_FROST_BLUE}">Agradecemos a atenção de todos os avaliadores!</text>
    </g>
"""

# Lista de todos os slides: (número, sufixo_nome, conteúdo_svg, título_nota, roteiro_fala)
SLIDES = [
    (1, "hero", s01_content, "Abertura Hero e Abstract Executivo", "Apresentamos o Pyron MVP. O Pyron é uma plataforma metrológica termodinâmica 100% offline projetada para subestações elétricas críticas. Unimos a física do efeito Joule, a inversão analítica da curva de Planck e redes neurais transformers RF-DETR com aceleração DirectML na GPU."),
    (2, "joule", s02_content, "O Paradoxo da Baixa Carga e Efeito Joule", "A termografia comum falha gravemente quando inspeciona condutores sob carga baixa. O calor resistivo varia com o quadrado da corrente. Um aquecimento de apenas 5,4 graus a 30% de corrente se transforma em 60 graus a plena carga, atingindo nível de intervenção imediata em 24 horas pela NBR 15866."),
    (3, "planck", s03_content, "Desenrolamento Radiométrico e Inversão de Planck", "Descompactamos o JPEG radiométrico no segmento APP1 da câmera em 1 ms e invertemos a curva de Planck em 9 ms. Em fotos comuns sem radiometria, nosso algoritmo de programação dinâmica rastreia a barra de escala e calibra as temperaturas com erro mediano comprovado de 0,53 °C."),
    (4, "transformers", s04_content, "Detecção de Ativos com Transformers RF-DETR", "Nosso modelo RF-DETR com base DINOv2 foi treinado em fotos reais de subestação. Ele segmenta o corpo do para-raios com AP50 de 0,99, as aletas com 1,00 e os terminais com 0,84 e 0,73, atingindo mAP50 de 0,891 em apenas 71 ms na GPU via DirectML."),
    (5, "segmentation3d", s05_content, "Segmentação Fina SAM 2.1 e Profundidade 3D", "Caixas delimitadoras retangulares tradicionais capturam até 40% de céu frio de fundo (-20 °C a 5 °C), rebaixando a média térmica real do componente. O contorno fino do SAM 2.1 elimina o céu. O Depth Anything 3 estima coordenadas tridimensionais com erro mediano de apenas 5,1%."),
    (6, "arrester_zno", s06_content, "Diagnóstico Especializado de Para-raios ZnO", "Muitos softwares erram ao aplicar correção de corrente I²R a para-raios. Para-raios não transportam corrente de carga; operam sob tensão contínua. Aplicamos a norma internacional IEC 60099-5, onde uma diferença de 2 °C entre fases já requer atenção e 10 °C exige troca imediata."),
    (7, "normative_engine", s07_content, "Motor de Decisão Normativa Dupla NBR 15866", "O Pyron resolve 9 regiões térmicas em 1,8 ms. Ele cruza o aquecimento relativo trifásico corrigido com o percentual da MTA absoluta do componente, enquadrando automaticamente a severidade nos 5 níveis da norma brasileira, de 365 dias a 24 horas."),
    (8, "mobile_telemetry", s08_content, "Telemetria Mobile Edge e Fluxo Óptico", "O inspetor utiliza um smartphone conectado via WebSocket seguro a 15 fps num servidor Uvicorn secundário na porta 8791. O celular calcula o deslocamento por fluxo óptico com erro inferior a 0,3 pixel, mantendo as caixas térmicas alinhadas na tela mesmo com tremor das mãos."),
    (9, "offline_architecture", s09_content, "Arquitetura 100% Offline Edge e Cibersegurança", "Subestações de alta tensão são ambientes isolados da internet. O Pyron opera 100% offline com 128 rotas FastAPI, DirectML homologado para o Windows 11 Smart App Control e banco SQLite WAL com resposta de 58 ms para 6.000 inspeções."),
    (10, "automated_reports", s10_content, "Geração Instantânea de Laudos Regulatórios Typst", "A compilação de relatórios periciais que levava horas em Word é realizada em apenas 32 milissegundos com o motor Typst. Os dados do operador entram por JSON tipado sem risco de injeção, gerando documentos periciais completos para Prontuário NR-10."),
    (11, "business_roi", s11_content, "Valor do Produto: ROI Industrial e Prevenção", "Uma única parada forçada de subestação consome mais de R$ 450.000 por hora em multas da ANEEL. Além disso, evitar a queima de um transformador de força economiza até R$ 3,5 milhões. O Pyron traz retorno sobre o investimento imediato na primeira anomalia prevenida."),
    (12, "roadmap_closing", s12_content, "Cronograma de Homologação e Encerramento", "Com 458 testes automatizados aprovados e arquitetura validada, estamos prontos para o piloto de campo com 1.000 termogramas em subestação real parceira. Agradecemos à Embrapii e convidamos todos a testar o sistema no nosso servidor demonstrativo.")
]

def main():
    print("Iniciando geração de slides SVG e notas Obsidian Frost com padrões PPT-Master...")
    for num, suffix, content, title, note_speech in SLIDES:
        role = "cover" if num == 1 else "content"
        svg_code = wrap_svg(content, num, page_role=role)
        svg_filename = f"P{num:02d}_{suffix}.svg"
        svg_path = SVG_DIR / svg_filename
        svg_path.write_text(svg_code, encoding="utf-8")
        
        # Gera nota de orador Markdown correspondente
        note_filename = f"P{num:02d}_{suffix}.md"
        note_path = NOTES_DIR / note_filename
        note_text = f"# Slide {num:02d} - {title}\n\n## Roteiro de Apresentação (Notas de Orador)\n\n{note_speech}\n"
        note_path.write_text(note_text, encoding="utf-8")
        
        print(f"  [OK] Gerado {svg_filename} e {note_filename}")
        
    print("\nTodos os 12 slides e notas foram gerados com sucesso!")

if __name__ == "__main__":
    main()
