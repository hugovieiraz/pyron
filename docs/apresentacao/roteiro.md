# Roteiro da apresentação: Pyron por dentro (50 minutos)

Proposta para aprovação, 07/11/2026. Nada foi montado ainda. Tempo: 45 min de fala + 5 min de perguntas,
33 slides (cerca de 1 min 20 s cada). Os slides marcados com (opcional) saem se o tempo apertar.

Os números vêm do código e dos relatórios do repositório, ou foram medidos hoje neste notebook
(RTX 3050 Laptop, Windows 11); a fonte de cada um está no fim do arquivo.

## Direção visual (para aprovar junto)

- Fundo dos slides de conteúdo claro e frio (`#F7F8FA`), texto ardósia (`#161B22`); capa, aberturas de
  bloco e o slide de encerramento no palco grafite do Pyron (`#121418`).
- Um acento só: a chama da marca (`#EF5F0C`), nos números principais. Cobalto (`#1F5BC4`) só para
  marcar "onde estamos" nos diagramas. A paleta ferro e as cores de severidade aparecem só como dado
  (termograma, tabela de severidade), como no aplicativo.
- Tipos: Barlow Semi Condensed nos títulos e diagramas (o papel da Bahnschrift no Pyron, que não existe
  no Google Fonts) e Source Sans 3 no texto; caminhos de arquivo e fórmulas em mono.
- O elemento marcante: nas aberturas de bloco, a barra de cores ferro funciona como a linha do tempo
  da palestra (o bloco atual é a posição na escala). Fora disso, slides sóbrios, um assunto por slide.
- Imagens: capturas reais das telas do Pyron (`docs/interface/capturas`) e a logo vetorial (`marca/vetor`).

## Blocos

| Bloco | Minutos | Slides | Ideia central |
|---|---|---|---|
| 0. Abertura | 3 | 1-2 | O que é o Pyron e o que ele resolve |
| 1. O que ele faz | 5 | 3-5 | O caminho de uma inspeção, do arquivo ao laudo |
| 2. Arquitetura e código | 7 | 6-10 | Camadas, linguagens, bibliotecas, FastAPI |
| 3. Do pixel à temperatura | 7 | 11-14 | Planck no radiométrico e a inversão pela barra de cores |
| 4. Peças e severidade | 8 | 15-19 | Pontos quentes, modelo de para-raios, NBR 15866 |
| 5. Celular e medição | 6 | 20-23 | Conexão do celular e medida por profundidade |
| 6. Já otimizado | 4 | 24-26 | O que foi acelerado, com antes e depois |
| 7. Ainda dá para otimizar | 5 | 27-29 | Gargalos medidos hoje e dívidas do código |
| 8. Horizonte | 5 | 30-33 | Instalador, Docker, API e o que falta para virar plataforma |
| Perguntas | 5 | | |

## Slide a slide

### Bloco 0. Abertura (3 min)

1. **Capa.** Pyron: manutenção preditiva por termografia. Versão 0.9, projeto Embrapii.
2. **O problema em uma frase e quatro números.** Hoje: câmera, análise a olho, planilha e laudo à mão.
   No Pyron: a imagem entra e sai com as peças achadas, a temperatura de cada uma, a severidade pela
   NBR 15866, a pendência e o laudo. Números: 0,891 de mAP50 no detector; 9 ms para ler um termograma
   radiométrico; 71 ms de detecção na placa de vídeo; 458 testes automáticos passando.

### Bloco 1. O que ele faz (5 min)

3. **O caminho de uma inspeção.** Capturar (FLIR, pasta monitorada, celular, vídeo) → Analisar →
   Acompanhar (equipamento no tempo, tendência, próxima inspeção) → Agir (pendência) → Comunicar (laudo,
   alerta WhatsApp). Ao lado: Medição, Modelos, Configurações.
4. **A tela de Análise** (captura real). Para-raios com as partes numeradas ("Terminal Superior 2" é do
   "Para-raio 2"), ponto quente em bolinha na cor da severidade, salvamento automático, Desfazer.
   Alternativa: demonstração ao vivo de 3 minutos no `pyron-demo` (decidir).
5. **Três jeitos de rodar.** Local no Windows (Pyron.exe, sem internet, sem login); modo servidor com
   login e perfis (técnico, engenheiro, quem assina, administrador) e tablet como aplicativo (PWA);
   versão enxuta para apresentações e o site com teste no navegador.

### Bloco 2. Arquitetura e código (7 min)

6. **Quatro camadas.** Interface (`app/interface`, JavaScript puro) → servidor FastAPI (`app/`) → núcleo
   de cálculo (`nucleo/`) → dados (SQLite em WAL + imagens e matrizes em pasta ou S3). O treino (`ml/`)
   fica fora do dia a dia e entrega um modelo ONNX com um `cartao.json`.
7. **Do que o código é feito.** 62 mil linhas versionadas. Por tamanho: Python 53 %, JavaScript 30 %,
   CSS 10 %, HTML 3 %, C# 1,3 % (Pyron.exe), Rust 0,7 % (desktop Tauri), resto 1,6 % (Typst do laudo,
   Mojo, SQL do BI, notebook). Python: núcleo 10,9 mil linhas, servidor 9,4 mil, testes 9,4 mil, treino
   3,1 mil. 149 commits entre 28/09 e 03/11/2026 (Hugo 93, Gabriel 34, assistente 22).
8. **Bibliotecas por papel** (tabela). Web: FastAPI, Starlette, Uvicorn. Imagem e conta: NumPy, SciPy,
   Pillow, OpenCV. IA no uso: ONNX Runtime (DirectML; TensorRT e CUDA no servidor), RapidOCR. Treino:
   PyTorch + RF-DETR. Medição: Depth Anything 3, MoGe-2, SAM 2.1 (transformers). Laudo: Typst e reportlab.
   Dados: sqlite3, boto3 (S3), psycopg (PostgreSQL). Segurança: só a biblioteca padrão (scrypt, hmac,
   secrets). Regra de licença: só MIT, Apache, BSD e OFL.
9. **O FastAPI por dentro.** 128 rotas no `servidor.py` + 9 no servidor do celular; as maiores famílias:
   medição 27, análises 23, cadastro 11. Uma dependência global confere sessão e perfil em toda rota
   (no modo local não faz nada; rota nova sem grupo derruba um teste). Análise pesada roda fora do laço
   (`run_in_threadpool`); ao subir, retoma o monitor e pré-aquece o modelo na placa; a interface é
   servida como arquivos estáticos; a documentação OpenAPI sai sozinha.
10. **(opcional) O que moldou a arquitetura.** O Controle Inteligente de Aplicativos do Windows barra
    DLL sem assinatura: por isso a placa de vídeo entra pelo DirectML (assinado pela Microsoft) e não
    pelo PyTorch com CUDA, e o Pyron.exe fica em ~100 KB (uma versão de 390 KB foi barrada).

### Bloco 3. Do pixel à temperatura (7 min)

11. **Três caminhos, nesta ordem.** (1) JPEG radiométrico da FLIR: temperatura medida. (2) Imagem comum
    da FLIR C5: barra na posição conhecida. (3) Barra de cores em qualquer lugar, inclusive foto da tela.
    Sem nenhum: a imagem entra só com as peças e a severidade vira "Sem medida".
12. **Radiométrico: a física da câmera.** O JPEG traz, em segmentos APP1, um bloco FFF com o valor bruto
    do sensor (16 bits, 160 × 120 na C5) e as constantes da câmera. Para cada pixel:
    T = B / ln(R1 / (R2 · (S + O)) + F) − 273,15, com S já descontado da reflexão ((1 − ε)/ε · R(T refl)),
    da atmosfera (transmissão em dois termos com a umidade) e da janela. Mesma formulação do exiftool.
    Emissividade, distância e temperatura refletida podem ser trocadas depois. Medido: 1 ms a conversão,
    9 ms a leitura completa.
13. **Estimado pela cor.** Acha a barra (moldura, ou programação dinâmica para barra inclinada), lê
    máximo e mínimo com OCR (três preparações votam), leva cada cor ao CIELAB, acha a cor mais próxima da
    barra (árvore KD, com projeção no segmento) e converte posição em temperatura pela radiância, não de
    forma linear. Medido hoje: 1,5 s por imagem, quase tudo OCR. Erro por peça documentado: 0,5 °C na
    mediana.
14. **O limite que precisa ser dito.** Acima do topo da escala a temperatura não volta: no teste de hoje,
    um seccionador a 239 °C numa escala que ia até 64 °C. Por isso o arquivo original da câmera é sempre
    o caminho recomendado; o estimado sai com aviso.

### Bloco 4. Peças e severidade (8 min)

15. **Pontos quentes por regra.** Otsu separa equipamento e céu, média local do equipamento, marca o que
    passa 4 °C da vizinhança e junta em regiões. Não precisa de modelo; 1,9 ms por imagem.
16. **O modelo de para-raios.** RF-DETR Medium (detector DETR com base DINOv2), entrada 640 × 640 na imagem
    colorida, 4 classes: para-raio, aletas, terminal superior, terminal inferior. Rotulado no CVAT, treinado
    neste notebook em 18 min (100 épocas; 111 fotos de treino, 25 de validação, 27 de teste), exportado
    para ONNX com um `cartao.json` que diz como preparar a entrada, ler a saída e qual o limiar.
17. **Como ele se saiu no teste.** mAP50 0,891; mAP50-95 0,556; precisão 0,888; revocação 0,898; 159 de 177
    peças. Por parte: para-raio 0,99, aletas 1,0, terminal superior 0,84, terminal inferior 0,73. Erro da
    temperatura máxima por peça: 0,0 °C na mediana e até 0,94 °C em 90 % dos casos.
18. **Peças + calor.** Para-raio repetido sai; cada parte fica cortada dentro do seu para-raio e as aletas
    ficam entre os terminais (antes as caixas se cobriam e mediam o mesmo pixel); ponto quente dentro de uma
    peça sai, porque a peça já mede o seu ponto mais quente; o ponto mais quente da cena vem da matriz inteira.
19. **Severidade pela NBR 15866.** Relativa (ΔT contra a mesma peça das outras fases, corrigido pela carga
    (100/carga)²; para-raio e isolador com faixa própria de 2, 5 e 10 °C), absoluta (% da MTA projetada
    para plena carga, cortes em 60, 70, 80 e 100 %) e ambiente (NETA, opcional). Vale a pior. Reinspeção
    em 365, 90, 30, 7 e 1 dia. Avisos: sem ambiente, acima de 150 °C (sol ou reflexo), ponto fora das
    peças. Tudo isso em 1,8 ms.

### Bloco 5. Celular e medição (6 min)

20. **Como o celular conecta.** O Pyron sobe um segundo servidor na rede local só com as rotas do celular
    (ninguém na rede chega às inspeções), em HTTPS com certificado gerado na hora (o navegador só libera a
    câmera em conexão segura) e com um código novo no link a cada vez, mostrado num QR. O celular manda
    JPEG por WebSocket, de 5 a 15 quadros por segundo conforme o computador dá conta; o servidor analisa
    sempre o mais novo e descarta os atrasados. Entre uma resposta e outra, o próprio celular segue o
    movimento da câmera e leva as caixas junto. Rede que bloqueia WebSocket: cai para HTTP.
21. **Medir um objeto numa foto comum.** O usuário marca as duas pontas; o modelo de profundidade dá um
    ponto 3D por pixel; a medida é a distância 3D entre as pontas (mediana de 5 × 5 pixels em cada uma).
    Um post-it rosa de 8 cm, achado sozinho pela cor, corrige a escala. Sem modelo instalado: retângulo de
    tamanho conhecido (A4, cartão) e homografia, com a margem calculada por Monte Carlo.
22. **Depth Anything 3 Metric.** Da ByteDance, Apache 2.0. Entra só a rede (a API do pacote puxa
    código GPL). Ele dá profundidade relativa à focal: metros = saída × focal / 300, com a focal tirada do
    EXIF do celular. MoGe-2 (Microsoft, MIT) fica de reserva.
23. **Quanto erra.** 31 fotos e 55 medidas num Galaxy S23, erro mediano: sem referência 19,8 % (DA3) e
    29,6 % (MoGe-2); com post-it 5,1 % e 8,1 %; 2 s e 20 s por foto na CPU. Limite: validado em poucas
    fotos de um celular, e não dá para pôr post-it em equipamento energizado.

### Bloco 6. Já otimizado (4 min)

24. **Na leitura da imagem** (antes → depois). OCR com detecção até 320 px e cache de recortes:
    1,4 s → 0,9 s. Cor da paleta projetada uma vez por cor distinta: 350 ms → 40 ms. Mediana no OpenCV em
    vez do SciPy: cerca de 8 vezes mais rápida. No vídeo, tabela de cor de 64³ e OCR só quando o rótulo muda.
25. **Na detecção** (medido hoje). Modelo na CPU 483 ms → INT8 329 ms (arquivo de 122,8 para 43,5 MB, mesmo
    mAP50 medido do mesmo jeito: 0,859 e 0,859) → placa pelo DirectML 71 ms (6,8 vezes). Na GTX 1650 do
    Gabriel, TensorRT em 27 ms (36 imagens por segundo). Sessão guardada em memória, pré-aquecimento ao
    subir, placa carregando em outro fio e o motor do TensorRT montado em outro processo.
26. **No resto.** Laudo em Typst: 111 → 32 ms por inspeção. Profundidade: MoGe-2 20 s → DA3 2 s, errando
    menos. Celular sem fila de quadros. Banco em WAL com índices.

### Bloco 7. Ainda dá para otimizar (5 min)

27. **O gargalo medido hoje: a lista de inspeções.** Ela abre o JSON completo de todas as inspeções a cada
    pedido. Numa cópia do banco: 60 inspeções 6 ms; 600, 74 ms; 6.000, 884 ms e 12 MB de resposta. Lendo só
    as colunas que o banco já tem: 58 ms para as 6.000 (15 vezes menos), e com paginação a resposta fica pequena.
28. **No código.** Uma trava global faz uma análise por vez (no modo servidor, uma fila para a equipe);
    `servidor.py` com 3.449 linhas e 128 rotas num arquivo (dividir por assunto); a interface antiga
    (10 mil linhas) ainda é servida; a matriz de temperatura vai em base64 dentro do JSON (100 KB por
    160 × 120; em binário seriam 75 KB); duas versões do OpenCV instaladas disputam o mesmo módulo; os
    kernels Mojo não têm binário compilado e roda o caminho NumPy; o `pyproject.toml` só declara 3
    dependências; não há integração contínua rodando os testes a cada envio.
29. **O que pesa mais que velocidade: validação.** Teste com 27 fotos de uma subestação e uma câmera;
    terminais, onde costuma estar o defeito, são a parte mais fraca; não há medida registrada da
    concordância com um especialista nem do erro frente ao software da FLIR.

### Bloco 8. Horizonte: de software a plataforma (5 min)

30. **Instalar sem ajuda.** Instalador assinado (o desktop em Tauri já gera MSI/NSIS); a assinatura de
    código é pré-requisito por causa do Controle Inteligente; Python embutido; dependências declaradas;
    atualização automática.
31. **Servidor em contêiner.** Imagem Docker do modo servidor (FastAPI + ONNX com TensorRT) e um compose
    com PostgreSQL, Grafana e proxy HTTPS próprio, no lugar do Tailscale gratuito (não comercial); backup
    em S3; logs, métricas e alerta de erro.
32. **API para outros sistemas.** API versionada com chave: enviar inspeção, consultar severidade, gerar o
    laudo em PDF por chamada, avisar por webhook; integração com sistemas de manutenção (SAP PM, Maximo);
    alerta automático pela API oficial do WhatsApp Business.
33. **Produto e IA, e o fechamento.** Mais classes (bucha, conexão, seccionadora); as correções que o
    usuário faz na Análise viram rótulos para o próximo treino; câmera fixa (RTSP/ONVIF); várias empresas
    no mesmo servidor; GPS tirado das fotos (LGPD). Fecho: três prioridades de curto, médio e longo prazo.

## Pontos para decidir

1. Público: técnico (engenharia, banca) ou coordenação/gestão? Muda quanto entra de fórmula e código.
2. Demonstração ao vivo no slide 4 (3 min, com o `pyron-demo`) ou só capturas?
3. Entra o trabalho em dupla com assistentes de IA (diário da equipe, Claude, Codex, Antigravity)? Hoje
   não está no roteiro.
4. A direção visual acima, em especial a barra ferro como linha do tempo nas aberturas de bloco.
5. Os slides 10 e 14 podem sair se faltar tempo.

## Fontes dos números

| Número | Fonte |
|---|---|
| Linhas por linguagem, commits | `git ls-files` e `git log`, contados em 07/11/2026 |
| 128 + 9 rotas | `app/servidor.py` e `app/celular.py`, contados em 07/11/2026 |
| 9 ms, 1 ms, 1,5 s, 483/329/71 ms, 1,9 ms, 1,8 ms, 6/74/884/58 ms | medidos em 07/11/2026 neste notebook (43 termogramas de `app/dados_app`, 24 do ScienceDB sem radiometria, cópia do banco) |
| mAP, precisão, revocação, por parte, erro Tmáx | `modelos/para-raios-rfdetr-local-20260930-1627/relatorio.json` |
| INT8 0,859 × 0,859 | `modelos/para-raios-rfdetr-local-20260930-1627-int8/relatorio.json` |
| 27 ms TensorRT, GTX 1650 | `docs/v09/4-tensorrt.md` |
| Typst 111 → 32 ms | `docs/v09/3-laudo.md` |
| Medição 5,1 %, 19,8 %, 2 s × 20 s | `docs/medicao/relatorio_postit.md` |
| OCR 1,4 → 0,9 s; 350 → 40 ms; mediana 8× | comentários em `nucleo/entrada.py` e `nucleo/paleta.py` |
| 0,5 °C estimado | aviso em `nucleo/entrada.py` |
