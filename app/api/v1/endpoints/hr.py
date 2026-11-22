from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import (
    HRDashboardResponse,
    RepartoMetric,
    AvvisoOrario,
)
from app.services.analytics import (
    compute_hr_dashboard,
    compute_reparto_metrics,
    load_dataframes_from_db,
    compute_all_indicators,
    get_latest_month,
)
from app.core.config import settings

router = APIRouter()

@router.get("/dashboard", response_model=HRDashboardResponse, summary="Dashboard HR con KPI, Heatmap e Reparti")
def get_hr_dashboard(
    mese: Optional[str] = Query(None, description="Mese di riferimento (formato YYYY-MM)"),
    costo_turnover: Optional[float] = Query(None, description="Costo unitario per dimissione (default 45.000 €)"),
    db: Session = Depends(get_db),
):
    try:
        data = compute_hr_dashboard(db, target_mese=mese, costo_turnover_unitario=costo_turnover)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel calcolo della dashboard HR: {str(e)}",
        )

@router.get("/reparti", response_model=List[RepartoMetric], summary="Lista reparti con metriche di rischio")
def get_reparti(
    mese: Optional[str] = Query(None, description="Mese YYYY-MM"),
    db: Session = Depends(get_db),
):
    data_dict = load_dataframes_from_db(db)
    target = mese or get_latest_month(data_dict)
    return compute_reparto_metrics(data_dict, target)

@router.get("/reparto/{reparto_nome}", response_model=RepartoMetric, summary="Dettaglio singolo reparto")
def get_reparto_detail(
    reparto_nome: str,
    mese: Optional[str] = Query(None, description="Mese YYYY-MM"),
    db: Session = Depends(get_db),
):
    data_dict = load_dataframes_from_db(db)
    target = mese or get_latest_month(data_dict)
    reparti = compute_reparto_metrics(data_dict, target)
    matched = next((r for r in reparti if r["reparto"].lower() == reparto_nome.lower()), None)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reparto '{reparto_nome}' non trovato.",
        )
    return matched

@router.get("/avvisi-orario", response_model=List[AvvisoOrario], summary="Avvisi sull'orario di lavoro (senza etichetta burnout)")
def get_avvisi_orario(
    mese: Optional[str] = Query(None, description="Mese YYYY-MM"),
    db: Session = Depends(get_db),
):
    """
    Mostra codici con riposo sotto le 11 ore o turni di 12 ore o più.
    Attivo solo se l'opzione AVVISI_ORARIO_HR è abilitata (di default false per parere legale).
    Non contiene MAI la dicitura 'burnout' o riferimenti sanitari.
    """
    data_dict = load_dataframes_from_db(db)
    target = mese or get_latest_month(data_dict)
    ind_dfs = compute_all_indicators(data_dict)

    avvisi = []
    dip = data_dict.get("dipendenti")
    dip_map = {}
    if dip is not None and not dip.empty:
        dip_map = dict(zip(dip["codice"], dip["reparto"]))

    # 1. Rientri rapidi
    df_rr = ind_dfs.get("rientri_rapidi")
    if df_rr is not None and not df_rr.empty:
        df_m = df_rr[df_rr["mese"] == target]
        for _, row in df_m[df_m["valore"] > 0].iterrows():
            c = row["codice"]
            avvisi.append(AvvisoOrario(
                codice=c,
                reparto=dip_map.get(c, "N/D"),
                mese=target,
                tipo_avviso="pausa_inferiore_11_ore",
                conteggio=int(row["valore"]),
            ))

    # 2. Turni lunghi
    df_tl = ind_dfs.get("turni_lunghi")
    if df_tl is not None and not df_tl.empty:
        df_m = df_tl[df_tl["mese"] == target]
        for _, row in df_m[df_m["valore"] > 0].iterrows():
            c = row["codice"]
            avvisi.append(AvvisoOrario(
                codice=c,
                reparto=dip_map.get(c, "N/D"),
                mese=target,
                tipo_avviso="turno_12_ore_o_superiore",
                conteggio=int(row["valore"]),
            ))

    return avvisi
