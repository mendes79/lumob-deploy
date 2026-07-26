# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

LUMOB is a Flask + MySQL internal management system (Portuguese UI) for a construction/engineering company (VM/MC Engenharia), covering three business modules — Pessoal (HR), Obras (construction projects/contracts), Segurança/SSMA (workplace safety) — plus a Usuários (admin) module. It is currently being incrementally modernized into a multi-tenant SaaS product; see "Modernization plan" below before making backend/architecture or visual changes.

## Commands

```bash
# Setup
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Run (loads .env via load_dotenv() in the __main__ block)
python app.py                     # http://127.0.0.1:5000
```

There is no test suite, linter, or build step configured in this repo — don't assume `pytest`/`ruff`/`npm` commands exist.

Database schema lives in `1_estrutura.sql`, `2_dados_admin.sql`, `3_dados_iniciais.sql` (run in that order against a fresh MySQL 8+ `lumob` database). `dbs_lumob.md` (gitignored, local-only) has an exported schema dump — check it before assuming a column name.

## Architecture

**Request flow**: `app.py` creates the Flask app, CSRFProtect, Flask-Login, and registers four blueprints from `modulos/`. Each blueprint owns one URL prefix and talks to the DB only through a matching manager class in `database/`:

```
app.py                         → auth (/login, /logout), /welcome, blueprint registration
modulos/users_bp.py            → /users/*      uses database/db_user_manager.py
modulos/pessoal_bp.py          → /pessoal/*    uses database/db_pessoal_manager.py
modulos/obras_bp.py            → /obras/*      uses database/db_obras_manager.py
modulos/seguranca_bp.py        → /seguranca/*  uses database/db_seguranca_manager.py
```

`modulos/*_bp.py` are large monolithic blueprint files (obras_bp.py ~2,970 lines, pessoal_bp.py ~2,450 lines, seguranca_bp.py ~1,800 lines) mixing route handling, CRUD, Excel export (pandas/openpyxl), and response formatting per module — there's no separate service layer yet.

**Database access**: every request opens a fresh connection via `with DatabaseManager(**current_app.config['DB_CONFIG']) as db_base:` (`database/db_base.py`), then wraps it in a domain manager (e.g. `UserManager(db_base)`) whose methods run parameterized SQL and return dicts. There is **no connection pool** today — each `with` block is a full connect/query/close cycle. `db_base.execute_query()` is the single chokepoint: `fetch_results=True` for SELECT, `False` for INSERT/UPDATE/DELETE (auto-commits, rolls back on error).

Ignore `conexao_db.py` and the root-level `db_manager.py` — legacy standalone scripts, not imported by `app.py` or any blueprint. The live pattern is `database/db_base.py` + the per-module managers.

**Auth/permissions**: Flask-Login `User` (defined in `app.py`) carries `role` and a `permissions` list of module names loaded from `permissoes_usuarios`/`modulos` tables. `role == 'admin'` bypasses all module permission checks. Route-level guards are two patterns used interchangeably: the `@utils.module_required('ModuleName')` decorator, and inline `if current_user.role != 'admin': flash(...); redirect(...)` checks scattered inside route bodies (see `modulos/users_bp.py`) — check both when auditing access control on a route.

**Templates**: `templates/base.html` is the shared layout; `login.html` and `welcome.html` are standalone/special-cased (see modernization plan — do not touch). Each module has its own template subfolder (`templates/pessoal/`, `templates/obras/`, `templates/seguranca/`, `templates/users/`) mirroring its blueprint's sub-resources (e.g. `obras/clientes/`, `obras/contratos/`, `pessoal/funcionarios/`).

**Config/secrets**: DB credentials and `SECRET_KEY` come from `.env` (gitignored) via `python-dotenv`, read into `db_config` / `app.config['DB_CONFIG']` in `app.py`. Never hardcode credentials in code (note `conexao_db.py` does — it's legacy/unused, don't copy that pattern).

## Route pattern

Nearly every CRUD resource across the three business modules follows the same route shape — worth knowing before adding a new one:

```
GET  /<module>/<resource>                          list
GET,POST /<module>/<resource>/add                  create
GET,POST /<module>/<resource>/edit/<id>             update
POST /<module>/<resource>/delete/<id>                delete
GET  /<module>/<resource>/details/<id>               detail view
GET  /<module>/<resource>/export/excel                pandas/openpyxl export
```

Full route map is documented in `ABOUT.md` (gitignored, local reference doc).

## Modernization plan

`lumob-modernizacao/SKILL.md` (a Claude skill, auto-loads for work in this repo) is the source of truth for the ongoing modernization/SaaS-productization effort — connection pooling, caching, dashboard query consolidation, indexing, multi-tenant `tenant_id` isolation, design-system tokens (Tailwind), and the staged rollout plan. Key non-negotiables from it:

- `templates/login.html`, `templates/welcome.html`, `static/css/style_welcome.css`, `static/js/script_welcome.js` are off-limits — zero intentional diffs, in any step.
- Flask endpoint names and URLs must stay stable (`url_for` calls throughout templates depend on them).
- No `.py`/`.html`/`.css`/`.sql` change ships without the user explicitly approving that step in chat first.
- Any multi-tenant work must centralize `tenant_id` filtering in the manager/repository layer, never per-query by hand.

Read that file in full before proposing backend performance work, schema/index changes, or visual/design-system changes in this repo.
