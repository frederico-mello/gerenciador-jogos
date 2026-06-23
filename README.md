# Gerenciador de Jogos

CRUD local de jogos educacionais (anatomia, histologia, microbiologia) com Flask + SQLite.

## Setup

```powershell
pip install -r requirements.txt
```

### Variáveis de ambiente

Copie `.env.example` para `.env` e defina uma `FLASK_SECRET_KEY` segura:

```powershell
cp .env.example .env
```

Gere uma chave com:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Cole o valor gerado no `.env`:

```
FLASK_SECRET_KEY=seu-token-hex-aqui
```

## Inicializar banco

```powershell
python scripts\init_db.py
```

Cria `instance\jogos.db` (vazio).

## Importar jogos do Downloads

```powershell
python scripts\import_from_downloads.py
```

Varre `IMPORT_SOURCE_DIR` (definido no `.env`) para as 3 áreas, copia e redimensiona imagens para `data\<area>\<jogo-slug>\`, converte DOCX para Markdown, e popula o banco. **Idempotente**: re-executar não duplica.

## Rodar o servidor

```powershell
flask run
```

Abra `http://localhost:5000`.

## Testes

```powershell
python -m pytest
```

## Estrutura

- `app/` — aplicação Flask (db, models, routes, importer, templates, static)
- `data/` — imagens e descrições normalizadas (geradas pelo importer)
- `instance/jogos.db` — banco SQLite
- `scripts/` — CLIs (init_db, import_from_downloads)
- `tests/` — pytest
- `openspec/` — specs e change proposals (OpenSpec)
