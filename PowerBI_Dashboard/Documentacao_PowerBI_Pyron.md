# Guia de Implementação: Dashboard Power BI — Projeto Pyron
**Monitoramento Termográfico Preditivo e Visão Computacional em Subestações de Alta Tensão**  
*Localidade de Referência: Paraíba, Brasil (SE Patos Oeste, SE Campina Grande II, SE Santa Rita Norte)*  
*Data de Compilação: 03/11/2026*

---

## 1. Visão Geral da Solução

O **Projeto Pyron** integra sensores termográficos radiométricos (câmeras FLIR T1020, C5, E8-XT e T540) e inteligência artificial de ponta (**SAM 2** para segmentação fundacional zero-shot e **DINOv2** para extração de representações vetoriais de componentes elétricos) para monitorar subestações de alta tensão e ativos estratégicos (autotransformadores de 500 kV, transformadores de 230/69 kV, para-raios e seccionadoras).

Este documento detalha a arquitetura analítica completa para o Microsoft Power BI Desktop e Power BI Service, incluindo:
1. **Modelo Estrela (Star Schema)** com cardinalidades ótimas e integridade referencial.
2. **Scripts Power Query (M)** prontos para copiar e colar no Editor Avançado.
3. **Catálogo de Medidas DAX** organizadas em pastas temáticas com tratamento de nulos.
4. **Matriz de Layout Visual** estruturada em 4 páginas analíticas.
5. **Procedimento de Carga e Atualização Contínua**.

---

## 2. Arquitetura Dimensional (Star Schema)

A modelagem foi desenhada sob a metodologia de Ralph Kimball, separando fatos transacionais (inspeções, detecções térmicas e ordens de serviço) de dimensões de contexto (equipamentos, subestações, calendário e criticidade).

```
                      +-------------------+
                      |   d_Calendario    |
                      |-------------------|
                      | PK Data           |
                      |    Ano, Mês, Trim |
                      +---------+---------+
                                | 1
                                |
                                | *
+--------------------+ 1        |        1 +---------------------+
|   d_Subestacao     +----------+----------+    d_Equipamento    |
|--------------------|          |          |---------------------|
| PK instalacao_id   |          |          | PK equipamento_id   |
|    instalacao_chave|          |          |    chave, nome      |
|    municipio, UF   |          |          |    tensao_kv        |
+---------+----------+          |          +----------+----------+
          | 1                   |                     | 1
          |                     |                     |
          | *                   | *                   | *
+---------+---------------------+---------------------+----------+
|                          f_Inspecoes                           |
|----------------------------------------------------------------|
| PK inspecao_id                                                 |
| FK instalacao_id, FK equipamento_id, FK data_calendario        |
|    t_max_cena, t_min_cena, delta_t_ambiente_c, maior_pct_mta   |
|    ambiente_c, carga_pct, severidade, modelo, camera           |
+---------+--------------------------------------------+---------+
          | 1                                          | 1
          |                                            |
          | *                                          | *
+---------+----------------+          +----------------+---------+
|    f_Regioes_Hotspots    |          |  f_Pendencias_Logistica  |
|--------------------------|          |--------------------------|
| PK regiao_id             |          | PK ordem_servico         |
| FK inspecao_id           |          | FK inspecao_id           |
|    classe_componente     |          |    status_manutencao     |
|    confianca, t_max      |          |    dias_restantes        |
|    dt_corrigido, pct_mta |          |    equipe_responsavel    |
+--------------------------+          +--------------------------+
```

### Relacionamentos do Modelo

| Tabela Origem (1) | Tabela Destino (*) | Coluna Chave | Cardinalidade | Direção do Filtro |
| :--- | :--- | :--- | :--- | :--- |
| `d_Subestacao` | `f_Inspecoes` | `instalacao_id` | 1 : N | Única (1 → *) |
| `d_Equipamento` | `f_Inspecoes` | `equipamento_id` | 1 : N | Única (1 → *) |
| `d_Calendario` | `f_Inspecoes` | `data_calendario` | 1 : N | Única (1 → *) |
| `f_Inspecoes` | `f_Regioes_Hotspots` | `inspecao_id` | 1 : N | Única (1 → *) |
| `f_Inspecoes` | `f_Pendencias_Logistica` | `inspecao_id` | 1 : N | Única (1 → *) |

---

## 3. Scripts Power Query (M)

Para carregar os 5 arquivos CSV no Power BI Desktop com tratamento automático de separadores decimais e tipagem de dados, utilize as consultas M abaixo no **Editor Avançado**:

### 3.1. Parâmetro de Caminho Base (`CaminhoDados`)
```powerquery
let
    Caminho = "C:\Projetos\Pyron\Dados\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
in
    Caminho
```

### 3.2. Consulta: `f_Inspecoes`
```powerquery
let
    Fonte = Csv.Document(File.Contents(CaminhoDados & "vw_bi_inspecoes.csv"), [Delimiter=";", Columns=30, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {
        {"inspecao_id", type text},
        {"arquivo_original", type text},
        {"criado_em", type datetime},
        {"capturado_em", type datetime},
        {"data_calendario", type date},
        {"instalacao_id", Int64.Type},
        {"instalacao_chave", type text},
        {"instalacao", type text},
        {"equipamento_id", Int64.Type},
        {"equipamento_chave", type text},
        {"equipamento", type text},
        {"fonte", type text},
        {"radiometrica", Int64.Type},
        {"modelo", type text},
        {"severidade", type text},
        {"severidade_ordem", Int64.Type},
        {"t_max_cena", type number},
        {"t_min_cena", type number},
        {"delta_t_ambiente_c", type number},
        {"maior_pct_mta", type number},
        {"ambiente_c", type number},
        {"carga_pct", type number},
        {"camera", type text},
        {"emissividade", type number},
        {"distancia_m", type number},
        {"temp_refletida_c", type number},
        {"umidade_relativa", type number},
        {"resolucao_sensor", type text},
        {"miniatura_url", type text},
        {"termograma_url", type text}
    })
in
    Tipos
```

### 3.3. Consulta: `f_Pendencias_Logistica`
```powerquery
let
    Fonte = Csv.Document(File.Contents(CaminhoDados & "vw_bi_pendencias_logistica.csv"), [Delimiter=";", Columns=17, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {
        {"inspecao_id", type text},
        {"status_manutencao", type text},
        {"ordem_servico", type text},
        {"subestacao_instalacao", type text},
        {"equipamento", type text},
        {"equipamento_chave", type text},
        {"peca_a_reparar_substituir", type text},
        {"classe_componente", type text},
        {"severidade", type text},
        {"t_max_detectada_c", type number},
        {"pct_mta_atingido", type number},
        {"data_deteccao", type date},
        {"data_limite", type date},
        {"dias_restantes_para_reparo", Int64.Type},
        {"janela_logistica_prioridade", type text},
        {"equipe_responsavel", type text},
        {"nota_tecnica", type text}
    })
in
    Tipos
```

### 3.4. Consulta: `f_Regioes_Hotspots`
```powerquery
let
    Fonte = Csv.Document(File.Contents(CaminhoDados & "vw_bi_regioes.csv"), [Delimiter=";", Columns=19, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {
        {"inspecao_id", type text},
        {"ordem", Int64.Type},
        {"regiao_id", type text},
        {"capturado_em", type datetime},
        {"instalacao", type text},
        {"equipamento", type text},
        {"equipamento_chave", type text},
        {"regiao_nome", type text},
        {"classe_componente", type text},
        {"origem", type text},
        {"confianca", type number},
        {"t_max", type number},
        {"t_med", type number},
        {"t_min", type number},
        {"dt_corrigido", type number},
        {"pct_mta", type number},
        {"severidade", type text},
        {"x_max", type number},
        {"y_max", type number}
    })
in
    Tipos
```

### 3.5. Consulta: `d_Equipamento`
```powerquery
let
    Fonte = Csv.Document(File.Contents(CaminhoDados & "vw_equipamentos.csv"), [Delimiter=";", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {
        {"equipamento_id", Int64.Type},
        {"chave", type text},
        {"instalacao", type text},
        {"equipamento", type text},
        {"inspecoes", Int64.Type},
        {"primeira", type datetime},
        {"ultima", type datetime},
        {"maior_t_max_cena", type number},
        {"maior_pct_mta", type number}
    })
in
    Tipos
```

---

## 4. Catálogo de Medidas DAX

Crie uma tabela vazia no Power BI chamada `_Medidas` para centralizar as fórmulas calculadas organizadas por pastas de exibição.

### 4.1. Pasta: `01. KPIs Gerais`

```dax
Total Inspeções = 
COUNTROWS(f_Inspecoes)
```

```dax
Inspeções Radiométricas = 
CALCULATE(
    COUNTROWS(f_Inspecoes),
    f_Inspecoes[radiometrica] = 1
)
```

```dax
Total Subestações Ativas = 
DISTINCTCOUNT(f_Inspecoes[instalacao_id])
```

```dax
Total Ativos Monitorados = 
DISTINCTCOUNT(f_Inspecoes[equipamento_id])
```

### 4.2. Pasta: `02. Criticidade & Risco`

```dax
Inspeções Críticas = 
CALCULATE(
    COUNTROWS(f_Inspecoes),
    f_Inspecoes[severidade] IN {"imediato", "urgente"}
)
```

```dax
Inspeções Imediatas = 
CALCULATE(
    COUNTROWS(f_Inspecoes),
    f_Inspecoes[severidade] = "imediato"
)
```

```dax
Taxa de Criticidade % = 
DIVIDE([Inspeções Críticas], [Total Inspeções], 0)
```

```dax
Cor Severidade Hex = 
SWITCH(
    SELECTEDVALUE(f_Inspecoes[severidade]),
    "imediato", "#DC2626",
    "urgente", "#EA580C",
    "programar", "#D97706",
    "normal", "#16A34A",
    "sem_medida", "#64748B",
    "#94A3B8"
)
```

### 4.3. Pasta: `03. Métricas Térmicas & MTA`

```dax
Temperatura Máxima Global = 
MAX(f_Inspecoes[t_max_cena])
```

```dax
Temperatura Média Cena = 
AVERAGE(f_Inspecoes[t_max_cena])
```

```dax
Delta T Médio Corrigido = 
AVERAGEX(
    f_Regioes_Hotspots,
    f_Regioes_Hotspots[dt_corrigido]
)
```

```dax
Maior % MTA Registrado = 
MAX(f_Inspecoes[maior_pct_mta])
```

```dax
Status MTA Alerta = 
VAR vMTA = [Maior % MTA Registrado]
RETURN
    SWITCH(
        TRUE(),
        vMTA >= 200, "🚨 Emergência (> 200% MTA)",
        vMTA >= 100, "⚠️ Alarme (> 100% MTA)",
        vMTA >= 75, "⚡ Atenção (75-100% MTA)",
        "✅ Normal (< 75% MTA)"
    )
```

### 4.4. Pasta: `04. Logística de Reparos`

```dax
Total Ordens de Serviço = 
COUNTROWS(f_Pendencias_Logistica)
```

```dax
OS Abertas = 
CALCULATE(
    COUNTROWS(f_Pendencias_Logistica),
    f_Pendencias_Logistica[status_manutencao] = "aberta"
)
```

```dax
OS Programadas = 
CALCULATE(
    COUNTROWS(f_Pendencias_Logistica),
    f_Pendencias_Logistica[status_manutencao] = "programada"
)
```

```dax
OS Corrigidas = 
CALCULATE(
    COUNTROWS(f_Pendencias_Logistica),
    f_Pendencias_Logistica[status_manutencao] = "corrigida"
)
```

```dax
OS Vencidas (Parada Urgente) = 
CALCULATE(
    COUNTROWS(f_Pendencias_Logistica),
    f_Pendencias_Logistica[dias_restantes_para_reparo] < 0,
    f_Pendencias_Logistica[status_manutencao] <> "corrigida"
)
```

```dax
Taxa de Resolução OS = 
DIVIDE([OS Corrigidas], [Total Ordens de Serviço], 0)
```

### 4.5. Pasta: `05. Modelos de IA (SAM 2 & DINOv2)`

```dax
Total Regiões Detectadas = 
COUNTROWS(f_Regioes_Hotspots)
```

```dax
Confiança Média IA = 
AVERAGEX(
    FILTER(f_Regioes_Hotspots, f_Regioes_Hotspots[confianca] > 0),
    f_Regioes_Hotspots[confianca]
)
```

```dax
Volume SAM2 + DINOv2 = 
CALCULATE(
    COUNTROWS(f_Inspecoes),
    CONTAINSSTRING(f_Inspecoes[modelo], "DINOv2")
)
```

---

## 5. Estrutura Visual do Relatório (Páginas)

### Página 1: Visão Geral Executiva
- **Filtros de Topo (Slicers)**: Subestação (`d_Subestacao[instalacao]`), Equipamento (`d_Equipamento[equipamento]`), Severidade (`f_Inspecoes[severidade]`).
- **Cards de Métricas Superiores**:
  1. `[Total Inspeções]` com subtítulo `[Inspeções Radiométricas]`.
  2. `[Inspeções Críticas]` com destaque vermelho.
  3. `[OS Vencidas (Parada Urgente)]` com ícone de alerta.
  4. `[Temperatura Máxima Global]` em °C.
  5. `[Maior % MTA Registrado]` com meta de 100%.
- **Visual Esquerdo**: Gráfico de Rosca (Donut) — `f_Inspecoes[severidade]` x `[Total Inspeções]`.
- **Visual Direito**: Gráfico de Barras Empilhadas — `d_Subestacao[instalacao]` no Eixo Y, `[Total Inspeções]` no Eixo X, fatiado por `f_Inspecoes[severidade]`.
- **Visual Inferior**: Matriz de Ativos — Nome do Equipamento, Subestação, Qtd Inspeções, Maior T_Max, % MTA com barra de dados.

### Página 2: Análise Térmica & Hotspots
- **Visual Superior Esquerdo**: Gráfico de Barras Horizontais — `d_Equipamento[equipamento]` x `[Temperatura Máxima Global]`.
- **Visual Superior Direito**: Gráfico de Dispersão (Scatter Plot) — Eixo X: `f_Inspecoes[carga_pct]`, Eixo Y: `f_Inspecoes[delta_t_ambiente_c]`.
- **Visual Inferior**: Tabela Detalhada de Inspeções com URL de miniatura e termograma para navegação direta ao portal Pyron.

### Página 3: Logística & Ordens de Serviço
- **Funil de Status**: Aberta (8) → Programada (3) → Corrigida (2).
- **Gráfico de Barras por Equipe**: Eixo X: `equipe_responsavel`, Eixo Y: Qtd OS.
- **Tabela Operacional**: OS ID, Subestação, Equipamento, Peça Crítica, Dias de Atraso (com formatação condicional em vermelho se < 0), Nota Técnica.

### Página 4: Inteligência Artificial (SAM 2 & DINOv2)
- **Comparativo de Modelos**: Gráfico de Colunas comparando Inspeções por Arquitetura (`SAM 2 + DINOv2` vs `Regra Heurística` vs `SAM 2 puro`).
- **Distribuição de Classes**: Gráfico de Barras verticais com a contagem de buchas, cabos, conexões, terminais e transformadores identificados.
- **Amostra de Confiança**: Tabela de ROIs com confiança percentual e temperatura média na região.

---

## 6. Procedimento de Atualização

1. **Atualização Manual**: Substitua ou adicione novas linhas nos arquivos CSV na pasta de dados configurada e clique em **Atualizar** no menu inicial do Power BI Desktop.
2. **Atualização Automatizada via Gateway**: No Power BI Service, configure um *On-Premises Data Gateway* apontando para a pasta onde a API do Pyron despeja as views exportadas (`vw_bi_inspecoes.csv`, etc.). Programe atualizações a cada hora ou diariamente após as rondas de inspeção.
