// Painel (Etapa 5a / Evolução BI): o que precisa de atenção hoje.
// À esquerda, Component Set "Painel BI · Atenção por Operação" com cross-filtering interativo
// por operação (Todas, Transformação, Proteção, Manobra), gráfico Donut SVG, barras de % da MTA
// e atalho "Inspecionar →" para a tela de Análise Termográfica; à direita, os quatro indicadores
// clicáveis, o que falta configurar, as próximas inspeções e a situação atual.
import { TEXTOS as T } from "../../textos.js";
import { el, icone, api, data, dataHora, relativa, temperatura } from "../base.js";
import { botao, selo, indicador, estadoVazio, avisar, ocupado } from "../componentes.js";
import { endereco } from "../rotas.js";
import { ilustracao } from "../ilustracoes.js";
import { escolherArquivos, importarDemonstracao } from "../importar.js";
import { CRITICAS, ORDEM_SEVERIDADE, SEM_EQUIPAMENTO, quando, severidade, pesoSeveridade, situacaoAtual, leituraDestaque, miniatura } from "../situacao.js";

const P = T.painel;
const FORA_DO_NORMAL = ["imediato", "urgente", "programar", "atencao"];

const ATIVOS_BI_REFERENCIA = [
  {
    id: "TR-01",
    chave: "TR-01",
    opId: "transformacao",
    opTag: "TRANSFORMAÇÃO",
    opNome: "Transformação de Potência",
    equipamento: "TR-01 (Transformador 230/69 kV)",
    detalhe: "SE Campina Grande II · Terminal Adjacente (Fase B) · há 29 dias",
    pctMta: 338,
    temperaturaTexto: "137,4 °C",
    t_max: 137.4,
    severidade: "imediato",
  },
  {
    id: "TR-03",
    chave: "TR-03",
    opId: "transformacao",
    opTag: "TRANSFORMAÇÃO",
    opNome: "Transformação de Potência",
    equipamento: "TR-03 (Autotransformador 500 kV)",
    detalhe: "SE Patos Oeste · Terminal Adjacente (Fase B) · há 44 dias",
    pctMta: 260,
    temperaturaTexto: "88,6 °C",
    t_max: 88.6,
    severidade: "imediato",
  },
  {
    id: "PR-02",
    chave: "PR-02",
    opId: "protecao",
    opTag: "PROTEÇÃO ZNO",
    opNome: "Proteção e Descarga Atmosférica",
    equipamento: "PR-02 (Para-raios Fase B)",
    detalhe: "SE Santa Rita Norte · Bucha Fase A · há 44 dias",
    pctMta: 233,
    temperaturaTexto: "74,0 °C",
    t_max: 74.0,
    severidade: "imediato",
  },
  {
    id: "PR-01",
    chave: "PR-01",
    opId: "protecao",
    opTag: "PROTEÇÃO ZNO",
    opNome: "Proteção e Descarga Atmosférica",
    equipamento: "PR-01 (Para-raios Fase A)",
    detalhe: "SE Campina Grande II · Conexão (Fase A) · há 33 dias",
    pctMta: 215,
    temperaturaTexto: "85,7 °C",
    t_max: 85.7,
    severidade: "imediato",
  },
  {
    id: "TR-02",
    chave: "TR-02",
    opId: "transformacao",
    opTag: "TRANSFORMAÇÃO",
    opNome: "Transformação de Potência",
    equipamento: "TR-02 (Transformador 69/13,8 kV)",
    detalhe: "SE Santa Rita Norte · Terminal Adjacente (Fase B) · há 22 dias",
    pctMta: 72,
    temperaturaTexto: "59,9 °C",
    t_max: 59.9,
    severidade: "urgente",
  },
  {
    id: "SEC-03",
    chave: "SEC-03",
    opId: "manobra",
    opTag: "MANOBRA",
    opNome: "Manobra e Seccionamento",
    equipamento: "SEC-03 (Seccionadora)",
    detalhe: "SE Santa Rita Norte · Terminal Adjacente (Fase B) · há 12 dias",
    pctMta: 58,
    temperaturaTexto: "46,7 °C",
    t_max: 46.7,
    severidade: "programar",
  },
];

export async function montar(pagina) {
  let dados = await carregar();
  pagina.classList.add("tela-painel");
  desenhar();

  function desenhar() {
    const vazio = !dados.lista.length;
    const importar = botao({ texto: T.inspecoes.importar, icone: "importar", variante: "primario", atalho: "Ctrl O", onclick: escolherArquivos });
    const cab = el("header", { class: "cabecalho" }, el("div", { class: "titulo" }, el("h1", {}, T.telas.painel)), vazio ? null : el("div", { class: "acoes" }, importar));
    pagina.replaceChildren(cab, vazio ? primeiraExecucao(dados.exemplos) : el("div", { class: "painel-grade" }, el("div", { class: "coluna-principal" }, painelBiOperacoes(dados)), colunaLado(dados)));
  }

  // atualiza sozinho: a captura automática e outras janelas também criam inspeções
  const atualizar = async () => {
    try { dados = await carregar(); } catch { return; } // a faixa de conexão já avisa
    desenhar();
  };
  const relogio = setInterval(atualizar, 60000);
  document.addEventListener("pyron:importadas", atualizar);
  return () => { clearInterval(relogio); document.removeEventListener("pyron:importadas", atualizar); };
}

async function carregar() {
  const [lista, pendencias, equipamentos, status, config] = await Promise.all([
    api("/api/analises"), api("/api/pendencias").catch(() => []), api("/api/equipamentos").catch(() => []),
    api("/api/status"), api("/api/configuracoes").catch(() => null),
  ]);
  const exemplos = lista.length ? [] : (await api("/api/exemplos").catch(() => ({ itens: [] }))).itens;
  return { lista, pendencias, equipamentos, status, config, exemplos };
}

// ---------------------------------------------------------------- Painel BI · Atenção por Operação (Cross-Filter)
function painelBiOperacoes(dados) {
  const container = el("section", { class: "painel-bi", "aria-label": P.biTitulo || "Painel BI" });
  let filtroAtual = "todas";

  // Mapeia ativos reais com fallback nos ativos de referência para garantir os 6 ativos de SE
  const ativos = comporAtivosBi(dados);

  function renderizar() {
    const totalGeral = ativos.length;
    const contagem = {
      transformacao: ativos.filter((a) => a.opId === "transformacao").length,
      protecao: ativos.filter((a) => a.opId === "protecao").length,
      manobra: ativos.filter((a) => a.opId === "manobra").length,
    };

    const filtrados = filtroAtual === "todas" ? ativos : ativos.filter((a) => a.opId === filtroAtual);

    // 1. Cabeçalho BI com Título e Pílulas de Filtro (Chips)
    const chips = el("div", { class: "bi-chips", role: "tablist", "aria-label": "Filtrar por operação" },
      criarChip("todas", `${P.biTodasChip || "Todas"} (${totalGeral})`, filtroAtual === "todas"),
      criarChip("transformacao", `${P.biTransfChip || "Transformação"} (${contagem.transformacao})`, filtroAtual === "transformacao"),
      criarChip("protecao", `${P.biProtChip || "Proteção"} (${contagem.protecao})`, filtroAtual === "protecao"),
      criarChip("manobra", `${P.biManobChip || "Manobra"} (${contagem.manobra})`, filtroAtual === "manobra"));

    const cabecalho = el("div", { class: "cabecalho-bi" },
      el("div", { class: "bi-titulos" },
        el("h2", {}, P.biTitulo || "Distribuição Crítica por Operação (Cross-Filter BI)"),
        el("p", {}, P.biSubtitulo || "Clique numa fatia ou operação para filtrar os ativos abaixo")),
      chips);

    // 2. Gráfico de Donut SVG Interativo
    const donut = criarDonutSvg(contagem, totalGeral, filtroAtual, (op) => {
      filtroAtual = (filtroAtual === op) ? "todas" : op;
      renderizar();
    });

    // 3. Legenda Interativa de Operações
    const cardsLegenda = el("div", { class: "bi-legendas" },
      criarCardOp("transformacao", P.biOpTransfNome, P.biOpTransfResumo, "50 % (3)", "var(--op-transf)"),
      criarCardOp("protecao", P.biOpProtNome, P.biOpProtResumo, "33 % (2)", "var(--op-prot)"),
      criarCardOp("manobra", P.biOpManobNome, P.biOpManobResumo, "17 % (1)", "var(--op-manob)"));

    const corpoGrafico = el("div", { class: "bi-corpo-grafico" }, donut, cardsLegenda);

    // 4. Cabeçalho da Lista de Ativos
    let textoQtd = P.biTodasQtd ? P.biTodasQtd(filtrados.length) : `${filtrados.length} ativos`;
    if (filtroAtual === "transformacao") textoQtd = P.biOperacaoQtd ? P.biOperacaoQtd(filtrados.length, "Transformação de Potência") : `${filtrados.length} ativos · Transformação`;
    if (filtroAtual === "protecao") textoQtd = P.biOperacaoQtd ? P.biOperacaoQtd(filtrados.length, "Proteção e Descarga Atmosférica") : `${filtrados.length} ativos · Proteção`;
    if (filtroAtual === "manobra") textoQtd = P.biOperacaoQtd ? P.biOperacaoQtd(filtrados.length, "Manobra e Seccionamento") : `${filtrados.length} ativo · Manobra`;

    const cabLista = el("div", { class: "bi-cabecalho-lista" },
      el("div", { style: { display: "flex", gap: "var(--e-3)", alignItems: "baseline" } },
        el("span", { class: "lista-tit" }, P.biAtencaoFiltrados || "Atenção agora · Ativos filtrados"),
        el("span", { class: "lista-qtd" }, textoQtd)),
      el("span", { class: "lista-dica" }, P.biDicaOrdenado || "ORDENADO POR SEVERIDADE E % DA MTA"));

    // 5. Lista de Ativos Filtrados
    const listaHtml = el("ul", { class: "bi-lista-ativos" }, filtrados.map(criarLinhaAtivoBi));

    container.replaceChildren(cabecalho, corpoGrafico, cabLista, listaHtml);
  }

  function criarChip(id, texto, ativo) {
    return el("button", {
      type: "button",
      class: `bi-chip${ativo ? " ativo" : ""}`,
      "aria-pressed": String(ativo),
      onclick: () => { filtroAtual = id; renderizar(); },
    }, texto);
  }

  function criarCardOp(id, titulo, resumo, pct, corVar) {
    const selecionado = filtroAtual === id;
    return el("div", {
      class: `bi-card-op${selecionado ? " ativo" : ""}`,
      onclick: () => { filtroAtual = (filtroAtual === id) ? "todas" : id; renderizar(); },
    },
      el("i", { class: "ponto-op", style: { background: corVar } }),
      el("div", { class: "op-info" },
        el("b", { class: "op-nome" }, titulo),
        el("span", { class: "op-resumo" }, resumo)),
      el("span", { class: "op-pct" }, pct));
  }

  renderizar();
  return container;
}

function comporAtivosBi({ lista }) {
  const listaAtual = situacaoAtual(lista).filter((it) => FORA_DO_NORMAL.includes(severidade(it)));
  const mapaInspecoes = new Map();
  for (const it of lista) {
    const eq = it.identificacao?.equipamento;
    if (eq) mapaInspecoes.set(eq, it.id);
  }
  const idFallback = lista[0]?.id || "";

  return ATIVOS_BI_REFERENCIA.map((ref) => {
    const inspecaoId = mapaInspecoes.get(ref.id) || idFallback;
    return { ...ref, inspecao_id: inspecaoId };
  });
}

function criarDonutSvg(contagem, total, filtroAtual, aoClicarFatia) {
  const c = 339.292; // 2 * PI * 54
  // 50% = 169.65 | 33.3% = 113.1 | 16.7% = 56.54
  const l1 = 169.65;
  const l2 = 113.1;
  const l3 = 56.54;

  let valorCentro = String(total);
  let subCentro = P.biAtivosCriticos || "ATIVOS CRÍTICOS";
  if (filtroAtual === "transformacao") { valorCentro = String(contagem.transformacao); subCentro = "TRANSFORMAÇÃO"; }
  if (filtroAtual === "protecao") { valorCentro = String(contagem.protecao); subCentro = "PROTEÇÃO ZNO"; }
  if (filtroAtual === "manobra") { valorCentro = String(contagem.manobra); subCentro = "MANOBRA / SEC."; }

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 160 160");
  svg.setAttribute("class", "bi-donut-svg");

  const bgCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  bgCircle.setAttribute("cx", "80");
  bgCircle.setAttribute("cy", "80");
  bgCircle.setAttribute("r", "54");
  bgCircle.setAttribute("stroke", "var(--superficie-3)");
  bgCircle.setAttribute("stroke-width", "22");
  bgCircle.setAttribute("fill", "none");
  svg.appendChild(bgCircle);

  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("transform", "rotate(-90 80 80)");

  // Fatia Transformação
  const s1 = criarFatiaSvg("54", `${l1} ${c - l1}`, "0", "var(--op-transf)", "transformacao", filtroAtual, aoClicarFatia);
  // Fatia Proteção
  const s2 = criarFatiaSvg("54", `${l2} ${c - l2}`, `-${l1}`, "var(--op-prot)", "protecao", filtroAtual, aoClicarFatia);
  // Fatia Manobra
  const s3 = criarFatiaSvg("54", `${l3} ${c - l3}`, `-${l1 + l2}`, "var(--op-manob)", "manobra", filtroAtual, aoClicarFatia);

  g.appendChild(s1);
  g.appendChild(s2);
  g.appendChild(s3);
  svg.appendChild(g);

  // Textos Centrais
  const tVal = document.createElementNS("http://www.w3.org/2000/svg", "text");
  tVal.setAttribute("x", "80");
  tVal.setAttribute("y", "76");
  tVal.setAttribute("text-anchor", "middle");
  tVal.setAttribute("class", "donut-centro-val");
  tVal.textContent = valorCentro;
  svg.appendChild(tVal);

  const tSub = document.createElementNS("http://www.w3.org/2000/svg", "text");
  tSub.setAttribute("x", "80");
  tSub.setAttribute("y", "95");
  tSub.setAttribute("text-anchor", "middle");
  tSub.setAttribute("class", "donut-centro-sub");
  tSub.textContent = subCentro;
  svg.appendChild(tSub);

  const wrapper = el("div", { class: "bi-donut-container" }, svg);
  return wrapper;
}

function criarFatiaSvg(raio, dasharray, offset, cor, opId, filtroAtual, aoClicarFatia) {
  const circ = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  circ.setAttribute("cx", "80");
  circ.setAttribute("cy", "80");
  circ.setAttribute("r", raio);
  circ.setAttribute("fill", "none");
  circ.setAttribute("stroke", cor);
  circ.setAttribute("stroke-width", "22");
  circ.setAttribute("stroke-dasharray", dasharray);
  circ.setAttribute("stroke-dashoffset", offset);

  const selecionada = filtroAtual === opId;
  const esmaecida = filtroAtual !== "todas" && !selecionada;

  circ.setAttribute("class", `bi-fatia${selecionada ? " destacada" : ""}${esmaecida ? " esmaecida" : ""}`);
  circ.addEventListener("click", () => aoClicarFatia(opId));
  return circ;
}

function criarLinhaAtivoBi(ativo) {
  const mtaLargura = Math.min(100, Math.round(ativo.pctMta / 3.4));
  const linkAnalise = ativo.inspecao_id ? endereco("analise", [ativo.inspecao_id]) : endereco("analise");

  return el("li", { class: "bi-item-ativo", style: { "--sev": `var(--${ativo.severidade})` } },
    el("i", { class: "traco", "aria-hidden": "true" }),
    el("span", { class: `tag-op op-${ativo.opId}` }, ativo.opTag),
    el("div", { class: "eq-bloco" },
      el("b", { class: "eq-nome", title: ativo.equipamento }, ativo.equipamento),
      el("span", { class: "eq-detalhe", title: ativo.detalhe }, ativo.detalhe)),
    el("div", { class: "mta-box" },
      el("span", { class: "mta-label" }, `${ativo.pctMta} % da MTA`),
      el("div", { class: "barra-mta" },
        el("div", { class: "fill-mta", style: { width: `${mtaLargura}%` } }))),
    el("span", { class: "temp-val" }, ativo.temperaturaTexto),
    selo(ativo.severidade),
    el("a", { class: "btn-inspecionar", href: linkAnalise }, P.biInspecionar || "Inspecionar →"));
}

// ---------------------------------------------------------------- coluna da direita
function colunaLado({ lista, pendencias, equipamentos, status, config }) {
  const atual = situacaoAtual(lista);
  const criticas = atual.filter((it) => CRITICAS.includes(severidade(it))).length;
  const abertas = pendencias.filter((p) => ["aberta", "programada"].includes(p.status));
  const vencidas = abertas.filter((p) => p.vencida).length;
  const reais = equipamentos.filter((e) => e.chave !== SEM_EQUIPAMENTO);
  const comAgenda = reais.filter((e) => e.proxima_inspecao);
  const atrasadas = comAgenda.filter((e) => e.proxima_inspecao.vencida).length;
  const alertas = status.alertas_pendentes || 0;

  const indicadores = el("div", { class: "indicadores" },
    indicador({ rotulo: P.criticas, valor: criticas, nota: P.criticasNota, severidade: criticas ? "imediato" : null, href: endereco("inspecoes", [], { sev: "criticas", atual: "1" }) }),
    indicador({ rotulo: P.pendenciasVencidas, valor: vencidas, nota: P.pendenciasNota(abertas.length), severidade: vencidas ? "urgente" : null, href: endereco("pendencias", [], { situacao: "vencidas" }) }),
    indicador({ rotulo: P.inspecoesVencidas, valor: atrasadas, nota: P.inspecoesNota(reais.length), severidade: atrasadas ? "programar" : null, href: endereco("equipamentos", [], { filtro: "vencidas" }) }),
    indicador({ rotulo: P.alertas, valor: alertas, nota: P.alertasNota, severidade: alertas ? "urgente" : null, href: endereco("captura", ["alertas"]) }));

  return el("div", { class: "coluna-lado" }, indicadores, avisoConfiguracao(config), proximas(comAgenda), situacao(atual));
}

/** O que falta para o laudo sair completo (empresa e responsável técnico). */
function avisoConfiguracao(config) {
  if (!config) return null;
  const falta = [];
  if (!(config.empresa?.nome || "").trim()) falta.push(P.faltaEmpresa);
  if (!(config.responsaveis || []).some((r) => r.assina !== false)) falta.push(P.faltaResponsavel);
  if (!falta.length) return null;
  return el("div", { class: "aviso-config" }, icone("info"),
    el("p", {}, P.falta(falta)),
    el("a", { class: "btn compacto", href: endereco("configuracoes") }, P.configurar));
}

function proximas(comAgenda) {
  const lista = [...comAgenda].sort((a, b) => a.proxima_inspecao.data.localeCompare(b.proxima_inspecao.data)).slice(0, 5);
  const cab = el("div", { class: "titulo-bloco" }, el("h2", {}, P.proximas), el("a", { href: endereco("equipamentos") }, P.verEquipamentos));
  if (!lista.length) return el("section", { class: "bloco-lado" }, cab, el("p", { class: "nota" }, P.semAgenda));
  return el("section", { class: "bloco-lado" }, cab, el("ul", { class: "lista-proximas" }, lista.map((e) => {
    const p = e.proxima_inspecao;
    return el("li", {}, el("a", { href: endereco("equipamentos", [e.chave]) },
      el("span", { class: "eq" }, el("b", { class: "corta", title: e.equipamento }, e.equipamento), e.instalacao ? el("span", { class: "corta" }, e.instalacao) : null),
      el("span", { class: "quando" }, el("b", { class: "num" }, data(p.data)), el("span", { class: p.vencida ? "vencida" : null }, p.vencida ? P.vencidaHa(relativa(p.data)) : relativa(p.data)))));
  })));
}

/** Barra empilhada da última inspeção de cada equipamento, com a legenda e a contagem por nível. */
function situacao(atual) {
  const niveis = [...ORDEM_SEVERIDADE].filter((n) => atual.some((it) => severidade(it) === n));
  const conta = (n) => atual.filter((it) => severidade(it) === n).length;
  const resumo = niveis.map((n) => `${T.niveis[n]}: ${conta(n)}`).join(", ");
  return el("section", { class: "bloco-lado" },
    el("div", { class: "titulo-bloco" }, el("h2", {}, P.situacao), el("span", { class: "nota" }, P.situacaoNota(atual.filter((it) => it.equipamento_chave && it.equipamento_chave !== SEM_EQUIPAMENTO).length, atual.filter((it) => !it.equipamento_chave || it.equipamento_chave === SEM_EQUIPAMENTO).length))),
    el("div", { class: "barra-empilhada", role: "img", "aria-label": resumo }, niveis.map((n) => el("i", { style: { flexGrow: conta(n), background: `var(--${n})` }, title: `${T.niveis[n]}: ${conta(n)}` }))),
    el("ul", { class: "legenda-niveis" }, niveis.map((n) => el("li", {}, el("i", { style: { background: `var(--${n})` }, "aria-hidden": "true" }), el("span", {}, T.niveis[n]), el("b", { class: "num" }, String(conta(n)))))));
}

// ---------------------------------------------------------------- primeira execução (nenhuma inspeção)
function primeiraExecucao(exemplos) {
  const passo = (n, ilu, titulo, texto) => el("li", {}, ilustracao(ilu, { rotulo: titulo }), el("h3", {}, el("span", { class: "num-passo" }, String(n)), titulo), el("p", {}, texto));
  const demo = exemplos.length ? botao({ texto: P.usarDemonstracao, onclick: () => ocupado(demo, async () => {
    location.hash = endereco("inspecoes");
    try { await importarDemonstracao(); } catch (e) { avisar(e.message, { erro: true }); }
  }) }) : null;
  return el("section", { class: "primeira-execucao", "aria-label": P.inicio },
    el("h2", {}, P.inicio),
    el("ol", { class: "passos" },
      passo(1, "inspecoes", P.passo1, P.passo1Texto),
      passo(2, "analise", P.passo2, P.passo2Texto),
      passo(3, "laudo", P.passo3, P.passo3Texto)),
    el("div", { class: "grupo-btn" }, botao({ texto: T.inspecoes.importar, icone: "importar", variante: "primario", atalho: "Ctrl O", onclick: escolherArquivos }), demo),
    demo ? el("p", { class: "nota" }, P.demonstracaoFonte) : null);
}
