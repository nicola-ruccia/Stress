from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models.entities import (
    Dipendente,
    Turno,
    Assenza,
    OreMese,
    EventoHR,
    Aggressione,
    Occupazione,
    Checkin,
    PresaInCarico,
)
from app.core.config import settings, soglie_config
from app.core.indicators import REGISTRO
from app.core.scoring import (
    calcola_punteggio_sintetico,
    verifica_da_contattare,
    get_semaforo,
)
from app.core.privacy import is_k_min_satisfied

def load_dataframes_from_db(db: Session) -> Dict[str, pd.DataFrame]:
    """
    Carica i dati dal database SQLite nei DataFrame pandas per il motore di calcolo.
    """
    dip_q = db.query(Dipendente).all()
    tur_q = db.query(Turno).all()
    ass_q = db.query(Assenza).all()
    ore_q = db.query(OreMese).all()
    eve_q = db.query(EventoHR).all()
    agg_q = db.query(Aggressione).all()
    occ_q = db.query(Occupazione).all()
    chk_q = db.query(Checkin).all()

    df_dip = pd.DataFrame([{
        "codice": d.codice,
        "reparto": d.reparto,
        "ruolo": d.ruolo,
        "data_assunzione": d.data_assunzione,
        "data_cessazione": d.data_cessazione,
        "tipo_cessazione": d.tipo_cessazione,
    } for d in dip_q])

    df_tur = pd.DataFrame([{
        "codice": t.codice,
        "reparto": t.reparto,
        "inizio": t.inizio,
        "fine": t.fine,
    } for t in tur_q])

    df_ass = pd.DataFrame([{
        "codice": a.codice,
        "tipo": a.tipo,
        "data_inizio": a.data_inizio,
        "data_fine": a.data_fine,
    } for a in ass_q])

    df_ore = pd.DataFrame([{
        "codice": o.codice,
        "mese": o.mese,
        "ore_straordinario": o.ore_straordinario,
        "ferie_residue_giorni": o.ferie_residue_giorni,
    } for o in ore_q])

    df_eve = pd.DataFrame([{
        "codice": e.codice,
        "data": e.data,
        "tipo": e.tipo,
    } for e in eve_q])

    df_agg = pd.DataFrame([{
        "reparto": a.reparto,
        "data": a.data,
    } for a in agg_q])

    df_occ = pd.DataFrame([{
        "reparto": o.reparto,
        "data": o.data,
        "pazienti_presenti": o.pazienti_presenti,
    } for o in occ_q])

    df_chk = pd.DataFrame([{
        "codice": c.codice,
        "data": c.data,
        "domanda_singola": c.domanda_singola,
        "bat12_punteggio": c.bat12_punteggio,
        "consenso_medico": c.consenso_medico,
    } for c in chk_q])

    return {
        "dipendenti": df_dip,
        "turni": df_tur,
        "assenze": df_ass,
        "ore_mese": df_ore,
        "eventi_hr": df_eve,
        "aggressioni": df_agg,
        "occupazione": df_occ,
        "checkin": df_chk,
    }

def get_latest_month(data_dict: Dict[str, pd.DataFrame]) -> str:
    """Restituisce il mese più recente presente nei dati nel formato YYYY-MM."""
    turni = data_dict.get("turni", pd.DataFrame())
    if not turni.empty and "inizio" in turni.columns:
        return pd.to_datetime(turni["inizio"]).max().strftime("%Y-%m")
    ore = data_dict.get("ore_mese", pd.DataFrame())
    if not ore.empty and "mese" in ore.columns:
        return str(ore["mese"].max())
    return datetime.utcnow().strftime("%Y-%m")

def compute_all_indicators(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Esegue tutti i 13 indicatori registrati."""
    risultati = {}
    for ind_id, ind in REGISTRO.items():
        try:
            df_res = ind.calcola(data_dict)
            risultati[ind_id] = df_res
        except Exception:
            risultati[ind_id] = pd.DataFrame()
    return risultati

def compute_reparto_metrics(
    data_dict: Dict[str, pd.DataFrame],
    target_mese: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Calcola il punteggio di rischio e i semafori per ciascun reparto nel mese specificato.
    Applica la regola K_MIN = 6: se un reparto ha meno di 6 individui, mostra dati_insufficienti.
    """
    dip = data_dict.get("dipendenti", pd.DataFrame())
    if dip.empty:
        return []

    if target_mese is None:
        target_mese = get_latest_month(data_dict)

    ind_dfs = compute_all_indicators(data_dict)
    reparti = dip["reparto"].unique()
    reparto_list = []

    for rep in sorted(reparti):
        organico = len(dip[dip["reparto"] == rep])
        if not is_k_min_satisfied(organico):
            reparto_list.append({
                "reparto": rep,
                "mese": target_mese,
                "organico": organico,
                "dati_insufficienti": True,
                "motivo": f"Reparto con organico inferiore a K_MIN ({settings.K_MIN}). Dati aggregati mascherati a tutela della privacy.",
                "punteggio": None,
                "fascia": "insufficiente",
                "semafori": {},
                "top_3_fattori": [],
            })
            continue

        codici_rep = set(dip[dip["reparto"] == rep]["codice"])
        indicatori_valori = {}

        for ind_id, ind in REGISTRO.items():
            df_ind = ind_dfs.get(ind_id, pd.DataFrame())
            if df_ind.empty:
                continue

            # Filtra per mese
            if "mese" in df_ind.columns:
                df_mese = df_ind[df_ind["mese"] == target_mese]
            else:
                df_mese = df_ind

            if df_mese.empty:
                continue

            if ind.livello == "persona":
                df_persone_rep = df_mese[df_mese["codice"].isin(codici_rep)]
                if not df_persone_rep.empty and "valore" in df_persone_rep.columns:
                    indicatori_valori[ind_id] = float(df_persone_rep["valore"].mean())
            elif ind.livello == "reparto":
                df_rep = df_mese[df_mese["reparto"] == rep]
                if not df_rep.empty and "valore" in df_rep.columns:
                    indicatori_valori[ind_id] = float(df_rep["valore"].mean())

        score_res = calcola_punteggio_sintetico(indicatori_valori)
        reparto_list.append({
            "reparto": rep,
            "mese": target_mese,
            "organico": organico,
            "dati_insufficienti": False,
            "punteggio": score_res["punteggio"],
            "fascia": score_res["fascia"],
            "semafori": score_res["semafori"],
            "top_3_fattori": score_res["top_3_fattori"],
        })

    return reparto_list

def compute_hr_dashboard(
    db: Session,
    target_mese: Optional[str] = None,
    costo_turnover_unitario: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Restituisce i dati per la Dashboard HR:
    - 4 KPI in alto:
      1. Livello di rischio della struttura (punteggio medio e fascia)
      2. Reparti in rosso (conteggio e nomi)
      3. Costo del turnover ultimi 12 mesi (dimissioni * 45.000 € parametrizzabile)
      4. Persone prese in carico dal medico competente (SOLO il numero aggregato!)
    - Heatmap reparti × mesi
    - Lista reparti con semafori e azioni suggerite
    """
    data_dict = load_dataframes_from_db(db)
    if target_mese is None:
        target_mese = get_latest_month(data_dict)

    reparti_metrics = compute_reparto_metrics(data_dict, target_mese)
    reparti_validi = [r for r in reparti_metrics if not r.get("dati_insufficienti")]

    # 1. Punteggio medio struttura
    if reparti_validi:
        punteggio_struttura = round(
            float(np.mean([r["punteggio"] for r in reparti_validi if r["punteggio"] is not None])), 1
        )
    else:
        punteggio_struttura = 0.0

    fasce = soglie_config.get("fasce", {"basso": 34, "alto": 66})
    if punteggio_struttura >= fasce.get("alto", 66):
        fascia_struttura = "alto"
    elif punteggio_struttura >= fasce.get("basso", 34):
        fascia_struttura = "medio"
    else:
        fascia_struttura = "basso"

    # 2. Reparti in rosso
    reparti_rossi = [r["reparto"] for r in reparti_validi if r["fascia"] == "alto"]

    # 3. Costo del turnover
    costo_unit = costo_turnover_unitario or settings.COSTO_TURNOVER_DEFAULT
    dip = data_dict.get("dipendenti", pd.DataFrame())
    dimissioni_count = 0
    if not dip.empty and "tipo_cessazione" in dip.columns:
        dim_df = dip[dip["tipo_cessazione"].astype(str).str.lower().str.contains("dimission", na=False)]
        dimissioni_count = len(dim_df)
    costo_turnover_totale = dimissioni_count * costo_unit

    # 4. Persone prese in carico dal medico (solo conteggio anonimo)
    persone_in_carico_count = db.query(PresaInCarico).count()

    # 5. Heatmap reparti x mesi (ultimi 6 o 12 mesi)
    mesi_disponibili = set()
    turni = data_dict.get("turni", pd.DataFrame())
    if not turni.empty:
        mesi_disponibili.update(pd.to_datetime(turni["inizio"]).dt.strftime("%Y-%m").unique())
    ore = data_dict.get("ore_mese", pd.DataFrame())
    if not ore.empty:
        mesi_disponibili.update(ore["mese"].dropna().unique())

    mesi_ordinati = sorted(mesi_disponibili)[-6:] if mesi_disponibili else [target_mese]
    heatmap_matrix = []
    for rep_m in reparti_metrics:
        rep_nome = rep_m["reparto"]
        if rep_m.get("dati_insufficienti"):
            heatmap_matrix.append({
                "reparto": rep_nome,
                "dati_insufficienti": True,
                "mesi_valori": {m: None for m in mesi_ordinati},
            })
            continue

        mesi_valori = {}
        for m in mesi_ordinati:
            m_metrics = compute_reparto_metrics(data_dict, m)
            matched = next((x for x in m_metrics if x["reparto"] == rep_nome), None)
            mesi_valori[m] = matched["punteggio"] if matched else None

        heatmap_matrix.append({
            "reparto": rep_nome,
            "dati_insufficienti": False,
            "mesi_valori": mesi_valori,
        })

    return {
        "mese_riferimento": target_mese,
        "kpi": {
            "punteggio_struttura": punteggio_struttura,
            "fascia_rischio_struttura": fascia_struttura,
            "reparti_in_rosso_count": len(reparti_rossi),
            "reparti_in_rosso": reparti_rossi,
            "dimissioni_ultimi_12_mesi": dimissioni_count,
            "costo_turnover_unitario": costo_unit,
            "costo_turnover_stimato": costo_turnover_totale,
            "persone_in_carico_medico": persone_in_carico_count,
        },
        "heatmap": {
            "mesi": mesi_ordinati,
            "matrix": heatmap_matrix,
        },
        "reparti": reparti_metrics,
    }

def compute_medico_dashboard(
    db: Session,
    reparto_filtro: Optional[str] = None,
    target_mese: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Vista Medico Competente / Psicologo:
    Elenco codici pseudonimizzati ordinati per punteggio di rischio,
    con la bandiera 'da contattare' (checkin >= 3 o BAT-12 oltre soglia)
    e stato presa in carico.
    """
    data_dict = load_dataframes_from_db(db)
    if target_mese is None:
        target_mese = get_latest_month(data_dict)

    dip = data_dict.get("dipendenti", pd.DataFrame())
    if dip.empty:
        return []

    if reparto_filtro:
        dip = dip[dip["reparto"] == reparto_filtro]

    ind_dfs = compute_all_indicators(data_dict)
    prese_in_carico_map = {p.codice: p for p in db.query(PresaInCarico).all()}

    risultati_operatori = []
    for _, row in dip.iterrows():
        codice = row["codice"]
        reparto = row["reparto"]
        ruolo = row["ruolo"]

        ind_valori = {}
        checkin_val = None
        bat12_val = None

        for ind_id, ind in REGISTRO.items():
            df_ind = ind_dfs.get(ind_id, pd.DataFrame())
            if df_ind.empty:
                continue

            df_mese = df_ind[df_ind["mese"] == target_mese] if "mese" in df_ind.columns else df_ind
            if df_mese.empty:
                continue

            if ind.livello == "persona":
                df_cod = df_mese[df_mese["codice"] == codice]
                if not df_cod.empty and "valore" in df_cod.columns:
                    val = float(df_cod["valore"].iloc[0])
                    ind_valori[ind_id] = val
                    if ind_id == "checkin":
                        checkin_val = val
                    elif ind_id == "bat12":
                        bat12_val = val
            elif ind.livello == "reparto":
                df_rep = df_mese[df_mese["reparto"] == reparto]
                if not df_rep.empty and "valore" in df_rep.columns:
                    ind_valori[ind_id] = float(df_rep["valore"].iloc[0])

        score_res = calcola_punteggio_sintetico(ind_valori)
        da_contattare = verifica_da_contattare(checkin_val, bat12_val)

        pic = prese_in_carico_map.get(codice)
        stato_presa_in_carico = pic.stato if pic else "non_preso_in_carico"
        note_presa_in_carico = pic.note if pic else None

        risultati_operatori.append({
            "codice": codice,
            "reparto": reparto,
            "ruolo": ruolo,
            "mese": target_mese,
            "punteggio": score_res["punteggio"],
            "fascia": score_res["fascia"],
            "da_contattare": da_contattare,
            "stato_presa_in_carico": stato_presa_in_carico,
            "note_presa_in_carico": note_presa_in_carico,
            "top_3_fattori": score_res["top_3_fattori"],
            "semafori": score_res["semafori"],
        })

    # Ordina per da_contattare (True prima) e poi per punteggio decrescente
    risultati_operatori.sort(key=lambda x: (x["da_contattare"], x["punteggio"]), reverse=True)
    return risultati_operatori

def get_operatore_scheda_medico(
    db: Session,
    codice: str,
) -> Optional[Dict[str, Any]]:
    """
    Restituisce la scheda dettagliata di un operatore per il Medico:
    - Dati anagrafici minimi (codice pseudonimo, reparto, ruolo)
    - Andamento mensile indicatori
    - Top 3 fattori
    - Storico checkin e BAT-12 SOLO se consenso_medico == True
    """
    dip = db.query(Dipendente).filter(Dipendente.codice == codice).first()
    if not dip:
        return None

    data_dict = load_dataframes_from_db(db)
    target_mese = get_latest_month(data_dict)
    ind_dfs = compute_all_indicators(data_dict)

    # Raccogli mesi
    turni = data_dict.get("turni", pd.DataFrame())
    mesi = sorted(pd.to_datetime(turni["inizio"]).dt.strftime("%Y-%m").unique()) if not turni.empty else [target_mese]

    trend_mensile = []
    for m in mesi[-12:]:
        m_valori = {}
        for ind_id, ind in REGISTRO.items():
            df_ind = ind_dfs.get(ind_id, pd.DataFrame())
            if df_ind.empty or "mese" not in df_ind.columns:
                continue
            df_m = df_ind[df_ind["mese"] == m]
            if ind.livello == "persona":
                df_c = df_m[df_m["codice"] == codice]
                if not df_c.empty:
                    m_valori[ind_id] = float(df_c["valore"].iloc[0])
            elif ind.livello == "reparto":
                df_r = df_m[df_m["reparto"] == dip.reparto]
                if not df_r.empty:
                    m_valori[ind_id] = float(df_r["valore"].iloc[0])

        score_res = calcola_punteggio_sintetico(m_valori)
        trend_mensile.append({
            "mese": m,
            "punteggio": score_res["punteggio"],
            "fascia": score_res["fascia"],
        })

    # Checkin dell'operatore
    checkins = db.query(Checkin).filter(Checkin.codice == codice).order_by(Checkin.data.desc()).all()
    checkin_history = []
    ultimo_consenso = True

    if checkins:
        ultimo_consenso = checkins[0].consenso_medico
        for chk in checkins:
            if chk.consenso_medico:
                checkin_history.append({
                    "data": chk.data.isoformat(),
                    "domanda_singola": chk.domanda_singola,
                    "bat12_punteggio": chk.bat12_punteggio,
                    "bat12_dettaglio": chk.bat12_dettaglio,
                    "richiesta_colloquio": chk.richiesta_colloquio,
                })
            else:
                # Consenso negato/revocato: non mostrare i dettagli
                checkin_history.append({
                    "data": chk.data.isoformat(),
                    "consenso_negato": True,
                    "messaggio": "Dato oscurato per assenza o revoca del consenso dell'operatore.",
                })

    pic = db.query(PresaInCarico).filter(PresaInCarico.codice == codice).first()

    return {
        "codice": dip.codice,
        "reparto": dip.reparto,
        "ruolo": dip.ruolo,
        "data_assunzione": dip.data_assunzione.isoformat() if dip.data_assunzione else None,
        "ultimo_mese": target_mese,
        "trend_mensile": trend_mensile,
        "consenso_medico_attivo": ultimo_consenso,
        "checkin_history": checkin_history if ultimo_consenso else [],
        "presa_in_carico": {
            "stato": pic.stato if pic else "non_preso_in_carico",
            "note": pic.note if pic else None,
            "data": pic.data_presa_in_carico.isoformat() if pic else None,
        },
    }
