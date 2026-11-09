import json

slides = [
    "p",
    "SLIDES_API2058668409_0",
    "SLIDES_API1523361023_0",
    "SLIDES_API2122815573_0",
    "SLIDES_API1722072494_0"
]

ops = []

def add_swiss_left_column(
    slide_id,
    big_title,
    big_title_size,
    sec_tag,
    formula_header,
    formula_body,
    kpi_big,
    kpi_sub,
    pills,
    notes_text
):
    # 1. Oversized Swiss Editorial Headline (Charcoal #18181B)
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": big_title,
        "x": 34, "y": 32, "width": 240, "height": 96,
        "font_size": big_title_size, "bold": True, "color": "#18181B",
        "font_family": "Roboto"
    })
    # 2. Cobalt Blue Swiss Index & Category Tag (01 // ...)
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": sec_tag,
        "x": 34, "y": 132, "width": 240, "height": 26,
        "font_size": 10.5, "bold": True, "color": "#1D4ED8",
        "font_family": "Roboto"
    })
    # 3. White Technical Card — Top Half (Formula & Physics Explanation)
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": f"{formula_header}\n{formula_body}",
        "x": 34, "y": 170, "width": 236, "height": 96,
        "font_size": 9.5, "bold": True, "color": "#18181B",
        "background_color": "#FFFFFF",
        "content_alignment": "MIDDLE",
        "font_family": "Roboto"
    })
    # 4. White Technical Card — Bottom Half (Giant Swiss Metric + Subcaption)
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": kpi_big,
        "x": 34, "y": 268, "width": 236, "height": 58,
        "font_size": 32, "bold": True, "color": "#18181B",
        "background_color": "#FFFFFF",
        "content_alignment": "BOTTOM",
        "font_family": "Roboto"
    })
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": kpi_sub,
        "x": 34, "y": 326, "width": 236, "height": 34,
        "font_size": 9, "bold": True, "color": "#52525B",
        "background_color": "#FFFFFF",
        "content_alignment": "TOP",
        "font_family": "Roboto"
    })
    # 5. Bottom-Right Swiss Normative Pills (3 crisp pills at y=362)
    pill_xs = [454, 540, 626]
    for px, p_txt in zip(pill_xs, pills):
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": p_txt,
            "x": px, "y": 360, "width": 80, "height": 22,
            "font_size": 7.5, "bold": True, "color": "#18181B",
            "background_color": "#FFFFFF",
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "font_family": "Roboto"
        })
    # 6. Speaker notes
    ops.append({
        "op": "set-notes",
        "slide": slide_id,
        "text": notes_text
    })

# ==============================================================================
# SLIDE 1: PYRON MVP — VISÃO GERAL & TERMOGRAFIA PREDITIVA
# ==============================================================================
add_swiss_left_column(
    slide_id="p",
    big_title="PYRON\nMVP",
    big_title_size=40,
    sec_tag="01 // ANÁLISE TERMOGRÁFICA & IA",
    formula_header="T_proj = T_amb + ΔT · (100/Carga)²",
    formula_body="\nLeitura radiométrica Planck (9 ms) +\nSegmentação RF-DETR & SAM 2.1",
    kpi_big="0,53 °C",
    kpi_sub="MAE Erro Mediano no Unwrapping da Barra",
    pills=["ABNT NBR 15866", "IEC 60099-5", "EMBRAPII"],
    notes_text="Slide 1 (Editorial Técnico Suíço): Apresentação do Pyron MVP. À esquerda, a tipografia suíça destaca a equação de projeção quadrática de carga e o erro mediano de 0,53 °C no desdobramento radiométrico universal da barra de cores. À direita, a ilustração CAD/termográfica híbrida mostra o transformador de 138 kV com anomalia severa na Bucha Fase A (84,6 °C)."
)

# ==============================================================================
# SLIDE 2: PARADOXO DA CARGA BAIXA & PROJEÇÃO DE JOULE (I²R)
# ==============================================================================
add_swiss_left_column(
    slide_id="SLIDES_API2058668409_0",
    big_title="EFEITO\nJOULE I²R",
    big_title_size=34,
    sec_tag="02 // PARADOXO DA CARGA BAIXA",
    formula_header="Carga_máx = √[(MTA − T_amb) / ΔT]",
    formula_body="\nA 30% de carga, 58 °C parece normal,\nmas esconde fator quadrático 11,1×",
    kpi_big="118 °C",
    kpi_sub="Temperatura Projetada a 100% (> MTA 95 °C)",
    pills=["LEI DE JOULE", "IEC 62271-1", "NBR 15866"],
    notes_text="Slide 2 (Paradoxo da Carga Baixa): Pela Lei de Joule (P = I²R), a elevação térmica cresce com o quadrado da corrente. Um conector inspecionado a 30% de carga medindo 58 °C (T_amb = 30 °C) gera um falso diagnóstico normal sob limiares estáticos, mas em carga nominal (100%) atingirá 118 °C, ultrapassando a MTA de 95 °C."
)

# ==============================================================================
# SLIDE 3: CONSTRIÇÃO DE CONTATO VS. ENVELHECIMENTO DE ARRHENIUS
# ==============================================================================
add_swiss_left_column(
    slide_id="SLIDES_API1523361023_0",
    big_title="VIDA ÚTIL\nARRHENIUS",
    big_title_size=31,
    sec_tag="03 // CINÉTICA DE DEGRADAÇÃO",
    formula_header="k = A · exp(−E_a / R·T)",
    formula_body="\nConstrição ôhmica: R_c = ρ / (2·a·n)\nOxidação reduz pontes de contato metálico",
    kpi_big="−50 %",
    kpi_sub="Perda de Vida Útil do Isolante a cada +8 °C",
    pills=["IEEE C57.91", "MONTSINGER", "ARRHENIUS"],
    notes_text="Slide 3 (Cinética de Degradação): Dois fenômenos acoplados destroem ativos de alta tensão: (A) a resistência de constrição R_c nas microasperezas de conexões oxidadas gera calor por efeito Joule; (B) a Lei de Arrhenius e a Regra de Montsinger determinam que cada +8 °C a +10 °C reduz pela metade a vida útil mecânica e dielétrica do isolamento."
)
# Clean white/cream editable label covering the tiny "Infrared Thotspot" artifact inside Panel A on Slide 3
ops.append({
    "op": "add-textbox",
    "slide": "SLIDES_API1523361023_0",
    "text": "Ponto Quente IR",
    "x": 428, "y": 270, "width": 66, "height": 28,
    "font_size": 7.5, "bold": True, "color": "#9A3412",
    "background_color": "#F6F5F0",
    "alignment": "center",
    "content_alignment": "MIDDLE",
    "font_family": "Roboto"
})

# ==============================================================================
# SLIDE 4: PARA-RAIOS DE ZnO & AQUECIMENTO DIELÉTRICO (IEC 60099-5)
# ==============================================================================
add_swiss_left_column(
    slide_id="SLIDES_API2122815573_0",
    big_title="VARISTOR\nZnO // AT",
    big_title_size=32,
    sec_tag="04 // PERDA DIELÉTRICA INTERNA",
    formula_header="P_diel = V_fase · I_R(T, V)",
    formula_body="\nAquecimento por corrente de fuga resistiva\nsob tensão nominal (independe da carga!)",
    kpi_big="+2,0 °C",
    kpi_sub="Limiar Estrito de Atenção (5 °C Prog. / 10 °C Urg.)",
    pills=["IEC 60099-5", "47 PARA-RAIOS", "306 PEÇAS"],
    notes_text="Slide 4 (Diagnóstico de Para-Raios de ZnO): Ao contrário de buchas e conectores, para-raios de óxido de zinco (ZnO) aquecem por corrente de fuga resistiva nos discos internos submetidos à tensão fase-terra constante. Por isso o Pyron desativa a correção quadrática de carga para a regra 'pararaios' e aplica limiares dedicados de 2 °C / 5 °C / 10 °C conforme IEC 60099-5."
)

# ==============================================================================
# SLIDE 5: TERMOGRAFIA COMPARATIVA TRIFÁSICA & DUPLO CRITÉRIO NBR 15866
# ==============================================================================
add_swiss_left_column(
    slide_id="SLIDES_API1722072494_0",
    big_title="MATRIZ\nNBR 15866",
    big_title_size=31,
    sec_tag="05 // DUPLO CRITÉRIO NORMATIVO",
    formula_header="Severidade = máx(S_MTA , S_ΔT)",
    formula_body="\nComparação entre fases homólogas (A/B/C)\ncancela viés de radiação solar e vento",
    kpi_big="+24,2 °C",
    kpi_sub="ΔT entre Fases B e A → Intervenção Urgente",
    pills=["ABNT NBR 15866", "NETA MTS", "NR-10 / PIE"],
    notes_text="Slide 5 (Duplo Critério NBR 15866): O motor normativo do Pyron cruza simultaneamente a fração da Temperatura Máxima Admissível (MTA: Bucha 95 °C, Conexão 100 °C, Cabo PVC 70 °C) com o diferencial ΔT entre fases homólogas submetidas às mesmas condições solares e convectivas, adotando sempre o grau de risco mais conservador."
)

with open("apresentacao_mvp/batch_parte1_swiss.json", "w", encoding="utf-8") as f:
    json.dump(ops, f, ensure_ascii=False, indent=2)

print(f"Generated {len(ops)} Swiss batch operations.")
