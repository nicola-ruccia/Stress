import io
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from app.core.privacy import (
    ALLOWED_EXCEL_FIELDS,
    pseudonimize_matricola,
)
from app.models.entities import (
    Dipendente,
    Turno,
    Assenza,
    OreMese,
    EventoHR,
    Aggressione,
    Occupazione,
    ImportHistory,
)

def process_excel_upload(
    file_bytes: bytes,
    filename: str,
    db: Session,
    pseudo_key: Optional[str] = None,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Legge il file Excel con i 7 fogli, valida i campi scartando colonne non ammesse,
    pseudonimizza immediatamente le matricole (HMAC-SHA256), carica i dati nel database
    e genera la tabella di decodifica matricola -> codice da restituire (NON salvata nel DB).
    """
    excel_file = io.BytesIO(file_bytes)
    xls = pd.ExcelFile(excel_file)
    available_sheets = xls.sheet_names

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "filename": filename,
        "fogli_trovati": available_sheets,
        "righe_accettate": {},
        "righe_scartate": {},
        "colonne_ignorate": {},
        "errori": [],
    }

    mapping_records = []
    totale_accettate = 0
    totale_scartate = 0

    # 1. Foglio DIPENDENTI
    reparti_validi = set()
    if "dipendenti" in available_sheets:
        df = pd.read_excel(xls, sheet_name="dipendenti")
        allowed = ALLOWED_EXCEL_FIELDS["dipendenti"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["dipendenti"] = colonne_scartate

        valid_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            matricola = str(row.get("matricola", "")).strip()
            reparto = str(row.get("reparto", "")).strip()
            ruolo = str(row.get("ruolo", "altro")).strip()
            data_ass = row.get("data_assunzione")

            if not matricola or not reparto or pd.isna(data_ass):
                scartate_count += 1
                continue

            codice = pseudonimize_matricola(matricola, key=pseudo_key)
            mapping_records.append({"matricola": matricola, "codice": codice, "reparto": reparto})
            reparti_validi.add(reparto)

            data_cess = row.get("data_cessazione")
            tipo_cess = row.get("tipo_cessazione")
            if pd.isna(data_cess):
                data_cess = None
            else:
                data_cess = pd.to_datetime(data_cess).date()

            valid_rows.append(Dipendente(
                codice=codice,
                reparto=reparto,
                ruolo=ruolo,
                data_assunzione=pd.to_datetime(data_ass).date(),
                data_cessazione=data_cess,
                tipo_cessazione=str(tipo_cess) if not pd.isna(tipo_cess) else None,
            ))

        # Salva o aggiorna dipendenti
        for dip in valid_rows:
            db.merge(dip)
        db.commit()

        report["righe_accettate"]["dipendenti"] = len(valid_rows)
        report["righe_scartate"]["dipendenti"] = scartate_count
        totale_accettate += len(valid_rows)
        totale_scartate += scartate_count

    # 2. Foglio TURNI
    if "turni" in available_sheets:
        df = pd.read_excel(xls, sheet_name="turni")
        allowed = ALLOWED_EXCEL_FIELDS["turni"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["turni"] = colonne_scartate

        turni_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            matricola = str(row.get("matricola", "")).strip()
            reparto = str(row.get("reparto", "")).strip()
            inizio = row.get("inizio")
            fine = row.get("fine")

            if not matricola or pd.isna(inizio) or pd.isna(fine):
                scartate_count += 1
                continue

            dt_inizio = pd.to_datetime(inizio)
            dt_fine = pd.to_datetime(fine)

            # Validazione integrità: il turno non può finire prima di iniziare
            if dt_fine <= dt_inizio:
                scartate_count += 1
                continue

            codice = pseudonimize_matricola(matricola, key=pseudo_key)
            turni_rows.append(Turno(
                codice=codice,
                reparto=reparto,
                inizio=dt_inizio.to_pydatetime(),
                fine=dt_fine.to_pydatetime(),
            ))

        if turni_rows:
            db.bulk_save_objects(turni_rows)
            db.commit()

        report["righe_accettate"]["turni"] = len(turni_rows)
        report["righe_scartate"]["turni"] = scartate_count
        totale_accettate += len(turni_rows)
        totale_scartate += scartate_count

    # 3. Foglio ASSENZE
    if "assenze" in available_sheets:
        df = pd.read_excel(xls, sheet_name="assenze")
        allowed = ALLOWED_EXCEL_FIELDS["assenze"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["assenze"] = colonne_scartate

        assenze_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            matricola = str(row.get("matricola", "")).strip()
            tipo = str(row.get("tipo", "")).strip()
            inizio = row.get("data_inizio")
            fine = row.get("data_fine")

            if not matricola or not tipo or pd.isna(inizio) or pd.isna(fine):
                scartate_count += 1
                continue

            dt_inizio = pd.to_datetime(inizio).date()
            dt_fine = pd.to_datetime(fine).date()
            if dt_fine < dt_inizio:
                scartate_count += 1
                continue

            codice = pseudonimize_matricola(matricola, key=pseudo_key)
            assenze_rows.append(Assenza(
                codice=codice,
                tipo=tipo,
                data_inizio=dt_inizio,
                data_fine=dt_fine,
            ))

        if assenze_rows:
            db.bulk_save_objects(assenze_rows)
            db.commit()

        report["righe_accettate"]["assenze"] = len(assenze_rows)
        report["righe_scartate"]["assenze"] = scartate_count
        totale_accettate += len(assenze_rows)
        totale_scartate += scartate_count

    # 4. Foglio ORE_MESE
    if "ore_mese" in available_sheets:
        df = pd.read_excel(xls, sheet_name="ore_mese")
        allowed = ALLOWED_EXCEL_FIELDS["ore_mese"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["ore_mese"] = colonne_scartate

        ore_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            matricola = str(row.get("matricola", "")).strip()
            mese = str(row.get("mese", "")).strip()
            if not matricola or not mese:
                scartate_count += 1
                continue

            straordinari = float(row.get("ore_straordinario", 0.0) or 0.0)
            ferie_res = float(row.get("ferie_residue_giorni", 0.0) or 0.0)

            codice = pseudonimize_matricola(matricola, key=pseudo_key)
            ore_rows.append(OreMese(
                codice=codice,
                mese=mese,
                ore_straordinario=straordinari,
                ferie_residue_giorni=ferie_res,
            ))

        if ore_rows:
            db.bulk_save_objects(ore_rows)
            db.commit()

        report["righe_accettate"]["ore_mese"] = len(ore_rows)
        report["righe_scartate"]["ore_mese"] = scartate_count
        totale_accettate += len(ore_rows)
        totale_scartate += scartate_count

    # 5. Foglio EVENTI_HR
    if "eventi_hr" in available_sheets:
        df = pd.read_excel(xls, sheet_name="eventi_hr")
        allowed = ALLOWED_EXCEL_FIELDS["eventi_hr"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["eventi_hr"] = colonne_scartate

        eventi_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            matricola = str(row.get("matricola", "")).strip()
            data_ev = row.get("data")
            tipo = str(row.get("tipo", "")).strip()
            if not matricola or pd.isna(data_ev) or not tipo:
                scartate_count += 1
                continue

            codice = pseudonimize_matricola(matricola, key=pseudo_key)
            eventi_rows.append(EventoHR(
                codice=codice,
                data=pd.to_datetime(data_ev).date(),
                tipo=tipo,
            ))

        if eventi_rows:
            db.bulk_save_objects(eventi_rows)
            db.commit()

        report["righe_accettate"]["eventi_hr"] = len(eventi_rows)
        report["righe_scartate"]["eventi_hr"] = scartate_count
        totale_accettate += len(eventi_rows)
        totale_scartate += scartate_count

    # 6. Foglio AGGRESSIONI
    if "aggressioni" in available_sheets:
        df = pd.read_excel(xls, sheet_name="aggressioni")
        allowed = ALLOWED_EXCEL_FIELDS["aggressioni"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["aggressioni"] = colonne_scartate

        aggr_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            reparto = str(row.get("reparto", "")).strip()
            data_aggr = row.get("data")
            if not reparto or pd.isna(data_aggr):
                scartate_count += 1
                continue

            aggr_rows.append(Aggressione(
                reparto=reparto,
                data=pd.to_datetime(data_aggr).date(),
            ))

        if aggr_rows:
            db.bulk_save_objects(aggr_rows)
            db.commit()

        report["righe_accettate"]["aggressioni"] = len(aggr_rows)
        report["righe_scartate"]["aggressioni"] = scartate_count
        totale_accettate += len(aggr_rows)
        totale_scartate += scartate_count

    # 7. Foglio OCCUPAZIONE
    if "occupazione" in available_sheets:
        df = pd.read_excel(xls, sheet_name="occupazione")
        allowed = ALLOWED_EXCEL_FIELDS["occupazione"]
        colonne_scartate = [c for c in df.columns if c not in allowed]
        if colonne_scartate:
            report["colonne_ignorate"]["occupazione"] = colonne_scartate

        occ_rows = []
        scartate_count = 0
        for _, row in df.iterrows():
            reparto = str(row.get("reparto", "")).strip()
            data_occ = row.get("data")
            if not reparto or pd.isna(data_occ):
                scartate_count += 1
                continue

            pazienti = int(row.get("pazienti_presenti", 0) or 0)
            occ_rows.append(Occupazione(
                reparto=reparto,
                data=pd.to_datetime(data_occ).date(),
                pazienti_presenti=pazienti,
            ))

        if occ_rows:
            db.bulk_save_objects(occ_rows)
            db.commit()

        report["righe_accettate"]["occupazione"] = len(occ_rows)
        report["righe_scartate"]["occupazione"] = scartate_count
        totale_accettate += len(occ_rows)
        totale_scartate += scartate_count

    # Registra import history
    import_rec = ImportHistory(
        nome_file=filename,
        righe_accettate=totale_accettate,
        righe_scartate=totale_scartate,
        report_json=str(report),
    )
    db.add(import_rec)
    db.commit()

    df_mapping = pd.DataFrame(mapping_records).drop_duplicates(subset=["codice"])
    return report, df_mapping
