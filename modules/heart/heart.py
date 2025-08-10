from typing import List, Optional
import math
import streamlit as st
from core.types import PatientData, ResultItem
from core.utils import color_box

id = "heart"
title = "Heart: Lab-based Heart Health Index (0–100)"

# ---------- helpers ----------
def _num(label: str, key: str, default: Optional[float], lo: float, hi: float, step: float = 0.1):
    val = default if default is not None else lo
    return st.number_input(label, min_value=lo, max_value=hi, value=float(val), step=step, key=key)

def _get(d: dict, k: str) -> Optional[float]:
    v = d.get(k)
    try:
        return None if v is None else float(v)
    except Exception:
        return None

def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))

def _wavg(pairs: list[tuple[float, float]]) -> Optional[float]:
    # pairs: (score, weight)
    pairs = [(s, w) for s, w in pairs if s is not None and w > 0]
    if not pairs:
        return None
    sw = sum(w for _, w in pairs)
    return sum(s * w for s, w in pairs) / sw if sw > 0 else None

# ----- scoring functions (0–100; higher = better) -----
def score_apob(apob: Optional[float]) -> Optional[float]:
    if apob is None: return None
    # ≤80 optimal; 81–100 near-optimal; 101–130 elevated; >130 high
    if apob <= 80: return 100.0
    if apob <= 100: return 85.0
    if apob <= 130: return 60.0
    return 30.0

def score_nonhdl(nonhdl: Optional[float]) -> Optional[float]:
    if nonhdl is None: return None
    # ≤100 optimal; 101–129 near-optimal; 130–159 borderline; 160–189 high; ≥190 very high
    x = nonhdl
    if x <= 100: return 100.0
    if x <= 129: return 80.0
    if x <= 159: return 60.0
    if x <= 189: return 40.0
    return 20.0

def score_ldl(ldl: Optional[float]) -> Optional[float]:
    if ldl is None: return None
    if ldl < 100: return 100.0
    if ldl < 130: return 80.0
    if ldl < 160: return 60.0
    if ldl < 190: return 40.0
    return 20.0

def score_tg_hdl(tg: Optional[float], hdl: Optional[float]) -> Optional[float]:
    if tg is None or hdl is None or hdl <= 0: return None
    r = tg / hdl
    if r <= 2.0: return 100.0
    if r <= 3.5: return 70.0
    if r <= 5.0: return 40.0
    return 25.0

def score_lpa(lpa: Optional[float]) -> Optional[float]:
    if lpa is None: return None
    if lpa < 30: return 100.0
    if lpa <= 50: return 70.0
    return 40.0

def score_hscrp(h: Optional[float]) -> Optional[float]:
    if h is None: return None
    if h < 1: return 100.0
    if h <= 3: return 70.0
    return 40.0

def score_hba1c(a: Optional[float]) -> Optional[float]:
    if a is None: return None
    if a < 5.7: return 100.0
    if a < 6.5: return 70.0
    return 40.0

def score_fasting_glucose(g: Optional[float]) -> Optional[float]:
    if g is None: return None
    if g < 100: return 100.0
    if g < 126: return 70.0
    return 40.0

def score_sbp(sbp: Optional[float]) -> Optional[float]:
    if sbp is None: return None
    if sbp < 120: return 100.0
    if sbp < 140: return 70.0
    if sbp < 160: return 40.0
    return 20.0

def score_egfr(e: Optional[float]) -> Optional[float]:
    if e is None: return None
    if e >= 90: return 100.0
    if e >= 60: return 80.0
    if e >= 30: return 50.0
    return 20.0

def sev_good(border: bool) -> str:
    return "indeterminate" if border else "low"

# ---------- UI inputs ----------
def inputs(data: PatientData) -> PatientData:
    labs = data.labs
    flags = data.flags

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tc = _num("Total Cholesterol (mg/dL)", "heart_tc", _get(labs, "tc_mgdl"), 80.0, 400.0, 1.0)
        hdl = _num("HDL-C (mg/dL)", "heart_hdl", _get(labs, "hdl_mgdl"), 10.0, 120.0, 1.0)
        ldl = _num("LDL-C (mg/dL)", "heart_ldl", _get(labs, "ldl_mgdl"), 10.0, 400.0, 1.0)
    with c2:
        tg = _num("Triglycerides (mg/dL)", "heart_tg", _get(labs, "tg_mgdl"), 10.0, 2000.0, 1.0)
        apob = _num("ApoB (mg/dL)", "heart_apob", _get(labs, "apob_mgdl"), 20.0, 250.0, 1.0)
        lpa = _num("Lp(a) (mg/dL)", "heart_lpa", _get(labs, "lpa_mgdl"), 1.0, 200.0, 1.0)
    with c3:
        hscrp = _num("hs‑CRP (mg/L)", "heart_hscrp", _get(labs, "hscrp_mgL"), 0.1, 50.0, 0.1)
        a1c = _num("HbA1c (%)", "heart_hba1c", _get(labs, "hba1c_pct"), 4.0, 15.0, 0.1)
        fg = _num("Fasting Glucose (mg/dL)", "heart_fg", _get(labs, "fasting_glucose_mgdl"), 60.0, 400.0, 1.0)
    with c4:
        sbp = _num("Systolic BP (mmHg)", "heart_sbp", _get(labs, "sbp_mmhg"), 80.0, 220.0, 1.0)
        egfr = _num("eGFR (mL/min/1.73m²)", "heart_egfr", _get(labs, "egfr_ml_min"), 5.0, 140.0, 1.0)
        smoker_opt = st.selectbox("Current smoker", ["No", "Yes"], index=1 if str(flags.get("smoker", 0)) in ["1","Yes","True"] else 0, key="heart_smkr")
        diabetes_opt = st.selectbox("Known diabetes", ["No", "Yes"], index=1 if str(flags.get("diabetes", flags.get("diab_ifg", 0))) in ["1","Yes","True"] else 0, key="heart_dm")

    # write back to shared state
    labs.update({
        "tc_mgdl": tc, "hdl_mgdl": hdl, "ldl_mgdl": ldl, "tg_mgdl": tg,
        "apob_mgdl": apob, "lpa_mgdl": lpa, "hscrp_mgL": hscrp,
        "hba1c_pct": a1c, "fasting_glucose_mgdl": fg, "sbp_mmhg": sbp, "egfr_ml_min": egfr
    })
    flags.update({
        "smoker": 1 if smoker_opt == "Yes" else 0,
        "diabetes": 1 if diabetes_opt == "Yes" else 0
    })
    return data

# ---------- compute ----------
def compute(data: PatientData) -> List[ResultItem]:
    L = data.labs
    F = data.flags

    tc = _get(L, "tc_mgdl")
    hdl = _get(L, "hdl_mgdl")
    ldl = _get(L, "ldl_mgdl")
    tg  = _get(L, "tg_mgdl")
    apob = _get(L, "apob_mgdl")
    lpa = _get(L, "lpa_mgdl")
    hscrp = _get(L, "hscrp_mgL")
    a1c = _get(L, "hba1c_pct")
    fg = _get(L, "fasting_glucose_mgdl")
    sbp = _get(L, "sbp_mmhg")
    egfr = _get(L, "egfr_ml_min")

    # derived
    nonhdl = None
    if tc is not None and hdl is not None:
        nonhdl = tc - hdl if (tc - hdl) >= 0 else None
    tgr = tg / hdl if (tg is not None and hdl is not None and hdl > 0) else None

    # lipid subscore (prefer ApoB; fallback to non‑HDL; fallback to LDL)
    s_apob = score_apob(apob)
    s_nonhdl = score_nonhdl(nonhdl)
    s_ldl = score_ldl(ldl)
    primary_lipid = s_apob if s_apob is not None else (s_nonhdl if s_nonhdl is not None else s_ldl)

    s_tgr = score_tg_hdl(tg, hdl)
    s_lpa = score_lpa(lpa)

    lipid = _wavg([
        (primary_lipid, 0.5),
        (s_tgr, 0.2),
        (s_lpa, 0.3),
    ])

    inflam = score_hscrp(hscrp)
    gly_a1c = score_hba1c(a1c)
    gly_fg = score_fasting_glucose(fg)
    gly = None
    if gly_a1c is not None and gly_fg is not None:
        gly = (gly_a1c + gly_fg) / 2.0
    else:
        gly = gly_a1c if gly_a1c is not None else gly_fg

    bp = score_sbp(sbp)
    kidney = score_egfr(egfr)

    # combine to Heart Health (0–100)
    base = _wavg([
        (lipid, 0.45),
        (inflam, 0.15),
        (gly, 0.15),
        (bp, 0.15),
        (kidney, 0.10),
    ]) or 0.0

    penalty = 0.0
    if int(F.get("smoker", 0)) == 1:
        penalty += 15.0
    if int(F.get("diabetes", F.get("diab_ifg", 0))) == 1:
        penalty += 10.0

    heart100 = _clamp(base - penalty)

    # interpretations/severity
    results: List[ResultItem] = []

    # Lipid detail
    if apob is not None:
        sev = "low" if apob <= 80 else ("indeterminate" if apob <= 130 else "high")
        results.append(ResultItem("ApoB (mg/dL)", round(apob,1), "Optimal" if apob<=80 else ("Near‑optimal/Borderline" if apob<=130 else "High"), sev))
    elif nonhdl is not None:
        sev = "low" if nonhdl <= 100 else ("indeterminate" if nonhdl <= 159 else "high")
        results.append(ResultItem("Non‑HDL‑C (mg/dL)", round(nonhdl,1), "Optimal" if nonhdl<=100 else ("Borderline" if nonhdl<=159 else "High"), sev))
    elif ldl is not None:
        sev = "low" if ldl < 100 else ("indeterminate" if ldl < 160 else "high")
        results.append(ResultItem("LDL‑C (mg/dL)", round(ldl,1), "Optimal" if ldl<100 else ("Borderline" if ldl<160 else "High"), sev))

    if tgr is not None:
        sev = "low" if tgr <= 2.0 else ("indeterminate" if tgr <= 3.5 else "high")
        results.append(ResultItem("TG/HDL ratio", round(tgr,2), "Favourable" if tgr<=2 else ("Borderline" if tgr<=3.5 else "Unfavourable"), sev))

    if lpa is not None:
        sev = "low" if lpa < 30 else ("indeterminate" if lpa <= 50 else "high")
        results.append(ResultItem("Lp(a) (mg/dL)", round(lpa,1), "Low" if lpa<30 else ("Intermediate" if lpa<=50 else "High"), sev))

    if hscrp is not None:
        sev = "low" if hscrp < 1 else ("indeterminate" if hscrp <= 3 else "high")
        results.append(ResultItem("hs‑CRP (mg/L)", round(hscrp,2), "Low inflammation" if hscrp<1 else ("Average" if hscrp<=3 else "High"), sev))

    if a1c is not None:
        sev = "low" if a1c < 5.7 else ("indeterminate" if a1c < 6.5 else "high")
        results.append(ResultItem("HbA1c (%)", round(a1c,2), "Normal" if a1c<5.7 else ("Prediabetes range" if a1c<6.5 else "Diabetes range"), sev))
    if fg is not None:
        sev = "low" if fg < 100 else ("indeterminate" if fg < 126 else "high")
        results.append(ResultItem("Fasting glucose (mg/dL)", round(fg,1), "Normal" if fg<100 else ("Prediabetes range" if fg<126 else "Diabetes range"), sev))

    if sbp is not None:
        sev = "low" if sbp < 120 else ("indeterminate" if sbp < 140 else "high")
        results.append(ResultItem("SBP (mmHg)", round(sbp,0), "Normal" if sbp<120 else ("Elevated/Stage 1" if sbp<140 else "Stage 2+" ), sev))

    if egfr is not None:
        sev = "low" if egfr >= 90 else ("indeterminate" if egfr >= 60 else "high")
        results.append(ResultItem("eGFR (mL/min/1.73m²)", round(egfr,0), "Normal" if egfr>=90 else ("Mild CKD risk" if egfr>=60 else "CKD risk"), sev))

    # final index
    if heart100 is not None:
        if heart100 >= 85:
            interp = "Excellent cardiometabolic profile — maintain."
            sev = "low"
        elif heart100 >= 70:
            interp = "Good overall — consider fine‑tuning lipids/BP/inflammation."
            sev = "indeterminate"
        elif heart100 >= 50:
            interp = "Borderline — lifestyle + guideline‑based optimization advised."
            sev = "indeterminate"
        elif heart100 >= 30:
            interp = "High‑risk signals — clinical evaluation and therapy escalation."
            sev = "high"
        else:
            interp = "Very high‑risk signals — prompt specialist management."
            sev = "high"
        results.append(ResultItem("Heart Health (0–100)", round(heart100,1), interp, sev))

    # behaviour flags (informational line)
    info_bits = []
    if int(F.get("smoker", 0)) == 1: info_bits.append("smoking penalty applied")
    if int(F.get("diabetes", F.get("diab_ifg", 0))) == 1: info_bits.append("diabetes penalty applied")
    if info_bits:
        results.append(ResultItem(metric="", value=None, interpretation="Note: " + ", ".join(info_bits) + ".", severity="info"))

    return results

# ---------- render ----------
def render(results: List[ResultItem]) -> None:
    st.subheader("Results")
    for x in results:
        if x.metric:
            color_box(f"{x.metric}: {x.value} • {x.interpretation}", level=x.severity)
        else:
            color_box(x.interpretation, level=x.severity)

# ---------- pdf rows ----------
def to_pdf(results: List[ResultItem]) -> List[list[str]]:
    rows = []
    for x in results:
        if x.metric:
            rows.append([x.metric, "—" if x.value is None else str(x.value), x.interpretation])
    return rows
