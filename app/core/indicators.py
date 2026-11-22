from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional
import pandas as pd
import numpy as np

@dataclass(frozen=True)
class Indicatore:
    id: str
    nome: str
    livello: str            # "persona" o "reparto"
    visibile_a: frozenset   # {"hr", "medico", "lavoratore"}
    fonte: str
    calcola: Callable[[Dict[str, pd.DataFrame]], pd.DataFrame]

REGISTRO: Dict[str, Indicatore] = {}

def indicatore(**meta):
    def registra(fn):
        REGISTRO[meta["id"]] = Indicatore(calcola=fn, **meta)
        return fn
    return registra

# ==========================================
# 1. Rientri rapidi (<11h tra turni)
# ==========================================
@indicatore(
    id="rientri_rapidi",
    nome="Rientri rapidi",
    livello="persona",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Vedaa e coll., rientri rapidi e malattia",
)
def calcola_rientri_rapidi(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    t = d.get("turni", pd.DataFrame())
    if t.empty or "inizio" not in t.columns or "fine" not in t.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df = t.copy()
    df["inizio"] = pd.to_datetime(df["inizio"])
    df["fine"] = pd.to_datetime(df["fine"])
    df = df.sort_values(["codice", "inizio"])

    # Calcola pausa tra la fine del turno corrente e l'inizio del successivo dello stesso codice
    df["prossimo_inizio"] = df.groupby("codice")["inizio"].shift(-1)
    df["pausa"] = df["prossimo_inizio"] - df["fine"]
    df["rapido"] = (df["pausa"] < pd.Timedelta(hours=11)) & (df["pausa"] >= pd.Timedelta(0))
    df["mese"] = df["inizio"].dt.strftime("%Y-%m")

    res = df.groupby(["codice", "mese"], as_index=False)["rapido"].sum()
    return res.rename(columns={"rapido": "valore"})

# ==========================================
# 2. Turni lunghi (>=12h)
# ==========================================
@indicatore(
    id="turni_lunghi",
    nome="Turni lunghi",
    livello="persona",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Dall'Ora e coll., BMJ Open 2015",
)
def calcola_turni_lunghi(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    t = d.get("turni", pd.DataFrame())
    if t.empty or "inizio" not in t.columns or "fine" not in t.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df = t.copy()
    df["inizio"] = pd.to_datetime(df["inizio"])
    df["fine"] = pd.to_datetime(df["fine"])
    durata_ore = (df["fine"] - df["inizio"]).dt.total_seconds() / 3600.0
    df["lungo"] = durata_ore >= 11.9  # tolleranza arrotondamento
    df["mese"] = df["inizio"].dt.strftime("%Y-%m")

    res = df.groupby(["codice", "mese"], as_index=False)["lungo"].sum()
    return res.rename(columns={"lungo": "valore"})

# ==========================================
# 3. Pazienti per infermiere
# ==========================================
@indicatore(
    id="pazienti_infermiere",
    nome="Pazienti per infermiere",
    livello="reparto",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Aiken e coll., JAMA 2002",
)
def calcola_pazienti_infermiere(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    turni = d.get("turni", pd.DataFrame())
    dip = d.get("dipendenti", pd.DataFrame())
    occ = d.get("occupazione", pd.DataFrame())

    if turni.empty or occ.empty:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    t = turni.copy()
    t["inizio"] = pd.to_datetime(t["inizio"])
    t["data"] = t["inizio"].dt.date
    t["mese"] = t["inizio"].dt.strftime("%Y-%m")

    # Filtra se possibile per infermieri, altrimenti considera gli operatori in turno
    if not dip.empty and "ruolo" in dip.columns:
        t = t.merge(dip[["codice", "ruolo"]], on="codice", how="left")
        inf_t = t[t["ruolo"].str.lower().str.contains("infermiere", na=False)]
        if inf_t.empty:
            inf_t = t
    else:
        inf_t = t

    inf_count = inf_t.groupby(["reparto", "data", "mese"], as_index=False)["codice"].nunique()
    inf_count.rename(columns={"codice": "infermieri_in_turno"}, inplace=True)

    o = occ.copy()
    o["data"] = pd.to_datetime(o["data"]).dt.date
    merged = pd.merge(inf_count, o, on=["reparto", "data"], how="inner")
    if merged.empty:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    merged["ratio"] = merged["pazienti_presenti"] / merged["infermieri_in_turno"].replace(0, np.nan)
    res = merged.groupby(["reparto", "mese"], as_index=False)["ratio"].mean()
    res["ratio"] = res["ratio"].round(2)
    return res.rename(columns={"ratio": "valore"})

# ==========================================
# 4. Straordinari
# ==========================================
@indicatore(
    id="straordinari",
    nome="Straordinari",
    livello="persona",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Lista di controllo INAIL (orario di lavoro)",
)
def calcola_straordinari(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    om = d.get("ore_mese", pd.DataFrame())
    if om.empty or "ore_straordinario" not in om.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])
    res = om[["codice", "mese", "ore_straordinario"]].copy()
    return res.rename(columns={"ore_straordinario": "valore"})

# ==========================================
# 5. Ferie non godute / residue
# ==========================================
@indicatore(
    id="ferie_residue",
    nome="Ferie non godute",
    livello="persona",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Evento sentinella INAIL",
)
def calcola_ferie_residue(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    om = d.get("ore_mese", pd.DataFrame())
    if om.empty or "ferie_residue_giorni" not in om.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])
    res = om[["codice", "mese", "ferie_residue_giorni"]].copy()
    return res.rename(columns={"ferie_residue_giorni": "valore"})

# ==========================================
# 6. Assenze brevi per malattia (1-3 giorni)
# ==========================================
@indicatore(
    id="malattia_brevi",
    nome="Assenze brevi per malattia",
    livello="persona",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Evento sentinella INAIL; studi su burnout e assenze",
)
def calcola_malattia_brevi(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    ass = d.get("assenze", pd.DataFrame())
    if ass.empty or "tipo" not in ass.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df = ass[ass["tipo"].astype(str).str.lower().str.contains("malattia", na=False)].copy()
    if df.empty:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df["data_inizio"] = pd.to_datetime(df["data_inizio"])
    df["data_fine"] = pd.to_datetime(df["data_fine"])
    df["durata"] = (df["data_fine"] - df["data_inizio"]).dt.days + 1
    # Episodi di 1-3 giorni
    df_brevi = df[(df["durata"] >= 1) & (df["durata"] <= 3)].copy()
    df_brevi["mese"] = df_brevi["data_inizio"].dt.strftime("%Y-%m")

    res = df_brevi.groupby(["codice", "mese"], as_index=False)["durata"].count()
    return res.rename(columns={"durata": "valore"})

# ==========================================
# 7. Infortuni
# ==========================================
@indicatore(
    id="infortuni",
    nome="Infortuni",
    livello="reparto",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Evento sentinella INAIL",
)
def calcola_infortuni(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    ass = d.get("assenze", pd.DataFrame())
    dip = d.get("dipendenti", pd.DataFrame())
    if ass.empty or dip.empty or "tipo" not in ass.columns:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = ass[ass["tipo"].astype(str).str.lower().str.contains("infortunio", na=False)].copy()
    if df.empty:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = df.merge(dip[["codice", "reparto"]], on="codice", how="left")
    df["data_inizio"] = pd.to_datetime(df["data_inizio"])
    df["mese"] = df["data_inizio"].dt.strftime("%Y-%m")

    res = df.groupby(["reparto", "mese"], as_index=False)["tipo"].count()
    return res.rename(columns={"tipo": "valore"})

# ==========================================
# 8. Aggressioni agli operatori
# ==========================================
@indicatore(
    id="aggressioni",
    nome="Aggressioni al personale",
    livello="reparto",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Studi su violenza e burnout",
)
def calcola_aggressioni(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    agg = d.get("aggressioni", pd.DataFrame())
    if agg.empty or "reparto" not in agg.columns or "data" not in agg.columns:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = agg.copy()
    df["data"] = pd.to_datetime(df["data"])
    df["mese"] = df["data"].dt.strftime("%Y-%m")

    res = df.groupby(["reparto", "mese"], as_index=False)["data"].count()
    return res.rename(columns={"data": "valore"})

# ==========================================
# 9. Dimissioni e turnover
# ==========================================
@indicatore(
    id="dimissioni",
    nome="Dimissioni",
    livello="reparto",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Evento sentinella INAIL (rotazione del personale)",
)
def calcola_dimissioni(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    dip = d.get("dipendenti", pd.DataFrame())
    if dip.empty or "tipo_cessazione" not in dip.columns or "data_cessazione" not in dip.columns:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = dip[
        (dip["data_cessazione"].notna())
        & (dip["tipo_cessazione"].astype(str).str.lower().str.contains("dimission", na=False))
    ].copy()
    if df.empty:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df["data_cessazione"] = pd.to_datetime(df["data_cessazione"])
    df["mese"] = df["data_cessazione"].dt.strftime("%Y-%m")

    res = df.groupby(["reparto", "mese"], as_index=False)["codice"].count()
    return res.rename(columns={"codice": "valore"})

# ==========================================
# 10. Richieste di trasferimento
# ==========================================
@indicatore(
    id="trasferimenti",
    nome="Richieste di trasferimento",
    livello="reparto",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Evento sentinella INAIL",
)
def calcola_trasferimenti(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    ev = d.get("eventi_hr", pd.DataFrame())
    dip = d.get("dipendenti", pd.DataFrame())
    if ev.empty or dip.empty or "tipo" not in ev.columns:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = ev[ev["tipo"].astype(str).str.lower().str.contains("trasferimento", na=False)].copy()
    if df.empty:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = df.merge(dip[["codice", "reparto"]], on="codice", how="left")
    df["data"] = pd.to_datetime(df["data"])
    df["mese"] = df["data"].dt.strftime("%Y-%m")

    res = df.groupby(["reparto", "mese"], as_index=False)["codice"].count()
    return res.rename(columns={"codice": "valore"})

# ==========================================
# 11. Procedimenti disciplinari
# ==========================================
@indicatore(
    id="disciplinari",
    nome="Procedimenti disciplinari",
    livello="reparto",
    visibile_a=frozenset({"hr", "medico"}),
    fonte="Evento sentinella INAIL",
)
def calcola_disciplinari(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    ev = d.get("eventi_hr", pd.DataFrame())
    dip = d.get("dipendenti", pd.DataFrame())
    if ev.empty or dip.empty or "tipo" not in ev.columns:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = ev[ev["tipo"].astype(str).str.lower().str.contains("disciplinare", na=False)].copy()
    if df.empty:
        return pd.DataFrame(columns=["reparto", "mese", "valore"])

    df = df.merge(dip[["codice", "reparto"]], on="codice", how="left")
    df["data"] = pd.to_datetime(df["data"])
    df["mese"] = df["data"].dt.strftime("%Y-%m")

    res = df.groupby(["reparto", "mese"], as_index=False)["codice"].count()
    return res.rename(columns={"codice": "valore"})

# ==========================================
# 12. Check-in domanda singola
# ==========================================
@indicatore(
    id="checkin",
    nome="Check-in domanda singola",
    livello="persona",
    visibile_a=frozenset({"lavoratore", "medico", "hr"}),
    fonte="Domanda singola validata (sensibilità 83%, specificità 87%)",
)
def calcola_checkin(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    chk = d.get("checkin", pd.DataFrame())
    if chk.empty or "domanda_singola" not in chk.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df = chk.copy()
    df["data"] = pd.to_datetime(df["data"])
    df["mese"] = df["data"].dt.strftime("%Y-%m")

    res = df.groupby(["codice", "mese"], as_index=False)["domanda_singola"].last()
    return res.rename(columns={"domanda_singola": "valore"})

# ==========================================
# 13. BAT-12 (Burnout Assessment Tool)
# ==========================================
@indicatore(
    id="bat12",
    nome="BAT-12",
    livello="persona",
    visibile_a=frozenset({"lavoratore", "medico"}),
    fonte="Burnout Assessment Tool (validazione italiana)",
)
def calcola_bat12(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    chk = d.get("checkin", pd.DataFrame())
    if chk.empty or "bat12_punteggio" not in chk.columns:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df = chk[chk["bat12_punteggio"].notna()].copy()
    if df.empty:
        return pd.DataFrame(columns=["codice", "mese", "valore"])

    df["data"] = pd.to_datetime(df["data"])
    df["mese"] = df["data"].dt.strftime("%Y-%m")

    res = df.groupby(["codice", "mese"], as_index=False)["bat12_punteggio"].mean()
    res["bat12_punteggio"] = res["bat12_punteggio"].round(2)
    return res.rename(columns={"bat12_punteggio": "valore"})
