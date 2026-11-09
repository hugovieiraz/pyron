import json

slides = [
    "p",
    "SLIDES_API932609610_0",
    "SLIDES_API640924346_0",
    "SLIDES_API2994205_0",
    "SLIDES_API663053325_0"
]

ops = []

for s in slides:
    ops.append({
        "op": "set-background",
        "slide": s,
        "color": "#FFFFFF"
    })

def add_header(slide_id, prefix, num_label, title_text, norm_badge):
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": f"   {num_label}   |   {title_text}",
        "x": 0, "y": 0, "width": 720, "height": 48,
        "font_size": 14, "bold": True, "color": "#FFFFFF",
        "background_color": "#0F172A",
        "content_alignment": "MIDDLE",
        "font_family": "Roboto"
    })
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": norm_badge,
        "x": 515, "y": 9, "width": 190, "height": 30,
        "font_size": 9.5, "bold": True, "color": "#0F172A",
        "background_color": "#38BDF8",
        "alignment": "center",
        "content_alignment": "MIDDLE",
        "font_family": "Roboto"
    })

# ==========================================================
# SLIDE 1: CAPA VISUAL ABSTRACT IEEE — PYRON MVP
# ==========================================================
add_header(
    "p", "s1",
    "PYRON MVP • EMBRAPII",
    "Termografia Preditiva & Visão Computacional em Subestações",
    "ABNT NBR 15866 • IEC 60099-5"
)

# Overlay stage banner over the top of fig_slide1 ("LEFT -> CENTER -> RIGHT" strip at y=52..96)
s1_stages = [
    (22,  "1. AQUISIÇÃO RADIOMÉTRICA (8–14 μm)\nEmissividade ε, Reflexão & Lei de Planck (9 ms)", "#0F172A", "#F8FAFC"),
    (252, "2. VISÃO COMPUTACIONAL (RF-DETR + SAM 2.1)\nRecorte do Ativo + Profundidade Métrica DA3/MoGe-2", "#0284C7", "#FFFFFF"),
    (482, "3. DECISÃO NORMATIVA (ABNT NBR 15866)\nProjeção Quadrática I²R & Matriz de Severidade", "#EA580C", "#FFFFFF")
]
for x_pos, st_txt, bg_col, fg_col in s1_stages:
    ops.append({
        "op": "add-textbox",
        "slide": "p",
        "text": st_txt,
        "x": x_pos, "y": 54, "width": 216, "height": 42,
        "font_size": 9, "bold": True, "color": fg_col,
        "background_color": bg_col,
        "alignment": "center",
        "content_alignment": "MIDDLE",
        "font_family": "Roboto"
    })

# Bottom 4 KPI Scientific Cards on Slide 1 (y=342..392)
s1_kpis = [
    (18,  "9 ms  |  Leitura Radiométrica\nConversão Planck 1 ms • 299/299 barras", "#F1F5F9", "#0F172A"),
    (192, "0,53 °C  |  Erro Mediano Barra\nUnwrapping radiométrico sem EXIF proprietário", "#F1F5F9", "#0F172A"),
    (366, "mAP50 0,891  |  RF-DETR + SAM 2.1\n54–71 ms DirectML GPU • 5,1% erro métrico 3D", "#F1F5F9", "#0F172A"),
    (540, "0,3 px  |  Rastreio Mobile 12 fps\nFluxo óptico 72 px + Laudo Typst NR-10 / PIE", "#FFF7ED", "#9A3412")
]
for x_pos, k_txt, bg_col, fg_col in s1_kpis:
    ops.append({
        "op": "add-textbox",
        "slide": "p",
        "text": k_txt,
        "x": x_pos, "y": 342, "width": 164, "height": 50,
        "font_size": 8.5, "bold": True, "color": fg_col,
        "background_color": bg_col,
        "alignment": "center",
        "content_alignment": "MIDDLE",
        "font_family": "Roboto"
    })

ops.append({
    "op": "set-notes",
    "slide": "p",
    "text": "Slide 1 (Visual Abstract IEEE): O Pyron MVP unifica física radiométrica (Lei de Planck em 1 ms, desdobramento universal da barra de cores com erro mediano de 0,53 °C), visão computacional (RF-DETR mAP50 = 0,891 + SAM 2.1 + profundidade métrica Depth Anything 3 / MoGe-2 com erro de 5,1%) e diagnóstico normativo ABNT NBR 15866 / IEC 60099-5."
})

# ==========================================================
# SLIDE 2: PARADOXO DA CARGA BAIXA & LEI DE JOULE (I²R)
# ==========================================================
add_header(
    "SLIDES_API932609610_0", "s2",
    "01 • FUNDAMENTAÇÃO FÍSICA",
    "O Paradoxo da Carga Baixa: Por que Limiares Fixos Falham?",
    "LEI DE JOULE (P = I²·R)"
)

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API932609610_0",
    "text": "PROJEÇÃO QUADRÁTICA DE CARGA\n\nT_proj = T_amb + ΔT_med · (100 / Carga)²\n\n• Inspeção a 30% de carga:\n   T_med = 58 °C  (T_amb = 30 °C)\n   Fator quadrático: (100/30)² = 11,1×\n\n• Em carga nominal (100%):\n   T_proj = 118 °C > MTA (95 °C)\n   Colapso térmico oculto em baixa carga!",
    "x": 502, "y": 56, "width": 200, "height": 182,
    "font_size": 9, "bold": True, "color": "#0F172A",
    "background_color": "#F8FAFC",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API932609610_0",
    "text": "MARGEM OPERACIONAL SEGURA\n\nCarga_máx = √[(MTA − T_amb) / ΔT_med]\n\nO Pyron calcula instantaneamente até qual percentual de carga o ativo pode operar antes de atingir a MTA normativa.",
    "x": 502, "y": 246, "width": 200, "height": 103,
    "font_size": 9, "bold": True, "color": "#9A3412",
    "background_color": "#FFF7ED",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API932609610_0",
    "text": "Referências: ABNT NBR 15866 (Termografia em Sistemas Elétricos)  •  IEC 62271-1 (Elevação de Temperatura)  •  MDPI Applied Sciences 12(22), 2022",
    "x": 18, "y": 356, "width": 684, "height": 36,
    "font_size": 9, "bold": True, "color": "#334155",
    "background_color": "#F1F5F9",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "set-notes",
    "slide": "SLIDES_API932609610_0",
    "text": "Slide 2: Demonstração da armadilha do 'Falso Normal'. Pela Lei de Joule (P = I²R), a elevação de temperatura acima do ambiente cresce com o quadrado da corrente. Um conector a 58 °C com 30% de carga parece normal se comparado diretamente à MTA de 95 °C, mas a 100% de carga atingirá 118 °C."
})

# ==========================================================
# SLIDE 3: EFEITO JOULE VS. LEI DE ARRHENIUS & MONTSINGER
# ==========================================================
add_header(
    "SLIDES_API640924346_0", "s3",
    "02 • CINÉTICA DE DEGRADAÇÃO",
    "Constrição de Contato (Joule) vs. Envelhecimento de Arrhenius",
    "IEEE C57.91 • MONTSINGER"
)

# Clean white editable label covering the tiny "Infrared Thotspot" artifact on Panel A
ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API640924346_0",
    "text": "Ponto Quente IR\n(P = R_c · I²)",
    "x": 22, "y": 290, "width": 120, "height": 36,
    "font_size": 8.5, "bold": True, "color": "#9A3412",
    "background_color": "#FFF7ED",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API640924346_0",
    "text": "A) CONEXÕES METÁLICAS: R_c = ρ / (2·a·n)  →  Oxidação reduz pontos de contato e cria avalanche ôhmica",
    "x": 18, "y": 343, "width": 336, "height": 48,
    "font_size": 9, "bold": True, "color": "#0F172A",
    "background_color": "#F1F5F9",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API640924346_0",
    "text": "B) ISOLAMENTO DIELÉTRICO: k = A · exp(−E_a / R·T)  →  Regra de Montsinger: +8 a +10 °C corta a vida útil em 50%",
    "x": 366, "y": 343, "width": 336, "height": 48,
    "font_size": 9, "bold": True, "color": "#9A3412",
    "background_color": "#FFF7ED",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "set-notes",
    "slide": "SLIDES_API640924346_0",
    "text": "Slide 3: Dois mecanismos físicos distintos regem as falhas em subestações: (A) Constrição de linhas de corrente em microrregiões de contato oxidado (R_c), e (B) Degradação química exponencial de polímeros e óleo isolante segundo Arrhenius e a Regra de Montsinger (IEEE C57.91: perda de 50% da vida útil a cada +8 a +10 °C)."
})

# ==========================================================
# SLIDE 4: ANATOMIA TÉRMICA DO PARA-RAIOS DE ZnO (IEC 60099-5)
# ==========================================================
add_header(
    "SLIDES_API2994205_0", "s4",
    "03 • DIAGNÓSTICO DE PARA-RAIOS (ZnO)",
    "Aquecimento Dielétrico em Varistores: Fuga Resistiva vs. Carga",
    "IEC 60099-5 • NBR 15866"
)

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API2994205_0",
    "text": "POR QUE NÃO APLICAR CORREÇÃO DE CARGA?\n\n• Para-raios de ZnO e isoladores operam submetidos à Tensão Fase-Terra constante.\n\n• O aquecimento decorre da corrente de fuga resistiva (I_R) nos discos de ZnO degradados ou umidade interna:\n   P_diel = V · I_R(T, V)\n\n• Independente da corrente de carga da linha!",
    "x": 502, "y": 56, "width": 200, "height": 165,
    "font_size": 9, "bold": True, "color": "#0F172A",
    "background_color": "#F8FAFC",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API2994205_0",
    "text": "LIMIARES DEDICADOS NO PYRON\n(Regra 'pararaios' • Sem Fator I²R)\n\n• ΔT ≥ 2,0 °C  →  ATENÇÃO\n• ΔT ≥ 5,0 °C  →  PROGRAMAR\n• ΔT ≥ 10,0 °C →  URGENTE\n\nPequenos ΔT externos (2–5 °C) já indicam perda de não-linearidade interna do ZnO.",
    "x": 502, "y": 229, "width": 200, "height": 120,
    "font_size": 9, "bold": True, "color": "#9A3412",
    "background_color": "#FFF7ED",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API2994205_0",
    "text": "Base Experimental Pyron: 47 Para-Raios de Alta Tensão Inspecionados  •  306 Peças Segmentadas  •  Norma IEC 60099-5",
    "x": 18, "y": 356, "width": 684, "height": 36,
    "font_size": 9, "bold": True, "color": "#334155",
    "background_color": "#F1F5F9",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "set-notes",
    "slide": "SLIDES_API2994205_0",
    "text": "Slide 4: Diferenciação física fundamental implementada no Pyron (nucleo/regras.py). Enquanto conexões e buchas aquecem por corrente de carga (I²R), para-raios de ZnO aquecem por perdas dielétricas e corrente de fuga resistiva sob tensão nominal. Por isso o Pyron desativa a projeção de carga para para-raios e aplica limiares estritos de 2 / 5 / 10 °C conforme IEC 60099-5."
})

# ==========================================================
# SLIDE 5: TERMOGRAFIA COMPARATIVA TRIFÁSICA & DUPLO CRITÉRIO
# ==========================================================
add_header(
    "SLIDES_API663053325_0", "s5",
    "04 • ARQUITETURA DE DECISÃO NORMATIVA",
    "Termografia Comparativa Trifásica & Duplo Critério NBR 15866",
    "ABNT NBR 15866 • NETA MTS"
)

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API663053325_0",
    "text": "CANCELAMENTO DE RUÍDO AMBIENTAL\nFases A, B e C sob mesma radiação solar e vento (convectivo) → ΔT = +24,2 °C isola a anomalia interna",
    "x": 18, "y": 343, "width": 336, "height": 48,
    "font_size": 9, "bold": True, "color": "#0F172A",
    "background_color": "#F1F5F9",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API663053325_0",
    "text": "CATÁLOGO DE MTA POR CLASSE DE ATIVO\nBucha: 95 °C  •  Conexão Nua: 100 °C  •  Óleo Topo: 100 °C  •  Cabo PVC: 70 °C  •  Cabo EPR/XLPE: 90 °C",
    "x": 366, "y": 343, "width": 336, "height": 48,
    "font_size": 9, "bold": True, "color": "#9A3412",
    "background_color": "#FFF7ED",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

ops.append({
    "op": "set-notes",
    "slide": "SLIDES_API663053325_0",
    "text": "Slide 5: O motor de regras do Pyron avalia simultaneamente o Critério Absoluto (fração da MTA projetada para 100% de carga: >60% Atenção, >70% Programar, >80% Urgente, >100% Imediato) e o Critério Relativo entre fases homólogas (ΔT: 5–10 °C Atenção, 10–20 °C Programar, 20–40 °C Urgente, >40 °C Imediato), adotando sempre o diagnóstico mais conservador."
})

with open("apresentacao_mvp/batch_parte1_ieee.json", "w", encoding="utf-8") as f:
    json.dump(ops, f, ensure_ascii=False, indent=2)

print(f"Generated {len(ops)} batch operations.")
