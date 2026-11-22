from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from app.core.config import soglie_config, settings
from app.core.indicators import REGISTRO

def get_semaforo(indicatore_id: str, valore: float) -> Tuple[int, str]:
    """
    Determina i punti (0, 1, 2) e il colore del semaforo ('verde', 'giallo', 'rosso')
    in base alle soglie definite in soglie.yaml.
    """
    indicatori_soglie = soglie_config.get("indicatori", {})
    soglia = indicatori_soglie.get(indicatore_id, {})
    giallo = soglia.get("giallo", 1.0)
    rosso = soglia.get("rosso", 2.0)

    if pd.isna(valore) or valore is None:
        return 0, "verde"

    if valore >= rosso:
        return 2, "rosso"
    elif valore >= giallo:
        return 1, "giallo"
    else:
        return 0, "verde"

def calcola_punteggio_sintetico(indicatori_valori: Dict[str, float]) -> Dict[str, Any]:
    """
    Calcola il punteggio 0-100:
    punteggio = (sum(punti) / (2 * n_indicatori)) * 100
    Restituisce punteggio, fascia, semafori per indicatore e top 3 fattori esplicativi.
    """
    if not indicatori_valori:
        return {
            "punteggio": 0.0,
            "fascia": "basso",
            "semafori": {},
            "top_3_fattori": [],
            "n_indicatori": 0,
        }

    somma_punti = 0
    dettagli = []
    semafori_map = {}

    for ind_id, val in indicatori_valori.items():
        punti, colore = get_semaforo(ind_id, val)
        somma_punti += punti
        semafori_map[ind_id] = {
            "valore": round(float(val), 2) if val is not None else 0.0,
            "punti": punti,
            "colore": colore,
        }
        meta = REGISTRO.get(ind_id)
        nome = meta.nome if meta else ind_id
        dettagli.append({
            "id": ind_id,
            "nome": nome,
            "valore": round(float(val), 2) if val is not None else 0.0,
            "punti": punti,
            "colore": colore,
        })

    n = len(indicatori_valori)
    if n > 0:
        punteggio = round((somma_punti / (2.0 * n)) * 100.0, 1)
    else:
        punteggio = 0.0

    fasce = soglie_config.get("fasce", {"basso": 34, "alto": 66})
    if punteggio >= fasce.get("alto", 66):
        fascia = "alto"
    elif punteggio >= fasce.get("basso", 34):
        fascia = "medio"
    else:
        fascia = "basso"

    # I 3 fattori che pesano di più (ordinati per punti decrescenti, poi valore)
    dettagli_ordinati = sorted(dettagli, key=lambda x: (x["punti"], x["valore"]), reverse=True)
    top_3 = dettagli_ordinati[:3]

    # Aggiungi azioni suggerite ai top 3 fattori
    azioni_map = soglie_config.get("azioni_suggerite", {})
    for fattore in top_3:
        fattore["azione_suggerita"] = azioni_map.get(
            fattore["id"],
            "Monitorare l'indicatore e pianificare azioni correttive mirate."
        )

    return {
        "punteggio": punteggio,
        "fascia": fascia,
        "semafori": semafori_map,
        "top_3_fattori": top_3,
        "n_indicatori": n,
    }

def verifica_da_contattare(checkin_val: Optional[float], bat12_val: Optional[float]) -> bool:
    """
    Bandiera 'da contattare' (vista medico):
    Si accende se la domanda singola vale 3 o più, oppure se il BAT-12 supera la soglia (>= 2.5).
    """
    if checkin_val is not None and checkin_val >= 3.0:
        return True
    if bat12_val is not None and bat12_val >= 2.5:
        return True
    return False
