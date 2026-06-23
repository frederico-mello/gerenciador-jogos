## Why

O sistema atual é single-user e não possui noção de usuários ou escolas. Para suportar autenticação (Change 1: `add-auth-system`) e empréstimos (Change 2: `add-loans-subsystem`), precisamos saber a qual escola cada usuário pertence. Se o campo "escola" for texto livre, teremos inconsistências ("E.E. João", "EM João", "Escola João") que inviabilizam relatórios e filtros por escola. Uma lista controlada resolve isso.

Existe uma fonte oficial e acessível: o **Censo Escolar INEP** (atualizado anualmente, gratuito), com código INEP único por escola e cobertura de todas as redes (federal, estadual, municipal, privada) para o município de São José dos Campos (código IBGE 3549904).

## What Changes

- **Nova tabela `schools`** em SQLite com campos: `id` (PK), `codigo_inep` (UNIQUE, pode ser NULL), `nome`, `rede` (federal/estadual/municipal/privada), `endereco`, `bairro`, `cep`, `ativo`, `created_at`, `updated_at`.
- **Novo script CLI** `scripts/import_schools.py` que lê os microdados do Censo Escolar INEP filtrando `CO_MUNICIPIO=3549904` (São José dos Campos), faz upsert idempotente por `codigo_inep`, e popula a tabela `schools`.
- **CRUD mínimo na UI** para `admin_sistema`: listar escolas, editar (endereço, bairro, ativo), inativar (`ativo=0`). Criação manual de escolas sem INEP é permitida (campo `codigo_inep` NULL).
- **Extensão do `scripts/init_db.py`** para criar também a tabela `schools` (além de `games` e `game_manual_pages`).
- **Novo capability** `school-directory` no OpenSpec.

## Capabilities

### New Capabilities
- `school-directory`: Diretório controlado de escolas de São José dos Campos, alimentado pelo Censo Escolar INEP, com CRUD mínimo para admin_sistema.

### Modified Capabilities
- `web-ui`: Adiciona rotas `/admin/schools` (lista), `/admin/schools/<id>/editar` (form), `/admin/schools/<id>/inativar` (POST) — acessíveis apenas a `admin_sistema` (quando auth existir; até então, estas rotas ficam sem proteção pois o auth é Change 1).

## Impact

- **Schema**: nova tabela `schools` em `app/schema.sql`. `scripts/init_db.py` estendido para criá-la.
- **Novo script**: `scripts/import_schools.py` (requer download manual do CSV do Censo Escolar INEP).
- **Novas rotas em `app/routes.py`**: `/admin/schools`, `/admin/schools/<id>/editar`, `/admin/schools/<id>/inativar`.
- **Novos templates**: `admin_schools.html` (lista), `admin_school_form.html` (editar).
- **Dependências Python**: nenhuma nova (usa apenas stdlib `csv`, `sqlite3`).
- **Sem breaking changes** — apenas adição. Catálogo de jogos existente não é afetado.
- **Pré-requisito** para Change 1 (`add-auth-system`): `users.escola_id` fará FK para `schools.id`.
