# Pyron por dentro: curadoria técnica

Levantamento de 07/11/2026, branch `pontos-quentes-para-raio` (commit `6d4bf59`, versão 0.9). Parte da
"visão técnica" de 31/10 e aprofunda: bibliotecas, transformações, servidor, celular, medição, modelos,
interface, o que já foi otimizado e o que ainda dá para otimizar.

Os números ou vêm do código e dos relatórios do repositório (fonte indicada), ou foram **medidos em
07/11/2026** neste notebook (RTX 3050 Laptop, Windows 11, `.venv` do projeto). Os roteiros de medição
ficaram fora do repositório; dá para repetir com as funções citadas.

Roteiro da apresentação de 50 minutos: `docs/apresentacao/roteiro.md`.

---

## 1. Resumo

O Pyron recebe um termograma, acha as peças do equipamento, mede a temperatura de cada uma, classifica a
severidade pela NBR 15866 e acompanha o equipamento no tempo, com pendência e laudo. Roda no Windows como
programa local (um servidor Python no próprio computador e a interface numa janela), sem internet; desde a
0.9 também roda como servidor da equipe, com login, perfis e tablet.

| Número | Valor | Fonte |
|---|---|---|
| Leitura de um termograma radiométrico | 9 ms (conversão de Planck: 1 ms) | medido, 43 imagens |
| Detecção de para-raios, CPU / placa | 483 ms / 71 ms | medido, 12 imagens |
| Classificação de severidade | 1,8 ms (9 regiões) | medido |
| Detector de para-raios no teste | mAP50 0,891 | `relatorio.json` do modelo |
| Medida de objeto em foto, com post-it | 5,1 % de erro mediano | `docs/medicao/relatorio_postit.md` |
| Testes automáticos | 458 passaram, 9 pulados, 0 falhas, 3 min 21 s | rodado em 07/11 |

---

## 2. O que o Pyron faz

Pelo caminho de uma inspeção:

| Etapa | O que acontece | Onde no código |
|---|---|---|
| Capturar | Arquivo da câmera FLIR, pasta monitorada (a cada 10 s), celular por QR, vídeo térmico gravado | `app/servidor.py`, `app/monitoramento.py`, `app/celular.py`, `app/videos.py` |
| Ler | Imagem vira matriz de temperatura (medida ou estimada) | `nucleo/entrada.py`, `nucleo/flir.py`, `nucleo/paleta.py`, `nucleo/barra.py` |
| Achar peças | Pontos quentes por regra e modelo treinado de para-raios, juntos | `nucleo/detectores/` |
| Classificar | Severidade por peça e da imagem, com o motivo | `nucleo/analise.py`, `nucleo/referencias.py` |
| Revisar | Tela de Análise: corrigir regiões, pontos e linhas de temperatura, carga e ambiente; salva sozinha | `app/interface/js/analise/` |
| Acompanhar | Equipamento no tempo, tendência, previsão de chegar ao limite, próxima inspeção | `app/equipamentos.py` |
| Agir | Pendência (ordem de serviço) do "aberta" ao "verificada" | `app/pendencias.py` |
| Comunicar | Laudo PDF (Typst ou reportlab), alerta com mensagem pronta para o WhatsApp | `app/laudo_typst.py`, `app/laudo.py` |
| Medir | Distância entre duas pontas numa foto comum, em cm | `nucleo/medicao/` |
| Modelos | Treinar, instalar, avaliar, ver se a detecção está na placa | `ml/`, `app/treinos.py` |
| Administrar | Critério, limites por componente, empresa e time, backup, exportação PostgreSQL | `app/servidor.py`, `app/exportar_postgres.py` |

Além do aplicativo principal, o repositório tem: uma versão enxuta para apresentações (`apresentacao/`), o
site com um teste no navegador (`site/`), o desktop em Tauri (`desktop/`) e o lançador `Pyron.exe` (`lancador/`).

---

## 3. Arquitetura

```
Entradas                  Servidor (app/)                Núcleo (nucleo/)              Dados
FLIR radiométrico   ─┐                                ┌─ entrada: pixel → °C         SQLite (WAL, esquema 3)
Pasta monitorada    ─┼─→  FastAPI, 128 rotas  ───────→ ├─ detectores: ONNX + regra    imagens/, matrizes/*.npy
Celular (QR, WSS)   ─┤    acesso.verificar global     ├─ analise: NBR 15866          (pasta local ou S3)
Vídeo               ─┘    laudo, monitor, backup      └─ medicao: profundidade 3D
                               │                                                     Saídas
                               └─→ interface web (app/interface, JS puro) ←───────   laudo PDF, alerta,
Treino (ml/, fora do dia a dia) ─→ modelos/<id>/modelo.onnx + cartao.json            PostgreSQL → Grafana/BI
```

| Camada | Pasta | Linhas Python | Tecnologia |
|---|---|---|---|
| Interface | `app/interface/` | 8,7 mil de JS, 1,5 mil de CSS | JavaScript puro em módulos ES, sem etapa de compilação |
| Servidor | `app/` | 9,4 mil | FastAPI, Uvicorn, SQLite |
| Núcleo | `nucleo/` | 10,9 mil | NumPy, SciPy, OpenCV, ONNX Runtime |
| Treino | `ml/` | 3,1 mil | PyTorch, RF-DETR |
| Lançador e desktop | `lancador/`, `desktop/` | | C# com WebView2; Rust com Tauri v2 |

**O caminho de uma imagem** (`_nova_analise` em `app/servidor.py`): `entrada.carregar()` →
`_detector()` resolve o modelo térmico ativo (para-raios + pontos quentes) → `_na_placa()` troca pela
versão na placa se ela já carregou → `analise.analisar_regioes()` → tira ponto quente sem anomalia →
grava JSON no SQLite, original e matriz `.npy` em arquivo. A resposta registra o tempo de cada etapa
(`etapas`), que a interface mostra.

**Ao abrir uma inspeção**, o servidor recalcula a severidade com o critério em vigor (1,8 ms) e manda a
matriz de temperatura junto, em base64 de float32, para a interface desenhar o termograma e ler a
temperatura sob o cursor sem voltar ao servidor.

---

## 4. Do que o código é feito

Contagem dos arquivos versionados em 07/11/2026 (`git ls-files`, sem imagens, modelos e PDFs).

| Linguagem | Bytes | Linhas | Onde |
|---|---|---|---|
| Python | 53,1 % | 58,7 % (36.384) | núcleo, servidor, treino, testes |
| JavaScript | 29,7 % | 27,5 % (17.040) | interface nova (8,7 mil), anterior (7,1 mil), apresentação, site |
| CSS | 10,3 % | 7,1 % (4.421) | tokens e telas |
| HTML | 3,3 % | 2,3 % | páginas |
| C# | 1,3 % | 1,5 % | `Pyron.exe` (WebView2) |
| Rust | 0,7 % | 0,9 % | desktop Tauri |
| Outros | 1,6 % | 1,9 % | notebook de treino, Typst do laudo, Mojo, SQL do BI, TOML |

Python por pasta: núcleo 10.914, servidor 9.424, testes 9.357, treino 3.076, apresentação 1.194, resto
1.460 linhas. Total versionado: 62 mil linhas.

Histórico: 149 commits de 28/09 a 03/11/2026 (Hugo 93, Gabriel 34, assistente 22). Testes: 52 arquivos em
`testes/`; 458 passam. Os testes também impõem regras de projeto: rota nova sem grupo de acesso falha
(`test_acesso.py`), CSS fora dos tokens falha (`test_interface_nova.py`), módulo JS fora do cache do
aplicativo falha (`test_pwa.py`), a página do servidor nunca ganha acesso a shell (`test_janela.py`).

---

## 5. Bibliotecas

Versões instaladas no `.venv` em 07/11/2026.

| Papel | Biblioteca | Versão | Licença | Onde entra |
|---|---|---|---|---|
| Servidor web | FastAPI, Starlette, Uvicorn, python-multipart | 0.141.1, 1.7.0, 0.54.0, 0.0.32 | MIT, BSD | `app/servidor.py`, `app/celular.py`, `app/iniciar.py` |
| Conta numérica | NumPy | 2.4.6 | BSD | 59 arquivos |
| Filtros, árvore KD, rótulos | SciPy | 1.17.1 | BSD | pontos quentes, paleta, medição |
| Imagem | Pillow (+ pillow-heif para HEIC) | 12.3.0 | HPND, BSD | leitura, laudo, celular |
| Visão computacional | OpenCV | 5.0.0.93 (e 4.10 headless) | Apache 2.0 | barra livre, mediana, QR, vídeo |
| Inferência | ONNX Runtime DirectML | 1.24.4 | MIT | `nucleo/detectores/` |
| Leitura da escala | RapidOCR (ONNX) | 1.4.4 | Apache 2.0 | `nucleo/entrada.py` |
| Treino | PyTorch + RF-DETR + supervision | 2.14 (CUDA 12.6), 1.11.0 | BSD, Apache 2.0, MIT | `ml/` |
| Profundidade | Depth Anything 3 Metric, MoGe-2 | pacote do GitHub | Apache 2.0, MIT | `nucleo/medicao/profundidade.py` |
| Segmentação | transformers (SAM 2.1) | 5.17.0 | Apache 2.0 | `nucleo/medicao/segmentar.py` |
| Laudo | Typst (padrão) e reportlab (reserva) | Typst não instalado aqui; reportlab 5.0.1 | Apache 2.0, BSD | `app/laudo_typst.py`, `app/laudo.py` |
| Nuvem e BI | boto3 (S3), psycopg (PostgreSQL) | opcionais, não instalados aqui | Apache 2.0, LGPL | `app/objetos.py`, `app/exportar_postgres.py` |
| Segurança | hashlib.scrypt, hmac, secrets | biblioteca padrão | | `app/acesso.py` |
| Servidor NVIDIA | onnxruntime-gpu, TensorRT 10 | 1.24.4, 10.16 | MIT, NVIDIA | `requirements-servidor-gpu.txt` |

Regra do projeto para modelos e pacotes de medição: só MIT, Apache 2.0, BSD e OFL; nada GPL, AGPL ou
CC BY-NC (por isso o Depth Pro ficou fora e o DA3 entra sem a API do pacote, que puxa o `evo`, GPL).

---

## 6. O servidor FastAPI

- **Um aplicativo, uma dependência global.** `FastAPI(..., dependencies=[Depends(acesso.verificar)])`:
  toda rota passa pelo controle de acesso. No modo local não faz nada; no modo servidor confere sessão e
  perfil. Cada rota pertence a um grupo em `_GRUPOS_DAS_ROTAS` (público, leitura, envio, revisão, laudo,
  administração, só local); rota sem grupo responde 403 e derruba um teste.
- **Tamanho.** 128 rotas em `app/servidor.py` (3.449 linhas) e 9 no servidor do celular. Maiores famílias:
  `/api/medicao` 27, `/api/analises` 23, `/api/cadastro` 11, `/api/videos` 9, `/api/treinos` 8.
- **Trabalho pesado fora do laço.** A análise e a medição rodam em `run_in_threadpool`: o servidor segue
  respondendo enquanto uma imagem é processada. Uma trava (`_trava`) garante uma análise por vez.
- **Ciclo de vida.** Ao subir (`lifespan`), retoma a pasta monitorada e pré-aquece o modelo na placa e o
  OCR num fio à parte; no modo servidor, não sobe sem um administrador com senha.
- **Interface.** Servida pelo próprio FastAPI como arquivos estáticos (`/` a nova, `/antiga` a anterior);
  um middleware manda `Cache-Control: no-cache` em tudo que não é `/api`, para atualização entrar sem limpar cache.
- **Erros.** Um tratador único devolve `{"erro": "..."}` com texto pronto para a tela.
- **Login (modo servidor).** Senha com scrypt e sal por pessoa (~50 ms por conferência), cookie de sessão
  HttpOnly, SameSite=Strict e Secure no HTTPS, conferência de origem nos pedidos que gravam, conflito de
  edição na Análise devolve 409.
- **Documentação.** O FastAPI gera o OpenAPI sozinho; é a base pronta para uma API pública (seção 15).

---

## 7. Do pixel à temperatura

`entrada.carregar()` tenta três caminhos, nesta ordem, e devolve sempre o mesmo objeto (`ImagemTermica`):
matriz em °C, se é medida ou estimada, a imagem colorida e os metadados.

### 7.1 Radiométrico (medido): `nucleo/flir.py`

1. O JPEG da FLIR guarda, em segmentos APP1 que começam com `FLIR\0`, um bloco FFF. O Pyron junta os
   pedaços, lê o diretório e tira dois registros: `RawData` (o valor bruto do sensor, 16 bits; 160 × 120
   na FLIR C5, às vezes num PNG com os bytes invertidos) e `CameraInfo` (constantes de Planck R1, R2, B, F,
   O, emissividade, distância, temperaturas refletida e atmosférica, umidade, janela, modelo da câmera).
2. Para cada pixel, desconta o que não é o objeto e inverte a curva de Planck da câmera:

   ```
   R(T)   = R1 / (R2 · (exp(B / T) − F)) − O                  radiância de um corpo a T kelvin
   τ      = X·exp(−√(d/2)·(α1 + β1·√H2O)) + (1−X)·exp(−√(d/2)·(α2 + β2·√H2O))   transmissão do ar
   S_obj  = S / (ε·τ1·τjan·τ2) − (1−ε)/ε·R(T_refl) − atmosfera − janela
   T_obj  = B / ln(R1 / (R2 · (S_obj + O)) + F) − 273,15
   ```

   É a formulação do exiftool e do pacote Thermimage. Emissividade, distância, temperatura refletida,
   umidade e temperatura do ar podem ser trocadas depois na Análise, como no software da câmera.
3. Medido: a conversão leva **1 ms** e a leitura completa (abrir, converter, girar pelo EXIF) **9 ms** na
   mediana de 43 termogramas.

### 7.2 Estimado pela barra da FLIR C5: `nucleo/paleta.py`

Para a imagem comum da câmera (sem radiometria), no leiaute conhecido da C5 (640 × 480, arco-íris):

1. acha a barra pela moldura branca (duas linhas longas paralelas perto da borda);
2. lê as cores da barra, do quente para o frio (o lado mais claro é o quente);
3. lê máximo e mínimo com o RapidOCR: três preparações do recorte votam, e o valor mais frequente vence;
4. converte cada cor para CIELAB, acha a cor mais próxima da barra numa árvore KD e refina projetando no
   segmento até a cor vizinha: isso dá a posição na barra (0 quente, 1 frio);
5. converte posição em temperatura **pela radiância**, não de forma linear: a FLIR distribui as cores
   linearmente no sinal do sensor, que segue Planck (constante B típica de 1430 K);
6. descarta o que não é cena (textos, logotipo, a própria barra, linhas finas do MSX) e marca pixel
   saturado (cor na ponta da barra: a temperatura real pode estar além da escala). A matriz sai com metade
   da resolução, pela mediana de blocos 2 × 2.

### 7.3 Barra em qualquer lugar: `nucleo/barra.py`

Para foto da tela, outra câmera ou captura: monta um mapa de candidatos (cor igual através da barra e
mudando devagar ao longo dela), acha os caminhos mais longos quase retos por programação dinâmica (aceita
barra inclinada até ~4,5°), confere o perfil (muita cor percorrida, pontas distantes, sem voltar atrás) e
lê os números junto das pontas. No acervo ScienceDB a barra foi achada em 298 de 299 termogramas e em
nenhuma de 149 fotos comuns (docstring de `barra.py`).

### 7.4 O que foi medido hoje no caminho estimado

24 termogramas do ScienceDB regravados sem radiometria, comparados com a leitura radiométrica do mesmo arquivo:

- tempo: **1,5 s** na mediana (máximo 2,2 s); a primeira imagem leva 4,5 s porque carrega o OCR. Quase
  todo o tempo é OCR;
- 23 de 24 viraram temperatura; em 1 o OCR leu uma escala inválida e a imagem foi recusada com mensagem;
- acima do topo da escala a temperatura não volta: um seccionador a 239 °C numa escala que ia até 64 °C, e
  um transformador a 58 °C numa escala até 43 °C;
- a máxima da cena (que pega marcadores e textos da câmera) diferiu 2,2 °C na mediana. O erro por peça
  documentado é 0,5 °C na mediana (`AVISO_ESTIMADA` em `nucleo/entrada.py`).

Conclusão para o uso: o arquivo radiométrico é medida (9 ms); o estimado é aproximação com aviso (1,5 s).

---

## 8. Achar as peças

Todo detector recebe a matriz de temperatura (e, se precisar, a imagem colorida) e devolve caixas com
classe e confiança (`nucleo/detectores/__init__.py`). Dois tipos: regra e modelo treinado, listados do mesmo jeito.

### 8.1 Pontos quentes por regra: `nucleo/detectores/pontos_quentes.py`

1. separa equipamento e céu pelo limiar de Otsu;
2. média do equipamento numa janela de 12 % da largura (convolução normalizada: o céu não entra);
3. marca o que passa **4 °C** dessa média, abre a máscara e junta vizinhos em regiões;
4. descarta mancha muito pequena ou faixa muito grande (peça inteira aquecida não é ponto quente); fica
   com as 6 mais intensas.

Medido: **1,9 ms** por imagem. Não sabe o que é cada peça.

### 8.2 Modelo de para-raios: RF-DETR

- **Arquitetura:** RF-DETR Medium (Roboflow, Apache 2.0), um detector da família DETR com base DINOv2.
  Olha a imagem colorida da câmera em 640 × 640, normalizada com a média e o desvio do ImageNet.
- **Classes:** para-raio, aletas isoladoras, terminal superior, terminal inferior.
- **Dados:** fotos do ScienceDB 10185 (só estudo, CC BY-NC-SA) rotuladas no CVAT; 111 de treino, 25 de
  validação, 27 de teste, 1.183 caixas. Fotos com peça inclinada mais de 15° ficam fora (a caixa reta
  engoliria o vizinho).
- **Treino:** `python -m ml.rfdetr_local`, neste notebook, 18 min, 100 épocas, lote 2 com acúmulo 2,
  paciência 20, a partir dos pesos do COCO. O limiar de confiança (0,5) e a numeração das classes são
  escolhidos na validação, nunca no teste.
- **Entrega:** ONNX + `cartao.json`, o contrato entre treino e programa: o que o modelo olha
  (`imagem_exibida` ou `temperatura`), tamanho, normalização, formato da saída (`rfdetr`: centro, largura
  e altura de 0 a 1 e notas antes da sigmoide, com a coluna de fundo), limiar, métricas e limitações. Trocar
  de modelo é instalar outra pasta. Treino e uso chamam as mesmas funções de preparo (`preparo.py`).

| Teste (27 fotos) | Valor |
|---|---|
| mAP50 / mAP50-95 | 0,891 / 0,556 |
| Precisão / revocação / F1 | 0,888 / 0,898 / 0,893 |
| Peças achadas | 159 de 177 (20 falsas, 18 perdidas) |
| AP50 por parte | para-raio 0,99; aletas 1,0; terminal superior 0,84; terminal inferior 0,73 |
| Erro da temperatura máxima por peça | 0,0 °C na mediana; até 0,94 °C em 90 % |

Fonte: `modelos/para-raios-rfdetr-local-20260930-1627/relatorio.json`.

### 8.3 Peças e calor juntos (`Combinado`)

O modelo térmico padrão é "para-raios + pontos quentes" (`_modelo_termico()`). Desde 03/11:

- para-raio repetido (caixas que se cobrem 60 %) fica um só, numerado da esquerda para a direita;
- cada parte vai para o para-raio que a contém, cortada dentro dele, uma de cada tipo; as aletas ficam entre o
  fim do terminal superior e o começo do inferior (antes as caixas se cobriam e o mesmo pixel quente aparecia
  em três regiões);
- ponto quente dentro de uma peça sai: a peça já mede o seu ponto mais quente;
- ponto quente sem anomalia (normal e com ΔT do entorno abaixo de 5 °C) sai depois da classificação;
- o ponto mais quente da cena vem da matriz inteira, com a peça onde ele está.

### 8.4 Outros detectores no código

`pontos-quentes-sam2` e `sam2-dinov2` (segmentação SAM 2 com classificação DINOv2) continuam no backend,
fora da tela desde 31/10: levam minutos por imagem e não ficam como padrão.

---

## 9. Severidade (NBR 15866): `nucleo/analise.py`

Para cada peça, até três avaliações; vale a pior, e o motivo fica registrado.

| Avaliação | Regra | Limites (critério brasileiro padrão) |
|---|---|---|
| Relativa | ΔT contra a mediana das peças iguais das outras fases, corrigido pela carga: × (100/carga)² | condutoras: 5 / 10,1 / 20,1 / 40,1 °C; para-raio e isolador: 2 / 5 / 10 °C, sem correção |
| Absoluta | temperatura projetada para plena carga, T_amb + (T − T_amb)·(100/carga)², em % da MTA do componente | 60,1 / 70,1 / 80,1 / 100,1 % |
| Ambiente (NETA MTS) | ΔT sobre o ar ambiente | desligada no critério brasileiro |

Níveis: normal, atenção, programar, urgente, imediato, com reinspeção em 365, 90, 30, 7 e 1 dia. Também
calcula quanto de corrente cabe até a MTA: √((MTA − T_amb)/(T − T_amb)).

Estados que não são "normal": **não avaliado** (para-raio sem a peça igual de outra fase na foto) e **sem
medida** (sem temperatura). Avisos: carga abaixo de 40 %, sem ambiente (classificação indicativa), ponto
acima de 150 °C (sol ou reflexo), ponto mais quente fora das peças, e "confira antes de agir" quando a
severidade vem só de um ponto fora das peças identificadas. Critério NETA disponível como alternativa.

Medido: **1,8 ms** para 9 regiões.

---

## 10. Conexão com o celular: `app/celular.py` + `app/estatico/celular.js`

1. **Segundo servidor.** O Pyron normal só atende o próprio computador (127.0.0.1). Ao ligar o modo
   celular, sobe outro Uvicorn ouvindo a rede local (porta a partir de 8791) com **só** as rotas do
   celular: ninguém na rede chega às inspeções, aos backups ou às configurações.
2. **HTTPS próprio.** O navegador do celular só libera a câmera em conexão segura. O certificado é gerado
   na hora pelo OpenSSL (o do sistema ou o do Git para Windows), para o IP da rede; o celular avisa uma vez.
3. **Código no link.** Cada vez que o modo liga, sai um código aleatório novo (`secrets`); sem ele, nada
   responde. O link vira QR code (OpenCV) na tela.
4. **Transmissão.** WebSocket binário. Cada quadro é um JPEG (lado 960, qualidade 0,72, ~60 KB) com um
   cabeçalho de 16 bytes: número do quadro, trecho do rastro e posição da câmera (x, y). O ritmo acompanha
   o computador: de 5 a 15 quadros por segundo. Se o WebSocket ainda tem mais de 192 KB na fila, o quadro é
   pulado.
5. **Sem fila no servidor.** Guarda sempre o quadro mais novo e analisa um por vez, descartando os que
   chegaram durante a análise. O enquadramento (`nucleo/enquadrar.py`) recorta só o termograma da foto.
6. **Caixas que andam com a câmera.** Entre uma resposta e outra (a análise volta atrasada), o celular
   compara miniaturas em cinza de 72 px com um quadro de referência, estima quanto a cena andou e leva as
   caixas junto. A temperatura de cada peça é a mediana dos últimos 5 quadros.
7. **Reserva.** Rede que bloqueia WebSocket: um quadro por vez por HTTP.
8. **Para medir:** o celular só tira a foto ou grava o vídeo e envia o original, sem recomprimir (até 40 MB
   por foto, 100 MB por vídeo); a medida é sempre no computador.

---

## 11. Medição em foto comum: `nucleo/medicao/`

Tela Medição (desde 31/10): o usuário abre a foto e marca **duas pontas**; sai uma distância em cm com a
margem de erro. Uma medida por vez, nada gravado.

1. **Profundidade.** O modelo estima um ponto 3D (metros, referencial da câmera) para cada pixel.
   - **Depth Anything 3 Metric Large** (ByteDance, Apache 2.0), o padrão. Entra só a rede, sem a API do
     pacote. Processa com o lado maior em 504 px; a saída é relativa à focal: metros = saída × focal / 300.
     A focal sai do EXIF (equivalente 35 mm, calculado sobre o quadro 4:3 do sensor, porque o celular corta
     a foto 16:9 e mantém o equivalente do quadro inteiro) ou de um campo de visão padrão de 65°.
   - **MoGe-2 ViT-L** (Microsoft, MIT), a reserva: estima também a lente; usa meia precisão na placa e
     volta para 32 bits sozinho se a placa devolver máscara vazia (GTX 16xx).
2. **Distância.** Ponto 3D de cada ponta pela mediana de 5 × 5 pixels; a distância é a norma da diferença.
   A margem soma o tamanho do pixel nas pontas, o ruído local e o erro de escala do modelo.
3. **Referência.** Um post-it rosa de 8 cm é achado sozinho pela cor e corrige a escala da cena inteira
   (ignorado se for menor que 100 px ou estiver fora da profundidade do objeto).
4. **Sem modelo.** "Retângulo de referência": 4 cantos de uma folha A4 ou cartão definem a homografia
   imagem → plano; a margem sai de 400 sorteios de Monte Carlo com erro de clique de 1 px.
5. **Vídeo.** Escolhe quadros nítidos, segue as pontas por fluxo óptico e faz a mediana por quadro.

| Erro mediano (31 fotos, 55 medidas, Galaxy S23) | MoGe-2 | Depth Anything 3 |
|---|---|---|
| Sem referência | 29,6 % | 19,8 % |
| Com post-it | 8,1 % | 5,1 % |
| Tempo por foto na CPU | 20 s | 2 s |

Fonte: `docs/medicao/relatorio_postit.md`. Limites: poucas fotos de um celular; em equipamento energizado não
dá para pôr post-it; na câmera térmica (160 × 120) um pixel já vale ±2,6 % do comprimento de um para-raio.

---

## 12. Interface

- **JavaScript puro em módulos ES, sem etapa de compilação** (`app/interface/`, 59 arquivos, 10,2 mil
  linhas com CSS). Uma tela por arquivo em `js/telas/`, mapa em `js/rotas.js`, componentes compartilhados
  em `js/componentes.js`, textos em `textos.js`.
- **Sistema de tokens** em `tokens.css` como fonte única (cor, espaço, tipo, raio, sombra, duração); um
  teste reprova CSS fora dos tokens. Cobalto só na ação e na seleção; paleta ferro e severidade só como dado.
- **O termograma é desenhado no navegador:** a matriz float32 chega em base64, vira cor por uma tabela da
  paleta num `<canvas>` (`js/analise/palco.js`); regiões, pontos e linhas ficam em SVG por cima; a mira lê a
  temperatura do pixel sem voltar ao servidor; zoom até 12×, isoterma, troca de paleta.
- **Padrão de tela** vindo da Análise: salvamento automático com "Salvo" e Desfazer em vez de pedir
  confirmação; listas com filtro e ordem no endereço; estados de carregamento, vazio e erro.
- **Acessibilidade:** axe sem violações (WCAG 2.2 AA) nos temas claro e escuro; alvo de 44 px no toque.
- **Tablet:** aplicativo instalável (PWA) no modo servidor, com cache "rede primeiro" e gestos de pinça.
- **Janela:** `Pyron.exe` (C#, WebView2) abre a interface sem a barra do Windows; o desktop em Tauri (Rust)
  é a próxima geração, ainda sem assinatura.
- **Interface anterior** (`app/estatico/`, 7,1 mil linhas de JS, `app.js` com 270 KB) ainda servida em
  `/antiga`; a página do celular mora na mesma pasta.

---

## 13. Dados, laudo, alertas e modo servidor

- **Banco:** SQLite em WAL, esquema versionado (3) que se atualiza sozinho; tabelas de análises, regiões,
  equipamentos, pendências, histórico, alertas, comentários, sessões e laudos emitidos, com índices.
  Imagens e matrizes em pasta ou num bucket S3 (`PYRON_OBJETOS=s3://...`). Backup agendado.
- **BI (Gabriel):** `app/exportar_postgres.py` leva o SQLite para PostgreSQL (ou gera um `.sql`), com views
  para Grafana e BI em `docs/`.
- **Laudo:** Typst como padrão desde 30/10 (2 a 3,5 vezes mais rápido; texto do usuário entra só por
  `dados.json`, nunca montado como código); sem o Typst, cai no reportlab. Neste notebook o pacote `typst`
  não está instalado, então sai pelo reportlab.
- **Monitor e alertas:** confere a pasta a cada 10 s; alerta a partir do nível configurado, sem repetir o
  mesmo nível por 60 min; a mensagem do WhatsApp sai pronta num link, o envio é manual.
- **Placa de vídeo:** a escolha do provedor fica num lugar só (`provedores.py`, TensorRT > CUDA > DirectML
  > CPU); a sessão da CPU é a referência e a da placa é conferida depois da primeira conta, porque o ONNX
  Runtime volta para a CPU em silêncio se a placa falhar.

---

## 14. Outras coisas que valem ser ditas

- **O Controle Inteligente de Aplicativos moldou a arquitetura.** Ele barra DLL sem assinatura: a placa
  entra pelo DirectML (DLLs assinadas pela Microsoft) e não pelo PyTorch com CUDA; o `Pyron.exe` precisa
  ficar pequeno (uma versão de 390 KB foi barrada); o desktop Tauri só vira padrão depois de assinado.
- **Contrato do modelo.** O `cartao.json` separa o treino do programa: o Pyron não sabe de PyTorch para
  usar um modelo, só de ONNX e do cartão.
- **Kernels em Mojo** (`nucleo/aceleradores/`, Gabriel): RANSAC de plano, homografia em lote, Planck e
  cosseno, com reserva em NumPy. A pasta `bin/` está vazia: hoje roda sempre a reserva.
- **Trabalho em dupla com assistentes.** Diário da equipe (`docs/equipe/diario.md`) com gancho que mostra
  as novidades do outro ao abrir a sessão; partes feitas com o orquestrador alethe (Claude, Codex e
  Antigravity), com revisão cruzada que achou defeitos reais.
- **Testes como regra:** 458 testes, inclusive os que impedem rota sem controle de acesso, CSS fora dos
  tokens e permissão de shell para a página do servidor.

---

## 15. O que já foi otimizado

| Onde | Mudança | Antes → depois | Fonte |
|---|---|---|---|
| OCR da escala | detecção de texto até 320 px e cache dos recortes | 1,4 s → 0,9 s, mesma temperatura | `nucleo/entrada.py` |
| Cor → posição na barra | projetar uma vez cada cor distinta | 350 → 40 ms | `nucleo/paleta.py` |
| Mediana das linhas finas | OpenCV em vez do SciPy | ~8 vezes, mesma máscara | `nucleo/paleta.py` |
| Vídeo | tabela de cor 64³ montada uma vez; OCR só quando o rótulo muda | | `nucleo/video.py` |
| Normalização do quadro | multiplicação e soma no lugar | 9 → 6 ms por quadro do celular | `onnx_modelo.py` |
| Modelo na CPU | INT8 dinâmico só nos MatMul | 483 → 329 ms (medido); 122,8 → 43,5 MB; mAP50 0,859 × 0,859 | `ml/otimizar.py`, relatório INT8 |
| Modelo na placa | DirectML com o mesmo ONNX | 483 → 71 ms (6,8 vezes, medido); carga em 2,7 s | `placa.py` |
| Servidor NVIDIA | TensorRT, motor em cache, montado em outro processo | 27 ms na GTX 1650 (CPU 163 ms) | `docs/v09/4-tensorrt.md` |
| Primeira imagem | sessão guardada, pré-aquecimento ao subir, placa carregando em outro fio | | `servidor.py` |
| Celular | só o quadro mais novo, ritmo adaptado, caixas seguindo a câmera no celular | | `celular.py`, `celular.js` |
| Laudo | Typst em vez de reportlab | 111 → 32 ms (1 inspeção); 1.944 → 1.024 ms (50) | `docs/v09/3-laudo.md` |
| Profundidade | Depth Anything 3 em vez de MoGe-2 | 20 → 2 s por foto, erro 8,1 → 5,1 % | `relatorio_postit.md` |
| Servidor | análise fora do laço; SQLite em WAL com índices | | `servidor.py`, `armazenamento.py` |

---

## 16. O que ainda dá para otimizar

Ordem: primeiro o que foi medido e tem ganho claro.

| # | Ponto | Medido / constatado | O que fazer | Esforço |
|---|---|---|---|---|
| 1 | A lista de inspeções abre o JSON completo de todas a cada pedido (`armazenamento.listar()`) | cópia do banco: 60 → 6 ms; 600 → 74 ms; 3.000 → 408 ms; 6.000 → 884 ms e 12 MB de resposta. Só as colunas indexadas: 58 ms nas 6.000 | ler as colunas que o banco já tem (ou uma coluna de resumo) e paginar | baixo |
| 2 | Uma análise por vez (`_trava` global) | constatado no código; no modo servidor, a equipe faz fila | travar só o que é compartilhado (sessão do modelo), ou fila de trabalhos | médio |
| 3 | Importação manual na CPU usa o modelo original | 483 ms; o INT8 dá 329 ms com o mesmo mAP50 | em máquina sem placa, usar o INT8 também na importação | baixo |
| 4 | Matriz em base64 dentro do JSON | 100 KB por termograma 160 × 120 (estimado: 4 vezes mais) | rota binária (75 KB) ou float16 (38 KB, passo de 0,03 °C a 60 °C) | baixo |
| 5 | Caminho estimado | 1,5 s por imagem, quase tudo OCR | a cache já ajuda câmera fixa; OCR na placa ou só nos dois rótulos | médio |
| 6 | `servidor.py` com 3.449 linhas e 128 rotas | | dividir em `APIRouter` por assunto (análises, cadastro, medição, celular) | médio |
| 7 | Interface anterior ainda servida | 7,1 mil linhas de JS, `app.js` com 270 KB | retirar depois de mudar a página do celular de pasta | médio |
| 8 | Duas versões do OpenCV no `.venv` | `opencv-python` 5.0 e `opencv-python-headless` 4.10, o mesmo módulo `cv2` | deixar uma só | baixo |
| 9 | Kernels Mojo sem binário | `nucleo/aceleradores/bin/` vazio | compilar e assinar, ou tirar | baixo |
| 10 | Dependências não declaradas | `pyproject.toml` lista só numpy, pillow e scipy | declarar tudo com versão (base do instalador) | baixo |
| 11 | Sem integração contínua | não há `.github/` | rodar `pytest -m "not lento"` a cada envio | baixo |
| 12 | Celular depende do OpenSSL do Git | sem ele, o modo celular não liga em máquina nova | gerar o certificado em Python | baixo |

**Validação, que pesa mais que velocidade:** teste com 27 fotos de uma subestação e uma câmera; terminais
com AP50 de 0,84 e 0,73; nenhuma medida registrada de concordância da severidade com um especialista (meta
de 85 %) nem do erro frente ao software da FLIR (meta de 0,5 °C); leitura pela barra ajustada à FLIR C5.

---

## 17. Horizonte: o que falta para virar plataforma

**Distribuição**
- Instalador assinado. O desktop em Tauri já gera MSI e NSIS; sem assinatura de código o Controle
  Inteligente barra. Python embutido e dependências declaradas (item 10). Atualização automática.

**Servidor**
- Imagem Docker do modo servidor (FastAPI + ONNX com TensorRT, imagem base da NVIDIA) e um compose com
  PostgreSQL, Grafana e proxy HTTPS próprio (o Tailscale gratuito é só para uso não comercial).
- Backup em S3 (o armazenamento já fala S3), logs estruturados, métricas e alerta de erro.
- Fila de trabalhos para análise e laudo em lote (resolve também o item 2).

**API para outros sistemas**
- API versionada (`/v1`) com chave por cliente, a partir do OpenAPI que o FastAPI já gera: enviar
  inspeção, consultar severidade, **gerar o laudo em PDF por chamada** (o motor Typst já recebe só dados),
  webhook quando um nível é atingido.
- Integração com sistemas de manutenção (SAP PM, Maximo): a pendência vira ordem de serviço lá.
- Alerta automático pela API oficial do WhatsApp Business.

**Produto e IA**
- Mais classes: bucha, conexão, seccionadora, TC/TP. Hoje só para-raio tem modelo.
- As correções que o usuário faz na Análise (caixas movidas, classes trocadas) viram rótulos para o
  próximo treino.
- Câmera fixa (RTSP/ONVIF) como fonte; cadastro de equipamentos como fonte única (hoje o nome digitado
  separa o histórico).
- Várias empresas no mesmo servidor; tirar o GPS das fotos ao guardar (LGPD).

---

## 18. Limites deste levantamento

- Tempos medidos num notebook com RTX 3050, não no servidor de produção (que ainda não existe).
- A comparação estimado × radiométrico de hoje usou a máxima da cena, não a de cada peça; o erro por peça
  vem da documentação.
- O dataset de treino é CC BY-NC-SA, só para estudo; uso comercial pede dados próprios.
- Os limites de severidade seguem o que o código declara como prática da NBR 15866; não foram conferidos
  contra a edição vigente da norma.
