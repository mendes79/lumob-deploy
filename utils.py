# utils.py

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def formatar_moeda_brl(valor):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56) de forma manual."""
    if valor is None:
        valor = 0.0
    # Formata o número com 2 casas decimais para separar o inteiro do decimal
    valor_str = f"{valor:.2f}"
    inteiro, decimal = valor_str.split('.')
    
    # Adiciona os pontos como separadores de milhar
    inteiro_rev = inteiro[::-1] # Inverte a string do inteiro
    partes = [inteiro_rev[i:i+3] for i in range(0, len(inteiro_rev), 3)]
    inteiro_formatado = '.'.join(partes)[::-1] # Junta com pontos e inverte de volta
    
    return f"R$ {inteiro_formatado},{decimal}"

# --- NOVO DECORATOR DE PERMISSÃO ---
def module_required(module_name):
    """
    Decorator que verifica se o usuário atual tem permissão para acessar um módulo.
    Redireciona para a página de boas-vindas se não tiver permissão.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Garante que o usuário está logado e tem a permissão necessária
            if not current_user.is_authenticated or not current_user.can_access_module(module_name):
                flash(f'Acesso negado. Você não tem permissão para acessar o Módulo {module_name}.', 'warning')
                return redirect(url_for('welcome'))
            # Se tiver permissão, executa a rota original
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- NOVA LÓGICA DE NORMALIZAÇÃO DE ENUM ---

# Dicionários de mapeamento para cada campo ENUM
# As chaves são as possíveis entradas do usuário (em minúsculas)
# Os valores são os dados corretos que devem ir para o banco

MAPA_ESTADO_CIVIL = {
    'solteiro': 'Solteiro(a)', 'solteira': 'Solteiro(a)', 'solt': 'Solteiro(a)', 's': 'Solteiro(a)',
    'solteir': 'Solteiro(a)', 'solteiros': 'Solteiro(a)', 'solteiras': 'Solteiro(a)',
    'solteiro-a': 'Solteiro(a)', 'solteiro/a': 'Solteiro(a)', 'solteiro(a)': 'Solteiro(a)',
    'casado': 'Casado(a)', 'casada': 'Casado(a)', 'casad': 'Casado(a)', 'c': 'Casado(a)',
    'casado-a': 'Casado(a)', 'casado/a': 'Casado(a)', 'casado(a)': 'Casado(a)',
    'divorciado': 'Divorciado(a)', 'divorciada': 'Divorciado(a)', 'd': 'Divorciado(a)', 'divorc': 'Divorciado(a)',
    'divorciado(a)': 'Divorciado(a)',
    'viuvo': 'Viuvo(a)', 'viuva': 'Viuvo(a)', 'v': 'Viuvo(a)', 'viúvo': 'Viuvo(a)', 'viúva': 'Viuvo(a)',
    'viuvo(a)': 'Viuvo(a)',
    'uniao estavel': 'Uniao Estavel', 'uniao': 'Uniao Estavel', 'ue': 'Uniao Estavel', 'união estável': 'Uniao Estavel'
}

MAPA_GENERO = {
    'masculino': 'Masculino', 'masc': 'Masculino', 'm': 'Masculino',
    'feminino': 'Feminino', 'fem': 'Feminino', 'f': 'Feminino',
    'outro': 'Outro', 'o': 'Outro',
    'prefiro nao informar': 'Prefiro nao informar', 'nao informar': 'Prefiro nao informar', 'pni': 'Prefiro nao informar'
}

MAPA_STATUS_FUNCIONARIO = {
    'ativo': 'Ativo', 'ativa': 'Ativo',
    'inativo': 'Inativo', 'inativa': 'Inativo',
    'ferias': 'Ferias', 'férias': 'Ferias',
    'afastado': 'Afastado', 'afastada': 'Afastado'
}

MAPA_TIPO_CONTRATACAO = {
    'clt': 'CLT',
    'pj': 'PJ', 'pessoa juridica': 'PJ', 'pessoa jurídica': 'PJ',
    'temporario': 'Temporario', 'temporário': 'Temporario'
}

def normalizar_valor_enum(valor_usuario, mapa_de_sinonimos):
    """
    Recebe um valor do usuário e um dicionário de mapeamento.
    Retorna o valor correto do ENUM ou None se não encontrar correspondência.
    """
    if not valor_usuario or not isinstance(valor_usuario, str):
        return None
    
    chave = valor_usuario.strip().lower()
    return mapa_de_sinonimos.get(chave)

# Você pode adicionar outras funções úteis e globais aqui no futuro.