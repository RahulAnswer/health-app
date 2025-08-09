import math
from typing import Optional
from core.types import PatientData, ResultItem

# --- helpers ---

def _safe_log(x: Optional[float]) -> Optional[float]:
    try:
        if x is None or float(x) <= 0:
            return None
        return math.log(float(x))
    except Exception:
        return None

# --- FLI ---

def fli_compute(tg, bmi, ggt, waist) -> Optional[float]:
    ln_tg = _safe_log(tg)
    ln_ggt = _safe_log(ggt)
    if None in (ln_tg, ln_ggt) or tg in (None, "") or bmi in (None, "") or waist in (None, ""):
        return None
    L = 0.953 * ln_tg + 0.139 * float(bmi) + 0.718 * ln_ggt + 0.053 * float(waist) - 15.745
    f = (math.exp(L) / (1 + math.exp(L))) * 100.0
    return max(0.0, min(100.0, f))

# --- FIB-4 / APRI / NFS ---

def fib4(age, ast, alt, platelets) -> Optional[float]:
    try:
        age, ast, alt, platelets = float(age), float(ast), float(alt), float(platelets)
        if alt <= 0 or platelets <= 0:
            return None
        return (age * ast) / (platelets * math.sqrt(alt))
    except Exception:
        return None


def apri(ast, uln_ast, platelets) -> Optional[float]:
    try:
        ast, uln_ast, platelets = float(ast), float(uln_ast), float(platelets)
        if uln_ast <= 0 or platelets <= 0:
            return None
        return (ast / uln_ast) * 100.0 / platelets
    except Exception:
        return None


def nfs(age, bmi, diab_ifg, ast, alt, platelets, albumin) -> Optional[float]:
    try:
        age, bmi, diab_ifg, ast, alt, platelets, albumin = float(age), float(bmi), int(diab_ifg), float(ast), float(alt), float(platelets), float(albumin)
        if alt <= 0:
            return None
        return -1.675 + 0.037 * age + 0.094 * bmi + 1.13 * diab_ifg + 0.99 * (ast / alt) - 0.013 * platelets - 0.66 * albumin
    except Exception:
        return None
