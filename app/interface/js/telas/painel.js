// Painel: a tela de abertura responde, nesta ordem, "tem algo errado?", "por onde começo?" e "o que vem aí?".
// Em cima, os quatro números que pedem ação (cada um abre a lista já filtrada). Embaixo, à esquerda,
// "Atenção agora": a última inspeção de cada equipamento fora do normal, da pior para a melhor, com a
// tendência da máxima (o lado preditivo); à direita, a situação geral numa rosca por nível, que filtra a lista ao
// lado ao clicar em qualquer nível (filtro cruzado do Painel BI), e as próximas inspeções. Tudo vem dos dados
// reais; sem inspeção, a primeira execução em três passos.
import { TEXTOS as T } from "../../textos.js";
import { el, icone, api, relativa, data, temperatura } from "../base.js";
import { botao, selo, indicador, estadoVazio, avisar, ocupado } from "../componentes.js";
import { endereco } from "../rotas.js";
import { ilustracao } from "../ilustracoes.js";
import { escolherArquivos, importarDemonstracao } from "../importar.js";
import { seloTendencia, miniSerie } from "../grafico.js";
import { CRITICAS, ORDEM_SEVERIDADE, SEM_EQUIPAMENTO, quando, severidade, pesoSeveridade, situacaoAtual, leituraDestaque } from "../situacao.js";

const P = T.painel;
const FORA_DO_NORMAL = ["imediato", "urgente", "programar", "atencao"];
const horaMinuto = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

export async function montar(pagina) {
  let dados = await carregar();
  let nivel = null; // filtro cruzado: o nível escolhido na rosca da Situação atual filtra "Atenção agora"
  pagina.classList.add("tela-painel");
  desenhar();

  /** Escolher o mesmo nível de novo tira o filtro; o foco volta ao item da legenda. */
  function escolher(n) {
    nivel = nivel === n ? null : n;
    desenhar();
    pagina.querySelector(`button[data-nivel="${n}"]`)?.focus();
  }

  function desenhar() {
    const vazio = !dados.lista.length;
    const cab = el("header", { class: "cabecalho" },
      el("div", { class: "titulo" }, el("h1", {}, T.telas.painel),
        vazio ? null : el("p", { class: "meta" }, P.atualizado(horaMinuto.format(dados.em)))),
      vazio ? null : el("div", { class: "acoes" }, botao({ texto: T.inspecoes.importar, icone: "importar", variante: "primario", atalho: "Ctrl O", onclick: escolherArquivos })));
    if (vazio) { pagina.replaceChildren(cab, primeiraExecucao(dados.exemplos)); return; }
    const atual = situacaoAtual(dados.lista);
    if (nivel && !atual.some((it) => severidade(it) === nivel)) nivel = null; // o nível sumiu depois de atualizar
    pagina.replaceChildren(cab, indicadores(dados, atual),
      el("div", { class: "painel-grade" }, atencao(atual, dados.equipamentos, nivel, escolher), colunaLado(dados, atual, nivel, escolher)));
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
  return { lista, pendencias, equipamentos, status, config, exemplos, em: new Date() };
}

// ---------------------------------------------------------------- os quatro números que pedem ação
function indicadores({ pendencias, equipamentos, status }, atual) {
  const criticas = atual.filter((it) => CRITICAS.includes(severidade(it))).length;
  const abertas = pendencias.filter((p) => ["aberta", "programada"].includes(p.status));
  const vencidas = abertas.filter((p) => p.vencida).length;
  const reais = equipamentos.filter((e) => e.chave !== SEM_EQUIPAMENTO);
  const atrasadas = reais.filter((e) => e.proxima_inspecao?.vencida).length;
  const alertas = status.alertas_pendentes || 0;
  return el("div", { class: "indicadores-linha" },
    indicador({ rotulo: P.criticas, valor: criticas, nota: P.criticasNota, severidade: criticas ? "imediato" : null, href: endereco("inspecoes", [], { sev: "criticas", atual: "1" }) }),
    indicador({ rotulo: P.pendenciasVencidas, valor: vencidas, nota: P.pendenciasNota(abertas.length), severidade: vencidas ? "urgente" : null, href: endereco("pendencias", [], { situacao: "vencidas" }) }),
    indicador({ rotulo: P.inspecoesVencidas, valor: atrasadas, nota: P.inspecoesNota(reais.length), severidade: atrasadas ? "programar" : null, href: endereco("equipamentos", [], { filtro: "vencidas" }) }),
    indicador({ rotulo: P.alertas, valor: alertas, nota: P.alertasNota, severidade: alertas ? "urgente" : null, href: endereco("captura", ["alertas"]) }));
}

// ---------------------------------------------------------------- Atenção agora
function atencao(atual, equipamentos, nivel, escolher) {
  const porChave = new Map(equipamentos.map((e) => [e.chave, e]));
  const fora = atual
    .filter((it) => (nivel ? severidade(it) === nivel : FORA_DO_NORMAL.includes(severidade(it))))
    .sort((a, b) => pesoSeveridade(severidade(a)) - pesoSeveridade(severidade(b))
      || (b.destaque?.pct_mta ?? 0) - (a.destaque?.pct_mta ?? 0)
      || quando(b).localeCompare(quando(a)));
  const lado = nivel
    ? el("span", { class: "filtro-ativo" }, selo(nivel), botao({ texto: P.mostrarTodos, icone: "x", variante: "fantasma", compacto: true, onclick: () => escolher(nivel) }))
    : fora.length ? el("span", { class: "nota" }, P.atencaoOrdem) : null;
  // filtrada por Normal ou Sem medida, a lista deixa de ser de atenção: o título diz só o que ela mostra
  const nome = !nivel || FORA_DO_NORMAL.includes(nivel) ? P.atencao : P.equipamentosNoNivel;
  const titulo = el("div", { class: "titulo-bloco" },
    el("h2", {}, nome, fora.length ? el("span", { class: "qtd" }, String(fora.length)) : null), lado);
  const corpo = fora.length
    ? el("ul", { class: "lista-atencao" }, fora.map((it) => linhaAtencao(it, porChave.get(it.equipamento_chave))))
    : estadoVazio({ ilustracao: "pendencias", titulo: P.tudoNormal, texto: P.tudoNormalTexto });
  return el("section", { class: "coluna-atencao", "aria-label": nome }, titulo, corpo);
}

/** Uma linha: nome e onde está, a tendência da máxima (com o equipamento), a temperatura e o nível. */
function linhaAtencao(it, equipamento) {
  const id = it.identificacao || {};
  const d = it.destaque || {};
  const sev = severidade(it);
  const detalhe = [id.instalacao, d.nome, leituraDestaque(d), relativa(quando(it))].filter(Boolean).join(" · ");
  const serie = equipamento?.serie?.length > 1;
  return el("li", {}, el("a", { class: "linha-atencao", href: endereco("inspecoes", [it.id]), style: { "--sev": `var(--${sev})` } },
    el("i", { class: "traco", "aria-hidden": "true" }),
    el("span", { class: "eq" }, el("b", { class: "corta", title: id.equipamento || it.arquivo }, id.equipamento || it.arquivo), el("span", { class: "corta", title: detalhe }, detalhe)),
    el("span", { class: "tend" }, serie ? miniSerie(equipamento.serie) : null, serie ? seloTendencia(equipamento.tendencia) : null),
    el("b", { class: "temp num" }, temperatura(d.t_max ?? it.resumo?.t_max_cena)),
    selo(sev, { indicativa: Boolean(it.resumo?.conferir) })));
}

// ---------------------------------------------------------------- coluna da direita
function colunaLado({ equipamentos, config }, atual, nivel, escolher) {
  const comAgenda = equipamentos.filter((e) => e.chave !== SEM_EQUIPAMENTO && e.proxima_inspecao);
  return el("div", { class: "coluna-lado" }, avisoConfiguracao(config), situacao(atual, nivel, escolher), proximas(comAgenda));
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

/**
 * Rosca da última inspeção de cada equipamento por nível, com a legenda e a contagem (vinda do Painel BI).
 * Todo nível filtra a lista ao lado (filtro cruzado): pela fatia, com o mouse, ou pela legenda, que é o alvo de
 * teclado e de leitor de tela. No centro, quantos estão fora do normal ou no nível escolhido.
 */
function situacao(atual, nivel, escolher) {
  const conta = (n) => atual.filter((it) => severidade(it) === n).length;
  const niveis = [...ORDEM_SEVERIDADE].filter((n) => conta(n));
  const comEquipamento = atual.filter((it) => it.equipamento_chave && it.equipamento_chave !== SEM_EQUIPAMENTO).length;
  const fora = atual.filter((it) => FORA_DO_NORMAL.includes(severidade(it))).length;
  const [valor, rotulo] = nivel ? [conta(nivel), T.niveis[nivel]] : [fora, P.foraDoNormal];

  const item = (n) => el("li", {}, el("button", { type: "button", class: "item-nivel", "data-nivel": n, "aria-pressed": String(nivel === n), title: P.filtrarNivel(T.niveis[n]), onclick: () => escolher(n) },
    el("i", { style: { background: `var(--${n})` }, "aria-hidden": "true" }), el("span", {}, T.niveis[n]), el("b", { class: "num" }, String(conta(n)))));
  return el("section", { class: "bloco-lado" },
    el("div", { class: "titulo-bloco" }, el("h2", {}, P.situacao), el("span", { class: "nota" }, P.situacaoNota(comEquipamento, atual.length - comEquipamento))),
    el("div", { class: "rosca-bloco" },
      el("div", { class: "rosca" }, rosca(niveis.map((n) => ({ nivel: n, qtd: conta(n) })), atual.length, nivel, escolher),
        el("div", { class: "centro-rosca", "aria-live": "polite" }, el("b", {}, String(valor)), el("span", {}, rotulo))),
      el("ul", { class: "legenda-niveis", "aria-label": P.legendaNiveis }, niveis.map(item))));
}

const SVG = "http://www.w3.org/2000/svg";
const circulo = (attrs) => {
  const c = document.createElementNS(SVG, "circle");
  for (const [k, v] of Object.entries({ cx: 60, cy: 60, r: 48, ...attrs })) c.setAttribute(k, String(v));
  return c;
};

/** Anel em SVG: uma fatia por nível, com uma folga entre elas; as outras esmaecem quando há nível escolhido. */
function rosca(fatias, total, nivel, escolher) {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 120 120");
  svg.setAttribute("aria-hidden", "true");
  svg.append(circulo({ class: "fundo-rosca" }));
  const volta = 2 * Math.PI * 48;
  const folga = fatias.length > 1 ? 2 : 0;
  let inicio = 0;
  for (const f of fatias) {
    const tamanho = total ? (f.qtd / total) * volta : 0;
    const classe = ["fatia", nivel === f.nivel && "escolhida", nivel && nivel !== f.nivel && "esmaecida"].filter(Boolean).join(" ");
    const c = circulo({ class: classe, style: `stroke: var(--${f.nivel})`, "stroke-dasharray": `${Math.max(tamanho - folga, 0)} ${volta}`, "stroke-dashoffset": -inicio });
    c.dataset.nivel = f.nivel;
    c.addEventListener("click", () => escolher(f.nivel));
    svg.append(c);
    inicio += tamanho;
  }
  return svg;
}

function proximas(comAgenda) {
  const lista = [...comAgenda].sort((a, b) => a.proxima_inspecao.data.localeCompare(b.proxima_inspecao.data)).slice(0, 3);
  const cab = el("div", { class: "titulo-bloco" }, el("h2", {}, P.proximas), el("a", { href: endereco("equipamentos") }, P.verEquipamentos));
  if (!lista.length) return el("section", { class: "bloco-lado" }, cab, el("p", { class: "nota" }, P.semAgenda));
  return el("section", { class: "bloco-lado" }, cab, el("ul", { class: "lista-proximas" }, lista.map((e) => {
    const p = e.proxima_inspecao;
    return el("li", {}, el("a", { href: endereco("equipamentos", [e.chave]) },
      el("span", { class: "eq" }, el("b", { class: "corta", title: e.equipamento }, e.equipamento), e.instalacao ? el("span", { class: "corta" }, e.instalacao) : null),
      el("span", { class: "quando" }, el("b", { class: "num" }, data(p.data)), el("span", { class: p.vencida ? "vencida" : null }, p.vencida ? P.vencidaHa(relativa(p.data)) : relativa(p.data)))));
  })));
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
