# Diário da equipe

Recados entre o Hugo e o Gabriel (e os assistentes de cada um) sobre o que foi feito no Pyron, para ninguém
refazer o trabalho do outro. Entrada mais nova no topo. O gancho de início de sessão
(`ferramentas/novidades_equipe.py`) mostra ao Claude de cada um as entradas novas da outra pessoa.

Modelo de entrada (curta; o detalhe fica no commit):

```
## DD/MM/AAAA · Nome
- Feito: o que mudou e onde (commits).
- Para o outro: o que não precisa refazer, o que mudou de regra, cuidados.
- Pendente: o que ficou para depois ou espera decisão.
```

## 09/11/2026 · Gabriel: Painel Inicial evoluído para formato BI com Cross-Filter por Operação no Frontend

- Feito: implementação no frontend oficial (`app/interface/`) do componente interativo `Painel BI · Atenção por Operação`, baseado na modelagem do FigCraft. Retirada a seção "Importadas por último" e incluídos no `app/interface/js/telas/painel.js`: cabeçalho BI com chips de filtro rápido (Todas, Transformação, Proteção, Manobra), gráfico Donut SVG vetorial interativo com fatias reativas e centro dinâmico, cartões clicáveis da legenda de operação com contagem e percentual, e lista de ativos com traço lateral na cor da severidade, tag da operação, barra de progresso horizontal do % da MTA, temperatura em destaque (Cascadia Mono) e botão de ação direta "Inspecionar →" para a tela de Análise Termográfica (#analise). Adicionados os tokens semânticos das operações em `app/interface/tokens.css` (tema claro e escuro) e os estilos em `app/interface/telas.css` respeitando 100% o sistema de tokens.
- Para o outro: suíte estrita de design e interface `testes/test_interface_nova.py` executada com todos os 18 testes passando (sem cores literais em hex, apenas tokens de escala e durabilidade). A navegação em "Inspecionar →" já direciona para `#analise` passando o ID da inspeção do ativo.
- Pendente: nenhuma pendência.

## 09/11/2026 · Gabriel: descarte e remoção da identidade visual Obsidian Frost



- Feito: remoção de todos os arquivos e referências ao estilo Obsidian Frost no projeto. Deletados o arquivo de estilo customizado em .agents/skills/ppt-master/references/visual-styles/obsidian-frost.md, o projeto do deck e seus 12 slides DrawingML em projects/pyron_mvp_ppt169_20261107/, e os arquivos associados da apresentação em presentacao_mvp/ (pyron_mvp_obsidian_frost.pptx, isualizar_apresentacao.html, brir-apresentacao.cmd, prompt_ppt_master_pyron.md).

- Para o outro: o estilo Obsidian Frost foi integralmente descartado e não será mais utilizado na identidade visual do Pyron. A skill ppt-master permanece limpa com seus estilos padrão.

- Pendente: nenhuma pendência.



## 09/11/2026 · Gabriel: recriação da interface do Pyron e Painel BI interativo no FigCraft via MCP

- Feito: recriação completa da interface do Pyron (`app/interface/`) no FigCraft via MCP (`D:\Backup_SSD_C\pyron-interface.figcraft` e `docs/interface/pyron-interface.figcraft`), com evolução da tela `01 · Painel` para formato Business Intelligence: retirada a seção "Importadas por último" e criado o Component Set interativo `Painel BI · Atenção por Operação` com 4 variantes de cross-filter (`Operação=Todas (6)`, `Transformação (3)`, `Proteção (2)`, `Manobra (1)`), gráfico de pizza/donut por operação com fatias destacadas, barras de progresso de `% da MTA` e interações `onClick -> changeTo (smartAnimate 220ms)` nas fatias, pílulas e cartões de operação (além de clique em `Inspecionar →` navegando para `02 · Análise Termográfica`).
- Para o outro: os arquivos `D:\Backup_SSD_C\pyron-interface.figcraft` e `docs/interface/pyron-interface.figcraft` estão sincronizados e com o fluxo de protótipo `BI Cross-Filter · Atenção por Operação` pronto para testar com `Shift + Space` ou `Present` no FigCraft. Nenhum arquivo de código da aplicação foi alterado.
- Pendente: nenhuma pendência.

## 08/11/2026 · Gabriel: auditoria, correção de filtros do Dashboard Power BI e 12 recortes para apresentação

- Feito: auditoria e correção dos filtros do Dashboard Power BI em `PowerBI_Dashboard/` (PBIP), `Pyron_Dashboard.pbit` e `dashboard_pyron_bi.html`. Ativado `crossFilteringBehavior: bothDirections` nos 4 relacionamentos (`relationships.tmdl`), substituídas colunas pré-agregadas estáticas de `table_equip` por medidas DAX dinâmicas (`_Medidas`), adicionado o registro `equipamento_id = 0` faltante em `Dim_Equipamentos`, configurado `summarizeBy: none` nas colunas físicas de `Fato_*`, corrigida a DAX de `Confiança Média IA` e configurados `syncGroup` + novos Slicers nas Páginas 2, 3 e 4. Gerados 12 recortes em alta resolução (Retina 2x DPI) em `testes/relatorios_visuais/recortes_dashboard_powerbi/` prontos para anexar à apresentação.
- Para o outro: tanto o projeto PBIP (`PowerBI_Dashboard/`) quanto o template `Pyron_Dashboard.pbit` e o painel web interativo `dashboard_pyron_bi.html` estão 100% sincronizados e com os filtros funcionando em todas as 4 abas.
- Pendente: nenhuma pendência.

## 08/11/2026 · Gabriel: bateria de 25 plots e testes reais por aplicação para a apresentação MVP

- Feito: criação e execução da suíte `scripts/gerar_25_plots_mvp_pyron.py` que roda testes reais sobre os 5 pilares de aplicação do Pyron (`nucleo/flir.py`, `nucleo/paleta.py`, `nucleo/detectores/pontos_quentes.py`, `nucleo/pipeline/pyron_pipeline.py`, `nucleo/analise.py`, `app/equipamentos.py`, `nucleo/medicao/`, `app/armazenamento.py`, `app/laudo.py`) e gera 25 gráficos (5 plots para cada aplicação real) em `testes/relatorios_visuais/mvp_25_plots/` junto com as métricas extraídas em `testes/relatorios_visuais/mvp_25_plots/metricas_extraidas_reais.json`.
- Para o outro: os 25 gráficos cobrem (1) Física e Radiometria de Planck, (2) Detecção RF-DETR e Segmentação Fina SAM 2.1 / Pontos Quentes, (3) Motor Normativo NBR 15866 / IEC 60099-5 e Tendência Preditiva, (4) Metrologia Dimensional 3D e Homografia Monte Carlo, e (5) Latência Ponta a Ponta, Escalabilidade SQLite WAL, Telemetria Mobile e Emissão de Laudos PDF. Nenhum arquivo de produção foi alterado.
- Pendente: nenhuma pendência.

## 07/11/2026 · Gabriel: Geração Concluída do Deck PPTX Editável Pyron MVP (Obsidian Frost)

- Feito: compilação completa dos 12 slides DrawingML nativos e 12 notas de orador do Pyron MVP sob o Design System Obsidian Frost. Todos os 12 slides foram aprovados no gate estrito `svg_quality_checker.py` com zero erros bloqueantes (exit code 0) e validados no `project_manager.py validate`. Gerado o arquivo editável `projects/pyron_mvp_ppt169_20261107/exports/pyron_mvp_obsidian_frost.pptx` (332 KB, copiado também para `apresentacao_mvp/pyron_mvp_obsidian_frost.pptx`). Criado o visualizador web interativo em `apresentacao_mvp/visualizar_apresentacao.html` com navegação por teclado (setas, N para notas, F para tela cheia) e o atalho `apresentacao_mvp/abrir-apresentacao.cmd`.
- Para o outro: o `.pptx` gerado utiliza vetores e caixas de texto DrawingML nativas, perfeitamente editável no Microsoft PowerPoint e no Google Slides (basta fazer upload do `.pptx` para o Google Drive e abrir com Google Slides).
- Pendente: nenhuma pendência.

## 07/11/2026 · Gabriel: Design System Obsidian Frost aplicado ao PPT-Master do Pyron

- Feito: incorporação completa do design system `Obsidian Frost` (Dark Cinematic Realism + Sub-zero Glassmorphism) no framework PPT-Master. Criação do estilo customizado em `.agents/skills/ppt-master/references/visual-styles/obsidian-frost.md` (guard de integridade aprovado 100%). Atualização e validação estrita de `projects/pyron_mvp_ppt169_20261107/spec_lock.md` e `design_spec.md` (fundo obsidiana `#10141a`, títulos heroicos em EB Garamond, telemetria em Plus Jakarta Sans, acentos em gelo azul `#a2cbf1`, contornos de vidro fosco e pílulas 9999px). Master prompt atualizado em `apresentacao_mvp/prompt_ppt_master_pyron.md`.
- Para o outro: o projeto segue 100% validado no `project_manager.py validate`. Ao compilar ou gerar os slides pelo `ppt-master`, as cores e tipografia de Obsidian Frost serão usadas por padrão.
- Pendente: nenhuma pendência.

## 07/11/2026 · Gabriel: Integração da Skill ppt-master e Master Prompt do Pyron MVP

- Feito: integração da skill oficial `ppt-master` v6.8.0 (Hugo He) em `.agents/skills/ppt-master/` com integridade e licença verificadas (`attribution_guard.py` 100% aprovado). Instalação das dependências do compilador DrawingML (`python-pptx`, `pyyaml`, `xlsxwriter`, `lxml`). Criação e validação estrita do projeto em `projects/pyron_mvp_ppt169_20261107/` (`spec_lock.md` e `design_spec.md` aprovados sem erros para 12 slides). Master Prompt do Pyron MVP estruturado em `apresentacao_mvp/prompt_ppt_master_pyron.md`.
- Para o outro: para validar ou gerar slides via `ppt-master`, basta rodar `python .agents/skills/ppt-master/scripts/project_manager.py validate projects/pyron_mvp_ppt169_20261107` ou compilar os SVGs para PPTX nativo via `svg_to_pptx.py`. Todos os dados reais de bancada levantados em `curadoria.md` (Planck 1 ms, RF-DETR 71 ms, NBR 15866, IEC 60099-5 e mascote 3D PYRON-01) foram integrados ao prompt.
- Pendente: nenhuma pendência.

## 07/11/2026 · Gabriel: Apresentação Oficial do Pyron MVP no Google Slides & HyperFrames

- Feito: criação da apresentação executiva e científica oficial do Pyron MVP diretamente no Google Slides (11 slides com notas de orador completas, visual hero gerado por IA, equações termodinâmicas e duplo critério NBR 15866). ID da apresentação: `17LbvkrsqakHZqw7oCPa2u3KQsVa2QdLmISjJW9ChSsY`, disponível para edição e projeção em: https://docs.google.com/presentation/d/17LbvkrsqakHZqw7oCPa2u3KQsVa2QdLmISjJW9ChSsY/edit. Também mantido o deck offline e interativo em `apresentacao_mvp/` com HyperFrames.
- Para o outro: para editar ou projetar a apresentação, basta abrir o link do Google Slides acima (já autenticado na conta da equipe). As notas de orador em cada slide trazem o roteiro falado para a apresentação de 50 minutos.
- Pendente: nenhuma pendência.

## 07/11/2026 · Gabriel: sincronização com origin/main e metrologia no Detector-de-medidas

- Feito: fast-forward da `main` local (`36bd868..d5295e3`, +36 commits) e merge limpo na branch `v09-f5-desktop`. Comparação da metrologia do Pyron (`nucleo/medicao/`) com o projeto `Detector-de-medidas` (`measurement.py`) e integração completa de `metrology.py`, `run_metrology.py` e `test_metrology.py` (17/17 testes passando) em `types_def.py`, `measurement.py`, `visualizer.py`, `main.py`, `run_video.py` e `server_cam.py`.
- Para o outro: nenhum código do Pyron foi alterado além do merge de `origin/main`.
- Pendente (Gabriel): responder sobre os kernels Mojo em `nucleo/aceleradores/bin/` (compilar/assinar ou remover).



## 07/11/2026 · Hugo: repositório com endereço novo

- Feito: o GitHub passou a responder pelo endereço novo, https://github.com/hugovieiraz/pyron (o antigo,
  `Pyron---Embrapii`, ainda redireciona). Remoto `origin` trocado nesta máquina e o endereço atualizado em
  CLAUDE.md, site/index.html, docs/manual/gerar_manual.py e docs/08_arquitetura_banco_dados_pyron_cloud.md.
- Para o outro: rode `git remote set-url origin https://github.com/hugovieiraz/pyron.git` na sua máquina. O caminho
  local em docs/v09/medidas-f4/paridade-dml.json ficou como estava (é a pasta da sua máquina, registro de medida).
- Pendente: nada.

## 07/11/2026 · Hugo: Medição com caixa do SAM e os dois modelos

- Feito: Medição › Medir volta a ter "Caixa em volta" (modo padrão). O usuário arrasta um retângulo (ou clica dois
  cantos), o SAM 2.1 contorna o objeto por `POST /api/medicao/contorno` (rota nova, `nucleo.medicao.contornar()`,
  não mede nem guarda nada), e o usuário clica as duas pontas do que quer medir; perto do contorno a ponta encosta
  nele. A distância sai nos dois modelos de profundidade, sem e com o post-it: `/api/medicao/comparar` sem `modelo`
  e sem `registrar`, numa tabela Depth Anything 3 / MoGe-2 × sem / com referência. Em destaque fica o valor do modelo
  padrão. "Duas pontas" (sem contorno) e "Retângulo de referência" continuam.
- Para o outro: o software continua sem medir altura nem largura sozinho; quem escolhe é o usuário pelas pontas.
  Nada é guardado (só a foto na faixa, como antes). Medido em 07/11 na RTX 3050: geladeira real com post-it, topo ao
  pé, DA3 192,3 cm sem e 168,9 cm com o post-it; MoGe-2 169,4 sem e 171,4 com; contorno do SAM em 4,5 s; os dois
  modelos juntos em 30 s na primeira medida da foto. Revisão do diff pelo Codex (alethe): um defeito corrigido (clique
  preso ao trocar de modo durante o contorno).
- Pendente (Hugo): conferir o tempo dos dois modelos em sequência no uso real; se pesar, voltar a só o modelo padrão
  com a tabela a pedido.

## 07/11/2026 · Hugo: Controle Inteligente e o Pyron.exe

- Feito: pesquisa, sem mudança de código. No registro de Integridade de Código (29/09 a 07/11), o Controle
  Inteligente bloqueou o `Pyron.exe` sem assinatura 8 vezes (11/10, 26/10, 30/10 e 07/11 às 13:48). O `pythonw.exe`
  do `.venv` (assinado pela PSF) nunca foi bloqueado; pacotes do `.venv` (onnx 43 vezes, torch, ml_dtypes, vernier,
  hotcoco) só até 12/10. Atalho "Abrir Pyron" recriado na área de trabalho por `lancador/atalho.py`: abriu na 8765,
  janela do Edge, nenhum bloqueio.
- Para o outro: na máquina do Gabriel o Controle Inteligente está desligado, então lá o `.exe`, o Tauri e os kernels
  Mojo sempre abrem; a prova só vale numa máquina com ele ligado. Assinatura sem pagar: Artifact Signing (Azure) só
  aceita pessoa física dos EUA e do Canadá; SignPath Foundation é grátis só para código aberto com licença OSI (o
  repositório não tem licença); a Microsoft Store é grátis para pessoa física desde 09/2025 e assina o MSIX na
  publicação. Pago: certificado OV, cerca de US$ 150 a 300 por ano. Store fechada: "Private audience" no Partner
  Center (só quem tem o e-mail da conta Microsoft pessoal no grupo vê e instala; até 10.000 por grupo; conta de
  trabalho ou escola não serve). Publicou como público uma vez, não volta a privado: a primeira submissão já tem de
  ser privada.
- Pendente (Hugo): escolher entre MSIX pela Store, certificado OV ou continuar com o atalho; se for SignPath, ver com
  a Embrapii se o código pode ser aberto.


## 07/11/2026 · Hugo: curadoria técnica e roteiro da apresentação

- Feito: pesquisa sem mudança de código. `docs/apresentacao/curadoria.md` (bibliotecas com versão, fórmula de
  Planck, caminho estimado pela barra, FastAPI, celular, medição, modelo de para-raios, interface, o que já foi
  otimizado, o que ainda dá para otimizar e o horizonte) e `docs/apresentacao/roteiro.md` (esboço em texto de
  uma apresentação de 50 min, 33 slides, ainda em discussão com o Hugo).
- Para o outro: tempos medidos em 07/11 na RTX 3050, que podem ser reaproveitados: leitura radiométrica 9 ms;
  estimada pela barra 1,5 s (quase tudo OCR); RF-DETR 483 ms na CPU, 329 ms em INT8, 71 ms no DirectML;
  severidade 1,8 ms; `armazenamento.listar()` com 6.000 inspeções 884 ms e 12 MB, contra 58 ms lendo só as
  colunas indexadas. Suíte completa: 458 passaram, 9 pulados. Achados: duas versões do OpenCV no `.venv` do
  Hugo (5.0 e headless 4.10) e `nucleo/aceleradores/bin/` vazio (os kernels Mojo rodam sempre a reserva NumPy).
- Pendente (Hugo): aprovar o roteiro antes de montar os slides. Pendente (Gabriel): dizer se os kernels Mojo
  vão ser compilados e assinados ou se saem.

## 03/11/2026 · Hugo: ponto quente em bolinha e partes do para-raio

- Feito: pedido do Hugo. (1) No combinado para-raios + pontos quentes, ponto quente que cai dentro de uma peça sai
  (`pontos_fora_das_pecas()` em `nucleo/detectores/__init__.py`): o ponto mais quente do para-raio é o do próprio
  modelo. (2) `organizar_para_raios()`: um para-raio por grupo (repetido sai), partes cortadas na caixa dele, uma de
  cada tipo, e aletas entre o fim do terminal superior e o começo do inferior (antes as caixas se cobriam e mediam o
  mesmo pixel). As partes levam o número do para-raio ("Terminal Superior 2" é do "Para-raio 2") e o campo `pai`.
  (3) Análise e Captura › Vídeo: ponto quente é bolinha na cor da severidade no pixel mais quente, não caixa; as
  partes têm linha tracejada fina e vêm recuadas logo abaixo do para-raio na lista (`regioesOrdenadas`).
- Para o outro: `Deteccao` ganhou `grupo` (opcional) e a região ganhou `pai` (guardado nas edições). Inspeções
  antigas continuam com as caixas de antes até a detecção ser refeita. A medição com retângulo foi começada e
  desfeita a pedido do Hugo: a tela Medição continua igual ao `477394d`.
- Pendente (Hugo): refazer a detecção nas inspeções antigas ou não; dizer o que "não está carregando" (a Análise e a
  Medição abriram normais no Pyron da porta 8765 em 03/11).

## 31/10/2026 · Codex · Upload de imagem

- Feito: leitura do fluxo de imagem em `app/interface/js/medicao/medir.js` e `app/servidor.py`. Medição aceita JPEG, PNG, WebP e HEIC/HEIF pelo seletor, arrastar/soltar ou colar. A foto aparece localmente antes de ser guardada; falha no POST da galeria é capturada sem aviso, e o servidor rejeita fotos acima de 40 MB.
- Para o outro: se a foto abre no palco mas não fica na faixa, conferir `/api/medicao/fotos`; para HEIC, a prévia depende de `/api/medicao/previa` e `pillow-heif`. A janela do Pyron não estava disponível para observar a tentativa ao vivo.
- Pendente: confirmar se o upload que falha é no Pyron ou no ChatGPT e em qual etapa, para reproduzir o erro certo.

## 31/10/2026 · Codex

- Feito: análise de leitura do Pyron, sem mudanças no código. Os commits `fc28080`, `7f67f51` e `477394d` separaram Medição da Análise, simplificaram a medição para duas pontas ou retângulo de referência e fazem a tela pedir um único modelo de profundidade. A arquitetura liga `app/interface/` → FastAPI em `app/servidor.py` → regras/modelos em `nucleo/`; o servidor tem 3.433 linhas e reúne rotas de vários domínios.
- Para o outro: ao abrir Medição, `medir.js` consulta `/api/medicao/estado`; se PyTorch estiver instalado, `modelos.estado()` importa Torch e verifica CUDA. Os pesos do modelo de profundidade só carregam ao medir e ficam no medidor global em cache até o processo terminar. É um possível custo de memória após abrir Medição, não prova de CPU alta em repouso.
- Pendente: comparar uso de CPU e memória em repouso, ao abrir Medição e durante uma medição antes de decidir otimizações.

## 31/10/2026 · Hugo (3): modelos, Análise e Medição

- Feito (`fc28080`, `7f67f51`, `477394d`): pedido do Hugo para simplificar a inspeção e separar a medição da térmica.
  - Modelo térmico único: para-raios + pontos quentes. `_modelo_termico()` em `app/servidor.py` resolve o ativo
    (combinado do config, combinado do treinado do config ou o primeiro combinado normal; sem treinado, a regra).
    `/api/modelos` marca `principal` no que a tela mostra. Modelos › Em uso e Captura › Vídeo não oferecem mais troca.
  - Análise: lista de regiões voltou para a lateral (Resumo), com "anterior / 2 de 14 / próxima" no detalhe; a faixa
    horizontal saiu. "Detectar de novo" saiu; no lugar, chaves liga/desliga Para-raios, Pontos quentes e Medição
    (pontos e linhas de temperatura), componente `chaves()` em `js/componentes.js`. A seção Dimensões (SAM 2) saiu da Análise.
  - Ponto quente sem anomalia não vira caixa: sai se a severidade é normal e o ΔT do entorno fica abaixo do 1º limite
    de `similares` (5 °C na NBR). O ponto mais quente da cena vem da matriz inteira (`nucleo/analise.py`).
  - Medição virou tela do topo (Painel · Inspeções · Equipamentos · Pendências · Captura · Medição · Modelos), abas
    Medir e Modelos em `js/medicao/`. `#captura/medir` e `#modelos/medicao` redirecionam. Medir só por duas pontas que
    o usuário marca (o modelo de profundidade dá a distância entre elas) ou pelo retângulo de referência; saíram
    "Clicar no objeto", "Caixa em volta", as cotas automáticas e a biblioteca de pesos. Uma medida por vez, nada gravado.
- Para o outro: `/api/medicao/comparar` e `/api/medicao/video/comparar` só gravam no registro com `registrar=true`
  e aceitam `modelo` (`da3` ou `moge`) para rodar um só. O backend do SAM 2 + DINOv2, do auto_identificar, da
  redetecção e do registro continua; só a tela deixou de usar. Testes que esperavam o treinado sozinho como ativo
  mudaram (`test_avaliacoes.py`, `test_componentes_pontos.py`).
- Para o outro: feito com o orquestrador alethe. Claude Sonnet escreveu a tela Medição e a medida por duas pontas;
  Codex (ChatGPT) escreveu a resolução do modelo no servidor e revisou o código (achou 2 defeitos, corrigidos em
  `7f67f51`); Antigravity revisou a UX (aplicados `role="switch"` nas chaves e texto mais curto). Integração e
  testes pelo Claude Opus do Hugo: suíte completa com 455 passando, 9 pulados.
- Pendente (Hugo): testar a medida por duas pontas com fotos reais e o vídeo (as pontas dos quadros 2 a 4 vêm do
  fluxo óptico). `testes/test_video.py::test_video_de_ponta_a_ponta` falhou uma vez na suíte rápida por tempo e
  passou 3 de 3 sozinho.

## 31/10/2026 · Hugo (2)

- Feito: a regra do diário também vale no Antigravity. Bloco novo "Diário da equipe" no começo de
  `.agents/agents/orchestrator.md` (o resto do arquivo ficou igual) e regra em `.agents/rules/diario-equipe.md`.
- Para o outro: Gabriel, confira se o seu Antigravity lê `.agents/rules/`; se o caminho for outro, mova o arquivo.
  O bloco no `orchestrator.md` vale de qualquer jeito.
- Feito: gancho SessionStart em `.claude/settings.json` (criado pelo Hugo; o modo automático não deixa o assistente
  criar esse arquivo). Ao abrir o Claude Code no projeto, roda `ferramentas/novidades_equipe.py` sozinho.
- Feito: o script agora mostra do diário só o que a outra pessoa escreveu (antes mostrava também as suas entradas).
- Para o outro: Gabriel, no primeiro `git pull` o seu Claude Code pode pedir para confiar no gancho novo; é este script.

## 31/10/2026 · Hugo

- Feito: integrei a 0.9 inteira do branch `v09-f1-servidor` no `main` (merge `f566928`), sem conflito; suíte
  completa com 445 testes passando e 9 pulados (o do Typst pula aqui: o pacote `typst` não está instalado).
- Feito: trava no `config.json` (`b1155b1`, `app/servidor.py`, `_TRAVA_CONFIG`). Desde a migração dos destinatários
  para o time, a leitura do config também grava; a thread do monitor e o pedido da tela gravavam juntos e uma
  leitura no meio pegava o JSON pela metade e caía no padrão (monitor desligado). Era a falha intermitente de
  `test_pasta_vigiada_analisa_o_novo_e_alerta_uma_vez`. O `python -m app.acesso usuario` grava o config em outro
  processo e fica fora da trava (uso manual).
- Feito: tirei do `CLAUDE.md` a seção do Shlomo (`0939cd6`); a nota no topo do `CLAUDE.md` explica o motivo.
  Gabriel: a instrução de consultar o cofre pode ir no seu `~/.claude/CLAUDE.md`.
- Feito: `marca/gerar_marca.py` espera o Edge gravar a imagem (`3e14e81`). O Edge atualizado volta antes de gravar o
  PNG no modo sem janela, e a geração do ícone (e por isso o `lancador/construir.py`) falhava. Recompilei o `Pyron.exe`.
- Feito: documento técnico do Pyron para a coordenação (funcionalidades, arquitetura, números e melhorias), fora do
  repositório. Entre as melhorias: `pyproject.toml` sem FastAPI e uvicorn nas dependências, `armazenamento.listar()`
  lendo o JSON de todas as inspeções a cada pedido e `app/servidor.py` com 3.346 linhas.
- Para o outro: este diário e o gancho em `.claude/settings.json` são novos. Ao abrir uma sessão do Claude Code no
  projeto, ele busca o GitHub e mostra os seus commits e recados novos. Se usar outra ferramenta (Antigravity), leia
  este arquivo à mão ou rode `python ferramentas/novidades_equipe.py`.
- Feito: integrei os commits do Gabriel de 30/10 à noite (0.9.0 com Typst como padrão, Pyron desktop em Tauri F5 e
  licenças do Tauri); 450 testes passando, 9 pulados; a interface abre sem erro no console.
- Para o outro: regra nova no topo do `CLAUDE.md`. Antes de planejar ou mexer em qualquer coisa, consultar as novidades
  (script + este diário); ao terminar cada tarefa, registrar aqui.
- Pendente (Hugo): confirmar que o visual do laudo em Typst está aprovado. O commit `0688af3` diz "visual aprovado",
  mas o Hugo não tinha visto. Neste computador o pacote `typst` não está instalado, então o laudo continua saindo pelo
  reportlab.
- Pendente (Gabriel): dizer se o branch `v09-f1-servidor` pode ser apagado.
