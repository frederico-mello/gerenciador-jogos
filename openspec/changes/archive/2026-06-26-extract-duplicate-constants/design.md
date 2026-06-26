## Context

SonarCloud rule `S1192` (and its language-specific variants `python:S1192`, `shelldre:S1192`, `plsql:S1192`) flags string literals that appear 3 or more times in the same file. The project has 23 such issues concentrated primarily in `app/routes.py` (13) and `app/models.py` (4).

**Current state by file:**

| File | Literal | Count |
|------|---------|-------|
| `app/routes.py` | `"Nome é obrigatório."` | 8 |
| `app/routes.py` | `"games.admin_users"` | 8 |
| `app/routes.py` | `"games.emprestimos_admin"` | 8 |
| `app/routes.py` | `"games.emprestimos"` | 8 |
| `app/routes.py` | `"games.admin_schools"` | 4 |
| `app/routes.py` | `"games.index"` | 4 |
| `app/routes.py` | `"form.html"` | 4 |
| `app/routes.py` | `"admin_school_form.html"` | 4 |
| `app/routes.py` | `"login.html"` | 3 |
| `app/routes.py` | `"perfil.html"` | 3 |
| `app/routes.py` | `"Email é obrigatório."` | 3 |
| `app/routes.py` | `"Email já cadastrado."` | 3 |
| `app/routes.py` | `"Senha deve ter pelo menos 4 caracteres."` | 3 |
| `app/models.py` | `" AND "` | 4 |
| `app/models.py` | `" WHERE "` | 4 |
| `app/models.py` | `" ORDER BY nome"` | 3 |
| `app/models.py` | `"updated_at = ?"` | 4 |
| `app/auth.py` | `"games.login"` | 4 |
| `app/auth.py` | `"Login necessário."` | 3 |
| `deploy/setup.sh` | `'/etc/nginx/sites-available/gerenciador-jogos'` | 6 |
| `deploy/setup.sh` | `'============================================'` | 4 |
| `scripts/create_admin.py` | (various messages) | (multiple) |
| `app/schema.sql` | Repeated column constraint | 11 |

## Goals / Non-Goals

**Goals:**
- Reduce duplicated string literals to single definitions
- Improve maintainability (single point of edit for messages, routes, paths)
- Reduce code duplication metric to pass Quality Gate

**Non-Goals:**
- Extracting ALL duplicated strings (only those flagged by SonarCloud S1192)
- Creating a centralized constants module (each file handles its own)
- Changing behavior or APIs

## Decisions

### 1. Module-level constants per file

**Decision**: Define constants at module level in the file where the duplication occurs, not in a shared `constants.py`.

**Rationale**: Keeps each constant close to its usage. Validation messages belong to routes, SQL fragments to models, shell paths to the shell script. A shared constants file would create import coupling without clear ownership.

**Alternative considered**: Central `app/constants.py`. Rejected — adds cross-module dependency for strings that are local concerns.

### 2. Naming convention

**Decision**: Use `SCREAMING_SNAKE_CASE` with a descriptive prefix indicating category.

| Category | Prefix | Example |
|----------|--------|---------|
| Validation messages | `MSG_` | `MSG_NOME_OBRIGATORIO` |
| Endpoint names | `ENDPOINT_` | `ENDPOINT_ADMIN_USERS` |
| Template names | `TEMPLATE_` | `TEMPLATE_LOGIN` |
| SQL fragments | `SQL_` | `SQL_AND` |

**Rationale**: Consistent naming makes the constant's role obvious at usage site. Follows Python convention of uppercase for constants.

### 3. Shell variable naming

**Decision**: Use lowercase with descriptive names, defined early in the script.

```bash
NGINX_SITES="/etc/nginx/sites-available/gerenciador-jogos"
SEPARATOR="============================================"
```

**Rationale**: Shell convention is lowercase for local variables. No special prefix needed in small scripts.

### 4. Schema.sql approach

**Decision**: The 11-time duplicated literal in `schema.sql` is likely a column default. If it's `DEFAULT ''`, consider whether a SQL variable or just accepting the duplication is appropriate. Since SQLite doesn't support variables in `CREATE TABLE`, this may require `# NOSONAR` or restructuring.

**Rationale**: SQL within `.sql` files has limited options for deduplication. The least invasive approach is to add a comment suppressing the warning if the duplication is structurally necessary.

## Risks / Trade-offs

- **Over-engineering**: Some 3× duplications (e.g., `"login.html"` ×3) may not warrant a constant if the strings are trivially short. → Mitigation: Apply the change uniformly; even short strings benefit from single-point-of-edit.
- **Schema.sql limitation**: SQLite CREATE TABLE doesn't support variables. → Mitigation: Use `# NOSONAR` with justification if restructuring is impossible.
