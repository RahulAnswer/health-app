import re
from dataclasses import dataclass
from typing import Dict, Optional
import streamlit as st

try:
    import pdfplumber
    PDF_ENABLED = True
except Exception:
    PDF_ENABLED = False


@dataclass
class Parsed:
    name: Optional[str]
    sex: Optional[str]          # normalized to "M" or "F"
    age: Optional[float]
    labs: Dict[str, float]
    flags: Dict[str, float]


# --------- patterns ---------
# Keep existing liver-related patterns and add heart-related ones.
STRICT = {
    # demographics
    "name": r"(?:Patient\s*Name|Name)\s*[:\-]\s*([A-Za-z][A-Za-z\s\.\-']{1,60}?)(?=\s+(?:barcode|id|patient\s*id|\d)|$)",
    "sex": r"(?:Sex|Gender)\s*[:\-]\s*(Male|Female|M|F)",
    "age": r"(?:Age)\s*[:\-]\s*(\d{1,3})",

    # core liver
    "ast_ul": r"(?:AST|SGOT)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}(?:U/?L|IU/?L))",
    "alt_ul": r"(?:ALT|SGPT)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}(?:U/?L|IU/?L))",
    "ggt_ul": r"(?:GGT|Gamma[\-\s]*glutamyl[\-\s]*transferase)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}(?:U/?L|IU/?L))",
    "tg_mgdl": r"(?:Triglycerides?|TG)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}mg/?dL)",
    "platelets": r"(?:Platelets?|Platelet\s*count)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,30}(?:10\^9/?L|10\^3/?µ?L))",
    "albumin_gdl": r"(?:Albumin)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}g/?[dD][lL])",

    # ULN AST (try to read the high end of a reference range line)
    "uln_ast": r"(?:AST|SGOT)[^\n]{0,80}?(?:ref(?:erence)?\s*range|range)[^\n]{0,40}?(\d{2,3})\s*(?:U/?L|IU/?L)?",

    # lipids for heart
    "tc_mgdl": r"(?:Total\s+Cholesterol|Total\s*Cholesterol|CHOL)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?dL)",
    "hdl_mgdl": r"(?:HDL[\-\s]*C|Serum\s+HDL\s+Cholesterol|HDL\s*Cholesterol)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?dL)",
    "ldl_mgdl": r"(?:LDL[\-\s]*C|Serum\s+LDL\s+Cholesterol|LDL\s*Cholesterol)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?dL)",

    # inflammation
    "hscrp_mgL": r"(?:hs[\-\s]*CRP|high[\-\s]*sensitivity\s*C[\.\s]*R[\.\s]*P)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?L)",

    # anchored fasting glucose – avoid grabbing ref ranges (70–100)
    "fasting_glucose_mgdl": r"(?:Glucose[, ]*Fasting|Fasting\s*Blood\s*Sugar|Fasting\s*Glucose)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?dL)",

    # HbA1c as % on same line
    "hba1c_pct": r"(?:HbA1c|Hba1c)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,6}%)",

    # ApoB / ApoA1
    "apob_mgdl": r"(?:APO[\-\s]*B|Apolipoprotein\s*B)\b[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?dL)",
    "apoa1_mgdl": r"(?:APO[\-\s]*A1|Apolipoprotein\s*A-?1)\b[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,12}mg/?dL)",

    # eGFR / GFR, ESTIMATED
    "egfr_ml_min": r"(?:eGFR|GFR[, ]*ESTIMATED|Estimated\s*GFR)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,30}mL/?min/?1\.?73m2)",
}

# looser fallbacks for name/sex/age only
LOOSE = {
    "name": r"(?:Patient\s*Name|Name)[^\n]{0,20}([A-Za-z][A-Za-z\s\.\-']{1,60}?)(?=\s+(?:barcode|id|patient\s*id|\d)|$)",
    "sex": r"(?:Sex|Gender)[^\n]{0,20}(Male|Female|M|F)",
    "age": r"(?:Age)[^\d]{0,20}(\d{1,3})",
}


def _find(pattern: str, text: str):
    m = re.search(pattern, text, flags=re.I)
    if not m:
        return None
    value = m.group(1).strip()
    # name cleanup
    if pattern in (STRICT["name"], LOOSE["name"]):
        value = re.sub(r"\s+(barcode|id|patient\s*id)\b.*$", "", value, flags=re.I).strip()
    return value


def parse_pdf() -> Parsed:
    name = sex = None
    age: Optional[float] = None
    labs: Dict[str, float] = {}
    flags: Dict[str, float] = {}

    with st.expander("Upload Lab PDF (optional)"):
        if not PDF_ENABLED:
            st.info("PDF parsing not available on this env.")
            return Parsed(name, sex, age, labs, flags)

        up = st.file_uploader("Upload lab PDF (text-based)", type=["pdf"])
        raw_text = ""
        if up is not None:
            try:
                with pdfplumber.open(up) as pdf:
                    texts = [page.extract_text() or "" for page in pdf.pages]
                    raw_text = "\n".join(texts)
            except Exception:
                raw_text = ""

        if raw_text:
            # collapse whitespace but keep line structure
            t = re.sub(r"[^\S\r\n]+", " ", raw_text, flags=re.M)

            # --- demographics ---
            name = _find(STRICT["name"], t) or _find(LOOSE["name"], t)

            sex_raw = _find(STRICT["sex"], t) or _find(LOOSE["sex"], t)
            if sex_raw:
                s0 = sex_raw.strip().lower()
                if s0.startswith("m"):
                    sex = "M"
                elif s0.startswith("f"):
                    sex = "F"

            a = _find(STRICT["age"], t) or _find(LOOSE["age"], t)
            try:
                age = float(a) if a else None
            except Exception:
                age = None

            # --- special handling for ULN AST reference ranges (like "40 - 60 U/L") ---
            ULN_RANGE_PATTERNS = [
                r"(?:AST|SGOT)[^\n]*?U/?L[^\n]*?(\d{1,3})\s*[-–‐]\s*(\d{2,3})",
                r"(?:AST|SGOT)[^\n]*?(?:ref(?:erence)?\s*(?:range|interval)|bio\.?\s*ref.*?|range)[^\n]*?(\d{1,3})\s*[-–‐]\s*(\d{2,3})"
            ]
            for pat in ULN_RANGE_PATTERNS:
                m = re.search(pat, t, flags=re.I)
                if m:
                    lo_v, hi_v = int(m.group(1)), int(m.group(2))
                    labs["uln_ast"] = float(max(lo_v, hi_v))
                    break

            # --- extract individual analytes ---
            for key, pat in STRICT.items():
                if key in ("name", "sex", "age", "uln_ast"):
                    # already handled above (and ULN done separately to prefer range logic)
                    continue
                if key == "uln_ast" and "uln_ast" in labs:
                    continue
                m = re.search(pat, t, flags=re.I)
                if m:
                    try:
                        labs[key] = float(m.group(1))
                    except Exception:
                        pass

            # albumin may be in g/L on some reports — convert to g/dL if so
            if "albumin_gdl" in labs:
                m = re.search(r"Albumin[^\n]{0,40}?(\d+(?:\.\d+)?)\s*(g/?dL|g/?L)", t, flags=re.I)
                if m:
                    unit = m.group(2).replace(" ", "").lower()
                    if "g/l" in unit:
                        labs["albumin_gdl"] = labs["albumin_gdl"] / 10.0

        # Show what we got
        if name or sex or age or labs:
            st.success("Parsed from PDF:")
            st.json({"name": name, "sex": sex, "age": age, **labs})

    return Parsed(name, sex, age, labs, flags)
