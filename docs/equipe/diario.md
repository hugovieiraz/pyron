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
  publicação. Pago: certificado OV, cerca de US$ 150 a 300 por ano.
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
