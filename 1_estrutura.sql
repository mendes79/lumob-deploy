-- MySQL dump 10.13  Distrib 8.0.35, for Win64 (x86_64)
--
-- Host: localhost    Database: lumob
-- ------------------------------------------------------
-- Server version	8.0.35

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `arts`
--

DROP TABLE IF EXISTS `arts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `arts` (
  `ID_Arts` int NOT NULL AUTO_INCREMENT,
  `ID_Obras` int NOT NULL,
  `Numero_Art` varchar(100) NOT NULL,
  `Data_Pagamento` date DEFAULT NULL,
  `Valor_Pagamento` decimal(10,2) DEFAULT NULL,
  `Status_Art` varchar(100) DEFAULT NULL,
  `Data_Criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Arts`),
  UNIQUE KEY `Numero_Art` (`Numero_Art`),
  KEY `ID_Obras` (`ID_Obras`),
  CONSTRAINT `arts_ibfk_1` FOREIGN KEY (`ID_Obras`) REFERENCES `obras` (`ID_Obras`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `asos`
--

DROP TABLE IF EXISTS `asos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asos` (
  `ID_ASO` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do ASO',
  `Matricula_Funcionario` varchar(20) NOT NULL COMMENT 'Chave estrangeira para a tabela funcionarios (Matricula)',
  `Tipo_ASO` enum('Admissional','Periódico','Mudança de Função','Retorno ao Trabalho','Demissional','Outro') NOT NULL COMMENT 'Tipo de ASO',
  `Data_Emissao` date NOT NULL COMMENT 'Data de emissão do ASO',
  `Data_Vencimento` date DEFAULT NULL COMMENT 'Data de vencimento do ASO (para periódicos)',
  `Resultado` enum('Apto','Inapto','Apto com Restrições') NOT NULL COMMENT 'Resultado do exame médico',
  `Medico_Responsavel` varchar(255) DEFAULT NULL COMMENT 'Nome do médico responsável pelo ASO',
  `Observacoes` text COMMENT 'Observações adicionais sobre o ASO',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_ASO`),
  KEY `Matricula_Funcionario` (`Matricula_Funcionario`),
  CONSTRAINT `asos_ibfk_1` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela para controle de Atestados de Saúde Ocupacional (ASOs)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `avancos_fisicos`
--

DROP TABLE IF EXISTS `avancos_fisicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `avancos_fisicos` (
  `ID_Avancos_Fisicos` int NOT NULL AUTO_INCREMENT,
  `ID_Obras` int NOT NULL,
  `Percentual_Avanco_Fisico` decimal(5,2) DEFAULT NULL,
  `Data_Avanco` date NOT NULL,
  `Data_Criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Avancos_Fisicos`),
  KEY `ID_Obras` (`ID_Obras`),
  CONSTRAINT `avancos_fisicos_ibfk_1` FOREIGN KEY (`ID_Obras`) REFERENCES `obras` (`ID_Obras`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cargos`
--

DROP TABLE IF EXISTS `cargos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cargos` (
  `ID_Cargos` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do cargo',
  `Nome_Cargo` varchar(100) NOT NULL COMMENT 'Nome do cargo (ex: Engenheiro Civil, Pedreiro)',
  `Descricao_Cargo` text COMMENT 'Descrição das responsabilidades do cargo',
  `Cbo` varchar(10) DEFAULT NULL COMMENT 'Código Brasileiro de Ocupações',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Cargos`),
  UNIQUE KEY `Nome_Cargo` (`Nome_Cargo`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela de Cargos Base da Empresa';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `clientes`
--

DROP TABLE IF EXISTS `clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clientes` (
  `ID_Clientes` int NOT NULL AUTO_INCREMENT,
  `Nome_Cliente` varchar(255) NOT NULL,
  `CNPJ_Cliente` varchar(18) DEFAULT NULL,
  `Razao_Social_Cliente` varchar(300) DEFAULT NULL,
  `Endereco_Cliente` varchar(500) DEFAULT NULL,
  `Telefone_Cliente` varchar(20) DEFAULT NULL,
  `Email_Cliente` varchar(255) DEFAULT NULL,
  `Contato_Principal_Nome` varchar(200) DEFAULT NULL,
  `Data_Criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Clientes`),
  UNIQUE KEY `CNPJ_Cliente` (`CNPJ_Cliente`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `contratos`
--

DROP TABLE IF EXISTS `contratos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contratos` (
  `ID_Contratos` int NOT NULL AUTO_INCREMENT,
  `ID_Clientes` int NOT NULL,
  `Numero_Contrato` varchar(50) NOT NULL,
  `Valor_Contrato` decimal(18,2) NOT NULL,
  `Data_Assinatura` date NOT NULL,
  `Data_Ordem_Inicio` date DEFAULT NULL,
  `Prazo_Contrato_Dias` int DEFAULT NULL,
  `Data_Termino_Previsto` date DEFAULT NULL,
  `Status_Contrato` varchar(100) NOT NULL,
  `Observacoes` varchar(1000) DEFAULT NULL,
  `Data_Criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Contratos`),
  UNIQUE KEY `Numero_Contrato` (`Numero_Contrato`),
  KEY `ID_Clientes` (`ID_Clientes`),
  CONSTRAINT `contratos_ibfk_1` FOREIGN KEY (`ID_Clientes`) REFERENCES `clientes` (`ID_Clientes`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dependentes`
--

DROP TABLE IF EXISTS `dependentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dependentes` (
  `ID_Dependente` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do dependente',
  `Matricula_Funcionario` varchar(20) NOT NULL COMMENT 'Chave estrangeira para a tabela funcionarios (Matricula)',
  `Nome_Completo` varchar(255) NOT NULL COMMENT 'Nome completo do dependente',
  `Parentesco` enum('Filho(a)','Cônjuge','Pai','Mãe','Irmão(ã)','Outro') NOT NULL COMMENT 'Grau de parentesco com o funcionário',
  `Data_Nascimento` date DEFAULT NULL COMMENT 'Data de nascimento do dependente',
  `Cpf` varchar(14) DEFAULT NULL COMMENT 'Número do Cadastro de Pessoa Física do dependente (opcional, pode ser NULL)',
  `Contato_Emergencia` tinyint(1) DEFAULT '0' COMMENT 'Indica se este dependente é um contato de emergência',
  `Telefone_Emergencia` varchar(20) DEFAULT NULL COMMENT 'Telefone para contato de emergência (se for contato de emergência)',
  `Observacoes` text COMMENT 'Observações adicionais sobre o dependente',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Dependente`),
  UNIQUE KEY `Cpf` (`Cpf`),
  KEY `Matricula_Funcionario` (`Matricula_Funcionario`),
  CONSTRAINT `dependentes_ibfk_1` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela para controle de Dependentes e Contatos de Emergência de Funcionários';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ferias`
--

DROP TABLE IF EXISTS `ferias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ferias` (
  `ID_Ferias` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do registro de férias',
  `Matricula_Funcionario` varchar(20) NOT NULL COMMENT 'Chave estrangeira para a tabela funcionarios (Matricula)',
  `Periodo_Aquisitivo_Inicio` date NOT NULL COMMENT 'Data de início do período aquisitivo de férias',
  `Periodo_Aquisitivo_Fim` date NOT NULL COMMENT 'Data de fim do período aquisitivo de férias',
  `Data_Inicio_Gozo` date DEFAULT NULL COMMENT 'Data de início do gozo das férias',
  `Data_Fim_Gozo` date DEFAULT NULL COMMENT 'Data de fim do gozo das férias',
  `Dias_Gozo` int DEFAULT NULL COMMENT 'Número de dias de gozo das férias',
  `Status_Ferias` enum('Programada','Aprovada','Gozo','Concluída','Cancelada') NOT NULL DEFAULT 'Programada' COMMENT 'Status atual das férias',
  `Observacoes` text COMMENT 'Observações adicionais sobre as férias',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Ferias`),
  KEY `Matricula_Funcionario` (`Matricula_Funcionario`),
  CONSTRAINT `ferias_ibfk_1` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela para controle de Férias de Funcionários';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `funcionarios`
--

DROP TABLE IF EXISTS `funcionarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `funcionarios` (
  `Matricula` varchar(20) NOT NULL COMMENT 'Matrícula ou código único e exclusivo do funcionário',
  `Nome_Completo` varchar(255) NOT NULL COMMENT 'Nome completo do funcionário',
  `Data_Admissao` date NOT NULL COMMENT 'Data de admissão do funcionário na empresa',
  `ID_Cargos` int NOT NULL COMMENT 'Chave estrangeira para a tabela cargos',
  `ID_Niveis` int NOT NULL COMMENT 'Chave estrangeira para a tabela niveis',
  `Status` enum('Ativo','Inativo','Ferias','Afastado') NOT NULL DEFAULT 'Ativo' COMMENT 'Status atual do funcionário na empresa',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  `Tipo_Contratacao` enum('CLT','PJ','Temporario') NOT NULL DEFAULT 'CLT',
  PRIMARY KEY (`Matricula`),
  KEY `ID_Cargos` (`ID_Cargos`),
  KEY `ID_Niveis` (`ID_Niveis`),
  CONSTRAINT `funcionarios_ibfk_1` FOREIGN KEY (`ID_Cargos`) REFERENCES `cargos` (`ID_Cargos`) ON DELETE RESTRICT,
  CONSTRAINT `funcionarios_ibfk_2` FOREIGN KEY (`ID_Niveis`) REFERENCES `niveis` (`ID_Niveis`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela principal de Funcionários';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `funcionarios_contatos`
--

DROP TABLE IF EXISTS `funcionarios_contatos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `funcionarios_contatos` (
  `ID_Funcionario_Contato` int NOT NULL AUTO_INCREMENT COMMENT 'ID único do contato do funcionário',
  `Matricula_Funcionario` varchar(20) NOT NULL COMMENT 'Chave estrangeira para a tabela funcionarios (Matricula)',
  `Tipo_Contato` varchar(50) NOT NULL COMMENT 'Tipo de contato (ex: Telefone Celular, Email Pessoal, Telefone Fixo)',
  `Valor_Contato` varchar(255) NOT NULL COMMENT 'O valor do contato (número de telefone, endereço de email, etc.)',
  `Observacoes` text COMMENT 'Observações adicionais sobre o contato',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Funcionario_Contato`),
  UNIQUE KEY `Matricula_Funcionario` (`Matricula_Funcionario`,`Tipo_Contato`,`Valor_Contato`),
  CONSTRAINT `funcionarios_contatos_ibfk_1` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=106 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Armazena informações de contato dos funcionários';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `funcionarios_documentos`
--

DROP TABLE IF EXISTS `funcionarios_documentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `funcionarios_documentos` (
  `Matricula_Funcionario` varchar(20) NOT NULL,
  `Data_Nascimento` date DEFAULT NULL,
  `Estado_Civil` enum('Solteiro(a)','Casado(a)','Divorciado(a)','Viuvo(a)','Uniao Estavel') DEFAULT NULL,
  `Nacionalidade` varchar(50) DEFAULT 'Brasileira',
  `Naturalidade` varchar(100) DEFAULT NULL,
  `Genero` enum('Masculino','Feminino','Outro','Prefiro nao informar') DEFAULT NULL,
  `Rg_Numero` varchar(20) DEFAULT NULL,
  `Rg_OrgaoEmissor` varchar(50) DEFAULT NULL,
  `Rg_UfEmissor` char(2) DEFAULT NULL,
  `Rg_DataEmissao` date DEFAULT NULL,
  `Cpf_Numero` varchar(14) DEFAULT NULL,
  `Ctps_Numero` varchar(20) DEFAULT NULL,
  `Ctps_Serie` varchar(20) DEFAULT NULL,
  `Pispasep` varchar(20) DEFAULT NULL,
  `Cnh_Numero` varchar(20) DEFAULT NULL,
  `Cnh_Categoria` varchar(10) DEFAULT NULL,
  `Cnh_DataValidade` date DEFAULT NULL,
  `Cnh_OrgaoEmissor` varchar(50) DEFAULT NULL,
  `TitEleitor_Numero` varchar(20) DEFAULT NULL,
  `TitEleitor_Zona` varchar(10) DEFAULT NULL,
  `TitEleitor_Secao` varchar(10) DEFAULT NULL,
  `Observacoes` text,
  `Link_Foto` varchar(500) DEFAULT NULL,
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`Matricula_Funcionario`),
  UNIQUE KEY `Cpf_Numero` (`Cpf_Numero`),
  CONSTRAINT `funcionarios_documentos_ibfk_1` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `funcionarios_enderecos`
--

DROP TABLE IF EXISTS `funcionarios_enderecos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `funcionarios_enderecos` (
  `ID_Funcionario_Endereco` int NOT NULL AUTO_INCREMENT COMMENT 'ID único do endereço do funcionário',
  `Matricula_Funcionario` varchar(20) NOT NULL COMMENT 'Chave estrangeira para a tabela funcionarios (Matricula)',
  `Tipo_Endereco` varchar(50) NOT NULL COMMENT 'Tipo do endereço (ex: Residencial, Comercial, Correspondência)',
  `Logradouro` varchar(255) NOT NULL COMMENT 'Nome da rua, avenida, etc.',
  `Numero` varchar(10) NOT NULL COMMENT 'Número do imóvel',
  `Complemento` varchar(100) DEFAULT NULL COMMENT 'Complemento (ex: Apto, Bloco)',
  `Bairro` varchar(100) DEFAULT NULL COMMENT 'Nome do bairro',
  `Cidade` varchar(100) DEFAULT NULL COMMENT 'Nome da cidade',
  `Estado` char(2) DEFAULT NULL COMMENT 'Sigla do estado',
  `Cep` varchar(10) DEFAULT NULL COMMENT 'CEP',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Funcionario_Endereco`),
  UNIQUE KEY `Matricula_Funcionario` (`Matricula_Funcionario`,`Tipo_Endereco`),
  CONSTRAINT `funcionarios_enderecos_ibfk_1` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Armazena endereços de funcionários';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `incidentes_acidentes`
--

DROP TABLE IF EXISTS `incidentes_acidentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `incidentes_acidentes` (
  `ID_Incidente_Acidente` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do incidente/acidente',
  `Tipo_Registro` enum('Incidente','Acidente') NOT NULL COMMENT 'Tipo de registro: Incidente (quase-acidente) ou Acidente (com dano/lesão)',
  `Data_Hora_Ocorrencia` datetime NOT NULL COMMENT 'Data e hora da ocorrência',
  `Local_Ocorrencia` varchar(255) DEFAULT NULL COMMENT 'Local específico da ocorrência (ex: Canteiro Obra X, Escritório Y)',
  `ID_Obras` int DEFAULT NULL COMMENT 'Chave estrangeira para a tabela obras (se relacionado a uma obra)',
  `Descricao_Resumida` text NOT NULL COMMENT 'Breve descrição do ocorrido',
  `Causas_Identificadas` text COMMENT 'Causas diretas e indiretas identificadas',
  `Acoes_Corretivas_Tomadas` text COMMENT 'Ações tomadas imediatamente após a ocorrência',
  `Acoes_Preventivas_Recomendadas` text COMMENT 'Ações para evitar recorrência',
  `Status_Registro` enum('Aberto','Em Investigação','Concluído','Fechado') NOT NULL DEFAULT 'Aberto' COMMENT 'Status do registro',
  `Responsavel_Investigacao_Funcionario_Matricula` varchar(20) DEFAULT NULL COMMENT 'Matrícula do funcionário responsável pela investigação (FK para funcionarios.Matricula)',
  `Data_Fechamento` date DEFAULT NULL COMMENT 'Data de fechamento da investigação/registro',
  `Observacoes` text COMMENT 'Observações adicionais',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Incidente_Acidente`),
  KEY `ID_Obras` (`ID_Obras`),
  KEY `Responsavel_Investigacao_Funcionario_Matricula` (`Responsavel_Investigacao_Funcionario_Matricula`),
  CONSTRAINT `incidentes_acidentes_ibfk_1` FOREIGN KEY (`ID_Obras`) REFERENCES `obras` (`ID_Obras`) ON DELETE SET NULL,
  CONSTRAINT `incidentes_acidentes_ibfk_2` FOREIGN KEY (`Responsavel_Investigacao_Funcionario_Matricula`) REFERENCES `funcionarios` (`Matricula`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela para registro e gestão de Incidentes e Acidentes';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `medicoes`
--

DROP TABLE IF EXISTS `medicoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicoes` (
  `ID_Medicoes` int NOT NULL AUTO_INCREMENT,
  `ID_Obras` int NOT NULL,
  `Numero_Medicao` int NOT NULL,
  `Valor_Medicao` decimal(18,2) NOT NULL,
  `Data_Medicao` date NOT NULL,
  `Mes_Referencia` varchar(20) DEFAULT NULL,
  `Data_Aprovacao` date DEFAULT NULL,
  `Status_Medicao` varchar(100) DEFAULT NULL,
  `Observacao_Medicao` varchar(500) DEFAULT NULL,
  `Data_Criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Medicoes`),
  UNIQUE KEY `ID_Obras` (`ID_Obras`,`Numero_Medicao`),
  CONSTRAINT `medicoes_ibfk_1` FOREIGN KEY (`ID_Obras`) REFERENCES `obras` (`ID_Obras`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `modulos`
--

DROP TABLE IF EXISTS `modulos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `modulos` (
  `ID_Modulo` int NOT NULL AUTO_INCREMENT,
  `Nome_Modulo` varchar(100) NOT NULL,
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Modulo`),
  UNIQUE KEY `Nome_Modulo` (`Nome_Modulo`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `niveis`
--

DROP TABLE IF EXISTS `niveis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `niveis` (
  `ID_Niveis` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do nível',
  `Nome_Nivel` varchar(50) NOT NULL COMMENT 'Nome do nível (ex: I, Júnior, N/A, Pleno, Sênior, Estagiário)',
  `Descricao` text COMMENT 'Descrição detalhada do nível',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Niveis`),
  UNIQUE KEY `Nome_Nivel` (`Nome_Nivel`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela de Níveis de Carreira da Empresa';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `obras`
--

DROP TABLE IF EXISTS `obras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `obras` (
  `ID_Obras` int NOT NULL AUTO_INCREMENT,
  `ID_Contratos` int NOT NULL,
  `Numero_Obra` varchar(50) NOT NULL,
  `Nome_Obra` varchar(300) NOT NULL,
  `Endereco_Obra` varchar(500) DEFAULT NULL,
  `Escopo_Obra` varchar(3000) DEFAULT NULL,
  `Valor_Obra` decimal(18,2) DEFAULT NULL,
  `Valor_Aditivo_Total` decimal(18,2) DEFAULT '0.00',
  `Status_Obra` varchar(100) NOT NULL,
  `Data_Inicio_Prevista` date DEFAULT NULL,
  `Data_Fim_Prevista` date DEFAULT NULL,
  `Data_Criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Obras`),
  UNIQUE KEY `Numero_Obra` (`Numero_Obra`),
  KEY `ID_Contratos` (`ID_Contratos`),
  CONSTRAINT `obras_ibfk_1` FOREIGN KEY (`ID_Contratos`) REFERENCES `contratos` (`ID_Contratos`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `permissoes_usuarios`
--

DROP TABLE IF EXISTS `permissoes_usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissoes_usuarios` (
  `ID_Permissao_Usuario` int NOT NULL AUTO_INCREMENT,
  `ID_Usuario` int NOT NULL,
  `ID_Modulo` int NOT NULL,
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Permissao_Usuario`),
  UNIQUE KEY `ID_Usuario` (`ID_Usuario`,`ID_Modulo`),
  KEY `ID_Modulo` (`ID_Modulo`),
  CONSTRAINT `permissoes_usuarios_ibfk_1` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `permissoes_usuarios_ibfk_2` FOREIGN KEY (`ID_Modulo`) REFERENCES `modulos` (`ID_Modulo`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reidis`
--

DROP TABLE IF EXISTS `reidis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reidis` (
  `ID_Reidis` int NOT NULL AUTO_INCREMENT,
  `ID_Obras` int NOT NULL,
  `Numero_Portaria` varchar(100) NOT NULL,
  `Numero_Ato_Declaratorio` varchar(100) NOT NULL,
  `Data_Aprovacao_Reidi` date DEFAULT NULL,
  `Data_Validade_Reidi` date DEFAULT NULL,
  `Status_Reidi` varchar(50) DEFAULT NULL,
  `Observacoes_Reidi` text,
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Reidis`),
  KEY `ID_Obras` (`ID_Obras`),
  CONSTRAINT `reidis_ibfk_1` FOREIGN KEY (`ID_Obras`) REFERENCES `obras` (`ID_Obras`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `salarios`
--

DROP TABLE IF EXISTS `salarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `salarios` (
  `ID_Salarios` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do pacote de salário e benefícios',
  `ID_Cargos` int NOT NULL COMMENT 'Chave estrangeira para a tabela cargos',
  `ID_Niveis` int NOT NULL COMMENT 'Chave estrangeira para a tabela niveis',
  `Salario_Base` decimal(10,2) NOT NULL COMMENT 'Valor do salário base em Reais',
  `Periculosidade` tinyint(1) DEFAULT '0' COMMENT 'Indica se há adicional de periculosidade (TRUE/FALSE)',
  `Insalubridade` tinyint(1) DEFAULT '0' COMMENT 'Indica se há adicional de insalubridade (TRUE/FALSE)',
  `Ajuda_De_Custo` decimal(10,2) DEFAULT '0.00' COMMENT 'Valor de ajuda de custo mensal em Reais',
  `Vale_Refeicao` decimal(10,2) DEFAULT '0.00' COMMENT 'Valor do vale refeição mensal em Reais',
  `Gratificacao` decimal(10,2) DEFAULT '0.00' COMMENT 'Valor da gratificação mensal em Reais',
  `Cesta_Basica` tinyint(1) DEFAULT '0' COMMENT 'Indica se há cesta básica (TRUE/FALSE)',
  `Outros_Beneficios` text COMMENT 'Descrição de outros benefícios adicionais não listados',
  `Data_Vigencia` date NOT NULL COMMENT 'Data a partir da qual este pacote salarial entra em vigor',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Salarios`),
  UNIQUE KEY `ID_Cargos` (`ID_Cargos`,`ID_Niveis`,`Data_Vigencia`),
  KEY `ID_Niveis` (`ID_Niveis`),
  CONSTRAINT `salarios_ibfk_1` FOREIGN KEY (`ID_Cargos`) REFERENCES `cargos` (`ID_Cargos`) ON DELETE RESTRICT,
  CONSTRAINT `salarios_ibfk_2` FOREIGN KEY (`ID_Niveis`) REFERENCES `niveis` (`ID_Niveis`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela de Pacotes Salariais e Benefícios por Cargo e Nível';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `seguros`
--

DROP TABLE IF EXISTS `seguros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seguros` (
  `ID_Seguros` int NOT NULL AUTO_INCREMENT,
  `ID_Obras` int NOT NULL,
  `Numero_Apolice` varchar(100) NOT NULL,
  `Seguradora` varchar(255) NOT NULL,
  `Tipo_Seguro` varchar(100) NOT NULL,
  `Valor_Segurado` decimal(15,2) DEFAULT NULL,
  `Data_Inicio_Vigencia` date DEFAULT NULL,
  `Data_Fim_Vigencia` date DEFAULT NULL,
  `Status_Seguro` varchar(50) DEFAULT NULL,
  `Observacoes_Seguro` text,
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID_Seguros`),
  UNIQUE KEY `Numero_Apolice` (`Numero_Apolice`),
  KEY `ID_Obras` (`ID_Obras`),
  CONSTRAINT `seguros_ibfk_1` FOREIGN KEY (`ID_Obras`) REFERENCES `obras` (`ID_Obras`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `treinamentos`
--

DROP TABLE IF EXISTS `treinamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `treinamentos` (
  `ID_Treinamento` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do tipo de treinamento',
  `Nome_Treinamento` varchar(255) NOT NULL COMMENT 'Nome do treinamento (ex: NR-35 Trabalho em Altura)',
  `Descricao` text COMMENT 'Descrição detalhada do treinamento',
  `Carga_Horaria_Horas` decimal(5,2) NOT NULL COMMENT 'Carga horária do treinamento em horas',
  `Tipo_Treinamento` enum('Obrigatório','Reciclagem','Voluntário','Outro') NOT NULL COMMENT 'Classificação do treinamento',
  `Validade_Dias` int DEFAULT NULL COMMENT 'Número de dias de validade do treinamento (para reciclagem)',
  `Instrutor_Responsavel` varchar(255) DEFAULT NULL COMMENT 'Nome do instrutor responsável (pode ser externo)',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Treinamento`),
  UNIQUE KEY `Nome_Treinamento` (`Nome_Treinamento`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela de Catálogo de Treinamentos de SSMA';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `treinamentos_agendamentos`
--

DROP TABLE IF EXISTS `treinamentos_agendamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `treinamentos_agendamentos` (
  `ID_Agendamento` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do agendamento de treinamento',
  `ID_Treinamento` int NOT NULL COMMENT 'Chave estrangeira para o tipo de treinamento',
  `Data_Hora_Inicio` datetime NOT NULL COMMENT 'Data e hora de início do agendamento',
  `Data_Hora_Fim` datetime DEFAULT NULL COMMENT 'Data e hora de fim do agendamento',
  `Local_Treinamento` varchar(255) DEFAULT NULL COMMENT 'Local físico ou online do treinamento',
  `Status_Agendamento` enum('Programado','Realizado','Cancelado','Adiado') NOT NULL DEFAULT 'Programado' COMMENT 'Status do agendamento',
  `Observacoes` text COMMENT 'Observações adicionais sobre o agendamento',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Agendamento`),
  KEY `ID_Treinamento` (`ID_Treinamento`),
  CONSTRAINT `treinamentos_agendamentos_ibfk_1` FOREIGN KEY (`ID_Treinamento`) REFERENCES `treinamentos` (`ID_Treinamento`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela de Agendamentos de Treinamentos de SSMA';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `treinamentos_participantes`
--

DROP TABLE IF EXISTS `treinamentos_participantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `treinamentos_participantes` (
  `ID_Participante` int NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do participante no agendamento',
  `ID_Agendamento` int NOT NULL COMMENT 'Chave estrangeira para o agendamento do treinamento',
  `Matricula_Funcionario` varchar(20) NOT NULL COMMENT 'Matrícula do funcionário participante',
  `Presenca` tinyint(1) DEFAULT '0' COMMENT 'Indica se o funcionário esteve presente',
  `Nota_Avaliacao` decimal(4,2) DEFAULT NULL COMMENT 'Nota de avaliação do participante (0.00 a 10.00)',
  `Data_Conclusao` date DEFAULT NULL COMMENT 'Data de conclusão do treinamento para este participante',
  `Certificado_Emitido` tinyint(1) DEFAULT '0' COMMENT 'Indica se o certificado foi emitido',
  `Data_Criacao` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da criação do registro',
  `Data_Modificacao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data e hora da última modificação do registro',
  PRIMARY KEY (`ID_Participante`),
  UNIQUE KEY `ID_Agendamento` (`ID_Agendamento`,`Matricula_Funcionario`),
  KEY `Matricula_Funcionario` (`Matricula_Funcionario`),
  CONSTRAINT `treinamentos_participantes_ibfk_1` FOREIGN KEY (`ID_Agendamento`) REFERENCES `treinamentos_agendamentos` (`ID_Agendamento`) ON DELETE CASCADE,
  CONSTRAINT `treinamentos_participantes_ibfk_2` FOREIGN KEY (`Matricula_Funcionario`) REFERENCES `funcionarios` (`Matricula`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tabela de Participantes em Agendamentos de Treinamentos';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) DEFAULT 'user',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `Email` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `Email` (`Email`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-26 12:11:00
