from typing import List
import streamlit as st
from core.types import PatientData, ResultItem
from core.utils import color_box
from .scores import fli_compute, fib4, apri, nfs

id = "liver"
title = "Liver: FLI, FIB-4, APRI, NFS"


def _num(label: str, key: str, default: float, minv: float, maxv: float, step: float):
    return st.number_input(label, min_value=minv, max_value=maxv, value=default, step=step, key=key)


def inputs(data: PatientData) -> PatientData:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        name = st.text_input("Patient Name", value=data.name or "")
        sex = st.selectbox("Sex", ["M", "F"], index=(0 if (data.sex or "M") == "M" else 1))
        age = _num("Age (years)", "age", float(data.age or 40), 0.0, 120.0, 1.0)
        bmi = _num("BMI (kg/m²)", "bmi", float(data.labs.get("bmi", 27.0)), 10.0, 80.0, 0.1)
    with c2:
        waist = _num("Waist (cm)", "waist", float(data.labs.get("waist", 95.0)), 40.0, 200.0, 0.5)
        tg = _num("Triglycerides (mg/dL)", "tg", float(data.labs.get("tg_mgdl", 160.0)), 10.0, 2000.0, 1.0)
        ggt = _num("GGT (U/L)", "ggt", float(data.labs.get("ggt_ul", 45.0)), 1.0, 2000.0, 1.0)
    with c3:
        ast = _num("AST (U/L)", "ast", float(data.labs.get("ast_ul", 35.0)), 1.0, 5000.0, 0.5)
        alt = _num("ALT (U/L)", "alt", float(data.labs.get("alt_ul", 30.0)), 1.0, 5000.0, 0.5)
        uln_ast = _num("ULN AST (U/L)", "uln_ast", float(data.labs.get("uln_ast", 40.0)), 10.0, 100.0, 1.0)
    with c4:
        platelets = _num("Platelets (10⁹/L)", "platelets", float(data.labs.get("platelets", 230.0)), 20.0, 1000.0, 1.0)
        albumin = _num("Albumin (g/dL)", "albumin", float(data.labs.get("albumin_gdl", 4.2)), 1.0, 6.0, 0.1)
        diab = st.selectbox("Diabetes / IFG", ["No", "Yes"], index=1 if str(data.flags.get("diab_ifg", 0)) in ["1","Yes"] else 0)

    data.name = name or data.name
    data.sex = sex
    data.age = age
    data.labs.update({
        "bmi": bmi, "waist": waist, "tg_mgdl": tg, "ggt_ul": ggt, "ast_ul": ast, "alt_ul": alt, "uln_ast": uln_ast,
        "platelets": platelets, "albumin_gdl": albumin,
    })
    data.flags.update({"diab_ifg": 1 if diab == "Yes" else 0})
    return data


def _interp(level: str, text: str) -> ResultItem:
    return ResultItem(metric="", value=None, interpretation=text, severity=level)


def compute(data: PatientData) -> List[ResultItem]:
    r: List[ResultItem] = []
    fli = fli_compute(data.labs.get("tg_mgdl"), data.labs.get("bmi"), data.labs.get("ggt_ul"), data.labs.get("waist"))
    if fli is not None:
        if fli < 30:
            r.append(ResultItem("FLI", round(fli,1), "Low (fatty liver unlikely) — maintain lifestyle; monitor.", "low"))
        elif fli < 60:
            r.append(ResultItem("FLI", round(fli,1), "Intermediate — consider ultrasound or repeat after optimisation.", "indeterminate"))
        else:
            r.append(ResultItem("FLI", round(fli,1), "High — proceed to fibrosis staging (NFS, FIB-4, APRI).", "high"))

    fib4_v = fib4(data.age, data.labs.get("ast_ul"), data.labs.get("alt_ul"), data.labs.get("platelets"))
    if fib4_v is not None:
        if fib4_v <= 1.3:
            r.append(ResultItem("FIB-4", round(fib4_v,3), "Low: rules out advanced fibrosis.", "low"))
        elif fib4_v < 2.67:
            r.append(ResultItem("FIB-4", round(fib4_v,3), "Indeterminate: consider elastography (FibroScan).", "indeterminate"))
        else:
            r.append(ResultItem("FIB-4", round(fib4_v,3), "High: advanced fibrosis likely; hepatology referral.", "high"))

    apri_v = apri(data.labs.get("ast_ul"), data.labs.get("uln_ast"), data.labs.get("platelets"))
    if apri_v is not None:
        if apri_v < 0.5:
            r.append(ResultItem("APRI", round(apri_v,3), "Low: significant fibrosis unlikely.", "low"))
        elif apri_v < 1.0:
            r.append(ResultItem("APRI", round(apri_v,3), "Indeterminate: consider elastography / repeat testing.", "indeterminate"))
        else:
            r.append(ResultItem("APRI", round(apri_v,3), "High: advanced fibrosis likely; specialist referral.", "high"))

    nfs_v = nfs(data.age, data.labs.get("bmi"), data.flags.get("diab_ifg", 0), data.labs.get("ast_ul"), data.labs.get("alt_ul"), data.labs.get("platelets"), data.labs.get("albumin_gdl"))
    if nfs_v is not None:
        if nfs_v < -1.455:
            r.append(ResultItem("NFS", round(nfs_v,3), "Low: advanced fibrosis unlikely.", "low"))
        elif nfs_v <= 0.675:
            r.append(ResultItem("NFS", round(nfs_v,3), "Indeterminate: consider elastography / specialist assessment.", "indeterminate"))
        else:
            r.append(ResultItem("NFS", round(nfs_v,3), "High: advanced fibrosis likely; specialist referral.", "high"))

    # Composite liver health (0-100) using subscores
    def sub_fib4(x):
        if x is None: return None
        if x <= 1.3: return 100.0
        if x < 2.67: return max(40.0, 100.0 - (x - 1.3) * (60.0 / (2.67 - 1.3)))
        return 20.0

    def sub_apri(x):
        if x is None: return None
        if x <= 0.5: return 100.0
        if x <= 1.5: return max(60.0, 100.0 - (x - 0.5) * 40.0)
        if x <= 2.0: return max(20.0, 60.0 - (x - 1.5) * (40.0 / 0.5))
        return 20.0

    def sub_nfs(x):
        if x is None: return None
        if x <= -1.455: return 100.0
        if x < 0.676: return 50.0
        return 20.0

    fib4_s = sub_fib4(fib4_v)
    apri_s = sub_apri(apri_v)
    nfs_s = sub_nfs(nfs_v)

    if fib4_s is not None or apri_s is not None or nfs_s is not None:
        if nfs_s is None:
            liver100 = max(0.0, min(100.0, 0.7 * (fib4_s or 0.0) + 0.3 * (apri_s or 0.0)))
        else:
            liver100 = max(0.0, min(100.0, 0.5 * (fib4_s or 0.0) + 0.25 * (apri_s or 0.0) + 0.25 * (nfs_s or 0.0)))
        if liver100 >= 85:
            r.append(ResultItem("Liver Health (0–100)", round(liver100,1), "Low probability of advanced fibrosis — routine monitoring.", "low"))
        elif liver100 >= 60:
            r.append(ResultItem("Liver Health (0–100)", round(liver100,1), "Indeterminate — consider elastography (FibroScan).", "indeterminate"))
        else:
            r.append(ResultItem("Liver Health (0–100)", round(liver100,1), "High probability — hepatology referral, imaging/workup.", "high"))
    return r


def render(results: List[ResultItem]) -> None:
    st.subheader("Results")
    for x in results:
        if x.metric:
            color_box(f"{x.metric}: {x.value} • {x.interpretation}", level=x.severity)
        else:
            color_box(x.interpretation, level=x.severity)


def to_pdf(results: List[ResultItem]) -> List[list[str]]:
    rows = []
    for x in results:
        if x.metric:
            rows.append([x.metric, "—" if x.value is None else str(x.value), x.interpretation])
    return rows
