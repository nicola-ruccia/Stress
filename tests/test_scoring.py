import pytest
from app.core.scoring import (
    get_semaforo,
    calcola_punteggio_sintetico,
    verifica_da_contattare,
)

def test_semaforo_thresholds():
    # Per rientri_rapidi: giallo=2, rosso=5
    punti, colore = get_semaforo("rientri_rapidi", 1.0)
    assert punti == 0 and colore == "verde"

    punti, colore = get_semaforo("rientri_rapidi", 3.0)
    assert punti == 1 and colore == "giallo"

    punti, colore = get_semaforo("rientri_rapidi", 6.0)
    assert punti == 2 and colore == "rosso"

def test_punteggio_sintetico_calcolo():
    # 2 indicatori in verde (0 punti), 1 in rosso (2 punti) -> somma = 2. n = 3.
    # formula: (2 / (2 * 3)) * 100 = (2 / 6) * 100 = 33.3% -> fascia basso (<34)
    valori = {
        "rientri_rapidi": 1.0,     # verde = 0
        "turni_lunghi": 1.0,       # verde = 0
        "pazienti_infermiere": 9.0 # rosso = 2
    }
    res = calcola_punteggio_sintetico(valori)
    assert res["punteggio"] == 33.3
    assert res["fascia"] == "basso"
    assert len(res["top_3_fattori"]) == 3
    # Il fattore che pesa di più deve essere pazienti_infermiere
    assert res["top_3_fattori"][0]["id"] == "pazienti_infermiere"
    assert "azione_suggerita" in res["top_3_fattori"][0]

def test_flag_da_contattare():
    # Si accende se domanda singola >= 3 o BAT-12 >= 2.5
    assert verifica_da_contattare(checkin_val=4.0, bat12_val=None) is True
    assert verifica_da_contattare(checkin_val=2.0, bat12_val=2.8) is True
    assert verifica_da_contattare(checkin_val=1.0, bat12_val=1.5) is False
    assert verifica_da_contattare(checkin_val=None, bat12_val=None) is False
