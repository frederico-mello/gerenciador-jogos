## 1. Schema e banco de dados

- [x] 1.1 Adicionar tabela `schools` e índices a `app/schema.sql` (codigo_inep UNIQUE, rede CHECK, ativo, timestamps)
- [x] 1.2 Verificar que `scripts/init_db.py` cria a nova tabela (já executa schema.sql completo — validar)
- [x] 1.3 Adicionar funções em `app/models.py`: `list_schools(rede=None, q=None, ativo_only=True)`, `get_school(id)`, `create_school(data)`, `update_school(id, data)`, `set_school_ativo(id, ativo)`
- [x] 1.4 Adicionar `upsert_school_by_inep(codigo_inep, data)` em `app/models.py` para o importer

## 2. Importador Censo Escolar

- [x] 2.1 Criar `scripts/import_schools.py` que aceita `--csv <path>` como argumento
- [x] 2.2 Implementar leitura do CSV com `csv.DictReader`, filtrando `CO_MUNICIPIO == '3549904'`
- [x] 2.3 Mapear `TP_DEPENDENCIA` (1=federal, 2=estadual, 3=municipal, 4=privada) para valores em inglês
- [x] 2.4 Mapear colunas: `CO_ENTIDADE`→codigo_inep, `NO_ENTIDADE`→nome, `DS_ENDERECO`→endereco, `NO_BAIRRO`→bairro, `CO_CEP`→cep
- [x] 2.5 Validar colunas esperadas presentes; abortar com mensagem clara se faltar
- [x] 2.6 Chamar `upsert_school_by_inep` por linha; imprimir `[OK] <inep> <nome>`; resumo final por rede
- [x] 2.7 Testar com CSV de exemplo (criar fixture em `tests/test_import_schools.py`)

## 3. Rotas Flask (web-ui)

- [x] 3.1 Adicionar `GET /admin/schools` em `app/routes.py` (lista com filtros `?rede=` e `?q=`, ordenada por nome)
- [x] 3.2 Adicionar `GET /admin/schools/criar` e `POST /admin/schools/criar` (form para nova escola, codigo_inep opcional)
- [x] 3.3 Adicionar `GET /admin/schools/<id>/editar` e `POST /admin/schools/<id>/editar` (form preenchido, atualiza)
- [x] 3.4 Adicionar `POST /admin/schools/<id>/inativar` e `POST /admin/schools/<id>/reativar` (soft delete toggle)
- [x] 3.5 Adicionar link na nav para `/admin/schools` (temporariamente visível a todos; protegido no Change 1)

## 4. Templates

- [x] 4.1 Criar `app/templates/admin_schools.html` (tabela de escolas com filtros, botões editar/inativar/reativar, link "Nova escola")
- [x] 4.2 Criar `app/templates/admin_school_form.html` (form criar/editar com campos nome/rede/codigo_inep/endereco/bairro/cep)

## 5. Testes

- [x] 5.1 Adicionar testes em `tests/test_schools.py` cobrindo create/read/update/inativar/reativar + upsert por INEP
- [x] 5.2 Adicionar testes em `tests/test_school_routes.py` cobrindo `/admin/schools` (lista, filtros), criar, editar, inativar, reativar
- [x] 5.3 Criar `tests/test_import_schools.py` com fixture CSV pequena, validando import e idempotência
- [x] 5.4 Rodar `python -m pytest` — **63 testes passando**

## 6. Validação manual (requer dados reais do INEP)

- [x] 6.1 Baixar microdados do Censo Escolar INEP mais recente de https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar e rodar:
  ```
  python scripts/import_schools.py --csv microdados_ed_basica_2024.csv
  ```
- [x] 6.2 Verificar que ~400 escolas foram importadas para SJC
- [x] 6.3 Navegar `/admin/schools`, testar filtros, editar, criar sem INEP, inativar/reativar
- [x] 6.4 Re-rodar o import e confirmar idempotência (nenhuma duplicada)

## 7. Finalização OpenSpec

- [x] 7.1 `/opsx:archive` da change `add-school-directory` após tudo verificado
