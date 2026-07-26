# database/db_obras_manager.py

import mysql.connector
from datetime import datetime, date

from database.db_base import TenantScopedManager

class ObrasManager(TenantScopedManager):

    def _format_date_fields(self, item):
        """
        Função auxiliar para converter campos de data em dicionários de resultados
        para objetos date ou None.
        Isso garante que o template não tente chamar .strftime() em strings.
        """
        if item is None:
            return None

        # Lista abrangente de todos os nomes de colunas que podem armazenar datas/datetimes
        # em todas as tabelas gerenciadas por esta classe, e que serão exibidos nos templates.
        date_fields_to_format = [
            'Data_Criacao', 'Data_Modificacao', # Comuns em quase todas as tabelas
            'Data_Inicio_Prevista', 'Data_Fim_Prevista', # Obras
            'Data_Assinatura', 'Data_Ordem_Inicio', 'Data_Termino_Previsto', # Contratos
            'Data_Pagamento', # Arts
            'Data_Medicao', 'Data_Aprovacao', # Medicoes
            'Data_Avanco', # Avancos_Fisicos
            'Data_Aprovacao_Reidi', 'Data_Validade_Reidi', # Reidis
            'Data_Inicio_Vigencia', 'Data_Fim_Vigencia' # Seguros
            # CRÍTICO: 'Valor_Obra' e 'Valor_Aditivo_Total' NÃO PODEM ESTAR AQUI!
            # Remova-os se estiverem.
        ]

        for key in date_fields_to_format:
            if key in item:
                value = item[key]
                if isinstance(value, str):
                    if not value.strip(): # Se for string vazia ou só espaços, trate como None
                        item[key] = None
                        continue # Pula para o próximo campo
                    try:
                        # Tenta analisar como data (AAAA-MM-DD)
                        item[key] = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # Se falhar, tenta analisar como datetime completo e pega a data
                            item[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').date()
                        except ValueError:
                            # Se ainda assim falhar, define como None e loga um aviso
                            print(f"AVISO: Não foi possível converter a string de data '{value}' para objeto date para o campo '{key}'. Definindo como None.")
                            item[key] = None

                # Se o valor já for um objeto datetime, converte para date para consistência
                elif isinstance(value, datetime):
                    item[key] = value.date()

                # Se o valor já for None, não faz nada
                elif value is None:
                    item[key] = None # Garante explicitamente que é None

        return item
    # --- Métodos OBRAS ---
    def get_all_obras(self, search_numero=None, search_nome=None, search_status=None, search_cliente_id=None):
        c_clause, c_param = self.tenant_clause('c')
        cl_clause, cl_param = self.tenant_clause('cl')
        o_clause, o_param = self.tenant_clause('o')
        query = f"""
            SELECT
                o.ID_Obras,
                o.ID_Contratos,
                o.Numero_Obra,
                o.Nome_Obra,
                o.Endereco_Obra,
                o.Escopo_Obra,
                o.Valor_Obra,
                o.Valor_Aditivo_Total,
                o.Status_Obra,
                o.Data_Inicio_Prevista,
                o.Data_Fim_Prevista,
                c.Numero_Contrato,
                cl.Nome_Cliente,
                o.Data_Criacao,
                o.Data_Modificacao
            FROM
                obras o
            LEFT JOIN
                contratos c ON o.ID_Contratos = c.ID_Contratos AND {c_clause}
            LEFT JOIN
                clientes cl ON c.ID_Clientes = cl.ID_Clientes AND {cl_clause}
            WHERE {o_clause}
        """
        params = [c_param, cl_param, o_param]

        if search_numero:
            query += " AND o.Numero_Obra LIKE %s"
            params.append(f"%{search_numero}%")
        if search_nome:
            query += " AND o.Nome_Obra LIKE %s"
            params.append(f"%{search_nome}%")
        if search_status:
            query += " AND o.Status_Obra = %s"
            params.append(search_status)
        if search_cliente_id:
            query += " AND cl.ID_Clientes = %s"
            params.append(search_cliente_id)

        query += " ORDER BY o.Nome_Obra"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_obra(self, id_contratos, numero_obra, nome_obra, endereco_obra, escopo_obra, valor_obra, valor_aditivo_total, status_obra, data_inicio_prevista, data_fim_prevista):
        query = """
            INSERT INTO obras (tenant_id, ID_Contratos, Numero_Obra, Nome_Obra, Endereco_Obra, Escopo_Obra, Valor_Obra, Valor_Aditivo_Total, Status_Obra, Data_Inicio_Prevista, Data_Fim_Prevista, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_contratos, numero_obra, nome_obra, endereco_obra, escopo_obra, valor_obra, valor_aditivo_total, status_obra, data_inicio_prevista, data_fim_prevista)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_obra_by_id(self, obra_id):
        c_clause, c_param = self.tenant_clause('c')
        cl_clause, cl_param = self.tenant_clause('cl')
        o_clause, o_param = self.tenant_clause('o')
        query = f"""
            SELECT
                o.ID_Obras,
                o.ID_Contratos,
                o.Numero_Obra,
                o.Nome_Obra,
                o.Endereco_Obra,
                o.Escopo_Obra,
                o.Valor_Obra,          -- O campo problemático
                o.Valor_Aditivo_Total, -- O campo problemático
                o.Status_Obra,
                o.Data_Inicio_Prevista,
                o.Data_Fim_Prevista,
                c.Numero_Contrato,
                cl.Nome_Cliente,
                o.Data_Criacao,
                o.Data_Modificacao
            FROM
                obras o
            LEFT JOIN
                contratos c ON o.ID_Contratos = c.ID_Contratos AND {c_clause}
            LEFT JOIN
                clientes cl ON c.ID_Clientes = cl.ID_Clientes AND {cl_clause}
            WHERE {o_clause} AND o.ID_Obras = %s
        """
        result = self.db.execute_query(query, (c_param, cl_param, o_param, obra_id), fetch_results=True)
        if result:
            item = result[0] # Pega o dicionário de resultado da query

            # --- DEBUG PRINTS AQUI ---
            print(f"DEBUG DB_OBRAS_MANAGER: Obra ID: {obra_id}")
            print(f"DEBUG DB_OBRAS_MANAGER: Valor_Obra - Tipo: {type(item.get('Valor_Obra'))}, Valor: {item.get('Valor_Obra')}")
            print(f"DEBUG DB_OBRAS_MANAGER: Valor_Aditivo_Total - Tipo: {type(item.get('Valor_Aditivo_Total'))}, Valor: {item.get('Valor_Aditivo_Total')}")
            # --- FIM DEBUG PRINTS ---

            # --- TRATAMENTO EXPLÍCITO DE DECIMAIS PARA FLOAT AQUI NO MANAGER ---
            # O mysql.connector pode retornar DECIMAL como Decimal (do módulo decimal)
            # ou como string se o modo SQL for especial.
            for key in ['Valor_Obra', 'Valor_Aditivo_Total']:
                value = item.get(key)
                if value is not None:
                    try:
                        # Converte para float explicitamente para garantir o tipo para o Blueprint
                        item[key] = float(value)
                    except (ValueError, TypeError):
                        # Se não puder ser float, define como None.
                        # Isso deve evitar o erro 'must be real number, not str' no Blueprint
                        item[key] = None
            # --- FIM DO TRATAMENTO ---

            return self._format_date_fields(item) # Formata as datas por último
        return None


    def update_obra(self, obra_id, id_contratos, numero_obra, nome_obra, endereco_obra, escopo_obra, valor_obra, valor_aditivo_total, status_obra, data_inicio_prevista, data_fim_prevista):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE obras
            SET
                ID_Contratos = %s,
                Numero_Obra = %s,
                Nome_Obra = %s,
                Endereco_Obra = %s,
                Escopo_Obra = %s,
                Valor_Obra = %s,
                Valor_Aditivo_Total = %s,
                Status_Obra = %s,
                Data_Inicio_Prevista = %s,
                Data_Fim_Prevista = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Obras = %s
        """
        params = (id_contratos, numero_obra, nome_obra, endereco_obra, escopo_obra, valor_obra, valor_aditivo_total, status_obra, data_inicio_prevista, data_fim_prevista, tenant_param, obra_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_obra(self, obra_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM obras WHERE {clause} AND ID_Obras = %s"
        return self.db.execute_query(query, (tenant_param, obra_id), fetch_results=False)

    def get_obra_by_numero(self, numero_obra):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Obras FROM obras WHERE {clause} AND Numero_Obra = %s"
        result = self.db.execute_query(query, (tenant_param, numero_obra), fetch_results=True)
        return result[0] if result else None

    def get_all_obras_for_dropdown(self):
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

    def get_all_contratos_for_dropdown(self):
        cl_clause, cl_param = self.tenant_clause('cl')
        c_clause, c_param = self.tenant_clause('c')
        query = f"""
            SELECT
                c.ID_Contratos,
                c.Numero_Contrato,
                cl.Nome_Cliente
            FROM
                contratos c
            JOIN
                clientes cl ON c.ID_Clientes = cl.ID_Clientes AND {cl_clause}
            WHERE {c_clause}
            ORDER BY c.Numero_Contrato
        """
        return self.db.execute_query(query, (cl_param, c_param), fetch_results=True)


    # --- Métodos CLIENTES ---
    def get_all_clientes(self, search_nome=None, search_cnpj=None):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Clientes,
                Nome_Cliente,
                CNPJ_Cliente,
                Razao_Social_Cliente,
                Endereco_Cliente,
                Telefone_Cliente,
                Email_Cliente,
                Contato_Principal_Nome,
                Data_Criacao,
                Data_Modificacao
            FROM
                clientes
            WHERE {clause}
        """
        params = [tenant_param]

        if search_nome:
            query += " AND Nome_Cliente LIKE %s"
            params.append(f"%{search_nome}%")
        if search_cnpj:
            query += " AND CNPJ_Cliente LIKE %s"
            params.append(f"%{search_cnpj}%")

        query += " ORDER BY Nome_Cliente"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results


    def add_cliente(self, nome_cliente, cnpj_cliente, razao_social_cliente, endereco_cliente, telefone_cliente, email_cliente, contato_principal_nome):
        query = """
            INSERT INTO clientes (tenant_id, Nome_Cliente, CNPJ_Cliente, Razao_Social_Cliente, Endereco_Cliente, Telefone_Cliente, Email_Cliente, Contato_Principal_Nome, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, nome_cliente, cnpj_cliente, razao_social_cliente, endereco_cliente, telefone_cliente, email_cliente, contato_principal_nome)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_cliente_by_id(self, cliente_id):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Clientes,
                Nome_Cliente,
                CNPJ_Cliente,
                Razao_Social_Cliente,
                Endereco_Cliente,
                Telefone_Cliente,
                Email_Cliente,
                Contato_Principal_Nome,
                Data_Criacao,
                Data_Modificacao
            FROM
                clientes
            WHERE {clause} AND ID_Clientes = %s
        """
        result = self.db.execute_query(query, (tenant_param, cliente_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_cliente(self, cliente_id, nome_cliente, cnpj_cliente, razao_social_cliente, endereco_cliente, telefone_cliente, email_cliente, contato_principal_nome):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE clientes
            SET
                Nome_Cliente = %s,
                CNPJ_Cliente = %s,
                Razao_Social_Cliente = %s,
                Endereco_Cliente = %s,
                Telefone_Cliente = %s,
                Email_Cliente = %s,
                Contato_Principal_Nome = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Clientes = %s
        """
        params = (nome_cliente, cnpj_cliente, razao_social_cliente, endereco_cliente, telefone_cliente, email_cliente, contato_principal_nome, tenant_param, cliente_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_cliente(self, cliente_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM clientes WHERE {clause} AND ID_Clientes = %s"
        return self.db.execute_query(query, (tenant_param, cliente_id), fetch_results=False)

    def get_cliente_by_cnpj(self, cnpj_cliente):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Clientes FROM clientes WHERE {clause} AND CNPJ_Cliente = %s"
        result = self.db.execute_query(query, (tenant_param, cnpj_cliente), fetch_results=True)
        return result[0] if result else None

    # --- Métodos CONTRATOS ---
    def get_all_contratos(self, search_numero=None, search_cliente_id=None, search_status=None):
        cl_clause, cl_param = self.tenant_clause('cl')
        c_clause, c_param = self.tenant_clause('c')
        query = f"""
            SELECT
                c.ID_Contratos,
                c.ID_Clientes,
                c.Numero_Contrato,
                c.Valor_Contrato,
                c.Data_Assinatura,
                c.Data_Ordem_Inicio,
                c.Prazo_Contrato_Dias,
                c.Data_Termino_Previsto,
                c.Status_Contrato,
                c.Observacoes,
                cl.Nome_Cliente,
                c.Data_Criacao,
                c.Data_Modificacao
            FROM
                contratos c
            LEFT JOIN
                clientes cl ON c.ID_Clientes = cl.ID_Clientes AND {cl_clause}
            WHERE {c_clause}
        """
        params = [cl_param, c_param]

        if search_numero:
            query += " AND c.Numero_Contrato LIKE %s"
            params.append(f"%{search_numero}%")
        if search_cliente_id:
            query += " AND c.ID_Clientes = %s"
            params.append(search_cliente_id)
        if search_status:
            query += " AND c.Status_Contrato = %s"
            params.append(search_status)

        query += " ORDER BY c.Numero_Contrato"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_contrato(self, id_clientes, numero_contrato, valor_contrato, data_assinatura, data_ordem_inicio, prazo_contrato_dias, data_termino_previsto, status_contrato, observacoes):
        query = """
            INSERT INTO contratos (tenant_id, ID_Clientes, Numero_Contrato, Valor_Contrato, Data_Assinatura, Data_Ordem_Inicio, Prazo_Contrato_Dias, Data_Termino_Previsto, Status_Contrato, Observacoes, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_clientes, numero_contrato, valor_contrato, data_assinatura, data_ordem_inicio, prazo_contrato_dias, data_termino_previsto, status_contrato, observacoes)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_contrato_by_id(self, contrato_id):
        cl_clause, cl_param = self.tenant_clause('cl')
        c_clause, c_param = self.tenant_clause('c')
        query = f"""
            SELECT
                c.ID_Contratos,
                c.ID_Clientes,
                c.Numero_Contrato,
                c.Valor_Contrato,
                c.Data_Assinatura,
                c.Data_Ordem_Inicio,
                c.Prazo_Contrato_Dias,
                c.Data_Termino_Previsto,
                c.Status_Contrato,
                c.Observacoes,
                cl.Nome_Cliente,
                c.Data_Criacao,
                c.Data_Modificacao
            FROM
                contratos c
            LEFT JOIN
                clientes cl ON c.ID_Clientes = cl.ID_Clientes AND {cl_clause}
            WHERE {c_clause} AND c.ID_Contratos = %s
        """
        result = self.db.execute_query(query, (cl_param, c_param, contrato_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0]) # <-- GARANTIR QUE ESTA LINHA ESTÁ PRESENTE E CORRETA
        return None

    def update_contrato(self, contrato_id, id_clientes, numero_contrato, valor_contrato, data_assinatura, data_ordem_inicio, prazo_contrato_dias, data_termino_previsto, status_contrato, observacoes):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE contratos
            SET
                ID_Clientes = %s,
                Numero_Contrato = %s,
                Valor_Contrato = %s,
                Data_Assinatura = %s,
                Data_Ordem_Inicio = %s,
                Prazo_Contrato_Dias = %s,
                Data_Termino_Previsto = %s,
                Status_Contrato = %s,
                Observacoes = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Contratos = %s
        """
        params = (id_clientes, numero_contrato, valor_contrato, data_assinatura, data_ordem_inicio, prazo_contrato_dias, data_termino_previsto, status_contrato, observacoes, tenant_param, contrato_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_contrato(self, contrato_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM contratos WHERE {clause} AND ID_Contratos = %s"
        return self.db.execute_query(query, (tenant_param, contrato_id), fetch_results=False)

    def get_contrato_by_numero(self, numero_contrato):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Contratos FROM contratos WHERE {clause} AND Numero_Contrato = %s"
        result = self.db.execute_query(query, (tenant_param, numero_contrato), fetch_results=True)
        return result[0] if result else None


    # --- Métodos ARTS ---
    def get_all_arts(self, search_numero=None, search_obra_id=None, search_status=None):
        o_clause, o_param = self.tenant_clause('o')
        a_clause, a_param = self.tenant_clause('a')
        query = f"""
            SELECT
                a.ID_Arts,
                a.ID_Obras,
                a.Numero_Art,
                a.Data_Pagamento,
                a.Valor_Pagamento,
                a.Status_Art,
                o.Numero_Obra,
                o.Nome_Obra,
                a.Data_Criacao,
                a.Data_Modificacao
            FROM
                arts a
            LEFT JOIN
                obras o ON a.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {a_clause}
        """
        params = [o_param, a_param]

        if search_numero:
            query += " AND a.Numero_Art LIKE %s"
            params.append(f"%{search_numero}%")
        if search_obra_id:
            query += " AND a.ID_Obras = %s"
            params.append(search_obra_id)
        if search_status:
            query += " AND a.Status_Art = %s"
            params.append(search_status)

        query += " ORDER BY a.Numero_Art"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_art(self, id_obras, numero_art, data_pagamento, valor_pagamento, status_art):
        query = """
            INSERT INTO arts (tenant_id, ID_Obras, Numero_Art, Data_Pagamento, Valor_Pagamento, Status_Art, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_obras, numero_art, data_pagamento, valor_pagamento, status_art)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_art_by_id(self, art_id):
        o_clause, o_param = self.tenant_clause('o')
        a_clause, a_param = self.tenant_clause('a')
        query = f"""
            SELECT
                a.ID_Arts,
                a.ID_Obras,
                a.Numero_Art,
                a.Data_Pagamento,
                a.Valor_Pagamento,
                a.Status_Art,
                o.Numero_Obra,
                o.Nome_Obra,
                a.Data_Criacao,
                a.Data_Modificacao
            FROM
                arts a
            LEFT JOIN
                obras o ON a.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {a_clause} AND a.ID_Arts = %s
        """
        result = self.db.execute_query(query, (o_param, a_param, art_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_art(self, art_id, id_obras, numero_art, data_pagamento, valor_pagamento, status_art):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE arts
            SET
                ID_Obras = %s,
                Numero_Art = %s,
                Data_Pagamento = %s,
                Valor_Pagamento = %s,
                Status_Art = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Arts = %s
        """
        params = (id_obras, numero_art, data_pagamento, valor_pagamento, status_art, tenant_param, art_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_art(self, art_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM arts WHERE {clause} AND ID_Arts = %s"
        return self.db.execute_query(query, (tenant_param, art_id), fetch_results=False)

    def get_art_by_numero(self, numero_art):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Arts FROM arts WHERE {clause} AND Numero_Art = %s"
        result = self.db.execute_query(query, (tenant_param, numero_art), fetch_results=True)
        return result[0] if result else None

    # --- Métodos MEDIÇÕES ---
    def get_all_medicoes(self, search_numero_medicao=None, search_obra_id=None, search_status=None):
        o_clause, o_param = self.tenant_clause('o')
        m_clause, m_param = self.tenant_clause('m')
        query = f"""
            SELECT
                m.ID_Medicoes,
                m.ID_Obras,
                m.Numero_Medicao,
                m.Valor_Medicao,
                m.Data_Medicao,
                m.Mes_Referencia,
                m.Data_Aprovacao,
                m.Status_Medicao,
                m.Observacao_Medicao,
                o.Numero_Obra,
                o.Nome_Obra,
                m.Data_Criacao,
                m.Data_Modificacao
            FROM
                medicoes m
            LEFT JOIN
                obras o ON m.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {m_clause}
        """
        params = [o_param, m_param]

        if search_numero_medicao:
            query += " AND m.Numero_Medicao = %s"
            params.append(search_numero_medicao)
        if search_obra_id:
            query += " AND m.ID_Obras = %s"
            params.append(search_obra_id)
        if search_status:
            query += " AND m.Status_Medicao = %s"
            params.append(search_status)

        query += " ORDER BY o.Numero_Obra, m.Numero_Medicao"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_medicao(self, id_obras, numero_medicao, valor_medicao, data_medicao, mes_referencia, data_aprovacao, status_medicao, observacao_medicao):
        query = """
            INSERT INTO medicoes (tenant_id, ID_Obras, Numero_Medicao, Valor_Medicao, Data_Medicao, Mes_Referencia, Data_Aprovacao, Status_Medicao, Observacao_Medicao, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_obras, numero_medicao, valor_medicao, data_medicao, mes_referencia, data_aprovacao, status_medicao, observacao_medicao)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_medicao_by_id(self, medicao_id):
        o_clause, o_param = self.tenant_clause('o')
        m_clause, m_param = self.tenant_clause('m')
        query = f"""
            SELECT
                m.ID_Medicoes,
                m.ID_Obras,
                m.Numero_Medicao,
                m.Valor_Medicao,
                m.Data_Medicao,
                m.Mes_Referencia,
                m.Data_Aprovacao,
                m.Status_Medicao,
                m.Observacao_Medicao,
                o.Numero_Obra,
                o.Nome_Obra,
                m.Data_Criacao,
                m.Data_Modificacao
            FROM
                medicoes m
            LEFT JOIN
                obras o ON m.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {m_clause} AND m.ID_Medicoes = %s
        """
        result = self.db.execute_query(query, (o_param, m_param, medicao_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_medicao(self, medicao_id, id_obras, numero_medicao, valor_medicao, data_medicao, mes_referencia, data_aprovacao, status_medicao, observacao_medicao):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE medicoes
            SET
                ID_Obras = %s,
                Numero_Medicao = %s,
                Valor_Medicao = %s,
                Data_Medicao = %s,
                Mes_Referencia = %s,
                Data_Aprovacao = %s,
                Status_Medicao = %s,
                Observacao_Medicao = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Medicoes = %s
        """
        params = (id_obras, numero_medicao, valor_medicao, data_medicao, mes_referencia, data_aprovacao, status_medicao, observacao_medicao, tenant_param, medicao_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_medicao(self, medicao_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM medicoes WHERE {clause} AND ID_Medicoes = %s"
        return self.db.execute_query(query, (tenant_param, medicao_id), fetch_results=False)

    def get_medicao_by_obra_numero(self, id_obras, numero_medicao):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Medicoes FROM medicoes WHERE {clause} AND ID_Obras = %s AND Numero_Medicao = %s"
        result = self.db.execute_query(query, (tenant_param, id_obras, numero_medicao), fetch_results=True)
        return result[0] if result else None

    # --- Métodos AVANÇOS FÍSICOS ---
    def get_all_avancos_fisicos(self, search_obra_id=None, search_data_inicio=None, search_data_fim=None):
        o_clause, o_param = self.tenant_clause('o')
        af_clause, af_param = self.tenant_clause('af')
        query = f"""
            SELECT
                af.ID_Avancos_Fisicos,
                af.ID_Obras,
                af.Percentual_Avanco_Fisico,
                af.Data_Avanco,
                o.Numero_Obra,
                o.Nome_Obra,
                af.Data_Criacao,
                af.Data_Modificacao
            FROM
                avancos_fisicos af
            LEFT JOIN
                obras o ON af.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {af_clause}
        """
        params = [o_param, af_param]

        if search_obra_id:
            query += " AND af.ID_Obras = %s"
            params.append(search_obra_id)
        if search_data_inicio:
            query += " AND af.Data_Avanco >= %s"
            params.append(search_data_inicio)
        if search_data_fim:
            query += " AND af.Data_Avanco <= %s"
            params.append(search_data_fim)

        query += " ORDER BY o.Nome_Obra, af.Data_Avanco DESC"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_avanco_fisico(self, id_obras, percentual_avanco_fisico, data_avanco):
        query = """
            INSERT INTO avancos_fisicos (tenant_id, ID_Obras, Percentual_Avanco_Fisico, Data_Avanco, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_obras, percentual_avanco_fisico, data_avanco)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_avanco_fisico_by_id(self, avanco_id):
        o_clause, o_param = self.tenant_clause('o')
        af_clause, af_param = self.tenant_clause('af')
        query = f"""
            SELECT
                af.ID_Avancos_Fisicos,
                af.ID_Obras,
                af.Percentual_Avanco_Fisico, -- O campo problemático
                af.Data_Avanco,
                o.Numero_Obra,
                o.Nome_Obra,
                af.Data_Criacao,
                af.Data_Modificacao
            FROM
                avancos_fisicos af
            LEFT JOIN
                obras o ON af.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {af_clause} AND af.ID_Avancos_Fisicos = %s
        """
        result = self.db.execute_query(query, (o_param, af_param, avanco_id), fetch_results=True)
        if result:
            item = result[0] # Pega o dicionário de resultado
            # --- CORRIGIDO AQUI: TRATAMENTO EXPLÍCITO PARA PERCENTUAL_AVANCO_FISICO NO MANAGER ---
            percentual = item.get('Percentual_Avanco_Fisico')
            if percentual is not None:
                try:
                    item['Percentual_Avanco_Fisico'] = float(percentual)
                except (ValueError, TypeError):
                    item['Percentual_Avanco_Fisico'] = None # Se não puder ser float, define como None
            # --- FIM DA CORREÇÃO ---
            return self._format_date_fields(item) # Continua formatando as datas
        return None

    def update_avanco_fisico(self, avanco_id, id_obras, percentual_avanco_fisico, data_avanco):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE avancos_fisicos
            SET
                ID_Obras = %s,
                Percentual_Avanco_Fisico = %s,
                Data_Avanco = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Avancos_Fisicos = %s
        """
        params = (id_obras, percentual_avanco_fisico, data_avanco, tenant_param, avanco_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_avanco_fisico(self, avanco_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM avancos_fisicos WHERE {clause} AND ID_Avancos_Fisicos = %s"
        return self.db.execute_query(query, (tenant_param, avanco_id), fetch_results=False)

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- NOVO MÉTODO: Avanço Físico Acumulado para uma Obra --------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_avanco_acumulado_para_obra(self, obra_id, avanco_id_excluir=None):
        """
        Retorna o percentual de avanço físico acumulado para uma obra específica,
        somando todos os percentuais pontuais até a data mais recente.
        Se avanco_id_excluir for fornecido, ele exclui o percentual desse avanço do cálculo (útil na edição).
        """
        clause, tenant_param = self.tenant_clause('af')
        query = f"""
            SELECT
                SUM(af.Percentual_Avanco_Fisico) AS Avanco_Acumulado
            FROM
                avancos_fisicos af
            WHERE
                {clause} AND af.ID_Obras = %s
        """
        params = [tenant_param, obra_id]

        if avanco_id_excluir:
            query += " AND af.ID_Avancos_Fisicos != %s"
            params.append(avanco_id_excluir)

        result = self.db.execute_query(query, tuple(params), fetch_results=True)

        # Retorna a soma como float. Se não houver avanços, retorna 0.0
        return float(result[0]['Avanco_Acumulado']) if result and result[0]['Avanco_Acumulado'] is not None else 0.0

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- NOVO MÉTODO: Contagem Total de Obras -----------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_total_obras_count(self):
        """
        Retorna a contagem total de obras registradas.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                COUNT(ID_Obras) AS Total_Obras
            FROM
                obras
            WHERE {clause}
        """
        result = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        # Retorna a contagem como int. Se não houver obras, retorna 0
        return int(result[0]['Total_Obras']) if result and result[0]['Total_Obras'] is not None else 0

    # --- Métodos REIDIS ---
    def get_all_reidis(self, search_numero_portaria=None, search_numero_ato=None, search_obra_id=None, search_status=None):
        o_clause, o_param = self.tenant_clause('o')
        r_clause, r_param = self.tenant_clause('r')
        query = f"""
            SELECT
                r.ID_Reidis,
                r.ID_Obras,
                r.Numero_Portaria,
                r.Numero_Ato_Declaratorio,
                r.Data_Aprovacao_Reidi,
                r.Data_Validade_Reidi,
                r.Status_Reidi,
                r.Observacoes_Reidi,
                o.Numero_Obra,
                o.Nome_Obra,
                r.Data_Criacao,
                r.Data_Modificacao
            FROM
                reidis r
            LEFT JOIN
                obras o ON r.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {r_clause}
        """
        params = [o_param, r_param]

        if search_numero_portaria:
            query += " AND r.Numero_Portaria LIKE %s"
            params.append(f"%{search_numero_portaria}%")
        if search_numero_ato:
            query += " AND r.Numero_Ato_Declaratorio LIKE %s"
            params.append(f"%{search_numero_ato}%")
        if search_obra_id:
            query += " AND r.ID_Obras = %s"
            params.append(search_obra_id)
        if search_status:
            query += " AND r.Status_Reidi = %s"
            params.append(search_status)

        query += " ORDER BY o.Numero_Obra, r.Numero_Portaria"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_reidi(self, id_obras, numero_portaria, numero_ato_declaratorio, data_aprovacao_reidi, data_validade_reidi, status_reidi, observacoes_reidi):
        query = """
            INSERT INTO reidis (tenant_id, ID_Obras, Numero_Portaria, Numero_Ato_Declaratorio, Data_Aprovacao_Reidi, Data_Validade_Reidi, Status_Reidi, Observacoes_Reidi, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_obras, numero_portaria, numero_ato_declaratorio, data_aprovacao_reidi, data_validade_reidi, status_reidi, observacoes_reidi)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_reidi_by_id(self, reidi_id):
        o_clause, o_param = self.tenant_clause('o')
        r_clause, r_param = self.tenant_clause('r')
        query = f"""
            SELECT
                r.ID_Reidis,
                r.ID_Obras,
                r.Numero_Portaria,
                r.Numero_Ato_Declaratorio,
                r.Data_Aprovacao_Reidi,
                r.Data_Validade_Reidi,
                r.Status_Reidi,
                r.Observacoes_Reidi,
                o.Numero_Obra,
                o.Nome_Obra,
                r.Data_Criacao,
                r.Data_Modificacao
            FROM
                reidis r
            LEFT JOIN
                obras o ON r.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {r_clause} AND r.ID_Reidis = %s
        """
        result = self.db.execute_query(query, (o_param, r_param, reidi_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_reidi(self, reidi_id, id_obras, numero_portaria, numero_ato_declaratorio, data_aprovacao_reidi, data_validade_reidi, status_reidi, observacoes_reidi):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE reidis
            SET
                ID_Obras = %s,
                Numero_Portaria = %s,
                Numero_Ato_Declaratorio = %s,
                Data_Aprovacao_Reidi = %s,
                Data_Validade_Reidi = %s,
                Status_Reidi = %s,
                Observacoes_Reidi = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Reidis = %s
        """
        params = (id_obras, numero_portaria, numero_ato_declaratorio, data_aprovacao_reidi, data_validade_reidi, status_reidi, observacoes_reidi, tenant_param, reidi_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_reidi(self, reidi_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM reidis WHERE {clause} AND ID_Reidis = %s"
        return self.db.execute_query(query, (tenant_param, reidi_id), fetch_results=False)

    def get_reidi_by_numero_portaria(self, numero_portaria):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Reidis FROM reidis WHERE {clause} AND Numero_Portaria = %s"
        result = self.db.execute_query(query, (tenant_param, numero_portaria), fetch_results=True)
        return result[0] if result else None

    def get_reidi_by_numero_ato_declaratorio(self, numero_ato_declaratorio):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Reidis FROM reidis WHERE {clause} AND Numero_Ato_Declaratorio = %s"
        result = self.db.execute_query(query, (tenant_param, numero_ato_declaratorio), fetch_results=True)
        return result[0] if result else None

    # --- Métodos SEGUROS ---
    def get_all_seguros(self, search_numero_apolice=None, search_obra_id=None, search_status=None, search_tipo=None):
        o_clause, o_param = self.tenant_clause('o')
        s_clause, s_param = self.tenant_clause('s')
        query = f"""
            SELECT
                s.ID_Seguros,
                s.ID_Obras,
                s.Numero_Apolice,
                s.Seguradora,
                s.Tipo_Seguro,
                s.Valor_Segurado,
                s.Data_Inicio_Vigencia,
                s.Data_Fim_Vigencia,
                s.Status_Seguro,
                s.Observacoes_Seguro,
                o.Numero_Obra,
                o.Nome_Obra,
                s.Data_Criacao,
                s.Data_Modificacao
            FROM
                seguros s
            LEFT JOIN
                obras o ON s.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {s_clause}
        """
        params = [o_param, s_param]

        if search_numero_apolice:
            query += " AND s.Numero_Apolice LIKE %s"
            params.append(f"%{search_numero_apolice}%")
        if search_obra_id:
            query += " AND s.ID_Obras = %s"
            params.append(search_obra_id)
        if search_status:
            query += " AND s.Status_Seguro = %s"
            params.append(search_status)
        if search_tipo:
            query += " AND s.Tipo_Seguro = %s"
            params.append(search_tipo)

        query += " ORDER BY o.Numero_Obra, s.Numero_Apolice"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_seguro(self, id_obras, numero_apolice, seguradora, tipo_seguro, valor_segurado, data_inicio_vigencia, data_fim_vigencia, status_seguro, observacoes_seguro):
        query = """
            INSERT INTO seguros (tenant_id, ID_Obras, Numero_Apolice, Seguradora, Tipo_Seguro, Valor_Segurado, Data_Inicio_Vigencia, Data_Fim_Vigencia, Status_Seguro, Observacoes_Seguro, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_obras, numero_apolice, seguradora, tipo_seguro, valor_segurado, data_inicio_vigencia, data_fim_vigencia, status_seguro, observacoes_seguro)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_seguro_by_id(self, seguro_id):
        o_clause, o_param = self.tenant_clause('o')
        s_clause, s_param = self.tenant_clause('s')
        query = f"""
            SELECT
                s.ID_Seguros,
                s.ID_Obras,
                s.Numero_Apolice,
                s.Seguradora,
                s.Tipo_Seguro,
                s.Valor_Segurado,
                s.Data_Inicio_Vigencia,
                s.Data_Fim_Vigencia,
                s.Status_Seguro,
                s.Observacoes_Seguro,
                o.Numero_Obra,
                o.Nome_Obra,
                s.Data_Criacao,
                s.Data_Modificacao
            FROM
                seguros s
            LEFT JOIN
                obras o ON s.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE {s_clause} AND s.ID_Seguros = %s
        """
        result = self.db.execute_query(query, (o_param, s_param, seguro_id), fetch_results=True)
        if result:
            item = result[0] # Pega o dicionário de resultado

            # --- NOVO: TRATAMENTO EXPLÍCITO PARA VALOR_SEGURADO ---
            valor = item.get('Valor_Segurado')
            if valor is not None:
                try:
                    item['Valor_Segurado'] = float(valor)
                except (ValueError, TypeError):
                    item['Valor_Segurado'] = None
            # --- FIM DO NOVO TRATAMENTO ---

            return self._format_date_fields(item) # Formata as datas por último
        return None

    def update_seguro(self, seguro_id, id_obras, numero_apolice, seguradora, tipo_seguro, valor_segurado, data_inicio_vigencia, data_fim_vigencia, status_seguro, observacoes_seguro):
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE seguros
            SET
                ID_Obras = %s,
                Numero_Apolice = %s,
                Seguradora = %s,
                Tipo_Seguro = %s,
                Valor_Segurado = %s,
                Data_Inicio_Vigencia = %s,
                Data_Fim_Vigencia = %s,
                Status_Seguro = %s,
                Observacoes_Seguro = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Seguros = %s
        """
        params = (id_obras, numero_apolice, seguradora, tipo_seguro, valor_segurado, data_inicio_vigencia, data_fim_vigencia, status_seguro, observacoes_seguro, tenant_param, seguro_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_seguro(self, seguro_id):
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM seguros WHERE {clause} AND ID_Seguros = %s"
        return self.db.execute_query(query, (tenant_param, seguro_id), fetch_results=False)

    def get_seguro_by_numero_apolice(self, numero_apolice):
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Seguros FROM seguros WHERE {clause} AND Numero_Apolice = %s"
        result = self.db.execute_query(query, (tenant_param, numero_apolice), fetch_results=True)
        return result[0] if result else None

    # ==================================================================================================================================
    # === MÉTODOS PARA DASHBOARD DE OBRAS ==============================================================================================
    # ==================================================================================================================================

    # --- Métodos para o Dashboard da Obra ---
    def get_avancos_by_obra_id(self, obra_id):
        """
        Retorna todos os registros de avanço físico para uma obra específica.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                Percentual_Avanco_Fisico,
                Data_Avanco
            FROM
                avancos_fisicos
            WHERE {clause} AND ID_Obras = %s
            ORDER BY Data_Avanco ASC
        """
        results = self.db.execute_query(query, (tenant_param, obra_id), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return []

    def get_medicoes_by_obra_id(self, obra_id):
        """
        Retorna todos os registros de medição para uma obra específica.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                Valor_Medicao,
                Data_Medicao
            FROM
                medicoes
            WHERE {clause} AND ID_Obras = %s AND Status_Medicao IN ('Aprovada', 'Paga')
            ORDER BY Data_Medicao ASC
        """
        results = self.db.execute_query(query, (tenant_param, obra_id), fetch_results=True)
        if results:
            # Tratamento explícito para o valor e formatação de data
            for item in results:
                value = item.get('Valor_Medicao')
                if value is not None:
                    try:
                        item['Valor_Medicao'] = float(value)
                    except (ValueError, TypeError):
                        item['Valor_Medicao'] = 0.0
            return [self._format_date_fields(item) for item in results]
        return []

    def get_obra_status_counts(self):
        """
        Retorna a contagem de obras por status.
        Ex: [{'Status_Obra': 'Em Andamento', 'Count': 5}, {'Status_Obra': 'Concluída', 'Count': 3}]
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                Status_Obra,
                COUNT(ID_Obras) AS Count
            FROM
                obras
            WHERE
                {clause}
            GROUP BY
                Status_Obra
            ORDER BY
                Status_Obra
        """
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        # O método execute_query do db_base já deve retornar uma lista de dicionários.
        # A chave 'Count' é o que precisamos. Jinja's 'sum' precisa ser ajustado.
        return results if results else []

    def get_total_contratos_ativos_valor(self):
        """
        Retorna o valor total dos contratos com status 'Ativo'.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                SUM(Valor_Contrato) AS Total_Valor_Contratos
            FROM
                contratos
            WHERE
                {clause} AND Status_Contrato = 'Ativo'
        """
        result = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return result[0]['Total_Valor_Contratos'] if result and result[0]['Total_Valor_Contratos'] is not None else 0.0

    def get_total_medicoes_realizadas_valor(self):
        """
        Retorna o valor total das medições realizadas (status 'Paga' ou 'Aprovada').
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                SUM(Valor_Medicao) AS Total_Valor_Medicoes
            FROM
                medicoes
            WHERE
                {clause} AND Status_Medicao IN ('Paga', 'Aprovada')
        """
        result = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return result[0]['Total_Valor_Medicoes'] if result and result[0]['Total_Valor_Medicoes'] is not None else 0.0

    def get_avg_avanco_fisico_obras_ativas(self):
        """
        Calcula o percentual médio de avanço físico para obras ativas.
        Assume que a tabela 'avancos_fisicos' guarda o percentual de avanço de cada obra em determinada data,
        e queremos o *último* avanço de cada obra ativa.
        """
        af_clause, af_param = self.tenant_clause()
        o_clause, o_param = self.tenant_clause('o')
        # Subquery para encontrar o último avanço físico para cada obra
        subquery = f"""
            SELECT
                ID_Obras,
                Percentual_Avanco_Fisico,
                Data_Avanco,
                ROW_NUMBER() OVER (PARTITION BY ID_Obras ORDER BY Data_Avanco DESC, Data_Criacao DESC) as rn
            FROM
                avancos_fisicos
            WHERE
                {af_clause}
        """
        # Query principal para calcular a média apenas das obras ativas
        query = f"""
            SELECT
                AVG(t1.Percentual_Avanco_Fisico) AS Media_Avanco_Fisico
            FROM
                ({subquery}) AS t1
            JOIN
                obras o ON t1.ID_Obras = o.ID_Obras AND {o_clause}
            WHERE
                t1.rn = 1 AND o.Status_Obra = 'Em Andamento'
        """
        result = self.db.execute_query(query, (af_param, o_param), fetch_results=True)
        return result[0]['Media_Avanco_Fisico'] if result and result[0]['Media_Avanco_Fisico'] is not None else 0.0

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- NOVO MÉTODO: Dados para Relatório de Andamento de Obras ---------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_obras_andamento_para_relatorio(self, search_numero=None, search_nome=None, search_status=None, search_cliente_id=None):
        """
        Retorna dados detalhados para o relatório de andamento de obras,
        incluindo o último percentual de avanço físico e a data desse avanço.
        """
        af1_clause, af1_param = self.tenant_clause('af')
        af2_clause, af2_param = self.tenant_clause('af')
        co_clause, co_param = self.tenant_clause('co')
        c_clause, c_param = self.tenant_clause('c')
        o_clause, o_param = self.tenant_clause('o')
        query = f"""
            SELECT
                o.ID_Obras,
                o.Numero_Obra,
                o.Nome_Obra,
                o.Status_Obra,
                o.Data_Inicio_Prevista,
                o.Data_Fim_Prevista,
                c.Nome_Cliente,
                -- Subquery para obter o último percentual e data de avanço físico para cada obra
                (SELECT
                    af.Percentual_Avanco_Fisico
                FROM
                    avancos_fisicos af
                WHERE
                    af.ID_Obras = o.ID_Obras AND {af1_clause}
                ORDER BY
                    af.Data_Avanco DESC, af.Data_Criacao DESC
                LIMIT 1) AS Ultimo_Avanco_Percentual,
                (SELECT
                    af.Data_Avanco
                FROM
                    avancos_fisicos af
                WHERE
                    af.ID_Obras = o.ID_Obras AND {af2_clause}
                ORDER BY
                    af.Data_Avanco DESC, af.Data_Criacao DESC
                LIMIT 1) AS Ultima_Data_Avanco
            FROM
                obras o
            LEFT JOIN
                contratos co ON o.ID_Contratos = co.ID_Contratos AND {co_clause}
            LEFT JOIN
                clientes c ON co.ID_Clientes = c.ID_Clientes AND {c_clause}
            WHERE {o_clause}
        """
        params = [af1_param, af2_param, co_param, c_param, o_param]

        if search_numero:
            query += " AND o.Numero_Obra LIKE %s"
            params.append(f"%{search_numero}%")
        if search_nome:
            query += " AND o.Nome_Obra LIKE %s"
            params.append(f"%{search_nome}%")
        if search_status:
            query += " AND o.Status_Obra = %s"
            params.append(search_status)
        if search_cliente_id:
            query += " AND c.ID_Clientes = %s"
            params.append(search_cliente_id)

        query += " ORDER BY o.Nome_Obra"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            # Garante que as datas sejam formatadas corretamente para Python (datetime.date)
            return [self._format_date_fields(item) for item in results]
        return results
