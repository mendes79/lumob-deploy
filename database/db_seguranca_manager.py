# Criado em 2025-06-30 - Mendes Gemini Pro
# database/db_seguranca_manager.py
# rev01 - migração pra TenantScopedManager (isolamento por tenant_id)

import mysql.connector
from datetime import datetime, date

from database.db_base import TenantScopedManager
from database.cache_ext import cache

class SegurancaManager(TenantScopedManager):

    def _dashboard_cache_key(self):
        return f"dash:seguranca:kpis:{self.tenant_id}"

    def _invalidate_dashboard_cache(self):
        cache.delete(self._dashboard_cache_key())

    def _format_date_fields(self, item):
        """
        Função auxiliar para converter campos de data em dicionários de resultados
        para objetos date ou None.
        """
        if item is None:
            return None

        date_fields_to_format = [
            'Data_Criacao', 'Data_Modificacao',
            'Data_Hora_Ocorrencia', # Incidentes_Acidentes (DATETIME)
            'Data_Fechamento', # Incidentes_Acidentes (DATE)
            'Data_Emissao', # ASOs (DATE)
            'Data_Vencimento', # ASOs (DATE)
            'Data_Hora_Inicio', # Treinamentos_Agendamentos (DATETIME)
            'Data_Hora_Fim', # Treinamentos_Agendamentos (DATETIME)
            'Data_Conclusao' # Treinamentos_Participantes (DATE)
        ]

        for key in date_fields_to_format:
            if key in item:
                value = item[key]
                if isinstance(value, str):
                    if not value.strip():
                        item[key] = None
                        continue
                    try:
                        # Tenta analisar como DATETIME completo primeiro
                        item[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            # Se falhar, tenta como DATE
                            item[key] = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            print(f"AVISO: Não foi possível converter a string de data '{value}' para objeto datetime/date para o campo '{key}'. Definindo como None.")
                            item[key] = None
                elif isinstance(value, date) and not isinstance(value, datetime):
                    # Se já for um objeto date, mantém como date
                    pass
                elif isinstance(value, datetime):
                    # Se for datetime, mantém como datetime
                    pass
                elif value is None:
                    item[key] = None

        return item

    # --- Métodos de Incidentes e Acidentes ---
    def get_all_incidentes_acidentes(self, search_tipo=None, search_status=None, search_obra_id=None, search_responsavel_matricula=None):
        """
        Retorna uma lista de todos os incidentes/acidentes, opcionalmente filtrada.
        """
        ia_clause, ia_param = self.tenant_clause('ia')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                ia.ID_Incidente_Acidente,
                ia.Tipo_Registro,
                ia.Data_Hora_Ocorrencia,
                ia.Local_Ocorrencia,
                ia.ID_Obras,
                ia.Descricao_Resumida,
                ia.Causas_Identificadas,
                ia.Acoes_Corretivas_Tomadas,
                ia.Acoes_Preventivas_Recomendadas,
                ia.Status_Registro,
                ia.Responsavel_Investigacao_Funcionario_Matricula,
                ia.Data_Fechamento,
                ia.Observacoes,
                o.Numero_Obra,
                o.Nome_Obra,
                f.Nome_Completo AS Nome_Responsavel_Investigacao,
                ia.Data_Criacao,
                ia.Data_Modificacao
            FROM
                incidentes_acidentes ia
            LEFT JOIN
                obras o ON ia.ID_Obras = o.ID_Obras
            LEFT JOIN
                funcionarios f ON ia.Responsavel_Investigacao_Funcionario_Matricula = f.Matricula AND {f_clause}
            WHERE {ia_clause}
        """
        params = [f_param, ia_param]

        if search_tipo:
            query += " AND ia.Tipo_Registro = %s"
            params.append(search_tipo)
        if search_status:
            query += " AND ia.Status_Registro = %s"
            params.append(search_status)
        if search_obra_id:
            query += " AND ia.ID_Obras = %s"
            params.append(search_obra_id)
        if search_responsavel_matricula:
            query += " AND ia.Responsavel_Investigacao_Funcionario_Matricula = %s"
            params.append(search_responsavel_matricula)

        query += " ORDER BY ia.Data_Hora_Ocorrencia DESC"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_incidente_acidente(self, tipo_registro, data_hora_ocorrencia, local_ocorrencia, id_obras, descricao_resumida, causas_identificadas, acoes_corretivas_tomadas, acoes_preventivas_recomendadas, status_registro, responsavel_investigacao_matricula, data_fechamento, observacoes):
        """
        Adiciona um novo registro de incidente/acidente.
        """
        query = """
            INSERT INTO incidentes_acidentes (
                tenant_id, Tipo_Registro, Data_Hora_Ocorrencia, Local_Ocorrencia, ID_Obras,
                Descricao_Resumida, Causas_Identificadas, Acoes_Corretivas_Tomadas,
                Acoes_Preventivas_Recomendadas, Status_Registro, Responsavel_Investigacao_Funcionario_Matricula,
                Data_Fechamento, Observacoes, Data_Criacao, Data_Modificacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (
            self.tenant_id, tipo_registro, data_hora_ocorrencia, local_ocorrencia, id_obras,
            descricao_resumida, causas_identificadas, acoes_corretivas_tomadas,
            acoes_preventivas_recomendadas, status_registro, responsavel_investigacao_matricula,
            data_fechamento, observacoes
        )
        result = self.db.execute_query(query, params, fetch_results=False)
        if result:
            self._invalidate_dashboard_cache()
        return result

    def get_incidente_acidente_by_id(self, incidente_id):
        """
        Retorna os dados de um incidente/acidente pelo ID.
        """
        ia_clause, ia_param = self.tenant_clause('ia')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                ia.ID_Incidente_Acidente,
                ia.Tipo_Registro,
                ia.Data_Hora_Ocorrencia,
                ia.Local_Ocorrencia,
                ia.ID_Obras,
                ia.Descricao_Resumida,
                ia.Causas_Identificadas,
                ia.Acoes_Corretivas_Tomadas,
                ia.Acoes_Preventivas_Recomendadas,
                ia.Status_Registro,
                ia.Responsavel_Investigacao_Funcionario_Matricula,
                ia.Data_Fechamento,
                ia.Observacoes,
                o.Numero_Obra,
                o.Nome_Obra,
                f.Nome_Completo AS Nome_Responsavel_Investigacao,
                ia.Data_Criacao,
                ia.Data_Modificacao
            FROM
                incidentes_acidentes ia
            LEFT JOIN
                obras o ON ia.ID_Obras = o.ID_Obras
            LEFT JOIN
                funcionarios f ON ia.Responsavel_Investigacao_Funcionario_Matricula = f.Matricula AND {f_clause}
            WHERE {ia_clause} AND ia.ID_Incidente_Acidente = %s
        """
        result = self.db.execute_query(query, (f_param, ia_param, incidente_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_incidente_acidente(self, incidente_id, tipo_registro, data_hora_ocorrencia, local_ocorrencia, id_obras, descricao_resumida, causas_identificadas, acoes_corretivas_tomadas, acoes_preventivas_recomendadas, status_registro, responsavel_investigacao_matricula, data_fechamento, observacoes):
        """
        Atualiza os dados de um registro de incidente/acidente existente.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE incidentes_acidentes
            SET
                Tipo_Registro = %s,
                Data_Hora_Ocorrencia = %s,
                Local_Ocorrencia = %s,
                ID_Obras = %s,
                Descricao_Resumida = %s,
                Causas_Identificadas = %s,
                Acoes_Corretivas_Tomadas = %s,
                Acoes_Preventivas_Recomendadas = %s,
                Status_Registro = %s,
                Responsavel_Investigacao_Funcionario_Matricula = %s,
                Data_Fechamento = %s,
                Observacoes = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Incidente_Acidente = %s
        """
        params = (
            tipo_registro, data_hora_ocorrencia, local_ocorrencia, id_obras,
            descricao_resumida, causas_identificadas, acoes_corretivas_tomadas,
            acoes_preventivas_recomendadas, status_registro, responsavel_investigacao_matricula,
            data_fechamento, observacoes, tenant_param, incidente_id
        )
        result = self.db.execute_query(query, params, fetch_results=False)
        if result:
            self._invalidate_dashboard_cache()
        return result

    def delete_incidente_acidente(self, incidente_id):
        """
        Exclui um registro de incidente/acidente do banco de dados.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM incidentes_acidentes WHERE {clause} AND ID_Incidente_Acidente = %s"
        result = self.db.execute_query(query, (tenant_param, incidente_id), fetch_results=False)
        if result:
            self._invalidate_dashboard_cache()
        return result

    # --- Métodos de ASOs ---
    def get_all_asos(self, search_matricula=None, search_tipo=None, search_resultado=None, search_data_emissao_inicio=None, search_data_emissao_fim=None):
        """
        Retorna uma lista de todos os ASOs, opcionalmente filtrada,
        incluindo informações do funcionário.
        """
        a_clause, a_param = self.tenant_clause('a')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                a.ID_ASO,
                a.Matricula_Funcionario,
                a.Tipo_ASO,
                a.Data_Emissao,
                a.Data_Vencimento,
                a.Resultado,
                a.Medico_Responsavel,
                a.Observacoes,
                f.Nome_Completo AS Nome_Funcionario,
                a.Data_Criacao,
                a.Data_Modificacao
            FROM
                asos a
            LEFT JOIN
                funcionarios f ON a.Matricula_Funcionario = f.Matricula AND {f_clause}
            WHERE {a_clause}
        """
        params = [f_param, a_param]

        if search_matricula:
            query += " AND a.Matricula_Funcionario LIKE %s"
            params.append(f"%{search_matricula}%")
        if search_tipo:
            query += " AND a.Tipo_ASO = %s"
            params.append(search_tipo)
        if search_resultado:
            query += " AND a.Resultado = %s"
            params.append(search_resultado)
        if search_data_emissao_inicio:
            query += " AND a.Data_Emissao >= %s"
            params.append(search_data_emissao_inicio)
        if search_data_emissao_fim:
            query += " AND a.Data_Emissao <= %s"
            params.append(search_data_emissao_fim)

        query += " ORDER BY a.Data_Emissao DESC, f.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_aso(self, matricula_funcionario, tipo_aso, data_emissao, data_vencimento, resultado, medico_responsavel, observacoes):
        """
        Adiciona um novo registro de ASO ao banco de dados.
        """
        query = """
            INSERT INTO asos (tenant_id, Matricula_Funcionario, Tipo_ASO, Data_Emissao, Data_Vencimento, Resultado, Medico_Responsavel, Observacoes, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, matricula_funcionario, tipo_aso, data_emissao, data_vencimento, resultado, medico_responsavel, observacoes)
        result = self.db.execute_query(query, params, fetch_results=False)
        if result:
            self._invalidate_dashboard_cache()
        return result

    def get_aso_by_id(self, aso_id):
        """
        Retorna os dados de um registro de ASO pelo ID.
        """
        a_clause, a_param = self.tenant_clause('a')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                a.ID_ASO,
                a.Matricula_Funcionario,
                a.Tipo_ASO,
                a.Data_Emissao,
                a.Data_Vencimento,
                a.Resultado,
                a.Medico_Responsavel,
                a.Observacoes,
                f.Nome_Completo AS Nome_Funcionario,
                a.Data_Criacao,
                a.Data_Modificacao
            FROM
                asos a
            LEFT JOIN
                funcionarios f ON a.Matricula_Funcionario = f.Matricula AND {f_clause}
            WHERE {a_clause} AND a.ID_ASO = %s
        """
        result = self.db.execute_query(query, (f_param, a_param, aso_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_aso(self, aso_id, matricula_funcionario, tipo_aso, data_emissao, data_vencimento, resultado, medico_responsavel, observacoes):
        """
        Atualiza os dados de um registro de ASO existente.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE asos
            SET
                Matricula_Funcionario = %s,
                Tipo_ASO = %s,
                Data_Emissao = %s,
                Data_Vencimento = %s,
                Resultado = %s,
                Medico_Responsavel = %s,
                Observacoes = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_ASO = %s
        """
        params = (matricula_funcionario, tipo_aso, data_emissao, data_vencimento, resultado, medico_responsavel, observacoes, tenant_param, aso_id)
        result = self.db.execute_query(query, params, fetch_results=False)
        if result:
            self._invalidate_dashboard_cache()
        return result

    def delete_aso(self, aso_id):
        """
        Exclui um registro de ASO do banco de dados.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM asos WHERE {clause} AND ID_ASO = %s"
        result = self.db.execute_query(query, (tenant_param, aso_id), fetch_results=False)
        if result:
            self._invalidate_dashboard_cache()
        return result

 # --- NOVOS MÉTODOS DE TREINAMENTOS (Catálogo) ---
    def get_all_treinamentos(self, search_nome=None, search_tipo=None):
        """
        Retorna uma lista de todos os tipos de treinamento, opcionalmente filtrada.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Treinamento,
                Nome_Treinamento,
                Descricao,
                Carga_Horaria_Horas,
                Tipo_Treinamento,
                Validade_Dias,
                Instrutor_Responsavel,
                Data_Criacao,
                Data_Modificacao
            FROM
                treinamentos
            WHERE {clause}
        """
        params = [tenant_param]

        if search_nome:
            query += " AND Nome_Treinamento LIKE %s"
            params.append(f"%{search_nome}%")
        if search_tipo:
            query += " AND Tipo_Treinamento = %s"
            params.append(search_tipo)

        query += " ORDER BY Nome_Treinamento"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_treinamento(self, nome_treinamento, descricao, carga_horaria_horas, tipo_treinamento, validade_dias, instrutor_responsavel):
        """
        Adiciona um novo tipo de treinamento ao catálogo.
        """
        query = """
            INSERT INTO treinamentos (tenant_id, Nome_Treinamento, Descricao, Carga_Horaria_Horas, Tipo_Treinamento, Validade_Dias, Instrutor_Responsavel, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, nome_treinamento, descricao, carga_horaria_horas, tipo_treinamento, validade_dias, instrutor_responsavel)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_treinamento_by_id(self, treinamento_id):
        """
        Retorna os dados de um tipo de treinamento pelo ID.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Treinamento,
                Nome_Treinamento,
                Descricao,
                Carga_Horaria_Horas,
                Tipo_Treinamento,
                Validade_Dias,
                Instrutor_Responsavel,
                Data_Criacao,
                Data_Modificacao
            FROM
                treinamentos
            WHERE {clause} AND ID_Treinamento = %s
        """
        result = self.db.execute_query(query, (tenant_param, treinamento_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_treinamento(self, treinamento_id, nome_treinamento, descricao, carga_horaria_horas, tipo_treinamento, validade_dias, instrutor_responsavel):
        """
        Atualiza os dados de um tipo de treinamento existente.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE treinamentos
            SET
                Nome_Treinamento = %s,
                Descricao = %s,
                Carga_Horaria_Horas = %s,
                Tipo_Treinamento = %s,
                Validade_Dias = %s,
                Instrutor_Responsavel = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Treinamento = %s
        """
        params = (nome_treinamento, descricao, carga_horaria_horas, tipo_treinamento, validade_dias, instrutor_responsavel, tenant_param, treinamento_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_treinamento(self, treinamento_id):
        """
        Exclui um tipo de treinamento do catálogo.
        Retorna False se houver agendamentos associados.
        """
        clause, tenant_param = self.tenant_clause()
        check_query = f"SELECT COUNT(*) AS count FROM treinamentos_agendamentos WHERE {clause} AND ID_Treinamento = %s"
        result = self.db.execute_query(check_query, (tenant_param, treinamento_id), fetch_results=True)
        if result and result[0]['count'] > 0:
            print(f"Não é possível excluir o treinamento ID {treinamento_id}: Existem agendamentos associados.")
            return False

        query = f"DELETE FROM treinamentos WHERE {clause} AND ID_Treinamento = %s"
        return self.db.execute_query(query, (tenant_param, treinamento_id), fetch_results=False)

    def get_treinamento_by_nome(self, nome_treinamento):
        """
        Verifica se um tipo de treinamento com o dado nome já existe.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Treinamento FROM treinamentos WHERE {clause} AND Nome_Treinamento = %s"
        result = self.db.execute_query(query, (tenant_param, nome_treinamento), fetch_results=True)
        return result[0] if result else None

    # --- NOVOS MÉTODOS DE AGENDAMENTOS DE TREINAMENTOS ---
    def get_all_treinamentos_agendamentos(self, search_treinamento_id=None, search_status=None, search_data_inicio=None, search_data_fim=None):
        """
        Retorna uma lista de todos os agendamentos de treinamentos, opcionalmente filtrada.
        """
        clause, tenant_param = self.tenant_clause('ta')
        query = f"""
            SELECT
                ta.ID_Agendamento,
                ta.ID_Treinamento,
                ta.Data_Hora_Inicio,
                ta.Data_Hora_Fim,
                ta.Local_Treinamento,
                ta.Status_Agendamento,
                ta.Observacoes,
                t.Nome_Treinamento,
                t.Tipo_Treinamento,
                ta.Data_Criacao,
                ta.Data_Modificacao
            FROM
                treinamentos_agendamentos ta
            LEFT JOIN
                treinamentos t ON ta.ID_Treinamento = t.ID_Treinamento
            WHERE {clause}
        """
        params = [tenant_param]

        if search_treinamento_id:
            query += " AND ta.ID_Treinamento = %s"
            params.append(search_treinamento_id)
        if search_status:
            query += " AND ta.Status_Agendamento = %s"
            params.append(search_status)
        if search_data_inicio:
            query += " AND ta.Data_Hora_Inicio >= %s"
            params.append(search_data_inicio)
        if search_data_fim:
            query += " AND ta.Data_Hora_Fim <= %s"
            params.append(search_data_fim)

        query += " ORDER BY ta.Data_Hora_Inicio DESC"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_treinamento_agendamento(self, id_treinamento, data_hora_inicio, data_hora_fim, local_treinamento, status_agendamento, observacoes):
        """
        Adiciona um novo agendamento de treinamento.
        """
        query = """
            INSERT INTO treinamentos_agendamentos (tenant_id, ID_Treinamento, Data_Hora_Inicio, Data_Hora_Fim, Local_Treinamento, Status_Agendamento, Observacoes, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_treinamento, data_hora_inicio, data_hora_fim, local_treinamento, status_agendamento, observacoes)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_treinamento_agendamento_by_id(self, agendamento_id):
        """
        Retorna os dados de um agendamento de treinamento pelo ID.
        """
        clause, tenant_param = self.tenant_clause('ta')
        query = f"""
            SELECT
                ta.ID_Agendamento,
                ta.ID_Treinamento,
                ta.Data_Hora_Inicio,
                ta.Data_Hora_Fim,
                ta.Local_Treinamento,
                ta.Status_Agendamento,
                ta.Observacoes,
                t.Nome_Treinamento,
                t.Tipo_Treinamento,
                ta.Data_Criacao,
                ta.Data_Modificacao
            FROM
                treinamentos_agendamentos ta
            LEFT JOIN
                treinamentos t ON ta.ID_Treinamento = t.ID_Treinamento
            WHERE {clause} AND ta.ID_Agendamento = %s
        """
        result = self.db.execute_query(query, (tenant_param, agendamento_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_treinamento_agendamento(self, agendamento_id, id_treinamento, data_hora_inicio, data_hora_fim, local_treinamento, status_agendamento, observacoes):
        """
        Atualiza os dados de um agendamento de treinamento existente.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE treinamentos_agendamentos
            SET
                ID_Treinamento = %s,
                Data_Hora_Inicio = %s,
                Data_Hora_Fim = %s,
                Local_Treinamento = %s,
                Status_Agendamento = %s,
                Observacoes = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Agendamento = %s
        """
        params = (id_treinamento, data_hora_inicio, data_hora_fim, local_treinamento, status_agendamento, observacoes, tenant_param, agendamento_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_treinamento_agendamento(self, agendamento_id):
        """
        Exclui um agendamento de treinamento.
        Retorna False se houver participantes associados.
        """
        clause, tenant_param = self.tenant_clause()
        check_query = f"SELECT COUNT(*) AS count FROM treinamentos_participantes WHERE {clause} AND ID_Agendamento = %s"
        result = self.db.execute_query(check_query, (tenant_param, agendamento_id), fetch_results=True)
        if result and result[0]['count'] > 0:
            print(f"Não é possível excluir o agendamento ID {agendamento_id}: Existem participantes associados.")
            return False

        query = f"DELETE FROM treinamentos_agendamentos WHERE {clause} AND ID_Agendamento = %s"
        return self.db.execute_query(query, (tenant_param, agendamento_id), fetch_results=False)

    # --- NOVOS MÉTODOS DE PARTICIPANTES DE TREINAMENTOS ---
    def get_all_treinamentos_participantes(self, search_agendamento_id=None, search_matricula=None, search_presenca=None):
        """
        Retorna uma lista de todos os participantes de treinamentos, opcionalmente filtrada.
        """
        tp_clause, tp_param = self.tenant_clause('tp')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                tp.ID_Participante,
                tp.ID_Agendamento,
                tp.Matricula_Funcionario,
                tp.Presenca,
                tp.Nota_Avaliacao,
                tp.Data_Conclusao,
                tp.Certificado_Emitido,
                ta.Data_Hora_Inicio,
                t.Nome_Treinamento,
                f.Nome_Completo AS Nome_Funcionario,
                tp.Data_Criacao,
                tp.Data_Modificacao
            FROM
                treinamentos_participantes tp
            LEFT JOIN
                treinamentos_agendamentos ta ON tp.ID_Agendamento = ta.ID_Agendamento
            LEFT JOIN
                treinamentos t ON ta.ID_Treinamento = t.ID_Treinamento
            LEFT JOIN
                funcionarios f ON tp.Matricula_Funcionario = f.Matricula AND {f_clause}
            WHERE {tp_clause}
        """
        params = [f_param, tp_param]

        if search_agendamento_id:
            query += " AND tp.ID_Agendamento = %s"
            params.append(search_agendamento_id)
        if search_matricula:
            query += " AND tp.Matricula_Funcionario LIKE %s"
            params.append(f"%{search_matricula}%")
        if search_presenca is not None: # Pode ser True ou False
            query += " AND tp.Presenca = %s"
            params.append(int(search_presenca)) # BOOLEAN em MySQL é 0 ou 1

        query += " ORDER BY ta.Data_Hora_Inicio DESC, f.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_treinamento_participante(self, id_agendamento, matricula_funcionario, presenca, nota_avaliacao, data_conclusao, certificado_emitido):
        """
        Adiciona um novo participante a um agendamento de treinamento.
        """
        query = """
            INSERT INTO treinamentos_participantes (tenant_id, ID_Agendamento, Matricula_Funcionario, Presenca, Nota_Avaliacao, Data_Conclusao, Certificado_Emitido, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_agendamento, matricula_funcionario, presenca, nota_avaliacao, data_conclusao, certificado_emitido)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_treinamento_participante_by_id(self, participante_id):
        """
        Retorna os dados de um participante de treinamento pelo ID.
        """
        tp_clause, tp_param = self.tenant_clause('tp')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                tp.ID_Participante,
                tp.ID_Agendamento,
                tp.Matricula_Funcionario,
                tp.Presenca,
                tp.Nota_Avaliacao,
                tp.Data_Conclusao,
                tp.Certificado_Emitido,
                ta.Data_Hora_Inicio,
                t.Nome_Treinamento,
                f.Nome_Completo AS Nome_Funcionario,
                tp.Data_Criacao,
                tp.Data_Modificacao
            FROM
                treinamentos_participantes tp
            LEFT JOIN
                treinamentos_agendamentos ta ON tp.ID_Agendamento = ta.ID_Agendamento
            LEFT JOIN
                treinamentos t ON ta.ID_Treinamento = t.ID_Treinamento
            LEFT JOIN
                funcionarios f ON tp.Matricula_Funcionario = f.Matricula AND {f_clause}
            WHERE {tp_clause} AND tp.ID_Participante = %s
        """
        result = self.db.execute_query(query, (f_param, tp_param, participante_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_treinamento_participante(self, participante_id, id_agendamento, matricula_funcionario, presenca, nota_avaliacao, data_conclusao, certificado_emitido):
        """
        Atualiza os dados de um participante de treinamento existente.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE treinamentos_participantes
            SET
                ID_Agendamento = %s,
                Matricula_Funcionario = %s,
                Presenca = %s,
                Nota_Avaliacao = %s,
                Data_Conclusao = %s,
                Certificado_Emitido = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Participante = %s
        """
        params = (id_agendamento, matricula_funcionario, presenca, nota_avaliacao, data_conclusao, certificado_emitido, tenant_param, participante_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_treinamento_participante(self, participante_id):
        """
        Exclui um participante de treinamento.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM treinamentos_participantes WHERE {clause} AND ID_Participante = %s"
        return self.db.execute_query(query, (tenant_param, participante_id), fetch_results=False)

    def get_participante_by_agendamento_funcionario(self, id_agendamento, matricula_funcionario, exclude_id=None):
        """
        Verifica se um funcionário já está registrado em um agendamento específico.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Participante FROM treinamentos_participantes WHERE {clause} AND ID_Agendamento = %s AND Matricula_Funcionario = %s"
        params = [tenant_param, id_agendamento, matricula_funcionario]
        if exclude_id:
            query += " AND ID_Participante != %s"
            params.append(exclude_id)
        result = self.db.execute_query(query, tuple(params), fetch_results=True)
        return result[0] if result else None

    # --- Métodos auxiliares para dropdowns (já devem existir ou serão adicionados) ---
    def get_all_obras_for_dropdown(self): # Do ObrasManager, mas pode ser útil aqui se não tiver o ObrasManager importado
        """Retorna uma lista de obras para preencher dropdowns."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Obras,
                Numero_Obra,
                Nome_Obra
            FROM
                obras
            WHERE {clause}
            ORDER BY Nome_Obra
        """
        return self.db.execute_query(query, (tenant_param,), fetch_results=True)

    def get_all_funcionarios_for_dropdown(self): # Do PessoalManager, mas pode ser útil aqui
        """Retorna uma lista de funcionários para preencher dropdowns."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT Matricula, Nome_Completo FROM funcionarios WHERE {clause} ORDER BY Nome_Completo"
        return self.db.execute_query(query, (tenant_param,), fetch_results=True)

    def get_all_treinamentos_for_dropdown(self):
        """Retorna uma lista de treinamentos para preencher dropdowns."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Treinamento, Nome_Treinamento FROM treinamentos WHERE {clause} ORDER BY Nome_Treinamento"
        return self.db.execute_query(query, (tenant_param,), fetch_results=True)

    def get_all_agendamentos_for_dropdown(self):
        """Retorna uma lista de agendamentos para preencher dropdowns."""
        clause, tenant_param = self.tenant_clause('ta')
        query = f"""
            SELECT
                ta.ID_Agendamento,
                ta.Data_Hora_Inicio,
                t.Nome_Treinamento
            FROM
                treinamentos_agendamentos ta
            JOIN
                treinamentos t ON ta.ID_Treinamento = t.ID_Treinamento
            WHERE {clause}
            ORDER BY ta.Data_Hora_Inicio DESC
        """
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        # Formatar a data/hora para o dropdown
        if results:
            for item in results:
                if item.get('Data_Hora_Inicio'):
                    item['Nome_Agendamento_Formatado'] = f"{item['Nome_Treinamento']} ({item['Data_Hora_Inicio'].strftime('%d/%m/%Y %H:%M')})"
                else:
                    item['Nome_Agendamento_Formatado'] = item['Nome_Treinamento']
        return results

    # ==================================================================================================================================
    # === MÉTODOS PARA DASHBOARD E RELATÓRIOS DE SEGURANÇA =============================================================================
    # ==================================================================================================================================

    def get_dashboard_kpis(self):
        """
        KPIs do dashboard de Segurança em 3 round-trips (antes eram 4 — o total geral era
        uma query redundante com a soma dos status), com cache por tenant (TTL 5 min,
        invalidado nas escritas de incidentes/acidentes e ASOs).
        """
        cached = cache.get(self._dashboard_cache_key())
        if cached is not None:
            return cached

        type_clause, type_param = self.tenant_clause()
        type_query = f"""
            SELECT Tipo_Registro, COUNT(ID_Incidente_Acidente) AS Count
            FROM incidentes_acidentes
            WHERE {type_clause}
            GROUP BY Tipo_Registro
            ORDER BY Tipo_Registro
        """
        type_counts = self.db.execute_query(type_query, (type_param,), fetch_results=True) or []

        status_clause, status_param = self.tenant_clause()
        status_query = f"""
            SELECT Status_Registro, COUNT(ID_Incidente_Acidente) AS Count
            FROM incidentes_acidentes
            WHERE {status_clause}
            GROUP BY Status_Registro
            ORDER BY Status_Registro
        """
        status_counts = self.db.execute_query(status_query, (status_param,), fetch_results=True) or []
        total_incidentes_acidentes = sum(item['Count'] for item in status_counts)

        month_clause, month_param = self.tenant_clause()
        month_query = f"""
            SELECT DATE_FORMAT(Data_Hora_Ocorrencia, '%Y-%m') AS AnoMes, COUNT(ID_Incidente_Acidente) AS Count
            FROM incidentes_acidentes
            WHERE {month_clause}
            GROUP BY AnoMes
            ORDER BY AnoMes
        """
        monthly_counts = self.db.execute_query(month_query, (month_param,), fetch_results=True) or []

        kpis = {
            'total_incidentes_acidentes': total_incidentes_acidentes,
            'type_counts': type_counts,
            'status_counts': status_counts,
            'monthly_counts': monthly_counts,
        }
        cache.set(self._dashboard_cache_key(), kpis, timeout=300)
        return kpis

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- NOVO MÉTODO: Dados para Relatório de Treinamentos de Segurança ----------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_treinamentos_para_relatorio(self, search_nome_treinamento=None, search_tipo_treinamento=None, search_status_agendamento=None, search_matricula_participante=None):
        """
        Retorna dados detalhados para o relatório de treinamentos, incluindo informações de agendamentos e participantes.
        LISTA APENAS TREINAMENTOS QUE POSSUEM AGENDAMENTOS OU PARTICIPANTES.
        Permite filtros por nome/tipo de treinamento, status do agendamento e matrícula do participante.
        """
        t_clause, t_param = self.tenant_clause('t')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                t.ID_Treinamento,
                t.Nome_Treinamento,
                t.Descricao,
                t.Carga_Horaria_Horas,
                t.Tipo_Treinamento,
                t.Validade_Dias,
                t.Instrutor_Responsavel,
                ta.ID_Agendamento,
                ta.Data_Hora_Inicio,
                ta.Data_Hora_Fim,
                ta.Local_Treinamento,
                ta.Status_Agendamento,
                tp.ID_Participante,
                tp.Matricula_Funcionario,
                f.Nome_Completo AS Nome_Participante,
                tp.Presenca,
                tp.Nota_Avaliacao,
                tp.Data_Conclusao,
                tp.Certificado_Emitido
            FROM
                treinamentos t
            INNER JOIN  -- ALTERADO DE LEFT JOIN PARA INNER JOIN AQUI
                treinamentos_agendamentos ta ON t.ID_Treinamento = ta.ID_Treinamento
            LEFT JOIN   -- MANTIDO LEFT JOIN para participantes, pois um agendamento pode não ter participantes ainda
                treinamentos_participantes tp ON ta.ID_Agendamento = tp.ID_Agendamento
            LEFT JOIN
                funcionarios f ON tp.Matricula_Funcionario = f.Matricula AND {f_clause}
            WHERE {t_clause}
        """
        params = [f_param, t_param]

        if search_nome_treinamento:
            query += " AND t.Nome_Treinamento LIKE %s"
            params.append(f"%{search_nome_treinamento}%")
        if search_tipo_treinamento:
            query += " AND t.Tipo_Treinamento = %s"
            params.append(search_tipo_treinamento)
        if search_status_agendamento:
            query += " AND ta.Status_Agendamento = %s"
            params.append(search_status_agendamento)
        if search_matricula_participante:
            query += " AND tp.Matricula_Funcionario = %s"
            params.append(search_matricula_participante)

        query += " ORDER BY t.Nome_Treinamento, ta.Data_Hora_Inicio DESC, f.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results
