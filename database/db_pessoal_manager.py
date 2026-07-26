# database/db_pessoal_manager.py
# rev01 - migração pra TenantScopedManager (isolamento por tenant_id)

import mysql.connector
from datetime import datetime, date, timedelta
import pandas as pd
from database.db_base import TenantScopedManager

class PessoalManager(TenantScopedManager):

    # ==================================================================================================================================
    # === MÉTODOS AUXILIARES GERAIS ====================================================================================================
    # ==================================================================================================================================

    def _format_date_fields(self, item):
        """
        Função auxiliar para converter campos de data em dicionários de resultados
        para objetos date ou None.
        """
        if item is None:
            return None

        # Lista de campos de data/datetime que precisam de formatação para objeto date
        # INCLUA AQUI TODAS AS NOVAS COLUNAS DE DATA DA TABELA funcionarios_documentos
        date_fields_to_format = [
            'Data_Criacao', 'Data_Modificacao',
            'Data_Admissao', # Funcionarios
            'Data_Vigencia', # Salarios
            'Periodo_Aquisitivo_Inicio', 'Periodo_Aquisitivo_Fim', # Ferias
            'Data_Inicio_Gozo', 'Data_Fim_Gozo', # Ferias
            'Data_Nascimento', # Funcionarios_Documentos e Dependentes
            'Rg_DataEmissao', # Funcionarios_Documentos
            'Cnh_DataValidade', # Funcionarios_Documentos
            'Ctps_DataEmissao', # Se decidir adicionar, descomente aqui (agora removida por opção)
            'Pispasep_DataCadastro' # Se decidir adicionar, descomente aqui (agora removida por opção)
        ]

        for key in date_fields_to_format:
            if key in item:
                value = item[key]
                if isinstance(value, str):
                    if not value.strip():
                        item[key] = None
                        continue
                    try:
                        item[key] = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            item[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').date()
                        except ValueError:
                            print(f"AVISO: Não foi possível converter a string de data '{value}' para objeto date para o campo '{key}'. Definindo como None.")
                            item[key] = None
                elif isinstance(value, datetime):
                    item[key] = value.date()
                elif value is None:
                    item[key] = None

        return item

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: FUNCIONÁRIOS ==========================================================================================
    # ==================================================================================================================================

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- GERADOR DE NÚMERO DE MATRÍCULA PADRÃO SEQUENCIAL PARA SUGERIR NA INCLUSÃO DE NOVO FUNCIONÁRIO ------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def generate_next_matricula(self):
        """Gera a próxima matrícula sequencial baseada na última matrícula existente do tenant."""
        try:
            clause, tenant_param = self.tenant_clause()
            query = f"SELECT Matricula FROM funcionarios WHERE {clause} AND Matricula REGEXP '^MATR[0-9]+$' ORDER BY LENGTH(Matricula) DESC, Matricula DESC LIMIT 1"
            last_matricula_data = self.db.execute_query(query, (tenant_param,), fetch_results=True)

            if last_matricula_data and last_matricula_data[0]['Matricula']:
                last_matricula = last_matricula_data[0]['Matricula']
                num = int(last_matricula[4:]) + 1
                return f"MATR{num:03d}"
            return "MATR001"
        except Exception as e:
            print(f"Erro ao gerar próxima matrícula: {e}")
            return "MATR001"

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- MÉTODOS CRUD PRINCIPAIS DE FUNCIONÁRIOS (TABELA 'funcionarios') --------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_all_funcionarios(self, search_matricula=None, search_nome=None, search_status=None, search_cargo_id=None):
        """
        Retorna uma lista de todos os funcionários, opcionalmente filtrada,
        incluindo informações de cargo e nível.
        """
        clause, tenant_param = self.tenant_clause('f')
        query = f"""
            SELECT
                f.Matricula,
                f.Nome_Completo,
                f.Data_Admissao,
                f.ID_Cargos,
                f.ID_Niveis,
                f.Status,
                c.Nome_Cargo,
                n.Nome_Nivel,
                f.Data_Criacao,
                f.Data_Modificacao
            FROM
                funcionarios f
            LEFT JOIN
                cargos c ON f.ID_Cargos = c.ID_Cargos
            LEFT JOIN
                niveis n ON f.ID_Niveis = n.ID_Niveis
            WHERE {clause}
        """
        params = [tenant_param]

        if search_matricula:
            query += " AND f.Matricula LIKE %s"
            params.append(f"%{search_matricula}%")
        if search_nome:
            query += " AND f.Nome_Completo LIKE %s"
            params.append(f"%{search_nome}%")
        if search_status:
            query += " AND f.Status = %s"
            params.append(search_status)
        if search_cargo_id:
            query += " AND f.ID_Cargos = %s"
            params.append(search_cargo_id)

        query += " ORDER BY f.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_funcionario(self, matricula, nome_completo, data_admissao, id_cargos, id_niveis, status, tipo_contratacao):
        """
        Adiciona um novo funcionário, incluindo o tipo de contratação.
        """
        query = """
            INSERT INTO funcionarios
            (tenant_id, Matricula, Nome_Completo, Data_Admissao, ID_Cargos, ID_Niveis, Status, Tipo_Contratacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (self.tenant_id, matricula, nome_completo, data_admissao, id_cargos, id_niveis, status, tipo_contratacao)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_funcionario_by_matricula(self, matricula):
        """
        Retorna os dados principais de um funcionário e seus dados pessoais/documentos
        pela matrícula, usando JOIN com funcionarios_documentos.
        """
        f_clause, f_param = self.tenant_clause('f')
        fd_clause, fd_param = self.tenant_clause('fd')
        query = f"""
            SELECT
                f.Matricula, f.Nome_Completo, f.Data_Admissao, f.ID_Cargos, f.ID_Niveis, f.Status,
                c.Nome_Cargo, n.Nome_Nivel,
                fd.Data_Nascimento, fd.Estado_Civil, fd.Nacionalidade, fd.Naturalidade, fd.Genero,
                fd.Rg_Numero, fd.Rg_OrgaoEmissor, fd.Rg_UfEmissor, fd.Rg_DataEmissao,
                fd.Cpf_Numero,
                fd.Ctps_Numero, fd.Ctps_Serie,
                fd.Pispasep,
                fd.Cnh_Numero, fd.Cnh_Categoria, fd.Cnh_DataValidade, fd.Cnh_OrgaoEmissor,
                fd.TitEleitor_Numero, fd.TitEleitor_Zona, fd.TitEleitor_Secao,
                fd.Observacoes, fd.Link_Foto,
                f.Data_Criacao, f.Data_Modificacao
            FROM
                funcionarios f
            LEFT JOIN cargos c ON f.ID_Cargos = c.ID_Cargos
            LEFT JOIN niveis n ON f.ID_Niveis = n.ID_Niveis
            LEFT JOIN funcionarios_documentos fd ON f.Matricula = fd.Matricula_Funcionario AND {fd_clause}
            WHERE {f_clause} AND f.Matricula = %s
        """
        result = self.db.execute_query(query, (fd_param, f_param, matricula), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_funcionario(self, old_matricula, new_matricula, nome_completo, data_admissao, id_cargos, id_niveis, status):
        """Atualiza os dados principais de um funcionário."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE funcionarios
            SET
                Matricula = %s,
                Nome_Completo = %s,
                Data_Admissao = %s,
                ID_Cargos = %s,
                ID_Niveis = %s,
                Status = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND Matricula = %s
        """
        params = (new_matricula, nome_completo, data_admissao, id_cargos, id_niveis, status, tenant_param, old_matricula)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_funcionario(self, matricula):
        """Exclui um funcionário pelo ID. ON DELETE CASCADE cuidará das tabelas relacionadas."""
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM funcionarios WHERE {clause} AND Matricula = %s"
        return self.db.execute_query(query, (tenant_param, matricula), fetch_results=False)

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- MÉTODOS PARA DADOS PESSOAIS E DOCUMENTOS (TABELA 'funcionarios_documentos') --------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def save_funcionario_dados_pessoais_documentos(self, matricula, data_nascimento, estado_civil, nacionalidade, naturalidade, genero,
                                                    rg_numero, rg_orgao_emissor, rg_uf_emissor, rg_data_emissao,
                                                    cpf_numero,
                                                    ctps_numero, ctps_serie,
                                                    pispasep,
                                                    cnh_numero, cnh_categoria, cnh_data_validade, cnh_orgao_emissor,
                                                    titeleitor_numero, titeleitor_zona, titeleitor_secao,
                                                    observacoes, link_foto):
        """
        Salva (insere ou atualiza) os dados pessoais e de documentos de um funcionário.
        """
        clause, tenant_param = self.tenant_clause()
        existing_data = self.db.execute_query(
            f"SELECT Matricula_Funcionario FROM funcionarios_documentos WHERE {clause} AND Matricula_Funcionario = %s",
            (tenant_param, matricula), fetch_results=True
        )

        params = (
            data_nascimento, estado_civil, nacionalidade, naturalidade, genero,
            rg_numero, rg_orgao_emissor, rg_uf_emissor, rg_data_emissao,
            cpf_numero, ctps_numero, ctps_serie, pispasep,
            cnh_numero, cnh_categoria, cnh_data_validade, cnh_orgao_emissor,
            titeleitor_numero, titeleitor_zona, titeleitor_secao,
            observacoes, link_foto
        )

        if existing_data:
            # ATUALIZAR registro existente
            query = f"""
                UPDATE funcionarios_documentos SET
                    Data_Nascimento = %s, Estado_Civil = %s, Nacionalidade = %s, Naturalidade = %s, Genero = %s,
                    Rg_Numero = %s, Rg_OrgaoEmissor = %s, Rg_UfEmissor = %s, Rg_DataEmissao = %s,
                    Cpf_Numero = %s, Ctps_Numero = %s, Ctps_Serie = %s, Pispasep = %s,
                    Cnh_Numero = %s, Cnh_Categoria = %s, Cnh_DataValidade = %s, Cnh_OrgaoEmissor = %s,
                    TitEleitor_Numero = %s, TitEleitor_Zona = %s, TitEleitor_Secao = %s,
                    Observacoes = %s, Link_Foto = %s, Data_Modificacao = NOW()
                WHERE {clause} AND Matricula_Funcionario = %s
            """
            update_params = params + (tenant_param, matricula)
            return self.db.execute_query(query, update_params, fetch_results=False)
        else:
            # INSERIR novo registro
            query = """
                INSERT INTO funcionarios_documentos (
                    tenant_id, Matricula_Funcionario, Data_Nascimento, Estado_Civil, Nacionalidade, Naturalidade, Genero,
                    Rg_Numero, Rg_OrgaoEmissor, Rg_UfEmissor, Rg_DataEmissao, Cpf_Numero,
                    Ctps_Numero, Ctps_Serie, Pispasep, Cnh_Numero, Cnh_Categoria, Cnh_DataValidade, Cnh_OrgaoEmissor,
                    TitEleitor_Numero, TitEleitor_Zona, TitEleitor_Secao, Observacoes, Link_Foto,
                    Data_Criacao, Data_Modificacao
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """
            insert_params = (self.tenant_id, matricula) + params
            return self.db.execute_query(query, insert_params, fetch_results=False)

    def get_funcionario_dados_pessoais_documentos_by_matricula(self, matricula):
        """
        Retorna os dados pessoais e de documentos de um funcionário
        diretamente da tabela 'funcionarios_documentos'.
        """
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                Matricula_Funcionario, Data_Nascimento, Estado_Civil, Nacionalidade, Naturalidade, Genero,
                Rg_Numero, Rg_OrgaoEmissor, Rg_UfEmissor, Rg_DataEmissao,
                Cpf_Numero,
                Ctps_Numero, Ctps_Serie,
                Pispasep,
                Cnh_Numero, Cnh_Categoria, Cnh_DataValidade, Cnh_OrgaoEmissor,
                TitEleitor_Numero, TitEleitor_Zona, TitEleitor_Secao,
                Observacoes, Link_Foto,
                Data_Criacao, Data_Modificacao
            FROM funcionarios_documentos
            WHERE {clause} AND Matricula_Funcionario = %s
        """
        result = self.db.execute_query(query, (tenant_param, matricula), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- MÉTODO PARA EXPORTAÇÃO COMPLETA DE FUNCIONÁRIOS (AGORA MAIS EFICIENTE) ------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_all_funcionarios_completo(self, search_matricula=None, search_nome=None, search_status=None, search_cargo_id=None):
        """
        Retorna uma lista de todos os funcionários com todos os dados associados (pessoais, documentos, endereços, contatos)
        para fins de exportação ou relatórios detalhados, utilizando JOINs.
        """
        f_clause, f_param = self.tenant_clause('f')
        fd_clause, fd_param = self.tenant_clause('fd')
        fe_clause, fe_param = self.tenant_clause('fe')
        fc_clause, fc_param = self.tenant_clause('fc')
        fc2_clause, fc2_param = self.tenant_clause('fc2')
        query = f"""
            SELECT
                f.Matricula, f.Nome_Completo, f.Data_Admissao, f.Status, f.Data_Criacao, f.Data_Modificacao,
                c.Nome_Cargo, n.Nome_Nivel,
                fd.Data_Nascimento, fd.Estado_Civil, fd.Nacionalidade, fd.Naturalidade, fd.Genero,
                fd.Rg_Numero, fd.Rg_OrgaoEmissor, fd.Rg_UfEmissor, fd.Rg_DataEmissao,
                fd.Cpf_Numero,
                fd.Ctps_Numero, fd.Ctps_Serie,
                fd.Pispasep,
                fd.Cnh_Numero, fd.Cnh_Categoria, fd.Cnh_DataValidade, fd.Cnh_OrgaoEmissor,
                fd.TitEleitor_Numero, fd.TitEleitor_Zona, fd.TitEleitor_Secao,
                fd.Observacoes AS Doc_Observacoes, fd.Link_Foto, -- Renomeado para evitar conflito com 'Observacoes' de outras tabelas
                fe.Logradouro AS End_Logradouro, fe.Numero AS End_Numero, fe.Complemento AS End_Complemento,
                fe.Bairro AS End_Bairro, fe.Cidade AS End_Cidade, fe.Estado AS End_Estado, fe.Cep AS End_Cep,
                fc.Valor_Contato AS Tel_Principal, fc2.Valor_Contato AS Email_Pessoal
            FROM
                funcionarios f
            LEFT JOIN cargos c ON f.ID_Cargos = c.ID_Cargos
            LEFT JOIN niveis n ON f.ID_Niveis = n.ID_Niveis
            LEFT JOIN funcionarios_documentos fd ON f.Matricula = fd.Matricula_Funcionario AND {fd_clause}
            LEFT JOIN funcionarios_enderecos fe ON f.Matricula = fe.Matricula_Funcionario AND fe.Tipo_Endereco = 'Residencial' AND {fe_clause}
            LEFT JOIN funcionarios_contatos fc ON f.Matricula = fc.Matricula_Funcionario AND fc.Tipo_Contato = 'Telefone Principal' AND {fc_clause}
            LEFT JOIN funcionarios_contatos fc2 ON f.Matricula = fc2.Matricula_Funcionario AND fc2.Tipo_Contato = 'Email Pessoal' AND {fc2_clause}
            WHERE {f_clause}
        """
        params = [fd_param, fe_param, fc_param, fc2_param, f_param]
        if search_matricula:
            query += " AND f.Matricula LIKE %s"
            params.append(f"%{search_matricula}%")
        if search_nome:
            query += " AND f.Nome_Completo LIKE %s"
            params.append(f"%{search_nome}%")
        if search_status:
            query += " AND f.Status = %s"
            params.append(search_status)
        if search_cargo_id:
            query += " AND f.ID_Cargos = %s"
            params.append(search_cargo_id)

        query += " ORDER BY f.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- MÉTODOS PARA IMPORTAÇÃO COMPLETA DE DADOS DE FUNCIONÁRIOS (IMPORTAÇÃO EM LOTE) NOVIDADE --------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------

    def get_all_matriculas(self):
        """Retorna um conjunto (set) de todas as matrículas de funcionários existentes do tenant."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT Matricula FROM funcionarios WHERE {clause}"
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return {row['Matricula'] for row in results} if results else set()

    def get_all_cpfs(self):
        """Retorna um conjunto (set) de todos os CPFs existentes na tabela de documentos do tenant."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT Cpf_Numero FROM funcionarios_documentos WHERE {clause} AND Cpf_Numero IS NOT NULL AND Cpf_Numero != ''"
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return {row['Cpf_Numero'] for row in results} if results else set()

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: ENDEREÇOS DE FUNCIONÁRIOS ==============================================================================
    # ==================================================================================================================================

    def add_funcionario_endereco(self, matricula, tipo, logradouro, numero, complemento, bairro, cidade, estado, cep):
        """Adiciona um endereço para um funcionário."""
        print(f"    [MANAGER] MÉTODO 'add_funcionario_endereco' INICIADO para matrícula: {matricula}.")
        query = """
            INSERT INTO funcionarios_enderecos
            (tenant_id, Matricula_Funcionario, Tipo_Endereco, Logradouro, Numero, Complemento, Bairro, Cidade, Estado, Cep, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, matricula, tipo, logradouro, numero, complemento, bairro, cidade, estado, cep)
        print(f"    [MANAGER] Executando INSERT em 'funcionarios_enderecos'...")
        success = self.db.execute_query(query, params, fetch_results=False)
        print(f"    [MANAGER] Resultado da execução: {success}")
        return success

    def update_or_add_funcionario_endereco(self, matricula, tipo_endereco, logradouro, numero, complemento, bairro, cidade, estado, cep):
        """Atualiza um endereço de um tipo específico ou o insere se não existir."""
        clause, tenant_param = self.tenant_clause()
        existing_end = self.db.execute_query(
            f"SELECT ID_Funcionario_Endereco FROM funcionarios_enderecos WHERE {clause} AND Matricula_Funcionario = %s AND Tipo_Endereco = %s",
            (tenant_param, matricula, tipo_endereco), fetch_results=True
        )

        if not any([logradouro, numero, bairro, cidade, estado, cep]):
            if existing_end: # Se não há dados novos e existe um antigo, apaga o antigo
                self.db.execute_query(
                    f"DELETE FROM funcionarios_enderecos WHERE {clause} AND ID_Funcionario_Endereco = %s",
                    (tenant_param, existing_end[0]['ID_Funcionario_Endereco']), fetch_results=False
                )
            return

        if existing_end: # Se existe um registro, atualiza
            query = f"""
                UPDATE funcionarios_enderecos SET
                    Logradouro = %s, Numero = %s, Complemento = %s, Bairro = %s,
                    Cidade = %s, Estado = %s, Cep = %s, Data_Modificacao = NOW()
                WHERE {clause} AND ID_Funcionario_Endereco = %s
            """
            params = (logradouro, numero, complemento, bairro, cidade, estado, cep, tenant_param, existing_end[0]['ID_Funcionario_Endereco'])
            self.db.execute_query(query, params, fetch_results=False)
        else: # Se não existe, cria um novo
            self.add_funcionario_endereco(matricula, tipo_endereco, logradouro, numero, complemento, bairro, cidade, estado, cep)

    def get_funcionario_enderecos_by_matricula(self, matricula):
        """Retorna todos os endereços de um funcionário."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT * FROM funcionarios_enderecos WHERE {clause} AND Matricula_Funcionario = %s"
        results = self.db.execute_query(query, (tenant_param, matricula), fetch_results=True)
        return [self._format_date_fields(item) for item in results] if results else []

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: CONTATOS DE FUNCIONÁRIOS ===============================================================================
    # ==================================================================================================================================

    def add_funcionario_contato(self, matricula, tipo, valor, observacoes=None):
        """Adiciona um contato para um funcionário."""
        print(f"    [MANAGER] MÉTODO 'add_funcionario_contato' INICIADO para matrícula: {matricula} | Tipo: {tipo}.")
        query = """
            INSERT INTO funcionarios_contatos
            (tenant_id, Matricula_Funcionario, Tipo_Contato, Valor_Contato, Observacoes, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, matricula, tipo, valor, observacoes)
        print(f"    [MANAGER] Executando INSERT em 'funcionarios_contatos'...")
        success = self.db.execute_query(query, params, fetch_results=False)
        print(f"    [MANAGER] Resultado da execução: {success}")
        return success

    def update_or_add_funcionario_contato(self, matricula, tipo_contato, valor_contato, observacoes=None):
        """Atualiza um contato de um tipo específico ou o insere se não existir."""
        clause, tenant_param = self.tenant_clause()
        existing_contato = self.db.execute_query(
            f"SELECT ID_Funcionario_Contato FROM funcionarios_contatos WHERE {clause} AND Matricula_Funcionario = %s AND Tipo_Contato = %s",
            (tenant_param, matricula, tipo_contato), fetch_results=True
        )

        if not valor_contato:
            if existing_contato: # Se o valor novo é vazio e existe um antigo, apaga
                self.db.execute_query(
                    f"DELETE FROM funcionarios_contatos WHERE {clause} AND ID_Funcionario_Contato = %s",
                    (tenant_param, existing_contato[0]['ID_Funcionario_Contato']), fetch_results=False
                )
            return

        if existing_contato: # Se existe, atualiza
            query = f"""
                UPDATE funcionarios_contatos SET
                    Valor_Contato = %s, Observacoes = %s, Data_Modificacao = NOW()
                WHERE {clause} AND ID_Funcionario_Contato = %s
            """
            params = (valor_contato, observacoes, tenant_param, existing_contato[0]['ID_Funcionario_Contato'])
            self.db.execute_query(query, params, fetch_results=False)
        else: # Se não existe, cria
            self.add_funcionario_contato(matricula, tipo_contato, valor_contato, observacoes)

    def get_funcionario_contatos_by_matricula(self, matricula):
        """Retorna todos os contatos de um funcionário."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT * FROM funcionarios_contatos WHERE {clause} AND Matricula_Funcionario = %s"
        results = self.db.execute_query(query, (tenant_param, matricula), fetch_results=True)
        return [self._format_date_fields(item) for item in results] if results else []

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: CARGOS =================================================================================================
    # ==================================================================================================================================

    def get_all_cargos_for_dropdown(self):
        """Retorna uma lista de cargos para preencher dropdowns."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Cargos, Nome_Cargo FROM cargos WHERE {clause} ORDER BY Nome_Cargo"
        return self.db.execute_query(query, (tenant_param,), fetch_results=True)

    def get_all_cargos(self, search_nome=None):
        """Retorna uma lista de todos os cargos, opcionalmente filtrada."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Cargos, Nome_Cargo, Descricao_Cargo, Cbo, Data_Criacao, Data_Modificacao
            FROM cargos
            WHERE {clause}
        """
        params = [tenant_param]
        if search_nome:
            query += " AND Nome_Cargo LIKE %s"
            params.append(f"%{search_nome}%")

        query += " ORDER BY Nome_Cargo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_cargo(self, nome_cargo, descricao_cargo, cbo):
        """Adiciona um novo cargo ao banco de dados."""
        query = """
            INSERT INTO cargos (tenant_id, Nome_Cargo, Descricao_Cargo, Cbo, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, nome_cargo, descricao_cargo, cbo)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_cargo_by_id(self, cargo_id):
        """Retorna os dados de um cargo pelo ID."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Cargos, Nome_Cargo, Descricao_Cargo, Cbo, Data_Criacao, Data_Modificacao
            FROM cargos
            WHERE {clause} AND ID_Cargos = %s
        """
        result = self.db.execute_query(query, (tenant_param, cargo_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_cargo(self, cargo_id, nome_cargo, descricao_cargo, cbo):
        """Atualiza os dados de um cargo existente."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE cargos
            SET
                Nome_Cargo = %s, Descricao_Cargo = %s, Cbo = %s, Data_Modificacao = NOW()
            WHERE {clause} AND ID_Cargos = %s
        """
        params = (nome_cargo, descricao_cargo, cbo, tenant_param, cargo_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_cargo(self, cargo_id):
        """
        Exclui um cargo do banco de dados.
        Retorna False se houver funcionários associados.
        """
        clause, tenant_param = self.tenant_clause()
        check_query = f"SELECT COUNT(*) AS count FROM funcionarios WHERE {clause} AND ID_Cargos = %s"
        result = self.db.execute_query(check_query, (tenant_param, cargo_id), fetch_results=True)
        if result and result[0]['count'] > 0:
            print(f"Não é possível excluir o cargo ID {cargo_id}: Existem funcionários associados.")
            return False
        query = f"DELETE FROM cargos WHERE {clause} AND ID_Cargos = %s"
        return self.db.execute_query(query, (tenant_param, cargo_id), fetch_results=False)

    def get_cargo_by_nome(self, nome_cargo):
        """Verifica se um cargo com o dado nome já existe."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Cargos FROM cargos WHERE {clause} AND Nome_Cargo = %s"
        result = self.db.execute_query(query, (tenant_param, nome_cargo), fetch_results=True)
        return result[0] if result else None

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: NÍVEIS =================================================================================================
    # ==================================================================================================================================

    def get_all_niveis_for_dropdown(self):
        """Retorna uma lista de níveis para preencher dropdowns."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Niveis, Nome_Nivel FROM niveis WHERE {clause} ORDER BY Nome_Nivel"
        return self.db.execute_query(query, (tenant_param,), fetch_results=True)

    def get_all_niveis(self, search_nome=None):
        """Retorna uma lista de todos os níveis, opcionalmente filtrada."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Niveis, Nome_Nivel, Descricao, Data_Criacao, Data_Modificacao
            FROM niveis
            WHERE {clause}
        """
        params = [tenant_param]
        if search_nome:
            query += " AND Nome_Nivel LIKE %s"
            params.append(f"%{search_nome}%")

        query += " ORDER BY Nome_Nivel"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_nivel(self, nome_nivel, descricao):
        """Adiciona um novo nível ao banco de dados."""
        query = """
            INSERT INTO niveis (tenant_id, Nome_Nivel, Descricao, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, nome_nivel, descricao)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_nivel_by_id(self, nivel_id):
        """Retorna os dados de um nível pelo ID."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            SELECT
                ID_Niveis, Nome_Nivel, Descricao, Data_Criacao, Data_Modificacao
            FROM niveis
            WHERE {clause} AND ID_Niveis = %s
        """
        result = self.db.execute_query(query, (tenant_param, nivel_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_nivel(self, nivel_id, nome_nivel, descricao):
        """Atualiza os dados de um nível existente."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE niveis
            SET
                Nome_Nivel = %s, Descricao = %s, Data_Modificacao = NOW()
            WHERE {clause} AND ID_Niveis = %s
        """
        params = (nome_nivel, descricao, tenant_param, nivel_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_nivel(self, nivel_id):
        """
        Exclui um nível do banco de dados.
        Retorna False se houver funcionários associados.
        """
        clause, tenant_param = self.tenant_clause()
        check_query = f"SELECT COUNT(*) AS count FROM funcionarios WHERE {clause} AND ID_Niveis = %s"
        result = self.db.execute_query(check_query, (tenant_param, nivel_id), fetch_results=True)
        if result and result[0]['count'] > 0:
            print(f"Não é possível excluir o nível ID {nivel_id}: Existem funcionários associados.")
            return False
        query = f"DELETE FROM niveis WHERE {clause} AND ID_Niveis = %s"
        return self.db.execute_query(query, (tenant_param, nivel_id), fetch_results=False)

    def get_nivel_by_nome(self, nome_nivel):
        """Verifica se um nível com o dado nome já existe."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Niveis FROM niveis WHERE {clause} AND Nome_Nivel = %s"
        result = self.db.execute_query(query, (tenant_param, nome_nivel), fetch_results=True)
        return result[0] if result else None

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: SALÁRIOS E BENEFÍCIOS ==================================================================================
    # ==================================================================================================================================

    def get_all_salarios(self, search_cargo_id=None, search_nivel_id=None):
        """
        Retorna uma lista de todos os pacotes salariais, opcionalmente filtrada,
        incluindo informações de cargo e nível.
        """
        clause, tenant_param = self.tenant_clause('s')
        query = f"""
            SELECT
                s.ID_Salarios, s.ID_Cargos, s.ID_Niveis, s.Salario_Base, s.Periculosidade,
                s.Insalubridade, s.Ajuda_De_Custo, s.Vale_Refeicao, s.Gratificacao, s.Cesta_Basica,
                s.Outros_Beneficios, s.Data_Vigencia, c.Nome_Cargo, n.Nome_Nivel,
                s.Data_Criacao, s.Data_Modificacao
            FROM salarios s
            LEFT JOIN cargos c ON s.ID_Cargos = c.ID_Cargos
            LEFT JOIN niveis n ON s.ID_Niveis = n.ID_Niveis
            WHERE {clause}
        """
        params = [tenant_param]

        if search_cargo_id:
            query += " AND s.ID_Cargos = %s"
            params.append(search_cargo_id)
        if search_nivel_id:
            query += " AND s.ID_Niveis = %s"
            params.append(search_nivel_id)

        query += " ORDER BY c.Nome_Cargo, n.Nome_Nivel, s.Data_Vigencia DESC"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_salario(self, id_cargos, id_niveis, salario_base, periculosidade, insalubridade, ajuda_de_custo, vale_refeicao, gratificacao, cesta_basica, outros_beneficios, data_vigencia):
        """Adiciona um novo pacote salarial ao banco de dados."""
        query = """
            INSERT INTO salarios (tenant_id, ID_Cargos, ID_Niveis, Salario_Base, Periculosidade, Insalubridade, Ajuda_De_Custo, Vale_Refeicao, Gratificacao, Cesta_Basica, Outros_Beneficios, Data_Vigencia, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, id_cargos, id_niveis, salario_base, periculosidade, insalubridade, ajuda_de_custo, vale_refeicao, gratificacao, cesta_basica, outros_beneficios, data_vigencia)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_salario_by_id(self, salario_id):
        """Retorna os dados de um pacote salarial pelo ID."""
        clause, tenant_param = self.tenant_clause('s')
        query = f"""
            SELECT
                s.ID_Salarios, s.ID_Cargos, s.ID_Niveis, s.Salario_Base, s.Periculosidade,
                s.Insalubridade, s.Ajuda_De_Custo, s.Vale_Refeicao, s.Gratificacao, s.Cesta_Basica,
                s.Outros_Beneficios, s.Data_Vigencia, c.Nome_Cargo, n.Nome_Nivel,
                s.Data_Criacao, s.Data_Modificacao
            FROM salarios s
            LEFT JOIN cargos c ON s.ID_Cargos = c.ID_Cargos
            LEFT JOIN niveis n ON s.ID_Niveis = n.ID_Niveis
            WHERE {clause} AND s.ID_Salarios = %s
        """
        result = self.db.execute_query(query, (tenant_param, salario_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_salario(self, salario_id, id_cargos, id_niveis, salario_base, periculosidade, insalubridade, ajuda_de_custo, vale_refeicao, gratificacao, cesta_basica, outros_beneficios, data_vigencia):
        """Atualiza os dados de um pacote salarial existente."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE salarios
            SET
                ID_Cargos = %s, ID_Niveis = %s, Salario_Base = %s, Periculosidade = %s, Insalubridade = %s,
                Ajuda_De_Custo = %s, Vale_Refeicao = %s, Gratificacao = %s, Cesta_Basica = %s,
                Outros_Beneficios = %s, Data_Vigencia = %s, Data_Modificacao = NOW()
            WHERE {clause} AND ID_Salarios = %s
        """
        params = (id_cargos, id_niveis, salario_base, periculosidade, insalubridade, ajuda_de_custo, vale_refeicao, gratificacao, cesta_basica, outros_beneficios, data_vigencia, tenant_param, salario_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_salario(self, salario_id):
        """Exclui um pacote salarial do banco de dados."""
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM salarios WHERE {clause} AND ID_Salarios = %s"
        return self.db.execute_query(query, (tenant_param, salario_id), fetch_results=False)

    def get_salario_by_cargo_nivel_vigencia(self, id_cargos, id_niveis, data_vigencia):
        """Verifica se já existe um pacote salarial para a mesma combinação de cargo, nível e data de vigência."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Salarios FROM salarios WHERE {clause} AND ID_Cargos = %s AND ID_Niveis = %s AND Data_Vigencia = %s"
        result = self.db.execute_query(query, (tenant_param, id_cargos, id_niveis, data_vigencia), fetch_results=True)
        return result[0] if result else None

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: FÉRIAS =================================================================================================
    # ==================================================================================================================================

    def get_all_ferias(self, search_matricula=None, search_status=None, search_periodo_inicio=None, search_periodo_fim=None):
        """
        Retorna uma lista de todos os registros de férias, opcionalmente filtrada,
        incluindo informações do funcionário.
        """
        f_clause, f_param = self.tenant_clause('f')
        func_clause, func_param = self.tenant_clause('func')
        query = f"""
            SELECT
                f.ID_Ferias, f.Matricula_Funcionario, f.Periodo_Aquisitivo_Inicio, f.Periodo_Aquisitivo_Fim,
                f.Data_Inicio_Gozo, f.Data_Fim_Gozo, f.Dias_Gozo, f.Status_Ferias, f.Observacoes,
                func.Nome_Completo AS Nome_Funcionario, f.Data_Criacao, f.Data_Modificacao
            FROM ferias f
            LEFT JOIN funcionarios func ON f.Matricula_Funcionario = func.Matricula AND {func_clause}
            WHERE {f_clause}
        """
        params = [func_param, f_param]

        if search_matricula:
            query += " AND f.Matricula_Funcionario LIKE %s"
            params.append(f"%{search_matricula}%")
        if search_status:
            query += " AND f.Status_Ferias = %s"
            params.append(search_status)
        if search_periodo_inicio:
            query += " AND f.Periodo_Aquisitivo_Inicio >= %s"
            params.append(search_periodo_inicio)
        if search_periodo_fim:
            query += " AND f.Periodo_Aquisitivo_Fim <= %s"
            params.append(search_periodo_fim)

        query += " ORDER BY f.Periodo_Aquisitivo_Inicio DESC, func.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_ferias(self, matricula_funcionario, periodo_aquisitivo_inicio, periodo_aquisitivo_fim, data_inicio_gozo, data_fim_gozo, dias_gozo, status_ferias, observacoes):
        """Adiciona um novo registro de férias ao banco de dados."""
        query = """
            INSERT INTO ferias (tenant_id, Matricula_Funcionario, Periodo_Aquisitivo_Inicio, Periodo_Aquisitivo_Fim, Data_Inicio_Gozo, Data_Fim_Gozo, Dias_Gozo, Status_Ferias, Observacoes, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, matricula_funcionario, periodo_aquisitivo_inicio, periodo_aquisitivo_fim, data_inicio_gozo, data_fim_gozo, dias_gozo, status_ferias, observacoes)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_ferias_by_id(self, ferias_id):
        """Retorna os dados de um registro de férias pelo ID."""
        f_clause, f_param = self.tenant_clause('f')
        func_clause, func_param = self.tenant_clause('func')
        query = f"""
            SELECT
                f.ID_Ferias, f.Matricula_Funcionario, f.Periodo_Aquisitivo_Inicio, f.Periodo_Aquisitivo_Fim,
                f.Data_Inicio_Gozo, f.Data_Fim_Gozo, f.Dias_Gozo, f.Status_Ferias, f.Observacoes,
                func.Nome_Completo AS Nome_Funcionario, f.Data_Criacao, f.Data_Modificacao
            FROM ferias f
            LEFT JOIN funcionarios func ON f.Matricula_Funcionario = func.Matricula AND {func_clause}
            WHERE {f_clause} AND f.ID_Ferias = %s
        """
        result = self.db.execute_query(query, (func_param, f_param, ferias_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_ferias(self, ferias_id, matricula_funcionario, periodo_aquisitivo_inicio, periodo_aquisitivo_fim, data_inicio_gozo, data_fim_gozo, dias_gozo, status_ferias, observacoes):
        """Atualiza os dados de um registro de férias existente."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE ferias
            SET
                Matricula_Funcionario = %s, Periodo_Aquisitivo_Inicio = %s, Periodo_Aquisitivo_Fim = %s,
                Data_Inicio_Gozo = %s, Data_Fim_Gozo = %s, Dias_Gozo = %s, Status_Ferias = %s,
                Observacoes = %s, Data_Modificacao = NOW()
            WHERE {clause} AND ID_Ferias = %s
        """
        params = (matricula_funcionario, periodo_aquisitivo_inicio, periodo_aquisitivo_fim, data_inicio_gozo, data_fim_gozo, dias_gozo, status_ferias, observacoes, tenant_param, ferias_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_ferias(self, ferias_id):
        """Exclui um registro de férias do banco de dados."""
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM ferias WHERE {clause} AND ID_Ferias = %s"
        return self.db.execute_query(query, (tenant_param, ferias_id), fetch_results=False)

    # ==================================================================================================================================
    # === MÉTODOS DO SUBMÓDULO: DEPENDENTES ============================================================================================
    # ==================================================================================================================================

    def get_all_dependentes(self, search_matricula=None, search_nome=None, search_parentesco=None):
        """
        Retorna uma lista de todos os dependentes, opcionalmente filtrada,
        incluindo informações do funcionário.
        """
        d_clause, d_param = self.tenant_clause('d')
        func_clause, func_param = self.tenant_clause('func')
        query = f"""
            SELECT
                d.ID_Dependente, d.Matricula_Funcionario, d.Nome_Completo, d.Parentesco, d.Data_Nascimento,
                d.Cpf, d.Contato_Emergencia, d.Telefone_Emergencia, d.Observacoes,
                func.Nome_Completo AS Nome_Funcionario, d.Data_Criacao, d.Data_Modificacao
            FROM dependentes d
            LEFT JOIN funcionarios func ON d.Matricula_Funcionario = func.Matricula AND {func_clause}
            WHERE {d_clause}
        """
        params = [func_param, d_param]

        if search_matricula:
            query += " AND d.Matricula_Funcionario LIKE %s"
            params.append(f"%{search_matricula}%")
        if search_nome:
            query += " AND d.Nome_Completo LIKE %s"
            params.append(f"%{search_nome}%")
        if search_parentesco:
            query += " AND d.Parentesco = %s"
            params.append(search_parentesco)

        query += " ORDER BY func.Nome_Completo, d.Nome_Completo"

        results = self.db.execute_query(query, tuple(params), fetch_results=True)
        if results:
            return [self._format_date_fields(item) for item in results]
        return results

    def add_dependente(self, matricula_funcionario, nome_completo, parentesco, data_nascimento, cpf, contato_emergencia, telefone_emergencia, observacoes):
        """Adiciona um novo dependente ao banco de dados."""
        query = """
            INSERT INTO dependentes (tenant_id, Matricula_Funcionario, Nome_Completo, Parentesco, Data_Nascimento, Cpf, Contato_Emergencia, Telefone_Emergencia, Observacoes, Data_Criacao, Data_Modificacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (self.tenant_id, matricula_funcionario, nome_completo, parentesco, data_nascimento, cpf, contato_emergencia, telefone_emergencia, observacoes)
        return self.db.execute_query(query, params, fetch_results=False)

    def get_dependente_by_id(self, dependente_id):
        """Retorna os dados de um dependente pelo ID."""
        d_clause, d_param = self.tenant_clause('d')
        func_clause, func_param = self.tenant_clause('func')
        query = f"""
            SELECT
                d.ID_Dependente, d.Matricula_Funcionario, d.Nome_Completo, d.Parentesco, d.Data_Nascimento,
                d.Cpf, d.Contato_Emergencia, d.Telefone_Emergencia, d.Observacoes,
                func.Nome_Completo AS Nome_Funcionario, d.Data_Criacao, d.Data_Modificacao
            FROM dependentes d
            LEFT JOIN funcionarios func ON d.Matricula_Funcionario = func.Matricula AND {func_clause}
            WHERE {d_clause} AND d.ID_Dependente = %s
        """
        result = self.db.execute_query(query, (func_param, d_param, dependente_id), fetch_results=True)
        if result:
            return self._format_date_fields(result[0])
        return None

    def update_dependente(self, dependente_id, matricula_funcionario, nome_completo, parentesco, data_nascimento, cpf, contato_emergencia, telefone_emergencia, observacoes):
        """Atualiza os dados de um dependente existente."""
        clause, tenant_param = self.tenant_clause()
        query = f"""
            UPDATE dependentes
            SET
                Matricula_Funcionario = %s, Nome_Completo = %s, Parentesco = %s, Data_Nascimento = %s,
                Cpf = %s, Contato_Emergencia = %s, Telefone_Emergencia = %s, Observacoes = %s,
                Data_Modificacao = NOW()
            WHERE {clause} AND ID_Dependente = %s
        """
        params = (matricula_funcionario, nome_completo, parentesco, data_nascimento, cpf, contato_emergencia, telefone_emergencia, observacoes, tenant_param, dependente_id)
        return self.db.execute_query(query, params, fetch_results=False)

    def delete_dependente(self, dependente_id):
        """Exclui um dependente do banco de dados."""
        clause, tenant_param = self.tenant_clause()
        query = f"DELETE FROM dependentes WHERE {clause} AND ID_Dependente = %s"
        return self.db.execute_query(query, (tenant_param, dependente_id), fetch_results=False)

    def get_dependente_by_cpf(self, cpf, exclude_id=None):
        """Verifica se um dependente com o dado CPF já existe (para CPF único)."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT ID_Dependente FROM dependentes WHERE {clause} AND Cpf = %s"
        params = [tenant_param, cpf]
        if exclude_id:
            query += " AND ID_Dependente != %s"
            params.append(exclude_id)
        result = self.db.execute_query(query, tuple(params), fetch_results=True)
        return result[0] if result else None

    # ==================================================================================================================================
    # === MÉTODOS PARA DASHBOARD E RELATÓRIOS (MÓDULO PESSOAL) =========================================================================
    # ==================================================================================================================================

    def get_funcionario_status_counts(self):
        """Retorna a contagem de funcionários por status."""
        clause, tenant_param = self.tenant_clause()
        query = f"SELECT Status, COUNT(*) AS Total FROM funcionarios WHERE {clause} GROUP BY Status"
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return {item['Status']: item['Total'] for item in results} if results else {}

    def get_funcionarios_by_cargo(self):
        """Retorna a contagem de funcionários por cargo."""
        clause, tenant_param = self.tenant_clause('f')
        query = f"""
            SELECT c.Nome_Cargo, COUNT(f.Matricula) AS Total
            FROM funcionarios f
            JOIN cargos c ON f.ID_Cargos = c.ID_Cargos
            WHERE {clause}
            GROUP BY c.Nome_Cargo
            ORDER BY Total DESC
        """
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return results if results else []

    def get_funcionarios_by_nivel(self):
        """Retorna a contagem de funcionários por nível."""
        clause, tenant_param = self.tenant_clause('f')
        query = f"""
            SELECT n.Nome_Nivel, COUNT(f.Matricula) AS Total
            FROM funcionarios f
            JOIN niveis n ON f.ID_Niveis = n.ID_Niveis
            WHERE {clause}
            GROUP BY n.Nome_Nivel
            ORDER BY Total DESC
        """
        results = self.db.execute_query(query, (tenant_param,), fetch_results=True)
        return results if results else []

    def get_proximas_ferias(self, dias_antecedencia=60):
        """
        Retorna uma lista de férias que estão 'Programada' ou 'Gozo' e que
        o período de gozo *inicia ou está ativo* nos próximos 'dias_antecedencia'
        ou termina nos próximos 'dias_antecedencia' a partir da data atual.
        """
        today = date.today()
        # Calculamos a data limite futura (hoje + 60 dias)
        future_date_limit = today + timedelta(days=dias_antecedencia)

        f_clause, f_param = self.tenant_clause('f')
        p_clause, p_param = self.tenant_clause('p')
        query = f"""
            SELECT
                f.ID_Ferias,
                f.Matricula_Funcionario,
                p.Nome_Completo AS Nome_Funcionario,
                f.Periodo_Aquisitivo_Inicio,
                f.Periodo_Aquisitivo_Fim,
                f.Data_Inicio_Gozo,
                f.Data_Fim_Gozo,
                f.Dias_Gozo,
                f.Status_Ferias
            FROM
                ferias f
            JOIN
                funcionarios p ON f.Matricula_Funcionario = p.Matricula AND {p_clause}
            WHERE
                {f_clause} AND (
                -- Férias PROGRAMADAS com Data_Inicio_Gozo no futuro próximo
                (f.Status_Ferias = 'Programada' AND
                 f.Data_Inicio_Gozo IS NOT NULL AND
                 f.Data_Inicio_Gozo BETWEEN %s AND %s)
                OR
                -- Férias em GOZO que ainda não terminaram (ou terminam em breve)
                (f.Status_Ferias = 'Gozo' AND
                 f.Data_Fim_Gozo IS NOT NULL AND
                 f.Data_Fim_Gozo >= %s) -- Que terminam de hoje em diante
                )
            ORDER BY
                f.Data_Inicio_Gozo ASC
        """
        params = (p_param, f_param, today, future_date_limit, today) # Parâmetros para os BETWEEN e o >=

        results = self.db.execute_query(query, params, fetch_results=True)

        if results:
            return [self._format_date_fields(item) for item in results]
        return results


    def get_aniversariantes_do_mes(self, mes=None):
        """
        Retorna uma lista de funcionários que fazem aniversário no mês especificado.
        Se 'mes' for None, usa o mês atual.
        """
        if mes is None:
            mes = date.today().month

        fd_clause, fd_param = self.tenant_clause('fd')
        f_clause, f_param = self.tenant_clause('f')
        query = f"""
            SELECT
                fd.Matricula_Funcionario AS Matricula,
                f.Nome_Completo,
                fd.Data_Nascimento,
                c.Nome_Cargo,
                fd.Naturalidade -- Adicionado naturalidade ao retorno
            FROM
                funcionarios_documentos fd
            JOIN
                funcionarios f ON fd.Matricula_Funcionario = f.Matricula AND {f_clause}
            LEFT JOIN
                cargos c ON f.ID_Cargos = c.ID_Cargos
            WHERE
                {fd_clause} AND
                fd.Data_Nascimento IS NOT NULL AND -- Garante que a data de nascimento existe
                MONTH(fd.Data_Nascimento) = %s AND
                f.Status = 'Ativo'
            ORDER BY
                DAY(fd.Data_Nascimento), f.Nome_Completo
        """
        results = self.db.execute_query(query, (f_param, fd_param, mes), fetch_results=True)

        if results:
            return [self._format_date_fields(item) for item in results]
        return []

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- NOVO MÉTODO: Períodos de Experiência à Vencer -------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_periodos_experiencia_a_vencer(self):
        """
        Retorna funcionários com períodos de experiência (30 ou 90 dias) próximos do vencimento
        (até 15 dias antes) ou recém-vencidos (até 7 dias depois).
        Assume período de 90 dias total, com um primeiro vencimento opcional aos 30 dias.
        """
        hoje = date.today()

        # Definindo as janelas de alerta conforme sua solicitação
        alerta_futuro_dias = 15
        alerta_passado_dias = 7

        clause, tenant_param = self.tenant_clause('f')
        query = f"""
            SELECT
                f.Matricula,
                f.Nome_Completo,
                f.Data_Admissao,
                c.Nome_Cargo,
                f.Status
            FROM
                funcionarios f
            LEFT JOIN
                cargos c ON f.ID_Cargos = c.ID_Cargos
            WHERE
                {clause} AND
                f.Status = 'Ativo' -- Apenas funcionários ativos
            ORDER BY
                f.Data_Admissao ASC
        """

        funcionarios = self.db.execute_query(query, (tenant_param,), fetch_results=True)

        alertas = []
        if funcionarios:
            for func in funcionarios:
                data_admissao = func['Data_Admissao']

                if data_admissao:
                    # Calcula as datas de vencimento dos períodos
                    vencimento_30_dias = data_admissao + timedelta(days=30)
                    vencimento_90_dias = data_admissao + timedelta(days=90)

                    # Lógica para o 1º Período (30 Dias)
                    # Alerta se estiver nos próximos 15 dias OU se venceu nos últimos 7 dias
                    if (vencimento_30_dias >= hoje and vencimento_30_dias <= hoje + timedelta(days=alerta_futuro_dias)) or \
                       (vencimento_30_dias < hoje and hoje <= vencimento_30_dias + timedelta(days=alerta_passado_dias)):

                        # Adiciona o alerta apenas se o 2º período ainda não venceu, para evitar alertas de 30 dias de funcionários já no período de 90
                        if hoje < vencimento_90_dias:
                            alerta = func.copy()
                            alerta['Tipo_Vencimento'] = '1º Período de Experiência (30 Dias)'
                            alerta['Data_Vencimento'] = vencimento_30_dias
                            alerta['Dias_Restantes'] = (vencimento_30_dias - hoje).days
                            alertas.append(alerta)

                    # Lógica para o 2º Período (90 Dias - Fim)
                    # Alerta se estiver nos próximos 15 dias OU se venceu nos últimos 7 dias
                    if (vencimento_90_dias >= hoje and vencimento_90_dias <= hoje + timedelta(days=alerta_futuro_dias)) or \
                       (vencimento_90_dias < hoje and hoje <= vencimento_90_dias + timedelta(days=alerta_passado_dias)):

                        # Evita duplicidade se o alerta de 30 e 90 dias caírem no mesmo "dias_alerta" para o mesmo funcionário
                        # e garante que o alerta de 90 dias é o mais relevante se ambos se aplicarem
                        # A lógica de desduplicação pode ser mais robusta se necessário, mas para este caso,
                        # um simples 'if' para evitar o 30dias se o 90dias já está em alerta pode ser suficiente.
                        # Ou podemos usar um set para garantir unicidade por (Matricula, Tipo_Vencimento)

                        # Para evitar duplicatas e priorizar o alerta de 90 dias se ambos forem válidos
                        # e caírem na mesma janela de alerta para o mesmo funcionário:
                        # Se o alerta de 30 dias já foi adicionado para este funcionário, e o alerta de 90 dias é mais recente/relevante,
                        # podemos substituir ou garantir que apenas um seja exibido.
                        # Para simplicidade e seguindo a solicitação de "não poluir", vamos garantir que o alerta de 90 dias
                        # seja o último a ser adicionado se ambos se aplicarem, e remover o de 30 dias se o de 90 dias for mais relevante.

                        # Uma forma mais limpa de evitar duplicatas e priorizar o alerta de 90 dias:
                        # Crie uma lista temporária para o funcionário atual e adicione o alerta de 90 dias.
                        # Se o alerta de 30 dias já foi adicionado e o de 90 dias também se aplica,
                        # o de 90 dias é geralmente mais crítico.

                        # Para garantir que não haja alertas duplicados para o mesmo funcionário no mesmo tipo de vencimento
                        # e que a prioridade seja o vencimento mais próximo ou o de 90 dias se ambos caírem na janela:

                        # Verifica se já existe um alerta de 30 dias para este funcionário e se o alerta de 90 dias é mais iminente/relevante
                        # (ex: se o de 90 dias está mais próximo de hoje do que o de 30 dias, ou se o de 30 dias já passou e o de 90 está na janela)

                        # Uma abordagem mais simples para evitar poluição: se o 90 dias está na janela, apenas mostre ele.
                        # Isso pode ser feito garantindo que o 30 dias só apareça se o 90 dias *não* estiver na janela de alerta.

                        # Melhorando a lógica de exclusão/priorização:
                        # Se o alerta de 90 dias está na janela, ele é o mais importante.
                        # Remove qualquer alerta de 30 dias para o mesmo funcionário que possa ter sido adicionado antes.
                        alertas = [a for a in alertas if not (a['Matricula'] == func['Matricula'] and a['Tipo_Vencimento'] == '1º Período de Experiência (30 Dias)')]

                        alerta = func.copy()
                        alerta['Tipo_Vencimento'] = '2º Período de Experiência (90 Dias - Fim)'
                        alerta['Data_Vencimento'] = vencimento_90_dias
                        alerta['Dias_Restantes'] = (vencimento_90_dias - hoje).days
                        alertas.append(alerta)

        # Opcional: Ordenar por Data_Vencimento para melhor visualização
        alertas.sort(key=lambda x: x['Data_Vencimento'])

        # Formata as datas no retorno
        return [self._format_date_fields(item) for item in alertas]

    # ----------------------------------------------------------------------------------------------------------------------------------
    # --- NOVO MÉTODO: Vencimento de Documentos e Contratos ---------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------
    def get_documentos_contratos_a_vencer(self, dias_alerta_futuro=30, dias_alerta_passado=7):
        """
        Retorna funcionários com documentos ou contratos específicos próximos do vencimento
        (nos próximos 'dias_alerta_futuro' dias) ou recém-vencidos (nos últimos 'dias_alerta_passado' dias).
        Foco inicial em CNH.
        """
        hoje = date.today()

        f_clause, f_param = self.tenant_clause('f')
        fd_clause, fd_param = self.tenant_clause('fd')
        query = f"""
            SELECT
                f.Matricula,
                f.Nome_Completo,
                f.Data_Admissao,
                c.Nome_Cargo,
                f.Status,
                fd.Cnh_Numero,
                fd.Cnh_DataValidade
            FROM
                funcionarios f
            LEFT JOIN
                cargos c ON f.ID_Cargos = c.ID_Cargos
            LEFT JOIN
                funcionarios_documentos fd ON f.Matricula = fd.Matricula_Funcionario AND {fd_clause}
            WHERE
                {f_clause} AND
                f.Status = 'Ativo' AND -- Apenas funcionários ativos
                fd.Cnh_DataValidade IS NOT NULL -- Apenas documentos com data de validade
            ORDER BY
                fd.Cnh_DataValidade ASC, f.Nome_Completo ASC
        """

        documentos_cnh = self.db.execute_query(query, (fd_param, f_param), fetch_results=True)

        alertas = []
        if documentos_cnh:
            for doc in documentos_cnh:
                data_validade = doc['Cnh_DataValidade']

                if data_validade:
                    # Verifica se a CNH está próxima do vencimento ou recém-vencida
                    if (data_validade >= hoje and data_validade <= hoje + timedelta(days=dias_alerta_futuro)) or \
                       (data_validade < hoje and hoje <= data_validade + timedelta(days=dias_alerta_passado)):

                        alerta = doc.copy()
                        alerta['Tipo_Documento_Contrato'] = 'CNH'
                        alerta['Numero_Documento_Contrato'] = doc['Cnh_Numero']
                        alerta['Data_Vencimento_Contrato'] = data_validade
                        alerta['Dias_Restantes'] = (data_validade - hoje).days
                        alertas.append(alerta)

        # Futuramente, podemos adicionar lógica para outros tipos de documentos ou contratos aqui,
        # consultando outras tabelas ou outras colunas de funcionarios_documentos.

        return [self._format_date_fields(item) for item in alertas]
