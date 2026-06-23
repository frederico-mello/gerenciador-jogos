## Context

O sistema `gerenciador-jogos` hoje é single-user, sem auth, sem noção de escolas. Para suportar empréstimos de jogos por professores de escolas de São José dos Campos, precisamos de um diretório controlado de escolas que sirva de FK para a futura tabela `users` (Change 1) e permita relatórios/dashboard por escola (Change 2).

O município de São José dos Campos (código IBGE 3549904) possui ~403 escolas segundo o Censo Escolar INEP, distribuídas entre redes federal, estadual, municipal e privada. O INEP publica microdados anuais em CSV aberto.

## Goals / Non-Goals

**Goals:**
- Tabela `schools` com código INEP como chave natural (quando disponível).
- Importador idempotente que lê o CSV do Censo Escolar INEP e popula `schools` para SJC.
- CRUD mínimo na UI para `admin_sistema` gerenciar escolas (editar, inativar, criar sem INEP).
- Base sólida para a FK `users.escola_id` no Change 1.

**Non-Goals:**
- Importação automática do CSV (download é manual anual; script espera o caminho do arquivo como argumento).
- Sincronização bidirecional com INEP (somente import).
- Endereços georreferenciados (apenas texto livre de endereço/bairro/CEP).
- Suporte a múltiplos municípios (escopo é apenas SJC).

## Decisions

### 1. Fonte dos dados: Censo Escolar INEP
**Por que:** Fonte oficial, gratuita, atualizada anualmente, com código INEP único por escola (chave natural estável).
**Alternativas consideradas:**
- QEdu (API não documentada publicamente) — descartado.
- escolas.com.br (scraping HTML) — descartado, frágil.
- Prefeitura de SJC (HTML, só municipal) — descartado, cobertura parcial.
- Texto livre (sem lista) — descartado pela inconsistência.

### 2. Modelo de dados: tabela `schools` com `codigo_inep` UNIQUE nullable
**Por que:** Escolas do Censo têm INEP; escolas criadas manualmente (ex: escola nova sem cadastro INEP) podem ter `codigo_inep = NULL`. A UNIQUE constraint permite NULLs no SQLite por padrão.
**Alternativas:** `codigo_inep NOT NULL` — descartado por impedir cadastro manual de escolas sem INEP.

**Schema:**
```sql
CREATE TABLE schools (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo_inep  TEXT UNIQUE,
  nome         TEXT NOT NULL,
  rede         TEXT CHECK(rede IN ('federal','estadual','municipal','privada')),
  endereco     TEXT,
  bairro       TEXT,
  cep          TEXT,
  ativo        INTEGER DEFAULT 1,
  created_at   TEXT DEFAULT (datetime('now','localtime')),
  updated_at   TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_schools_rede ON schools(rede);
CREATE INDEX idx_schools_ativo ON schools(ativo);
```

### 3. Idempotência por `codigo_inep`
**Por que:** Re-executar o import a cada novo Censo não deve duplicar. Se `codigo_inep` já existe, atualiza os demais campos. Se não existe, insere.
**Alternativas:** Idempotência por `nome` — descartado, nomes podem mudar entre censos.

### 4. Download manual do CSV (não automático)
**Por que:** O ZIP do Censo Escolar tem ~100MB e requer aceitação de termos no site do INEP. Automação de download é frágil e fora de escopo. O script recebe o caminho do CSV descompactado como argumento.
**Uso:** `python scripts/import_schools.py --csv microdados_ed_basica_2024.csv`

### 5. CRUD mínimo na UI (sem proteção de auth ainda)
**Por que:** O auth é Change 1. Até lá, as rotas `/admin/schools` ficam sem proteção. Quando o Change 1 for implementado, `@role_required('admin_sistema')` será adicionado a essas rotas.
**Risco aceito:** Janela temporária onde `/admin/schools` é acessível sem login. Como o sistema ainda é local e single-user, o risco é mínimo.

### 6. Soft delete (`ativo=0`) em vez de DELETE
**Por que:** Preserva integridade referencial futura (FK `users.escola_id`). Se uma escola fecha, seus usuários e empréstimos históricos permanecem vinculados.

## Risks / Trade-offs

- **[CSV do Censo pode mudar formato entre anos]** → Mitigação: script documenta as colunas esperadas (`CO_ENTIDADE`, `NO_ENTIDADE`, `TP_DEPENDENCIA`, `DS_ENDERECO`, `NO_BAIRRO`, `CO_CEP`) e falha com mensagem clara se faltar.
- **[Cobertura apenas SJC]** → Trade-off aceito: sistema é para SJC. Se expandir, generalizar o filtro de município.
- **[Escolas sem INEP criadas manualmente podem duplicar]** → Mitigação: antes de criar manual, admin deve buscar por nome.
- **[Rotas admin sem auth temporariamente]** → Mitigado pelo uso local; resolvido no Change 1.

## Migration Plan

1. Estender `app/schema.sql` com a tabela `schools` + índices.
2. Atualizar `scripts/init_db.py` (não precisa de mudança — já executa `schema.sql` inteiro).
3. Criar `scripts/import_schools.py`.
4. Adicionar rotas em `app/routes.py` e templates.
5. **Rollback:** reverter `schema.sql`, remover rotas/templates/script. DB existente precisa `DROP TABLE schools` manual.

## Open Questions

- Nenhuma pendente. As decisões foram confirmadas durante o explore mode.
