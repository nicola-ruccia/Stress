import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from app.core.indicators import (
    calcola_rientri_rapidi,
    calcola_turni_lunghi,
    calcola_pazienti_infermiere,
    calcola_straordinari,
    calcola_ferie_residue,
    calcola_malattia_brevi,
    calcola_dimissioni,
)

def test_rientri_rapidi():
    turni = pd.DataFrame([
        # Turno 1: termina alle 22:00
        {"codice": "c001", "reparto": "Medicina", "inizio": datetime(2026, 11, 1, 14, 0), "fine": datetime(2026, 11, 1, 22, 0)},
        # Turno 2: inizia alle 06:00 del giorno dopo (pausa di 8 ore -> < 11h: RIENTRO RAPIDO)
        {"codice": "c001", "reparto": "Medicina", "inizio": datetime(2026, 11, 2, 6, 0), "fine": datetime(2026, 11, 2, 14, 0)},
        # Turno 3: inizia dopo 24 ore (pausa regolare)
        {"codice": "c001", "reparto": "Medicina", "inizio": datetime(2026, 11, 3, 14, 0), "fine": datetime(2026, 11, 3, 22, 0)},
    ])
    d = {"turni": turni}
    res = calcola_rientri_rapidi(d)
    assert not res.empty
    assert res.iloc[0]["valore"] == 1
    assert res.iloc[0]["codice"] == "c001"

def test_turni_lunghi():
    turni = pd.DataFrame([
        # Turno da 8 ore
        {"codice": "c001", "reparto": "Medicina", "inizio": datetime(2026, 11, 1, 7, 0), "fine": datetime(2026, 11, 1, 15, 0)},
        # Turno da 12 ore
        {"codice": "c001", "reparto": "Medicina", "inizio": datetime(2026, 11, 3, 7, 0), "fine": datetime(2026, 11, 3, 19, 0)},
    ])
    d = {"turni": turni}
    res = calcola_turni_lunghi(d)
    assert not res.empty
    assert res.iloc[0]["valore"] == 1

def test_pazienti_infermiere():
    turni = pd.DataFrame([
        {"codice": "c001", "reparto": "Medicina", "inizio": datetime(2026, 11, 1, 7, 0), "fine": datetime(2026, 11, 1, 15, 0)},
        {"codice": "c002", "reparto": "Medicina", "inizio": datetime(2026, 11, 1, 7, 0), "fine": datetime(2026, 11, 1, 15, 0)},
    ])
    dipendenti = pd.DataFrame([
        {"codice": "c001", "reparto": "Medicina", "ruolo": "infermiere"},
        {"codice": "c002", "reparto": "Medicina", "ruolo": "infermiere"},
    ])
    occupazione = pd.DataFrame([
        {"reparto": "Medicina", "data": date(2026, 11, 1), "pazienti_presenti": 16},
    ])
    d = {"turni": turni, "dipendenti": dipendenti, "occupazione": occupazione}
    res = calcola_pazienti_infermiere(d)
    assert not res.empty
    # 16 pazienti / 2 infermieri = 8.0
    assert res.iloc[0]["valore"] == 8.0

def test_malattia_brevi():
    assenze = pd.DataFrame([
        # Assenza breve di 2 giorni (1-3 gg)
        {"codice": "c001", "tipo": "malattia", "data_inizio": date(2026, 11, 1), "data_fine": date(2026, 11, 2)},
        # Assenza lunga di 10 giorni
        {"codice": "c001", "tipo": "malattia", "data_inizio": date(2026, 11, 10), "data_fine": date(2026, 11, 19)},
    ])
    d = {"assenze": assenze}
    res = calcola_malattia_brevi(d)
    assert not res.empty
    assert res.iloc[0]["valore"] == 1

def test_dimissioni():
    dipendenti = pd.DataFrame([
        {"codice": "c001", "reparto": "Medicina", "data_cessazione": date(2026, 10, 1), "tipo_cessazione": "dimissioni"},
        {"codice": "c002", "reparto": "Medicina", "data_cessazione": date(2026, 10, 15), "tipo_cessazione": "dimissioni"},
        {"codice": "c003", "reparto": "Medicina", "data_cessazione": None, "tipo_cessazione": None},
    ])
    d = {"dipendenti": dipendenti}
    res = calcola_dimissioni(d)
    assert not res.empty
    assert res.iloc[0]["valore"] == 2
