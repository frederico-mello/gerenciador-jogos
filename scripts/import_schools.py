"""Importador de escolas do Censo Escolar INEP para São José dos Campos.

Uso:
    python scripts/import_schools.py --csv microdados_ed_basica_2024.csv

Baixe os microdados mais recentes em:
    https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar

Filtra CO_MUNICIPIO = 3549904 (São José dos Campos - SP).
Idempotente por código INEP (CO_ENTIDADE).
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import init_db, get_db
from app import create_app


TP_DEPENDENCIA_MAP = {
    "1": "federal",
    "2": "estadual",
    "3": "municipal",
    "4": "privada",
}

COLUNAS_ESPERADAS = {"CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "TP_DEPENDENCIA"}

COLUNA_MAP = {
    "CO_ENTIDADE": "codigo_inep",
    "NO_ENTIDADE": "nome",
    "DS_ENDERECO": "endereco",
    "NO_BAIRRO": "bairro",
    "CO_CEP": "cep",
}

MUNICIPIO_FILTRO = "3549904"


def _validar_colunas(cabecalho):
    colunas = set(cabecalho)
    faltando = COLUNAS_ESPERADAS - colunas
    if faltando:
        print(f"ERRO: Colunas obrigatórias ausentes no CSV: {', '.join(sorted(faltando))}", file=sys.stderr)
        print(f"Colunas encontradas: {', '.join(sorted(colunas))}", file=sys.stderr)
        sys.exit(1)


def import_schools(csv_path):
    from app.models import upsert_school_by_inep

    with open(csv_path, encoding="iso-8859-1", newline="") as f:
        sample = f.read(8192)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample)
        reader = csv.DictReader(f, dialect=dialect)
        _validar_colunas(reader.fieldnames)

        counts = {"federal": 0, "estadual": 0, "municipal": 0, "privada": 0, "sem_rede": 0}

        for row in reader:
            if row.get("CO_MUNICIPIO") != MUNICIPIO_FILTRO:
                continue

            codigo_inep = row.get("CO_ENTIDADE", "").strip()
            if not codigo_inep:
                continue

            data = {}
            for csv_col, model_col in COLUNA_MAP.items():
                val = row.get(csv_col, "").strip()
                if val:
                    data[model_col] = val

            tp_dependencia = row.get("TP_DEPENDENCIA", "").strip()
            rede = TP_DEPENDENCIA_MAP.get(tp_dependencia)
            if rede:
                data["rede"] = rede
                counts[rede] += 1
            else:
                counts["sem_rede"] += 1

            upsert_school_by_inep(codigo_inep, data)
            nome_escola = data.get("nome", "?")
            print(f"[OK] {codigo_inep} {nome_escola}")

    total = sum(counts.values()) - counts["sem_rede"]
    print(f"\nTotal: {total} escolas importadas "
          f"(federal: {counts['federal']}, estadual: {counts['estadual']}, "
          f"municipal: {counts['municipal']}, privada: {counts['privada']})")
    if counts["sem_rede"]:
        print(f"  ({counts['sem_rede']} escolas sem rede identificada)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Importa escolas de SJC do Censo Escolar INEP")
    parser.add_argument("--csv", required=True, help="Caminho para o CSV dos microdados")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERRO: Arquivo não encontrado: {csv_path}", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / "instance" / "jogos.db"
    init_db(str(db_path))

    app = create_app({"DATABASE_PATH": str(db_path), "TESTING": True, "SECRET_KEY": "import-secret"})
    with app.app_context():
        import_schools(str(csv_path))


if __name__ == "__main__":
    main()
