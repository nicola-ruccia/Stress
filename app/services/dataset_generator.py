import random
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.core.privacy import pseudonimize_matricola
from app.models.entities import (
    Dipendente,
    Turno,
    Assenza,
    OreMese,
    EventoHR,
    Aggressione,
    Occupazione,
    Checkin,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

REPARTI_CONFIG = [
    {"nome": "Medicina", "organico": 30, "target": "rosso"},
    {"nome": "Nucleo Alzheimer (RSA)", "organico": 30, "target": "giallo"},
    {"nome": "Chirurgia", "organico": 28, "target": "giallo-verde"},
    {"nome": "Cardiologia", "organico": 24, "target": "verde"},
    {"nome": "Riabilitazione", "organico": 22, "target": "verde"},
    {"nome": "Ambulatori", "organico": 16, "target": "verde"},
]

def build_dataset_dataframes(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Genera i 7 DataFrame sintetici e i check-in secondo lo scenario della demo:
    - 150 operatori, 6 reparti, 24 mesi (2024-12-01 al 2026-11-22).
    - Riproduce fedelmente la criticità in Medicina (carenza, dimissioni, rientri rapidi, 4 casi gravi)
      e le aggressioni nel Nucleo Alzheimer.
    """
    random.seed(seed)

    dipendenti_rows = []
    turni_rows = []
    assenze_rows = []
    ore_mese_rows = []
    eventi_hr_rows = []
    aggressioni_rows = []
    occupazione_rows = []
    checkin_rows = []

    matricola_counter = 1000
    start_date = date(2024, 12, 1)
    end_date = date(2026, 11, 20)

    # Elenco mesi (24 mesi)
    mesi_list = []
    cur_m = start_date.replace(day=1)
    while cur_m <= end_date:
        mesi_list.append(cur_m.strftime("%Y-%m"))
        # Increment month
        year = cur_m.year + (1 if cur_m.month == 12 else 0)
        month = 1 if cur_m.month == 12 else cur_m.month + 1
        cur_m = date(year, month, 1)

    all_operators = []

    # 1. GENERAZIONE DIPENDENTI
    for rep in REPARTI_CONFIG:
        rep_nome = rep["nome"]
        organico = rep["organico"]

        for i in range(organico):
            matricola_counter += 1
            mat_str = f"M{matricola_counter}"
            codice = pseudonimize_matricola(mat_str)

            # Ruolo
            if i < int(organico * 0.65):
                ruolo = "infermiere"
            elif i < int(organico * 0.85):
                ruolo = "OSS"
            else:
                ruolo = "medico"

            data_ass = date(2022, 1, 1) + timedelta(days=random.randint(0, 700))
            data_cess = None
            tipo_cess = None

            # Dimissioni in Medicina negli ultimi 4 mesi (3 dimissioni)
            is_dimesso = False
            if rep_nome == "Medicina" and i < 3:
                data_cess = date(2026, 8, 1) + timedelta(days=random.randint(10, 80))
                tipo_cess = "dimissioni"
                is_dimesso = True

            op_info = {
                "matricola": mat_str,
                "codice": codice,
                "reparto": rep_nome,
                "ruolo": ruolo,
                "data_assunzione": data_ass,
                "data_cessazione": data_cess,
                "tipo_cessazione": tipo_cess,
                "is_critical": (rep_nome == "Medicina" and 3 <= i < 7),  # 4 casi gravi
                "is_dimesso": is_dimesso,
            }
            all_operators.append(op_info)
            dipendenti_rows.append({
                "matricola": mat_str,
                "reparto": rep_nome,
                "ruolo": ruolo,
                "data_assunzione": data_ass.isoformat(),
                "data_cessazione": data_cess.isoformat() if data_cess else None,
                "tipo_cessazione": tipo_cess,
            })

    # 2. GENERAZIONE OCCUPAZIONE E AGGRESSIONI
    cur_d = start_date
    while cur_d <= end_date:
        mese_str = cur_d.strftime("%Y-%m")
        is_last_6_months = (cur_d >= date(2026, 6, 1))

        for rep in REPARTI_CONFIG:
            rep_nome = rep["nome"]

            # Occupazione letti
            if rep_nome == "Medicina":
                pazienti = random.randint(28, 35) if is_last_6_months else random.randint(20, 24)
            elif rep_nome == "Nucleo Alzheimer (RSA)":
                pazienti = random.randint(25, 30)
            elif rep_nome == "Chirurgia":
                pazienti = random.randint(20, 26)
            elif rep_nome == "Cardiologia":
                pazienti = random.randint(18, 22)
            elif rep_nome == "Riabilitazione":
                pazienti = random.randint(18, 22)
            else:  # Ambulatori
                pazienti = random.randint(10, 15)

            occupazione_rows.append({
                "reparto": rep_nome,
                "data": cur_d.isoformat(),
                "pazienti_presenti": pazienti,
            })

            # Aggressioni: frequenti nel Nucleo Alzheimer (3-5 al mese), rare altrove
            if rep_nome == "Nucleo Alzheimer (RSA)":
                if random.random() < 0.12:  # circa 3-4 al mese
                    aggressioni_rows.append({
                        "reparto": rep_nome,
                        "data": cur_d.isoformat(),
                    })
            elif rep_nome in {"Medicina", "Chirurgia"}:
                if random.random() < 0.02:
                    aggressioni_rows.append({
                        "reparto": rep_nome,
                        "data": cur_d.isoformat(),
                    })

        cur_d += timedelta(days=1)

    # 3. GENERAZIONE TURNI
    cur_d = start_date
    while cur_d <= end_date:
        is_last_6_months = (cur_d >= date(2026, 6, 1))

        for op in all_operators:
            if op["is_dimesso"] and op["data_cessazione"] and cur_d >= op["data_cessazione"]:
                continue

            rep_nome = op["reparto"]

            # Frequenza lavoro
            prob_lavoro = 0.72 if (rep_nome == "Medicina" and is_last_6_months) else 0.65
            if random.random() > prob_lavoro:
                continue

            # Orari
            if rep_nome == "Ambulatori":
                # Solo turni diurni
                t_ini = datetime.combine(cur_d, datetime.min.time()) + timedelta(hours=8)
                t_fin = t_ini + timedelta(hours=8)
            elif rep_nome in {"Chirurgia", "Medicina"} and random.random() < 0.40:
                # Turno 12 ore (7-19 oppure 19-7)
                start_h = 7 if random.random() < 0.5 else 19
                t_ini = datetime.combine(cur_d, datetime.min.time()) + timedelta(hours=start_h)
                t_fin = t_ini + timedelta(hours=12)
            else:
                # Turno 8 ore (7-14, 14-21, 21-7)
                slot = random.choice([(7, 7), (14, 7), (21, 10)])
                t_ini = datetime.combine(cur_d, datetime.min.time()) + timedelta(hours=slot[0])
                t_fin = t_ini + timedelta(hours=slot[1])

            # Rientri rapidi provocati intenzionalmente in Medicina (e nei casi critici)
            if op["is_critical"] and is_last_6_months and random.random() < 0.35:
                # Forza un rientro rapido (es. fine alle 22 e inizio alle 6 o 7)
                t_ini = datetime.combine(cur_d, datetime.min.time()) + timedelta(hours=6)
                t_fin = t_ini + timedelta(hours=8)

            turni_rows.append({
                "matricola": op["matricola"],
                "reparto": rep_nome,
                "inizio": t_ini.isoformat(),
                "fine": t_fin.isoformat(),
            })

        cur_d += timedelta(days=1)

    # 4. GENERAZIONE ORE_MESE E EVENTI HR
    for op in all_operators:
        rep_nome = op["reparto"]

        for m_str in mesi_list:
            is_recent = m_str >= "2026-06"

            if op["is_critical"] and is_recent:
                straord = random.uniform(32.0, 48.0)
                ferie = random.uniform(26.0, 35.0)
            elif rep_nome == "Medicina" and is_recent:
                straord = random.uniform(22.0, 36.0)
                ferie = random.uniform(20.0, 28.0)
            elif rep_nome == "Chirurgia":
                straord = random.uniform(14.0, 22.0)
                ferie = random.uniform(12.0, 18.0)
            else:
                straord = random.uniform(2.0, 10.0)
                ferie = random.uniform(5.0, 12.0)

            ore_mese_rows.append({
                "matricola": op["matricola"],
                "mese": m_str,
                "ore_straordinario": round(straord, 1),
                "ferie_residue_giorni": round(ferie, 1),
            })

        # Eventi HR: richieste di trasferimento o procedimenti
        if rep_nome == "Medicina" and random.random() < 0.30:
            eventi_hr_rows.append({
                "matricola": op["matricola"],
                "data": date(2026, random.randint(6, 11), random.randint(1, 25)).isoformat(),
                "tipo": "richiesta_trasferimento",
            })
        elif random.random() < 0.05:
            eventi_hr_rows.append({
                "matricola": op["matricola"],
                "data": date(2026, random.randint(1, 10), random.randint(1, 25)).isoformat(),
                "tipo": "richiesta_trasferimento",
            })

    # 5. GENERAZIONE ASSENZE (Poisson con frequenza più alta in Medicina)
    for op in all_operators:
        rep_nome = op["reparto"]
        n_assenze = 6 if op["is_critical"] else (4 if rep_nome == "Medicina" else 2)

        for _ in range(n_assenze):
            a_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            durata = random.randint(1, 3) if (op["is_critical"] or random.random() < 0.7) else random.randint(4, 10)
            a_fine = a_date + timedelta(days=durata - 1)

            assenze_rows.append({
                "matricola": op["matricola"],
                "tipo": "malattia",
                "data_inizio": a_date.isoformat(),
                "data_fine": a_fine.isoformat(),
            })

    # 6. GENERAZIONE CHECK-IN DEMO (risponde circa il 60% delle persone al mese)
    for op in all_operators:
        for m_str in mesi_list[-6:]:
            if random.random() > 0.60:
                continue

            anno, mese = map(int, m_str.split("-"))
            chk_date = date(anno, mese, random.randint(15, 28))

            if op["is_critical"]:
                v_singola = 4
                bat_score = round(random.uniform(3.4, 4.2), 2)
                richiesta_colloquio = True
            elif op["reparto"] == "Medicina" and m_str >= "2026-06":
                v_singola = random.choice([3, 4])
                bat_score = round(random.uniform(2.8, 3.5), 2)
                richiesta_colloquio = (random.random() < 0.4)
            else:
                v_singola = random.choice([1, 2])
                bat_score = None
                richiesta_colloquio = False

            checkin_rows.append({
                "codice": op["codice"],
                "data": chk_date.isoformat(),
                "domanda_singola": v_singola,
                "bat12_punteggio": bat_score,
                "consenso_medico": True,
                "richiesta_colloquio": richiesta_colloquio,
            })

    return {
        "dipendenti": pd.DataFrame(dipendenti_rows),
        "turni": pd.DataFrame(turni_rows),
        "assenze": pd.DataFrame(assenze_rows),
        "ore_mese": pd.DataFrame(ore_mese_rows),
        "eventi_hr": pd.DataFrame(eventi_hr_rows),
        "aggressioni": pd.DataFrame(aggressioni_rows),
        "occupazione": pd.DataFrame(occupazione_rows),
        "checkin_demo": pd.DataFrame(checkin_rows),
    }

def esporta_file_demo():
    """Genera i file demo.xlsx, checkin_demo.csv e modello_import.xlsx su disco."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dfs = build_dataset_dataframes()

    # 1. demo.xlsx con i 7 fogli
    demo_xlsx_path = DATA_DIR / "demo.xlsx"
    with pd.ExcelWriter(demo_xlsx_path, engine="openpyxl") as writer:
        dfs["dipendenti"].to_excel(writer, sheet_name="dipendenti", index=False)
        dfs["turni"].to_excel(writer, sheet_name="turni", index=False)
        dfs["assenze"].to_excel(writer, sheet_name="assenze", index=False)
        dfs["ore_mese"].to_excel(writer, sheet_name="ore_mese", index=False)
        dfs["eventi_hr"].to_excel(writer, sheet_name="eventi_hr", index=False)
        dfs["aggressioni"].to_excel(writer, sheet_name="aggressioni", index=False)
        dfs["occupazione"].to_excel(writer, sheet_name="occupazione", index=False)

    # 2. checkin_demo.csv
    checkin_csv_path = DATA_DIR / "checkin_demo.csv"
    dfs["checkin_demo"].to_csv(checkin_csv_path, index=False)

    # 3. modello_import.xlsx vuoto con le colonne corrette
    modello_path = DATA_DIR / "modello_import.xlsx"
    with pd.ExcelWriter(modello_path, engine="openpyxl") as writer:
        for sheet_name in ["dipendenti", "turni", "assenze", "ore_mese", "eventi_hr", "aggressioni", "occupazione"]:
            empty_df = dfs[sheet_name].iloc[0:0]
            empty_df.to_excel(writer, sheet_name=sheet_name, index=False)

    return {
        "demo_xlsx": str(demo_xlsx_path),
        "checkin_demo_csv": str(checkin_csv_path),
        "modello_import_xlsx": str(modello_path),
    }

def genera_dataset_demo(db: Session) -> Dict[str, Any]:
    """Precarica direttamente il dataset sintetico nel database SQLite."""
    files_info = esporta_file_demo()
    dfs = build_dataset_dataframes()

    # Pulisci tabelle esistenti
    db.query(Turno).delete()
    db.query(Assenza).delete()
    db.query(OreMese).delete()
    db.query(EventoHR).delete()
    db.query(Aggressione).delete()
    db.query(Occupazione).delete()
    db.query(Checkin).delete()
    db.query(Dipendente).delete()
    db.commit()

    # Inserisci Dipendenti
    dip_objs = []
    for _, row in dfs["dipendenti"].iterrows():
        codice = pseudonimize_matricola(row["matricola"])
        data_cess = pd.to_datetime(row["data_cessazione"]).date() if pd.notna(row["data_cessazione"]) else None
        dip_objs.append(Dipendente(
            codice=codice,
            reparto=row["reparto"],
            ruolo=row["ruolo"],
            data_assunzione=pd.to_datetime(row["data_assunzione"]).date(),
            data_cessazione=data_cess,
            tipo_cessazione=row["tipo_cessazione"] if pd.notna(row["tipo_cessazione"]) else None,
        ))
    db.bulk_save_objects(dip_objs)
    db.commit()

    # Inserisci Occupazione
    occ_objs = [
        Occupazione(
            reparto=row["reparto"],
            data=pd.to_datetime(row["data"]).date(),
            pazienti_presenti=int(row["pazienti_presenti"]),
        )
        for _, row in dfs["occupazione"].iterrows()
    ]
    db.bulk_save_objects(occ_objs)

    # Inserisci Aggressioni
    agg_objs = [
        Aggressione(
            reparto=row["reparto"],
            data=pd.to_datetime(row["data"]).date(),
        )
        for _, row in dfs["aggressioni"].iterrows()
    ]
    db.bulk_save_objects(agg_objs)

    # Inserisci Turni
    tur_objs = [
        Turno(
            codice=pseudonimize_matricola(row["matricola"]),
            reparto=row["reparto"],
            inizio=pd.to_datetime(row["inizio"]).to_pydatetime(),
            fine=pd.to_datetime(row["fine"]).to_pydatetime(),
        )
        for _, row in dfs["turni"].iterrows()
    ]
    db.bulk_save_objects(tur_objs)

    # Inserisci OreMese
    ore_objs = [
        OreMese(
            codice=pseudonimize_matricola(row["matricola"]),
            mese=str(row["mese"]),
            ore_straordinario=float(row["ore_straordinario"]),
            ferie_residue_giorni=float(row["ferie_residue_giorni"]),
        )
        for _, row in dfs["ore_mese"].iterrows()
    ]
    db.bulk_save_objects(ore_objs)

    # Inserisci Assenze
    ass_objs = [
        Assenza(
            codice=pseudonimize_matricola(row["matricola"]),
            tipo=row["tipo"],
            data_inizio=pd.to_datetime(row["data_inizio"]).date(),
            data_fine=pd.to_datetime(row["data_fine"]).date(),
        )
        for _, row in dfs["assenze"].iterrows()
    ]
    db.bulk_save_objects(ass_objs)

    # Inserisci Eventi HR
    eve_objs = [
        EventoHR(
            codice=pseudonimize_matricola(row["matricola"]),
            data=pd.to_datetime(row["data"]).date(),
            tipo=row["tipo"],
        )
        for _, row in dfs["eventi_hr"].iterrows()
    ]
    db.bulk_save_objects(eve_objs)

    # Inserisci Check-in demo
    chk_objs = [
        Checkin(
            codice=row["codice"],
            data=pd.to_datetime(row["data"]).date(),
            domanda_singola=int(row["domanda_singola"]),
            bat12_punteggio=float(row["bat12_punteggio"]) if pd.notna(row["bat12_punteggio"]) else None,
            consenso_medico=bool(row["consenso_medico"]),
            richiesta_colloquio=bool(row["richiesta_colloquio"]),
        )
        for _, row in dfs["checkin_demo"].iterrows()
    ]
    db.bulk_save_objects(chk_objs)

    db.commit()

    return {
        "dipendenti_inseriti": len(dip_objs),
        "turni_inseriti": len(tur_objs),
        "assenze_inserite": len(ass_objs),
        "ore_mese_inserite": len(ore_objs),
        "checkin_inseriti": len(chk_objs),
        "file_generati": files_info,
    }
