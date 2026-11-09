# Master Prompt: Apresentação Executiva & Técnica Pyron MVP (Design System Obsidian Frost)

> **Instrução de Execução para o Agente / LLM:**
> Você é um Arquiteto de Apresentações Técnicas sênior operando sob o framework oficial **PPT-Master** (`skills/ppt-master/SKILL.md`).
> Adote integralmente o design system **Obsidian Frost**: fusão solene entre *Dark Cinematic Realism* e *Refined Sub-zero Glassmorphism*.
> Siga a disciplina de execução: **Plan-Do-Check-Act**, sem transições conversacionais vazias, sem bullet points genéricos, com tipografia monumental em **EB Garamond**, telemetria afiada em **Plus Jakarta Sans**, cartelas em obsidiana profunda (`#10141a`) com vidro fosco (`rgba(20, 24, 32, 0.65)`), detalhes em gelo azul ártico (`#a2cbf1`), toques em pílula (`rounded-full`), métricas reais de bancada do Pyron (Embrapii) e equações em LaTeX renderizado.

---

## 1. Contrato de Execução (`spec_lock.md`)

```markdown
<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: pt-BR
- audience: Engenheiros de subestações, diretores técnicos de concessionárias e banca Embrapii
- objective: Demonstrar a viabilidade metrológica, conformidade normativa e arquitetura Edge AI do Pyron MVP sob o design system Obsidian Frost
- core_message: O Pyron transforma termogramas em diagnósticos físicos em tempo real (9 ms) com conformidade NBR 15866 e IEC 60099-5 100% offline
- consumption_mode: balanced

## mode
- mode: showcase

## visual_style
- visual_style: custom
- visual_style_references: obsidian-frost
- visual_style_behavior: Deep light-absorbing obsidian foundations with sub-zero glassmorphism, cold frost blue illumination, crystalline white Garamond typography, and pill-shaped telemetry touches

## colors
- bg: #10141a
- primary: #ffffff
- accent: #a2cbf1
- text: #dfe2eb

## typography
- font_family: Plus Jakarta Sans, EB Garamond, sans-serif
- title_family: EB Garamond, Georgia, serif
- body_family: Plus Jakarta Sans, sans-serif
- body: 16
- title: 36

## icons
- library: lucide-icons
- inventory: zap, activity, thermometer, cpu, shield-alert, layers, file-text, smartphone
- stroke_width: 2

## page_rhythm
- P01: anchor
- P02: dense
- P03: dense
- P04: dense
- P05: breathing
- P06: dense
- P07: dense
- P08: breathing
- P09: dense
- P10: dense
- P11: breathing
- P12: anchor

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
- Bullet points padronizados de IA (hífen ou bolinha solta com texto vago).
- Textos genéricos desprovidos de métricas físicas, números herói ou citações normativas.
```

---

## 2. Tokens Oficiais do Sistema de Design (Obsidian Frost)

```yaml
name: Obsidian Frost
colors:
  surface: '#10141a'
  surface-dim: '#10141a'
  surface-bright: '#353940'
  surface-container-lowest: '#0a0e14'
  surface-container-low: '#181c22'
  surface-container: '#1c2026'
  surface-container-high: '#262a31'
  surface-container-highest: '#31353c'
  on-surface: '#dfe2eb'
  on-surface-variant: '#c4c7c8'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  secondary: '#a2cbf1'          # Frost Blue Principal
  on-secondary: '#003351'
  secondary-container: '#1d4a6a'
  on-secondary-container: '#90b9df'
  tertiary: '#ffffff'
  on-tertiary: '#1b3344'
  tertiary-container: '#cde5fc'
  error: '#ffb4ab'              # Alertas Térmicos e Hotspots Críticos
  on-error: '#690005'
  error-container: '#93000a'
  background: '#10141a'
  on-background: '#dfe2eb'
  border-subtle: 'rgba(255, 255, 255, 0.08)'
  border-highlight: 'rgba(139, 180, 217, 0.25)'
  frost-glass: 'rgba(20, 24, 32, 0.65)'

typography:
  display-titan:
    fontFamily: EB Garamond
    fontSize: 96px
    fontWeight: '400'
    lineHeight: 96px
    letterSpacing: 0.18em
  headline-xl:
    fontFamily: EB Garamond
    fontSize: 48px
    fontWeight: '500'
    lineHeight: 56px
    letterSpacing: 0.06em
  headline-lg:
    fontFamily: EB Garamond
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: 0.04em
  headline-md:
    fontFamily: EB Garamond
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: 0.03em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.12em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  label-caps:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.15em       # Strict uppercase tracking
  stat-value:
    fontFamily: EB Garamond
    fontSize: 36px
    fontWeight: '400'
    lineHeight: 40px

rounded:
  sm: 0.5rem                    # 8px
  DEFAULT: 1rem                 # 16px
  md: 1.5rem                    # 24px
  lg: 2rem                      # 32px
  full: 9999px                  # Pill silhouette para botões e badges
```

---

## 3. Especificação de Design Detalhada (`design_spec.md`)

```markdown
<!-- ppt-master-schema: design-spec/v1 -->
# pyron_mvp - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | pyron_mvp |
| Canvas Format | PPT 16:9 (1280×720) |
| Page Count | 12 |
| Target Audience | Engenheiros de subestações, diretores de O&M de concessionárias de energia e comitê técnico Embrapii |
| Communication Intent | Apresentar o produto Pyron MVP sob o design system Obsidian Frost, destacando a fundamentação termodinâmica, rigor metrológico e as 8 funcionalidades de IA para inspeção preditiva em alta tensão |
| Desired Audience Outcome | Homologação técnica do estágio MVP e avanço estratégico para a realização dos pilotos de campo em subestação real |
| Core Message / Ask / Action | O Pyron elimina a ilusão de baixa carga do efeito Joule, operando 100% offline em 9 ms com conformidade estrita à NBR 15866 e IEC 60099-5 |
| Delivery Context | Apresentação executiva e científica presencial em tela panorâmica 16:9 com leitura subsequente como memória de engenharia |
| Artifact Afterlife | Documento permanente de arquitetura de software, metrologia termodinâmica e memorial descritivo do produto industrial |
| Reading Mode | Balanced |
| Content Strategy | Equilíbrio solene entre gravitas mítica nórdica e precisão metrológica suíça: superfícies de obsidiana profunda, tipografia lapidar em EB Garamond, telemetria afiada em Plus Jakarta Sans e ausência de bullet points genéricos |
| Design Style | Obsidian Frost (Dark Cinematic Realism + Sub-zero Glassmorphism com superfícies de obsidiana #10141a, destaques em gelo azul #a2cbf1 e texto lapidar #ffffff) |
| AI Image Acquisition Path | Render do Mascote Sentinela 3D PYRON-01 (Mira-3D Three.js) e termogramas radiométricos reais calibrados |
| Generation Mode | Native DrawingML Shapes & SVG Compilation |
| Spec Refinement | Refined and locked |
| Speaker Notes | Enabled (roteiro técnico oral completo para cada um dos 12 slides) |
| Custom Animations | Disabled |
| Narration Audio | Disabled |
| Created Date | 2026-11-07 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280×720 |
| viewBox | `0 0 1280 720` |
| Margins | Superior 48px, Inferior 40px, Laterais 56px |
| Content Area | 1168 x 632 px |

## III. Visual Theme

### Theme Style

- **Mode**: showcase
- **Visual style**: custom (obsidian-frost)
- **Theme**: Termografia Preditiva de Alta Tensão & Metrologia de Campo
- **Tone**: Heroico, solene, rigoroso e de missão crítica industrial

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #10141a | Superfície base Obsidian Abyss |
| Primary | #ffffff | Branco Cristalino Puro para títulos EB Garamond e métricas hero |
| Accent | #a2cbf1 | Gelo Azul Nórdico (Frost Secondary) para badges, HUD e telemetria |
| Body text | #dfe2eb | Silver On-surface para parágrafos em Plus Jakarta Sans |
| Surface Low | #181c22 | Cartelas e subpainéis de contenção |
| Surface High | #262a31 | Cartelas elevadas e nós de destaque |
| Outline Subtle | #444748 | Linhas de cota e divisores gravados (0.08 alpha) |
| Warning / Error | #ffb4ab | Alertas de severidade térmica e hotspots críticos |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | EB Garamond | EB Garamond | EB Garamond | Georgia, Times New Roman, serif |
| Body | Plus Jakarta Sans | Plus Jakarta Sans | Plus Jakarta Sans | Segoe UI, Roboto, Helvetica, Arial, sans-serif |

- **Title stack**: EB Garamond, Georgia, "Times New Roman", serif
- **Body stack**: "Plus Jakarta Sans", -apple-system, "Segoe UI", Roboto, sans-serif

### Font Size Hierarchy

| Purpose | Size |
| --- | --- |
| Body | 16 |
| Page title | 36 |
| Subtitle | 20 |
| Annotation | 12 |
| Footnote | 10 |

## V. Layout Principles

### Deck-wide Direction

- **Hierarchy direction**: Cabeçalho de telemetria fixo com overline em label-caps, cartelas de vidro fosco (glassmorphism) em grid de 12 colunas e régua de ancoragem na base
- **Composition tendency**: Solenidade e contenção visual; superfícies de obsidiana escura em camadas sobre neblina ártica e contraste cristalino
- **Cross-page continuity**: Elementos de status em pílula (rounded-full 9999px), containers com raio de curvatura refinado (24px a 32px), e destaques em azul gelo #a2cbf1
- **Spacing posture**: Espaçamento estrito de 24px entre módulos com margens generosas permitindo respiração espacial cinematográfica

## VI. Icon Usage Specification

| Icon Path | Suitable Scenarios |
| --- | --- |
| icons/zap.svg | Potência de Joule I²R e alta tensão |
| icons/activity.svg | Telemetria contínua e fluxo térmico |
| icons/thermometer.svg | Conversão Planck e leitura radiométrica |
| icons/cpu.svg | Inferência Edge AI DirectML e RF-DETR |
| icons/shield-alert.svg | Limiares de severidade NBR 15866 e IEC |
| icons/layers.svg | Arquitetura de software offline e SQLite WAL |
| icons/file-text.svg | Geração de laudos periciais NR-10 em Typst |
| icons/smartphone.svg | Conexão de campo mobile via WebSocket |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| images/pyron_mira3d_hero.png | 1280x720 | 16:9 | Sentinela 3D PYRON-01 sob ambientação Obsidian Frost | photo | hero-card | contain | local | ready | mira-3d | omit | hero |
| images/swiss_board_joule.png | 1280x720 | 16:9 | Curva Falsa vs Real de Aquecimento Joule | technical | split-card | contain | local | ready | board-2 | omit | supporting |
| images/swiss_board_planck.png | 1280x720 | 16:9 | Diagrama do Desenrolamento Radiométrico | technical | flow-card | contain | local | ready | board-3 | omit | supporting |

## IX. Content Outline

### Part 1: Visão Geral e Fundamentação Científica

#### Slide 01 - Abertura Hero e Abstract Executivo do Pyron MVP
- **Audience move**: Sentir o peso solene da missão do Pyron e reconhecer o sentinela 3D PYRON-01 como avatar de metrologia termodinâmica autônoma.
- **Relationships**: Link e Identidade visual unindo o sentinela 3D ao painel de telemetria Obsidian Frost.
- **Composition**: Split assimétrico: lado esquerdo com card em vidro fosco (glassmorphism 24px radius) exibindo PYRON-01 em perspectiva heroica; lado direito com cartelas em obsidiana destacando os 3 pilares de engenharia.
- **Title**: PYRON MVP: TERMOGRAFIA DIGITAL E INTELIGÊNCIA PREDITIVA EM ALTA TENSÃO
- **Core message**: O Pyron é o primeiro sistema de visão computacional com metrologia radiométrica rigorosa para subestações, operando 100% offline em 9 milissegundos.
- **Content**: Plataforma autônoma que une física de plasma, conversão analítica de Planck e redes neurais neurais Edge AI sob a disciplina severa da ABNT NBR 15866 e IEC 60099-5.
- **Mathematical content**: \Delta T_{\text{medido}} \to \Delta T_{\text{corrigido}} \quad (9\text{ ms})

#### Slide 02 - O Paradoxo da Baixa Carga e a Física do Efeito Joule
- **Audience move**: Perceber a vulnerabilidade dos métodos convencionais de inspeção termográfica que ignoram a corrente de carga e aceitar a formulação quadrática corretiva.
- **Relationships**: Contraste severo entre a aparente normalidade a 30% de carga e a catástrofe iminente calculada a 100% de carga.
- **Composition**: Dois blocos maciços de obsidiana lado a lado: card esquerdo com contorno sutil exibindo ΔT de 5,4 °C (Normal); card direito com contorno de alerta em #ffb4ab revelando colapso térmico de 60,0 °C (Imediato).
- **Title**: O PARADOXO DA BAIXA CARGA: POR QUE A TERMOGRAFIA TRADICIONAL FALHA
- **Core message**: O aquecimento por resistência de contato varia com o quadrado da corrente: inspeções sob baixa carga mascaram falhas letais para a subestação.
- **Content**: Conector operando a 30% de carga atinge 35,4 °C (ambiente 30 °C). O delta de 5,4 °C é considerado normal por termografistas desavisados. Corrigido para carga nominal (100%), o delta atinge 60,0 °C, exigindo intervenção imediata. Pela regra de Arrhenius/Montsinger, cada 8 °C acima da MTA corta a vida residual do isolamento pela metade.
- **Mathematical content**: P = R \cdot I^2 \implies \Delta T_{100\%} = \Delta T_{\text{medido}} \cdot \left(\frac{100}{\text{Carga \%}}\right)^2

#### Slide 03 - Feature 1: Desenrolamento Radiométrico Universal e Inversão de Planck
- **Audience move**: Compreender como o Pyron acessa a temperatura radiométrica pura do sensor FLIR em 1 ms e reconstitui a escala física em fotos comuns via programação dinâmica.
- **Relationships**: Ordem sequencial do pipeline de inversão física (Descompressão FFF -> Inversão de Planck -> Calibração de Barra por KD-Tree).
- **Composition**: Sequência horizontal de 3 cartelas de vidro fosco com badges numeradas em gelo azul #a2cbf1 e linhas de fluxo de dados gravadas.
- **Title**: DESENROLAMENTO RADIOMÉTRICO UNIVERSAL: DO PIXEL À MATRIZ TÉRMICA
- **Core message**: Conversão analítica exata da curva de Planck em 1 ms e reconstrução de escala térmica por programação dinâmica em 298 de 299 casos.
- **Content**: Leitura radiométrica direta em 9 ms (descontando transmissividade atmosférica τ e radiação refletida). Para imagens sem radiometria, algoritmo de programação dinâmica rastreia a barra de escala e converte cores em radiância via árvore KD com erro mediano de apenas 0,53 °C.
- **Mathematical content**: T_{\text{obj}} = \frac{B}{\ln\left(\frac{R_1}{R_2 \cdot (S_{\text{obj}} + O)} + F\right)} - 273{,}15

#### Slide 04 - Feature 2: Detecção de Ativos com Transformers (RF-DETR + DINOv2)
- **Audience move**: Admirar a precisão cirúrgica da rede neural RF-DETR que segmenta partes vitais de para-raios e isoladores sob sol escaldante e reflexos metálicos.
- **Relationships**: Pertinência hierárquica entre o equipamento completo e suas subpeças críticas (aletas isoladoras, terminal superior e terminal inferior).
- **Composition**: Grade técnica de telemetria com números monumentais em EB Garamond à esquerda e matriz de caixas delimitadoras com notas de precisão à direita.
- **Title**: DETECÇÃO ROBUSTA DE COMPONENTES: RF-DETR COM BACKBONE DINOv2
- **Core message**: Rede neural treinada em subestações de alta tensão atinge mAP50 de 0,891 e executa em 71 ms na GPU via DirectML.
- **Content**: RF-DETR Medium com base DINOv2 processando em 640x640 normalizado. Atinge AP50 de 0,99 no corpo do para-raios, 1,00 nas aletas isoladoras, 0,84 no terminal superior e 0,73 no terminal inferior, eliminando caixas sobrepostas.
- **Mathematical content**: \text{mAP}_{50} = 0{,}891 \quad \text{Inferência GPU} = 71\text{ ms}

#### Slide 05 - Feature 3: Segmentação Fina SAM 2.1 e Profundidade 3D (DA3 / MoGe-2)
- **Audience move**: Visualizar o isolamento geométrico que expurga o céu gélido e garante medições milimétricas de distância de segurança entre fases.
- **Relationships**: Contraste entre o erro induzido pelo fundo celeste em caixas convencionais e o isolamento puro da cerâmica via polígonos finos.
- **Composition**: Painel duplo: à esquerda, nuvem de pontos 3D emergindo da escuridão de obsidiana; à direita, máscara vetorial SAM 2.1 sobre o contorno do ativo.
- **Title**: SEGMENTAÇÃO FINA E PROFUNDIDADE 3D: ELIMINANDO O EFEITO CÉU
- **Core message**: O contorno poligonal fino elimina a contaminação do céu frio e a estimativa métrica 3D calcula distâncias com erro de apenas 5,1%.
- **Content**: O céu de fundo (-20 °C a 5 °C) falseia as temperaturas médias capturadas por caixas retangulares clássicas. O SAM 2.1 com convolução normalizada isola o contorno real do ativo. O Depth Anything 3 projeta coordenadas 3D para cálculo de distâncias físicas entre condutores.
- **Mathematical content**: \text{Erro Mediano 3D} = 5{,}1\% \quad \vec{P} = (X, Y, Z)_{\text{câmera}}

#### Slide 06 - Feature 4: Diagnóstico Especializado de Para-raios ZnO (IEC 60099-5)
- **Audience move**: Dominar a distinção essencial de que para-raios de óxido de zinco não sofrem efeito Joule de carga e devem ser diagnosticados por corrente de fuga resistiva.
- **Relationships**: Contraste de engenharia entre ativos condutores em série e varistores de derivação à terra regulados pela IEC 60099-5.
- **Composition**: Árvore normativa tripartite em pilares de obsidiana com faixas cromáticas de severidade crescente (Normal, Atenção, Intervenção Imediata).
- **Title**: DIAGNÓSTICO DE PARA-RAIOS ZnO: CORRENTE DE FUGA E A IEC 60099-5
- **Core message**: Para-raios não utilizam correção de carga: operam sob tensão permanente e delta térmico de 2 °C já indica anomalia interna.
- **Content**: A degradação dos blocos de varistor de óxido de zinco e a penetração de umidade causam aquecimento por corrente resistiva Irx. Limiares estritos da norma internacional: ΔT <= 2 °C normal; 2 a 5 °C atenção; 5 a 10 °C programar substituição; > 10 °C intervenção imediata contra explosão.
- **Mathematical content**: \Delta T_{\text{ZnO}} \le 2^\circ\text{C} \text{ (Normal)} \quad \Delta T_{\text{ZnO}} > 10^\circ\text{C} \text{ (Risco de Explosão)}

#### Slide 07 - Feature 5: Motor de Decisão Normativa Dupla (ABNT NBR 15866)
- **Audience move**: Conhecer a velocidade e consistência da matriz automatizada que resolve simultaneamente delta térmico comparativo e temperatura absoluta.
- **Relationships**: Sobreposição matricial bidimensional cruzando o aquecimento relativo trifásico com o percentual da MTA do material condutor.
- **Composition**: Matriz 4x4 em vidro fosco com badges de status padronizadas da NBR e contadores de tempo de reinspeção.
- **Title**: MOTOR DE DECISÃO NORMATIVA: CONFORMIDADE COM A ABNT NBR 15866
- **Core message**: Classificação instantânea de 9 regiões em 1,8 ms integrando delta relativo trifásico e porcentagem da MTA.
- **Content**: Níveis formais da norma brasileira: Normal (365 dias), Atenção (90 dias), Programar (30 dias), Urgente (7 dias) e Imediato (24 horas). O motor projeta a máxima corrente admissível antes do colapso térmico do conector.
- **Mathematical content**: I_{\text{máx}} = I_{\text{atual}} \cdot \sqrt{\frac{\text{MTA} - T_{\text{amb}}}{T_{\text{op}} - T_{\text{amb}}}}

#### Slide 08 - Feature 6: Telemetria Mobile Edge e Rastreamento em Tempo Real
- **Audience move**: Visualizar o inspetor em campo utilizando um smartphone comum que acompanha os ativos termográficos sem oscilação ou latência perceptível.
- **Relationships**: Sincronização em tempo real entre o sensor óptico do celular, o WebSocket binário local e o motor de rastreamento.
- **Composition**: Renderização minimalista de smartphone sobre tela de telemetria em obsidiana escura, demonstrando o fluxo adaptativo de 15 fps.
- **Title**: TELEMETRIA MOBILE EDGE: TRANSMISSÃO E FLUXO ÓPTICO ESTABILIZADO
- **Core message**: Conexão WebSocket local a 15 fps com compensação de tremor da mão do inspetor em erro inferior a 0,3 pixel.
- **Content**: Servidor Uvicorn secundário na porta 8791 operando em rede local air-gapped, pareado por QR Code e token criptográfico. O celular processa miniaturas de 72 px em escala de cinza e mantém as caixas térmicas alinhadas durante o movimento.
- **Mathematical content**: \text{Taxa} = 5\text{ a }15\text{ fps} \quad \text{Deslocamento Óptico} < 0{,}3\text{ px}

#### Slide 09 - Feature 7: Arquitetura 100% Offline Edge e Cibersegurança
- **Audience move**: Ter certeza inabalável de que o software cumpre os requisitos de blindagem cibernética de subestações de energia sem depender de conectividade externa.
- **Relationships**: Estrutura em camadas ortogonais isoladas do backend FastAPI assíncrono até o armazenamento local transacional SQLite WAL.
- **Composition**: Diagrama arquitetural em camadas de obsidiana empilhadas com bordas iluminadas em gelo azul e vetores de comunicação interna.
- **Title**: ARQUITETURA 100% OFFLINE EDGE: AIR-GAPPED E CIBERSEGURANÇA
- **Core message**: Sistema opera completamente sem internet, com 128 rotas FastAPI, DirectML homologado e banco SQLite WAL com resposta em 58 ms.
- **Content**: Controle de acesso por perfis RBAC em todas as rotas. Executáveis assinados compatíveis com o Smart App Control do Windows 11. Suporte nativo a mais de 6.000 inspeções sem degradação de memória e exportador para PostgreSQL/Grafana.
- **Mathematical content**: 128\text{ Rotas API} \quad \text{Consulta 6.000 Registros} = 58\text{ ms}

#### Slide 10 - Feature 8: Geração Instantânea de Laudos Regulatórios (Typst)
- **Audience move**: Constatar o salto de produtividade pericial com relatórios técnicos prontos para auditoria judicial compilados em frações de segundo.
- **Relationships**: Contraste de produtividade entre o desgaste de confeccionar relatórios em Word e a emissão automática pericial via Typst.
- **Composition**: Comparação lado a lado com painel de entrada de dados JSON à esquerda e o documento pericial vetorial com selo de ART à direita.
- **Title**: LAUDOS REGULATÓRIOS AUTOMATIZADOS: COMPILAÇÃO TYPST EM 32 MS
- **Core message**: Motor Typst emite laudos periciais auditáveis para prontuário de instalações elétricas (NR-10 / PIE) em 32 ms por inspeção.
- **Content**: Substituição de bibliotecas legadas pelo compilador Typst de alta performance. Os dados do operador entram via JSON tipado sem risco de injeção de código, gerando relatórios completos com gráficos, imagens térmicas e ART técnica.
- **Mathematical content**: \text{Compilação Typst} = 32\text{ ms (1 inspeção)} \quad 1.024\text{ ms (50 inspeções)}

#### Slide 11 - Valor do Produto: Retorno sobre Investimento (ROI) e Prevenção de Falhas
- **Audience move**: Justificar os números do caso de negócio demonstrando a preservação direta de milhões de reais em ativos de potência e multas regulatórias evitadas.
- **Relationships**: Causa e efeito entre o investimento preventivo no software e a eliminação de penalidades astronômicas da agência reguladora.
- **Composition**: Três cartelas verticais monumentais de impacto financeiro com números herói em EB Garamond destacados em branco puro e gelo azul.
- **Title**: VALOR DO PRODUTO: ROI INDUSTRIAL E PREVENÇÃO DE DESLIGAMENTOS
- **Core message**: Evitar uma única interrupção não programada em alta tensão economiza até R$ 450.000 por hora em multas da ANEEL.
- **Content**: Prevenção de multas de Parcela Variável (PV) e indicadores DIC/FIC da agência reguladora. Proteção contra perda acelerada de isolamento em transformadores de força (economia de até R$ 3,5 milhões). Ganho de 6,8x na produtividade dos técnicos de campo.
- **Mathematical content**: \text{ROI} > 12\times \quad \text{Multas Evitadas} \ge \text{R\$ } 450.000/\text{h}

#### Slide 12 - Roadmap de Homologação, Piloto de Campo e Encerramento
- **Audience move**: Celebrar os resultados alcançados pelo MVP e se engajar ativamente na fase de pilotos de campo em subestação real.
- **Relationships**: Ordem cronológica da timeline evolutiva desde a bancada laboratorial até a operação comercial em escala de rede.
- **Composition**: Timeline horizontal progressiva com nós numerados em gelo azul #a2cbf1, finalizando no crachá do sentinela 3D PYRON-01 com QR Code de acesso à demonstração.
- **Title**: CRONOGRAMA DE HOMOLOGAÇÃO: RUMO AO PILOTO DE CAMPO
- **Core message**: MVP validado com 458 testes unitários passando: prontos para o piloto assistido em concessionárias parceiras.
- **Content**: Etapa 1 (Concluída): MVP 0.9 com inferência DirectML a 71 ms e 458 testes aprovados. Etapa 2 (Q1/2027): Piloto assistido com 1.000 termogramas sob condições climáticas reais. Etapa 3 (Q2/2027): Empacotador desktop assinado Tauri e integração nativa com SAP PM.
- **Mathematical content**: 458\text{ Testes Automatizados} \quad 100\%\text{ Sucesso}

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under notes/
- **Content**: Roteiro falado completo para cada um dos 12 slides com justificativas normativas, físicas e instruções para a equipe de apresentação.
```

---

## 4. Instruções de Execução Automatizada no Repositório

```powershell
# 1. Validar a conformidade estrita do projeto sob o tema Obsidian Frost:
python .agents/skills/ppt-master/scripts/project_manager.py validate projects/pyron_mvp_ppt169_20261107

# 2. Inspecionar o contexto determinístico de cada slide (ex: P01 Hero):
python .agents/skills/ppt-master/scripts/project_manager.py page-context projects/pyron_mvp_ppt169_20261107 P01 --record-usage

# 3. Compilar os layouts vetoriais para PowerPoint nativo (.pptx):
python .agents/skills/ppt-master/scripts/svg_to_pptx.py --input-dir projects/pyron_mvp_ppt169_20261107/svg_output --output projects/pyron_mvp_ppt169_20261107/exports/pyron_mvp_obsidian_frost.pptx
```
