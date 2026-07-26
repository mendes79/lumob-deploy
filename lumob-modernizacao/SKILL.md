---
name: lumob-modernizacao
description: Contexto de engenharia do projeto LUMOB (Flask/MySQL) para qualquer modelo executar as etapas do plano de modernização e produtização como SaaS. Use sempre que for planejar, revisar ou implementar código no LUMOB — desempenho de backend, pool de conexões, cache, índices, multi-tenant (tenant_id), design system/tokens, dashboards, ou fluxo de branch/commit — mesmo que o pedido não mencione "LUMOB" explicitamente, mas trate de qualquer arquivo dentro de app.py, modulos/, database/ ou templates/ deste projeto.
---

# Skill: Modernização e Produtização do LUMOB

Base: auditoria real do repositório feita pelo plano `PLANO_MODERNIZACAO_GK.md` (autor: Grok/GK), mais as decisões de arquitetura de produtização (multi-tenant, git) definidas em conversa posterior. Este arquivo é a fonte de verdade condensada — não redescubra essas decisões do zero em cada sessão.

**Como usar em outras ferramentas:** em Claude Code, salve como `.claude/skills/lumob-modernizacao/SKILL.md`. Em qualquer outra ferramenta (OpenCode, Grok Build, etc.), cole o conteúdo inteiro como contexto/system prompt no início da sessão, ou mantenha na raiz do repo e peça explicitamente para o agente ler o arquivo antes de propor mudanças.

---

## 0. Contexto não negociável (vale em toda etapa, qualquer modelo)

- **Stack real:** Flask + MySQL via `mysql.connector` (raw SQL, sem ORM completo hoje). Não migrar para FastAPI/Django/SPA nem trocar de SGBD.
- **Intocável, sempre:** `templates/login.html`, `templates/welcome.html`, `static/css/style_welcome.css`, `static/js/script_welcome.js`. Zero diff intencional nesses arquivos em qualquer etapa.
- **Nomes estáveis:** endpoints Flask (`obras_bp.obras_dashboard` etc.) e URLs não podem mudar — templates dependem de `url_for` apontando pra eles.
- **Aprovação por etapa:** nenhuma mudança em `.py`/`.html`/`.css`/`.sql` sem o usuário confirmar explicitamente a etapa no chat.
- **Objetivo de negócio:** o app nasceu de uso interno (VM/MC Engenharia) e está sendo transformado em SaaS multi-cliente — toda decisão técnica deve considerar isolamento entre clientes (tenants), não só a empresa própria.

## 1. Mapa da aplicação

```
app.py                    → auth, welcome, factory de config
modulos/
  obras_bp.py              (~2.972 linhas) → /obras/*
  pessoal_bp.py             (~2.451 linhas) → /pessoal/*
  seguranca_bp.py           (~1.797 linhas) → /seguranca/*
  users_bp.py               → /users/*
database/
  db_base.py                → DatabaseManager (context manager, hoje sem pool)
  db_obras_manager.py / db_pessoal_manager.py / db_seguranca_manager.py / db_user_manager.py
templates/                  → ~100 HTML, muitos standalone com <!DOCTYPE>
static/bootstrap/           → Bootstrap 5 local
static/css/style.css        → quase vazio (login "marco zero")
```

Os blueprints já existem e estão registrados — a modernização **fatia** esse monólito gradualmente, não reescreve o roteamento.

## 2. Diagnóstico de backend (auditoria original) — relevante sobretudo na Etapa 1

| ID | Problema real encontrado | Proposta |
|---|---|---|
| B1 | `db_base.py` abre/fecha conexão MySQL a cada `with DatabaseManager(...)` (handshake por request) + `print` de log no hot path | `MySQLConnectionPool` reutilizável, inicializado uma vez no startup; trocar `print` por `logging` |
| B2 | Dashboard de Obras faz 5 round-trips sequenciais (`get_obra_status_counts`, `get_total_obras_count` redundante, `get_total_contratos_ativos_valor`, `get_total_medicoes_realizadas_valor`, `get_avg_avanco_fisico_obras_ativas` com window function) | Consolidar em 1–2 queries agregadas + cache TTL 5–15 min |
| B3 | `PessoalManager.get_periodos_experiencia_a_vencer()` traz **todos** os funcionários ativos e calcula as janelas de 30/90 dias em loop Python | Filtrar no `WHERE` por `Data_Admissao` nas janelas, com índice em `(Status, Data_Admissao)` |
| B4 | `get_aniversariantes_do_mes` usa `MONTH(fd.Data_Nascimento) = %s` — não sargável, ignora índice em `Data_Nascimento` | Coluna gerada `mes_nascimento TINYINT` + índice, ou filtro por intervalo de datas |
| B5 | Listagens (`get_all_*`) retornam o conjunto inteiro, sem paginação server-side | `LIMIT/OFFSET` ou keyset + busca |
| B6 | Faltam índices de filtro/agregação (FKs existem, índices de filtro não) | Ver tabela abaixo |
| B7 | Blueprints monólitos misturando CRUD + Excel + dashboard + formatação | Fatiar em `modulos/<dominio>/routes_*.py` + `services.py`, **sem** mudar nomes de endpoint |

**Índices candidatos (B6):**

| Tabela | Coluna(s) | Motivo |
|---|---|---|
| `obras` | `Status_Obra` | GROUP BY do dashboard |
| `funcionarios` | `(Status, Data_Admissao)` | alertas de experiência + headcount |
| `contratos` | `Status_Contrato` | SUM de ativos |
| `medicoes` | `Status_Medicao` | SUM Paga/Aprovada |
| `asos` | `Data_Vencimento` | alertas SSMA |
| `ferias` | `(Status_Ferias, Data_Inicio_Gozo)` | próximas férias |
| `incidentes_acidentes` | `(Tipo_Registro, Status_Registro, Data_Hora_Ocorrencia)` | dashboard SSMA |
| `avancos_fisicos` | `(ID_Obras, Data_Avanco DESC)` | último avanço / média |
| `funcionarios_documentos` | `Cnh_DataValidade` | documentos a vencer |

Índices só via script SQL versionado e aprovado — nunca `ALTER` ad-hoc em produção sem backup.

## 3. Arquitetura multi-tenant (`tenant_id`) — decisão de produtização, cross-cutting

Isto **não está** no plano GK original (que cobre só desempenho/visual); foi definido depois, como camada de produtização que entra antes/junto da Etapa 1.

- **Schema:** schema único do MySQL continua; toda tabela de negócio (as mesmas do diagnóstico B6 — `obras`, `funcionarios`, `contratos`, `medicoes`, `asos`, `ferias`, `incidentes_acidentes`, etc.) ganha uma coluna `tenant_id` com FK para uma nova tabela `tenants`.
- **Camada de repositório:** o filtro por `tenant_id` é aplicado **automaticamente** na camada de repositório/manager, nunca manualmente em cada query espalhada pelo código — dado o volume (~7.200 linhas nos três blueprints principais), confiar em disciplina manual por query é o cenário mais provável de vazamento de dado entre clientes.
- **Sessão/login:** o tenant é resolvido por **subdomínio** (`clientea.lumob.com.br` →
  tenant `clientea`), lido de `request.host` em `/login` **antes** de olhar usuário/senha —
  não por seletor manual nem por username global. Isso também vale pro `load_user` do
  Flask-Login (roda em toda request autenticada, também tem acesso a `request.host`), não só
  no POST de login. Consequência: `usuarios.username` e `usuarios.Email` deixam de ser únicos
  globalmente e passam a ser únicos por tenant (`UNIQUE(tenant_id, username)` /
  `UNIQUE(tenant_id, Email)`) — dois tenants podem cada um ter seu próprio "admin".
- **Padrão dos managers:** `TenantScopedManager` (base class em `database/db_base.py`,
  aprovada) — `tenant_id` fixado uma vez na instância do manager, não repassado por método.
  Ver plano de rollout método a método antes de editar `database/db_*_manager.py`.
- **Exceção arquitetural — família `funcionarios`:** `funcionarios` (PK real `Matricula`,
  não substituta) e as 8 tabelas que têm FK pra ela (`asos`, `dependentes`, `ferias`,
  `funcionarios_contatos`, `funcionarios_documentos`, `funcionarios_enderecos`,
  `treinamentos_participantes`, `incidentes_acidentes`) usam **chave composta**
  `(tenant_id, Matricula)` — não o bolt-on simples (`tenant_id` solto + FK direta pra
  `tenants`) que todas as outras 15 tabelas de negócio usam. Decisão consciente: custo de
  migração maior (recriar 8 FKs), em troca de o próprio banco impedir cruzamento entre
  tenants numa tabela onde a chave de negócio (matrícula) pode legitimamente se repetir
  entre empresas diferentes. Qualquer sessão futura mexendo em `funcionarios` ou nessas 8
  tabelas deve manter o padrão composto, não "simplificar" de volta pro bolt-on.
- **Índices:** compostos, liderados por `tenant_id` (ex.: `(tenant_id, Status)` em vez de só `(Status)`), já que toda query de negócio vai filtrar por ele primeiro.
- **Antes de implementar:** confirmar a estrutura real das tabelas contra o schema exportado (`dbs_lumob.md` / `INFORMATION_SCHEMA`) — nunca assumir nomes de coluna sem checar.
- **Por que é inegociável:** isolamento entre clientes é requisito de segurança B2B (risco de LGPD se vazar dado de RH/ASO entre tenants), não só uma feature — uma migração aplicada de forma inconsistente entre arquivos é pior do que nenhuma, porque passa segurança falsa.

## 4. Design system / tokens visuais — Etapas 2 a 4

Restrição absoluta idêntica à da seção 0: `login.html`/`welcome.html` fora de escopo, sempre.

**Tokens (CSS variables HSL + classe `dark`), já incorporando a paleta do plano AG dentro dos tokens do GK:**

| Token | Light | Dark |
|---|---|---|
| background | slate-50 / branco gelo | slate-950 `#020617` |
| surface / card | white + border slate-200 | slate-900 + border slate-800 |
| text primary | slate-900 | slate-50 |
| text muted | slate-500 | slate-400 |
| brand Engenharia/Obras | blue-600 | blue-400 |
| brand RH | indigo-600 | indigo-400 |
| brand SSMA | emerald-600 | emerald-400 |
| success | emerald-500 | emerald-400 |
| warning | amber-500 | amber-400 |
| danger | rose-600 | rose-400 |
| info | sky-500 | sky-400 |

- **Glassmorphism (dashboards):** `bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-slate-200/60 dark:border-slate-700/50 shadow-sm`.
- **Tipografia:** system UI stack; títulos `font-semibold tracking-tight`; corpo `text-sm md:text-base leading-relaxed`.
- **Espaçamento:** múltiplos de 4/8; container `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
- **Acessibilidade obrigatória:** `focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2`; contraste AA; `prefers-reduced-motion: reduce` desliga transições/animações de chart; labels associados a inputs.
- **Tailwind:** Fase A via CDN Play nas Etapas 2–4 (projeto não tem pipeline Node hoje); build local + purge só na Etapa 5, se aprovado.
- **Shell novo:** `templates/layouts/module_base.html` — não alterar `base.html` de um jeito que afete login/welcome, que também estende `base.html`.
- **Gráficos:** manter **Chart.js 3.9.1** (já em uso) nas Etapas 2–4; só avaliar troca por ApexCharts na Etapa 5 se precisar de tooltips/export mais ricos.
- **White-label (produtização):** logo/cor por cliente entra dentro desta mesma etapa de design system, não como etapa separada.

## 5. Roteiro de etapas

| Etapa | Escopo | Fora de escopo |
|---|---|---|
| 0 | Aprovação do plano | — |
| 1 | Pool de conexões, cache (Flask-Caching), SQL consolidado dos dashboards, script de índices versionado, remoção de prints do hot path. **Tenant_id entra aqui ou antes.** | Qualquer mudança visual |
| 2 | Design system + tokens + shell (`module_base.html`) + módulo Pessoal completo (dashboard, funcionários, cargos, níveis, salários, férias, dependentes, alertas). White-label entra aqui. | — |
| 3 | Módulo Obras (dashboard, obras, clientes, contratos, arts, medições, avanços, seguros) | — |
| 4 | Módulo SSMA + Users (incidentes, ASOs, treinamentos, agendamentos, admin de usuários) | — |
| 5 | Hardening: build Tailwind local, paginação server-side se o volume exigir, auditoria de diff zero em login/welcome, documentação, checklist final de performance | — |

Cada etapa só começa com o usuário dizendo explicitamente "Aprovo a Etapa N" no chat.

## 6. Fluxo de git e commits

- Uma branch por etapa.
- Push imediato para a branch de staging/teste ao final de cada mudança relevante — não esperar validação do usuário antes do commit, porque partes do LUMOB (login) só são testáveis online.
- Merge para a branch de produção **só** depois da validação do usuário no chat, com commit oficial.
- Mensagens de commit em **Conventional Commits**, em português (ex.: `feat: adiciona pool de conexões MySQL`, `fix: corrige filtro MONTH() não sargável`).

## 7. Matriz de riscos (do plano original)

| Risco | Mitigação |
|---|---|
| Quebrar login ao mexer em `base.html` | Shell novo (`module_base.html`); não alterar a cadeia do login |
| Pool mal dimensionado esgota conexões MySQL | `DB_POOL_SIZE` baixo em dev; documentar workers × pool |
| Cache servindo dado stale | TTL curto + invalidação explícita nos POSTs |
| Índice que piora escrita | Poucos índices de alto valor, medir antes/depois |
| Escopo visual infinito em ~100 templates | Etapas por módulo, macros reutilizáveis, não pixel-perfect numa sprint só |
| Migração de tenant_id aplicada de forma inconsistente | Filtro centralizado na camada de repositório, nunca manual por query |

## 8. Critérios de aceite globais

1. Zero diff intencional em `login.html` e `welcome.html`.
2. Dashboards dos 3 módulos com visual Tailwind tokenizado (light/dark) e gráficos dinâmicos.
3. Pool de conexões ativo; sem connect/print por request no modo default.
4. Cache de KPIs com invalidação nas escritas principais.
5. Índices de filtro aplicados e documentados em script SQL versionado.
6. Isolamento por `tenant_id` verificado em toda tabela/query de negócio.
7. Usuário aprovou cada etapa no chat antes da execução.

## 9. Explicitamente fora de escopo

- Reescrita em FastAPI/Django/SPA.
- Troca de MySQL por outro SGBD.
- Autenticação OAuth/SSO.
- Suíte completa de testes automatizados (smoke manual por etapa é suficiente por ora).
- Redesign de login/welcome.
- Migrar para React/Vue.
