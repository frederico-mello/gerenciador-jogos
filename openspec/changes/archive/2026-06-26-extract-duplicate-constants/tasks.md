## 1. app/routes.py — validation messages

- [x] 1.1 Define `MSG_NOME_OBRIGATORIO`, `MSG_EMAIL_OBRIGATORIO`, `MSG_EMAIL_JA_CADASTRADO`, `MSG_SENHA_MINIMA` constants
- [x] 1.2 Replace 17 string literal occurrences with constant references

## 2. app/routes.py — endpoint names

- [x] 2.1 Define `ENDPOINT_ADMIN_USERS`, `ENDPOINT_EMPRESTIMOS_ADMIN`, `ENDPOINT_EMPRESTIMOS`, `ENDPOINT_ADMIN_SCHOOLS`, `ENDPOINT_INDEX` constants
- [x] 2.2 Replace 28 endpoint string literal occurrences with constant references

## 3. app/routes.py — template names

- [x] 3.1 Define `TEMPLATE_LOGIN`, `TEMPLATE_FORM`, `TEMPLATE_ADMIN_SCHOOL_FORM`, `TEMPLATE_PERFIL` constants
- [x] 3.2 Replace 14 template filename occurrences with constant references

## 4. app/models.py — SQL fragments

- [x] 4.1 Define `SQL_AND`, `SQL_WHERE`, `SQL_ORDER_BY_NOME`, `SQL_UPDATED_AT` constants
- [x] 4.2 Replace 14 SQL fragment occurrences with constant references

## 5. app/auth.py — route names and messages

- [x] 5.1 Define `ENDPOINT_LOGIN` and `MSG_LOGIN_NECESSARIO` constants
- [x] 5.2 Replace 7 occurrences with constant references

## 6. deploy/setup.sh — shell variables

- [x] 6.1 Define `NGINX_SITES` and `SEPARATOR` shell variables early in the script
- [x] 6.2 Replace 10 occurrences with variable references

## 7. app/schema.sql — duplicated default

- [x] 7.1 Inspect the duplicated literal at line 13 and add `# NOSONAR` with justification if SQLite limitations prevent deduplication

## 8. scripts/create_admin.py — messages

- [x] 8.1 Extract duplicated message literals to module-level constants

## 9. Verification

- [x] 9.1 Run `python -m pytest` to verify no regressions
- [x] 9.2 Run `flask run` briefly to verify routes still resolve correctly
