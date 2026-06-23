"""Testes para scripts/import_schools.py — importação e idempotência."""

import csv
import io
from pathlib import Path

import pytest


CSV_SAMPLE = """CO_ENTIDADE,NO_ENTIDADE,CO_MUNICIPIO,TP_DEPENDENCIA,DS_ENDERECO,NO_BAIRRO,CO_CEP
35061274,EMEF PROF A A,3549904,3,RUA A 100,JARDIM MOTORAMA,12224100
35061275,EE PROF B B,3549904,2,RUA B 200,VILA RUBI,12245572
35061276,COLEGIO C C,3549904,4,RUA C 300,JARDIM AQUARIUS,12246000
35061277,ESCOLA FEDERAL D,3549904,1,RUA D 400,VILA INDUSTRIAL,12220000
99999999,OUTRO MUNICIPIO,3550308,3,RUA Z 999,OUTRA CIDADE,01001000
"""


@pytest.fixture
def csv_fixture(tmp_path):
    path = tmp_path / "censo_escolar_sample.csv"
    path.write_text(CSV_SAMPLE, encoding="utf-8")
    return str(path)


def test_import_schools(app, csv_fixture):
    from scripts.import_schools import import_schools

    with app.app_context():
        import_schools(csv_fixture)

    # verify imported
    from app.models import list_schools, get_school_by_inep

    with app.app_context():
        schools = list_schools(ativo_only=False)
        assert len(schools) == 4  # only SJC (3549904)

        school = get_school_by_inep("35061274")
        assert school is not None
        assert school["rede"] == "municipal"
        assert school["nome"] == "EMEF PROF A A"
        assert school["bairro"] == "JARDIM MOTORAMA"


def test_import_schools_idempotent(app, csv_fixture):
    from scripts.import_schools import import_schools

    with app.app_context():
        import_schools(csv_fixture)

    # second import
    with app.app_context():
        import_schools(csv_fixture)

    from app.models import list_schools

    with app.app_context():
        schools = list_schools(ativo_only=False)
        assert len(schools) == 4  # still 4, no duplicates


def test_import_schools_updates_existing(app, csv_fixture):
    from scripts.import_schools import import_schools

    with app.app_context():
        import_schools(csv_fixture)

    # modify CSV content in memory
    lines = CSV_SAMPLE.splitlines()
    lines[1] = lines[1].replace("EMEF PROF A A", "EMEF PROF A A RENOMEADA")
    modified_csv = "\n".join(lines)

    path = Path(csv_fixture)
    path.write_text(modified_csv, encoding="utf-8")

    with app.app_context():
        import_schools(str(path))

    from app.models import get_school_by_inep

    with app.app_context():
        school = get_school_by_inep("35061274")
        assert school["nome"] == "EMEF PROF A A RENOMEADA"


def test_missing_columns_aborts(app, tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("CO_ENTIDADE,NO_ENTIDADE\n3549904,Escola Teste\n", encoding="utf-8")

    from scripts.import_schools import import_schools

    with app.app_context():
        with pytest.raises(SystemExit):
            import_schools(str(bad_csv))
