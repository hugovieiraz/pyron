-- =============================================================================
-- PYRON: VIEWS ESTRATÉGICAS E MODELO STAR SCHEMA PARA POWER BI / TABLEAU / GRAFANA
-- Compatível com: PostgreSQL 14+ (com casts explícitos ::text para DirectQuery no Power BI)
-- Ferramentas compatíveis: Power BI Desktop (Gratuito), Metabase (Open Source), Grafana,
--                          Tableau, Apache Superset, DBeaver, Google Looker Studio
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. VIEW LOGÍSTICA E COMPRAS: Planejamento de aquisição de peças e cronograma de reparo
-- Informa: Equipamento, Subestação, Peça em falha, Severidade, Data Limite da Parada,
--          Ordem de Serviço (OS), Faixa de Aquisição (Lead Time) e Prioridade de Compra.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_logistica_suprimentos_reparos AS
SELECT
    p.id AS pendencia_id,
    p.status::text AS status_manutencao,
    p.ordem_servico_codigo AS ordem_servico,
    i.nome AS subestacao_instalacao,
    i.codigo_instalacao,
    e.nome AS equipamento,
    e.tag_codigo,
    e.tipo_equipamento,
    COALESCE(c.nome_exibicao, p.regiao_afetada, 'Componente Geral') AS peca_a_reparar_substituir,
    c.tipo_aquecimento,
    p.severidade::text AS severidade,
    p.t_max_detectada_c,
    COALESCE(it.mta_aplicada_c, c.mta_padrao_c) AS mta_padrao_c,
    COALESCE(
        it.maior_pct_mta,
        ROUND(((p.t_max_detectada_c / NULLIF(COALESCE(it.mta_aplicada_c, c.mta_padrao_c), 0)) * 100)::numeric, 1)
    ) AS pct_mta_atingido,
    p.detectada_em::date AS data_deteccao,
    p.data_limite,
    (p.data_limite - CURRENT_DATE) AS dias_restantes_para_reparo,
    CASE 
        WHEN p.data_limite < CURRENT_DATE THEN 'VENCIDO - PARADA URGENTE'
        WHEN (p.data_limite - CURRENT_DATE) <= 7 THEN 'CRÍTICO - REQUER COMPRA IMEDIATA (ATÉ 7 DIAS)'
        WHEN (p.data_limite - CURRENT_DATE) <= 30 THEN 'PROGRAMAR COMPRA (PRÓXIMOS 30 DIAS)'
        WHEN (p.data_limite - CURRENT_DATE) <= 60 THEN 'PLANEJAMENTO TRIMESTRAL (31-60 DIAS)'
        ELSE 'ROTINA PREVENTIVA (> 60 DIAS)'
    END AS janela_logistica_prioridade,
    p.responsavel_nome AS equipe_responsavel,
    p.nota_tecnica
FROM pendencias_manutencao p
JOIN instalacoes i ON i.id = p.instalacao_id
JOIN equipamentos e ON e.id = p.equipamento_id
LEFT JOIN inspecoes_termograficas it ON it.id = p.inspecao_origem_id
LEFT JOIN deteccoes_regioes dr ON dr.inspecao_id = it.id AND dr.severidade_regiao = p.severidade
LEFT JOIN catalogo_tipos_componente c ON c.codigo_classe = dr.classe_componente
WHERE p.status IN ('aberta', 'programada')
ORDER BY p.data_limite ASC, p.t_max_detectada_c DESC;


-- -----------------------------------------------------------------------------
-- 2. VIEW DEMANDA DE PEÇAS E SOBRESSALENTES: Matriz para Compras e Estoque
-- Agrupa quantas peças de cada tipo precisam ser adquiridas por mês/trimestre
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_demanda_compras_pecas AS
SELECT
    COALESCE(c.nome_exibicao, 'Sobressalente Geral') AS tipo_peca_material,
    c.tipo_aquecimento,
    COUNT(p.id) AS total_pecas_necessarias,
    COUNT(CASE WHEN p.data_limite <= (CURRENT_DATE + INTERVAL '7 days') THEN 1 END) AS demanda_imediata_7d,
    COUNT(CASE WHEN p.data_limite > (CURRENT_DATE + INTERVAL '7 days') AND p.data_limite <= (CURRENT_DATE + INTERVAL '30 days') THEN 1 END) AS demanda_curto_prazo_30d,
    COUNT(CASE WHEN p.data_limite > (CURRENT_DATE + INTERVAL '30 days') THEN 1 END) AS demanda_medio_prazo,
    STRING_AGG(DISTINCT i.nome, ', ') AS subestacoes_destinatarias
FROM pendencias_manutencao p
JOIN instalacoes i ON i.id = p.instalacao_id
LEFT JOIN inspecoes_termograficas it ON it.id = p.inspecao_origem_id
LEFT JOIN deteccoes_regioes dr ON dr.inspecao_id = it.id AND dr.severidade_regiao = p.severidade
LEFT JOIN catalogo_tipos_componente c ON c.codigo_classe = dr.classe_componente
WHERE p.status IN ('aberta', 'programada')
GROUP BY c.nome_exibicao, c.tipo_aquecimento
ORDER BY total_pecas_necessarias DESC;


-- -----------------------------------------------------------------------------
-- 3. VIEW GESTÃO DE ENGENHARIA: Saúde dos Ativos e Risco Operacional
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_engenharia_saude_ativos AS
SELECT
    i.nome AS instalacao,
    e.nome AS equipamento,
    e.tipo_equipamento,
    COUNT(it.id) AS total_inspecoes,
    MAX(it.capturado_em) AS data_ultima_inspecao,
    MAX(it.t_max_cena_c) AS pico_temperatura_historico_c,
    MAX(it.delta_t_global_c) AS max_delta_t_registrado_c,
    (ARRAY_AGG(it.severidade::text ORDER BY it.capturado_em DESC))[1] AS severidade_estado_atual,
    COUNT(CASE WHEN p.status = 'aberta' THEN 1 END) AS pendencias_abertas,
    COUNT(CASE WHEN p.status = 'programada' THEN 1 END) AS pendencias_em_ordem_servico,
    COUNT(CASE WHEN p.status = 'corrigida' THEN 1 END) AS reparos_aguardando_reinspecao
FROM equipamentos e
JOIN instalacoes i ON i.id = e.instalacao_id
LEFT JOIN inspecoes_termograficas it ON it.equipamento_id = e.id
LEFT JOIN pendencias_manutencao p ON p.equipamento_id = e.id
GROUP BY i.nome, e.nome, e.tipo_equipamento
ORDER BY pico_temperatura_historico_c DESC NULLS LAST;


-- -----------------------------------------------------------------------------
-- 4. VIEW INDICADORES ESTRATÉGICOS (KPIs GERAIS)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_kpis_estrategicos_diretoria AS
SELECT
    (SELECT COUNT(*) FROM instalacoes) AS total_subestacoes_ativas,
    (SELECT COUNT(*) FROM equipamentos) AS total_ativos_monitorados,
    (SELECT COUNT(*) FROM inspecoes_termograficas) AS total_inspecoes_realizadas,
    (SELECT COUNT(*) FROM pendencias_manutencao WHERE status IN ('aberta', 'programada')) AS total_reparos_pendentes,
    (SELECT COUNT(*) FROM pendencias_manutencao WHERE status IN ('aberta', 'programada') AND data_limite < CURRENT_DATE) AS reparos_vencidos,
    (SELECT COUNT(*) FROM pendencias_manutencao WHERE status IN ('aberta', 'programada') AND (data_limite - CURRENT_DATE) <= 7) AS reparos_urgencia_7_dias,
    (SELECT COUNT(*) FROM alertas WHERE status = 'pendente') AS alertas_nao_atendidos;


-- =============================================================================
-- 5. CAMADA SEMÂNTICA STAR SCHEMA (MODELO DIMENSIONAL PARA POWER BI / TABLEAU)
-- Relacionamentos recomendados no Power BI:
--   vw_dim_ativos[equipamento_id] 1 ---> * vw_fato_inspecoes[equipamento_id]
--   vw_dim_ativos[equipamento_id] 1 ---> * vw_fato_pendencias[equipamento_id]
--   vw_fato_inspecoes[inspecao_id] 1 ---> * vw_fato_deteccoes[inspecao_id]
--   vw_dim_componentes[codigo_classe] 1 ---> * vw_fato_deteccoes[classe_componente]
-- =============================================================================

CREATE OR REPLACE VIEW vw_dim_ativos AS
SELECT
    e.id AS equipamento_id,
    e.tag_codigo AS equipamento_chave,
    e.nome AS equipamento_nome,
    e.tipo_equipamento,
    e.fabricante,
    e.modelo_fabricante,
    e.fase,
    e.tensao_nominal_kv,
    e.corrente_nominal_a,
    e.ativo,
    i.id AS instalacao_id,
    i.codigo_instalacao AS instalacao_chave,
    i.nome AS instalacao_nome,
    i.subestacao,
    i.setor,
    i.ambiente,
    i.latitude,
    i.longitude
FROM equipamentos e
JOIN instalacoes i ON i.id = e.instalacao_id;


CREATE OR REPLACE VIEW vw_dim_componentes AS
SELECT
    c.codigo_classe,
    c.nome_exibicao,
    c.tipo_aquecimento,
    c.mta_padrao_c,
    c.fonte
FROM catalogo_tipos_componente c;


CREATE OR REPLACE VIEW vw_fato_inspecoes AS
SELECT
    it.id AS inspecao_id,
    it.codigo_legado,
    it.instalacao_id,
    it.equipamento_id,
    it.capturado_em,
    it.capturado_em::date AS data_calendario,
    it.criado_em,
    it.origem_captura AS fonte,
    COALESCE(it.radiometrica, TRUE) AS radiometrica,
    it.arquivo_original_nome,
    it.t_min_cena_c,
    it.t_max_cena_c,
    it.t_media_cena_c,
    it.ambiente_c,
    it.carga_pct,
    it.delta_t_global_c,
    it.mta_aplicada_c,
    it.maior_pct_mta,
    it.severidade::text AS severidade,
    CASE it.severidade::text
        WHEN 'imediato' THEN 5
        WHEN 'urgente' THEN 4
        WHEN 'programar' THEN 3
        WHEN 'atencao' THEN 2
        WHEN 'normal' THEN 1
        ELSE 0
    END AS severidade_ordem,
    pr.modelo_camera AS camera,
    pr.emissividade,
    pr.distancia_m,
    pr.temp_refletida_c,
    pr.umidade_relativa,
    it.imagem_termica_uri,
    '/api/analises/' || COALESCE(it.codigo_legado, it.id::text) || '/miniatura.png' AS miniatura_api_url,
    '/api/analises/' || COALESCE(it.codigo_legado, it.id::text) || '/imagem.png' AS termograma_api_url
FROM inspecoes_termograficas it
LEFT JOIN parametros_radiometricos_flir pr ON pr.inspecao_id = it.id;


CREATE OR REPLACE VIEW vw_fato_deteccoes AS
SELECT
    dr.id AS deteccao_id,
    dr.inspecao_id,
    it.equipamento_id,
    it.instalacao_id,
    it.capturado_em,
    it.capturado_em::date AS data_calendario,
    dr.indice_regiao,
    dr.classe_componente,
    dr.rotulo_regiao,
    dr.confianca_ml,
    dr.bbox_x_min,
    dr.bbox_y_min,
    dr.bbox_x_max,
    dr.bbox_y_max,
    dr.t_min_c,
    dr.t_max_c,
    dr.t_media_c,
    dr.delta_t_regiao_c,
    dr.pct_mta_regiao,
    dr.hotspot_x,
    dr.hotspot_y,
    dr.severidade_regiao::text AS severidade_regiao
FROM deteccoes_regioes dr
JOIN inspecoes_termograficas it ON it.id = dr.inspecao_id;


CREATE OR REPLACE VIEW vw_fato_pendencias AS
SELECT
    p.id AS pendencia_id,
    p.inspecao_origem_id AS inspecao_id,
    p.instalacao_id,
    p.equipamento_id,
    p.severidade::text AS severidade,
    p.status::text AS status,
    p.regiao_afetada,
    p.t_max_detectada_c,
    p.detectada_em,
    p.detectada_em::date AS data_deteccao,
    p.data_limite,
    p.prazo_padrao,
    (p.data_limite - CURRENT_DATE) AS dias_para_vencimento,
    (p.status IN ('aberta', 'programada') AND p.data_limite < CURRENT_DATE) AS vencida,
    p.ordem_servico_codigo AS ordem_servico,
    p.responsavel_nome AS responsavel,
    p.nota_tecnica
FROM pendencias_manutencao p;
