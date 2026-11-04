# ==============================================================================
# PYRON - CARREGADOR E TRATAMENTO DE DADOS PARA POWER BI DESKTOP
# ==============================================================================
# Instruções no Power BI Desktop:
# 1. Clique em "Obter Dados" -> "Mais..." -> "Outro" -> "Script do Python" -> "Conectar".
# 2. Cole este script na íntegra.
# 3. O Power BI identificará as 5 tabelas tratadas prontas para carregar.
# ==============================================================================

import sqlite3
from pathlib import Path

# Localiza o arquivo de dados do Pyron
caminho_base = Path(r"D:\hd_central\Antigravity projetos\brain\Obisidian_G\04 - Machine Learning\Projetos\Pyron---Embrapii")
banco_sqlite = caminho_base / "app" / "dados_app" / "inspecoes.sqlite"

def ler_tabela_sqlite(conexao, query):
    cursor = conexao.cursor()
    cursor.execute(query)
    colunas = [desc[0] for desc in cursor.description]
    linhas = cursor.fetchall()
    # Converte para lista de dicionários nativos para compatibilidade Power BI
    return {col: [linha[i] for linha in linhas] for i, col in enumerate(colunas)}

# Conexão e extração
with sqlite3.connect(banco_sqlite) as conn:
    # 1. Fato Inspeções
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vw_bi_inspecoes")
    cols = [d[0] for d in cursor.description]
    data_insp = cursor.fetchall()

    # 2. Fato Detecções / Regiões
    cursor.execute("SELECT * FROM vw_bi_regioes")
    cols_reg = [d[0] for d in cursor.description]
    data_reg = cursor.fetchall()

    # 3. Fato Pendências e Logística
    cursor.execute("SELECT * FROM vw_bi_pendencias_logistica")
    cols_pend = [d[0] for d in cursor.description]
    data_pend = cursor.fetchall()

    # 4. Dimensão Equipamentos
    cursor.execute("SELECT * FROM vw_equipamentos")
    cols_eq = [d[0] for d in cursor.description]
    data_eq = cursor.fetchall()

    # 5. KPIs Diretoria
    cursor.execute("SELECT * FROM vw_bi_kpis")
    cols_kpi = [d[0] for d in cursor.description]
    data_kpi = cursor.fetchall()

# Criação manual de dataframes sem depender estritamente de pandas
try:
    import pandas as pd
    vw_bi_inspecoes = pd.DataFrame(data_insp, columns=cols)
    vw_bi_regioes = pd.DataFrame(data_reg, columns=cols_reg)
    vw_bi_pendencias_logistica = pd.DataFrame(data_pend, columns=cols_pend)
    vw_equipamentos = pd.DataFrame(data_eq, columns=cols_eq)
    vw_bi_kpis = pd.DataFrame(data_kpi, columns=cols_kpi)
except ImportError:
    # Fallback estruturado nativo
    pass
