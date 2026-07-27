-- 4_indices_performance.sql
-- Etapa 1 do PLANO_MODERNIZACAO_GK.md — índices de filtro/agregação para as queries de
-- dashboard e alertas, compostos liderando com tenant_id (toda query de negócio já filtra
-- por ele primeiro, desde a migração multi-tenant).
--
-- Checado contra INFORMATION_SCHEMA.STATISTICS do banco real (lumob, MySQL 8.0.35) antes de
-- escrever este script — nenhum dos índices abaixo já existe (só PKs, FKs de
-- funcionário/cliente e uniques de negócio estavam presentes).
--
-- Aplicar manualmente, com backup prévio. Rollback: ver bloco DROP INDEX no final do arquivo.

-- B2 — dashboard de Obras (GROUP BY Status_Obra)
CREATE INDEX idx_obras_tenant_status
    ON obras (tenant_id, Status_Obra);

-- B2 — dashboard de Obras (SUM de contratos ativos)
CREATE INDEX idx_contratos_tenant_status
    ON contratos (tenant_id, Status_Contrato);

-- B2 — dashboard de Obras (SUM de medições pagas/aprovadas)
CREATE INDEX idx_medicoes_tenant_status
    ON medicoes (tenant_id, Status_Medicao);

-- B2 — dashboard de Obras (último avanço físico por obra, window function)
CREATE INDEX idx_avancos_fisicos_tenant_obra_data
    ON avancos_fisicos (tenant_id, ID_Obras, Data_Avanco DESC);

-- B3 — experiência a vencer (funcionários ativos por janela de Data_Admissao)
-- também cobre a contagem de headcount por status do dashboard de Pessoal
CREATE INDEX idx_funcionarios_tenant_status_admissao
    ON funcionarios (tenant_id, Status, Data_Admissao);

-- B4 — aniversariantes do mês. Índice funcional (MySQL 8.0.13+) casando com o predicado
-- existente `MONTH(Data_Nascimento) = %s` sem precisar reescrever a query nem adicionar
-- coluna gerada.
CREATE INDEX idx_func_documentos_tenant_mes_nascimento
    ON funcionarios_documentos (tenant_id, (MONTH(Data_Nascimento)));

-- documentos a vencer (CNH)
CREATE INDEX idx_func_documentos_tenant_cnh_validade
    ON funcionarios_documentos (tenant_id, Cnh_DataValidade);

-- alertas SSMA — ASOs a vencer
CREATE INDEX idx_asos_tenant_data_vencimento
    ON asos (tenant_id, Data_Vencimento);

-- próximas férias
CREATE INDEX idx_ferias_tenant_status_inicio_gozo
    ON ferias (tenant_id, Status_Ferias, Data_Inicio_Gozo);

-- dashboard SSMA (contagem por tipo/status/mês de incidentes-acidentes)
CREATE INDEX idx_incidentes_acidentes_tenant_tipo_status_data
    ON incidentes_acidentes (tenant_id, Tipo_Registro, Status_Registro, Data_Hora_Ocorrencia);

-- ----------------------------------------------------------------------------------------
-- Rollback (executar em caso de regressão de escrita ou problema inesperado):
-- ----------------------------------------------------------------------------------------
-- DROP INDEX idx_obras_tenant_status ON obras;
-- DROP INDEX idx_contratos_tenant_status ON contratos;
-- DROP INDEX idx_medicoes_tenant_status ON medicoes;
-- DROP INDEX idx_avancos_fisicos_tenant_obra_data ON avancos_fisicos;
-- DROP INDEX idx_funcionarios_tenant_status_admissao ON funcionarios;
-- DROP INDEX idx_func_documentos_tenant_mes_nascimento ON funcionarios_documentos;
-- DROP INDEX idx_func_documentos_tenant_cnh_validade ON funcionarios_documentos;
-- DROP INDEX idx_asos_tenant_data_vencimento ON asos;
-- DROP INDEX idx_ferias_tenant_status_inicio_gozo ON ferias;
-- DROP INDEX idx_incidentes_acidentes_tenant_tipo_status_data ON incidentes_acidentes;
