# Projeto Power BI Empresarial — Pyron (Manutenção Preditiva & Subestações)

Este documento é a especificação técnica e funcional completa para montagem do **Dashboard Empresarial no Microsoft Power BI** (versão Desktop ou Serviço), conectando diretamente à camada de dados do Pyron (SQLite local ou PostgreSQL em nuvem).

---

## 1. Arquitetura de Dados no Power BI (Star Schema)

Para garantir máxima performance no Power BI (*Query Folding* e compressão *VertiPaq*), o modelo utiliza um esquema estrela com 5 tabelas principais:

```
                   ┌───────────────────────────────┐
                   │        vw_equipamentos        │
                   │    (Dimensão de Ativos)       │
                   └───────────────┬───────────────┘
                                   │ 1
                                   │
                                   │ *
                   ┌───────────────┴───────────────┐
                   │        vw_bi_inspecoes        │
                   │     (Fato de Inspeções)       │
                   └───────┬───────────────┬───────┘
                         1 │             1 │
                           │               │
                         * │             * │
 ┌─────────────────────────┴─────┐   ┌─────┴─────────────────────────┐
 │         vw_bi_regioes         │   │  vw_bi_pendencias_logistica   │
 │   (Fato Detecções / Caixas)   │   │  (Fato Manutenção / Compras)  │
 └───────────────────────────────┘   └───────────────────────────────┘
```

### Relacionamentos:
1. `vw_equipamentos[chave]` **1 : N** `vw_bi_inspecoes[equipamento_chave]`
   - Direção do filtro cruzado: *Única (1 para N)*.
2. `vw_bi_inspecoes[inspecao_id]` **1 : N** `vw_bi_regioes[inspecao_id]`
   - Direção do filtro cruzado: *Única*.
3. `vw_bi_inspecoes[inspecao_id]` **1 : N** `vw_bi_pendencias_logistica[inspecao_id]`
   - Direção do filtro cruzado: *Ambas* (permite cruzar equipamentos e datas de inspeção com ordens de serviço).

---

## 2. Como Importar os Dados no Power BI Desktop

Você pode escolher um dos 2 métodos:

### Método A: Importação Instantânea via CSV (Mais Fácil)
Os dados já foram extraídos e normalizados em formato UTF-8 com separador `;` em `docs/powerbi_export/`:
1. No Power BI Desktop, clique em **Página Inicial** → **Obter Dados** → **Texto/CSV**.
2. Selecione e carregue cada arquivo da pasta `docs/powerbi_export/`:
   - `vw_bi_kpis.csv`
   - `vw_bi_inspecoes.csv`
   - `vw_bi_regioes.csv`
   - `vw_bi_pendencias_logistica.csv`
   - `vw_equipamentos.csv`

### Método B: Conexão Direta ao Banco SQLite (Tempo Real)
1. Clique em **Obter Dados** → **Mais...** → **Outro** → **Script do Python**.
2. Cole o script disponível em `docs/carregar_power_bi.py`.

---

## 3. Configuração de Tipos e Categorias no Power BI

Para habilitar a visualização dos termogramas diretamente nas tabelas e gráficos:

1. Selecione a tabela `vw_bi_inspecoes`.
2. Clique na coluna `miniatura_url` ou `termograma_url`.
3. Na barra de ferramentas superior, em **Ferramentas de Coluna** → **Categoria dos Dados**, altere de *Não Categorizado* para **URL da Imagem** (*Image URL*).
4. No campo `data_calendario`, altere o tipo para **Data** (`Date`).

---

## 4. Medidas em DAX (Métricas de Negócio)

Crie uma nova tabela de medidas chamada `_Medidas_Pyron` e adicione as fórmulas DAX abaixo:

### Totalizadores e Criticidade
```dax
Total Inspecoes = COUNTROWS(vw_bi_inspecoes)

Total Ativos Monitorados = DISTINCTCOUNT(vw_equipamentos[chave])

Inspecoes Criticas = 
CALCULATE(
    COUNTROWS(vw_bi_inspecoes),
    vw_bi_inspecoes[severidade] IN {"urgente", "imediato"}
)

Taxa de Falha Critica = 
DIVIDE([Inspecoes Criticas], [Total Inspecoes], 0)
```

### Logística e Prazo de Manutenção (NBR 15866)
```dax
Reparos Pendentes = COUNTROWS(vw_bi_pendencias_logistica)

Reparos Vencidos = 
CALCULATE(
    COUNTROWS(vw_bi_pendencias_logistica),
    vw_bi_pendencias_logistica[dias_restantes_para_reparo] < 0
)

Reparos Criticos 7 Dias = 
CALCULATE(
    COUNTROWS(vw_bi_pendencias_logistica),
    vw_bi_pendencias_logistica[dias_restantes_para_reparo] >= 0,
    vw_bi_pendencias_logistica[dias_restantes_para_reparo] <= 7
)

Pico Temperatura Global = MAX(vw_bi_inspecoes[t_max_cena])

Maior Delta T = MAX(vw_bi_regioes[dt_corrigido])
```

---

## 5. Estrutura das Telas do Dashboard (Layout Empresarial)

Recomendamos montar o dashboard em **3 páginas temáticas**:

### Página 1: Painel Executivo / Diretoria (Visão Geral)
- **Cabeçalho:** Logo Pyron + Indicadores de Data de Atualização e Filtro por Subestação (`instalacao`).
- **Cartões de KPI (Topo):**
  1. *Ativos Monitorados* (`[Total Ativos Monitorados]`)
  2. *Total de Inspeções* (`[Total Inspecoes]`)
  3. *Anomalias Críticas* (`[Inspecoes Criticas]`, cor de fundo Vermelho suave)
  4. *Reparos em Atraso* (`[Reparos Vencidos]`, destaque de alerta)
  5. *Pico Térmico Histórico* (`[Pico Temperatura Global]`, sufixo "°C")
- **Gráfico de Rosca (Centro-Esquerda):** Distribuição por Severidade (`severidade`: *Normal, Atenção, Programar, Urgente, Imediato*).
- **Gráfico de Barras Horizontais (Centro-Direita):** Top 5 Equipamentos com Maior Sobreaquecimento ($\Delta T$).
- **Matriz Analítica (Inferior):**
  - Colunas: `instalacao`, `equipamento`, `data_calendario`, `severidade`, `t_max_cena`, `miniatura_url`.

### Página 2: Engenharia de Manutenção & Degradação Térmica
- **Filtros Laterais (Slicers):** Subestação, Equipamento (`tag_codigo`), Classe de Componente (*Bucha, Para-raios, Conexão, Cabo*).
- **Gráfico de Dispersão (Scatter Plot):**
  - Eixo X: Temperatura Máxima ($T_{máx}$ °C).
  - Eixo Y: $\Delta T$ Corrigido pela Carga (°C).
  - Tamanho da Bolha: `% da MTA`.
  - Cores: Severidade.
- **Gráfico de Linha (Evolução Temporal):**
  - Eixo X: `capturado_em`.
  - Linha 1: Temperatura Máxima Registrada.
  - Linha 2: Temperatura Ambiente.
- **Tabela de Componentes:** Detalhamento por Caixa/ROI, Ponto Quente `(x_max, y_max)` e Confiança do Modelo de IA.

### Página 3: Logística, Suprimentos e Paradas de Manutenção
- **Filtros:** Status da OS (`aberta`, `programada`, `corrigida`), Prioridade Logística.
- **Gráfico de Barras Empilhadas:** Quantidade de Reparos por *Janela Logística*:
  - *Vencido - Parada Urgente* (Vermelho Escuro)
  - *Crítico - Compra Imediata ≤ 7 Dias* (Vermelho)
  - *Programar Compra ≤ 30 Dias* (Laranja)
  - *Planejamento Trimestral 31-60 Dias* (Amarelo)
  - *Rotina Preventiva > 60 Dias* (Verde)
- **Tabela de Suprimentos:**
  - Colunas: `ordem_servico`, `subestacao_instalacao`, `equipamento`, `peca_a_reparar_substituir`, `data_limite`, `dias_restantes_para_reparo`, `equipe_responsavel`.
  - Formatação condicional: fundo vermelho se `dias_restantes_para_reparo < 0`.

---

## 6. Cores e Identidade Visual (Design Tokens Pyron)

Para manter a sobriedade industrial e coerência com a interface do Pyron:

| Elemento | Código HEX | Aplicação |
| :--- | :--- | :--- |
| **Fundo de Tela** | `#F8FAFC` | Fundo suave (Ardósia claro) |
| **Fundo de Cartões/Containers** | `#FFFFFF` | Branco com borda de 1px `#E2E8F0` |
| **Primária / Ação** | `#2563EB` | Azul Cobalto |
| **Imediato / Parada Crítica** | `#DC2626` | Vermelho Carmim |
| **Urgente** | `#EA580C` | Laranja Fogo |
| **Programar** | `#D97706` | Âmbar |
| **Atenção** | `#EAB308` | Amarelo Alerta |
| **Normal** | `#16A34A` | Verde Seguro |
| **Tipografia** | Segoe UI Variable / Bahnschrift | Títulos e KPIs |
