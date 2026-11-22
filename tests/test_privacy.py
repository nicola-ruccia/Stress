import pytest
from app.core.privacy import (
    pseudonimize_matricola,
    is_k_min_satisfied,
    puo_vedere,
    ALLOWED_EXCEL_FIELDS,
)

def test_pseudonimizzazione():
    mat = "MATR_99214"
    c1 = pseudonimize_matricola(mat)
    c2 = pseudonimize_matricola(mat)
    # Deterministico
    assert c1 == c2
    # Lunghezza 10 caratteri
    assert len(c1) == 10
    # Non contiene la matricola originale
    assert "99214" not in c1
    # Matricole diverse generano codici diversi
    assert pseudonimize_matricola("MATR_00001") != c1

def test_k_anonymity():
    assert is_k_min_satisfied(6) is True
    assert is_k_min_satisfied(10) is True
    assert is_k_min_satisfied(5) is False
    assert is_k_min_satisfied(1) is False

def test_rbac_privacy_rules():
    # HR NON può mai vedere dati individuali di salute/burnout
    assert puo_vedere("checkin", "hr", livello="persona") is False
    assert puo_vedere("bat12", "hr", livello="persona") is False
    assert puo_vedere("malattia_brevi", "hr", livello="persona") is False

    # HR può vedere i dati aggregati di reparto
    assert puo_vedere("checkin", "hr", livello="reparto") is True
    assert puo_vedere("rientri_rapidi", "hr", livello="reparto") is True

    # Il medico competente può vedere i dati individuali
    assert puo_vedere("checkin", "medico", livello="persona") is True
    assert puo_vedere("bat12", "medico", livello="persona") is True

    # Il lavoratore vede solo checkin/bat12
    assert puo_vedere("checkin", "lavoratore", livello="persona") is True
    assert puo_vedere("infortuni", "lavoratore", livello="reparto") is False

def test_excel_allowed_fields_whitelist():
    # La whitelist non deve contenere dati sensibili non necessari (nomi, CF, diagnosi)
    for sheet, fields in ALLOWED_EXCEL_FIELDS.items():
        assert "nome" not in fields
        assert "cognome" not in fields
        assert "codice_fiscale" not in fields
        assert "diagnosi" not in fields
