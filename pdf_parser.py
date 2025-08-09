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
    sex: Optional[str]
    age: Optional[float]
    labs: Dict[str, float]
    flags: Dict[str, float]

STRICT = {
    "name": r"(?:Patient\s*Name|Name)\s*[:\-]\s*([A-Za-z][A-Za-z\s\.\-']{1,60}?)(?=\s+(?:barcode|id|patient\s*id|\d)|$)",
    "sex": r"(?:Sex|Gender)\s*[:\-]\s*(Male|Female|M|F)",
    "age": r"(?:Age)\s*[:\-]\s*(\d{1,3})",
    "ast_ul": r"(?:AST|SGOT)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}(?:U/?L|IU/?L))",
    "alt_ul": r"(?:ALT|SGPT)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}(?:U/?L|IU/?L))",
    "ggt_ul": r"(?:GGT|Gamma[\-\s]*glutamyl[\-\s]*transferase)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}(?:U/?L|IU/?L))",
    "tg_mgdl": r"(?:Triglycerides?|TG)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}mg/?dL)",
    "platelets": r"(?:Platelets?|Platelet\s*count)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,30}(?:10\^9/?L|10\^3/?µ?L))",
    "albumin_gdl": r"(?:Albumin)[^\n]{0,80}?(\d+(?:\.\d+)?)(?=[^\n]{0,20}g/?[dD][lL])",
    "uln_ast": r"(?:AST|SGOT)[^\n]{0,80}?(?:ref(?:erence)?\s*range|range)[^\n]{0,40}?(\d{2,3})\s*(?:U/?L|IU/?L)?",
}

LOOSE = {
    "name": r"(?:Patient\s*Name|Name)[^\n]{0,20}([A-Za-z][A-Za-z\s\.\-']{1,60}?)(?=\s+(?:barcode|id|patient\s*id|\d)|$)",
    "sex": r"(?:Sex|Gender)[^\n]{0,20}(Male|Female|M|F)",
    "age": r"(?:Age)[^\d]{0,20}(\d{1,3})",
}

def _find(pattern: str, text: str):
    m = re.search(pattern, text, flags=re.I)
    if m:
        value = m.group(1).strip()
        # Additional cleanup for name
        if pattern in (STRICT["name"], LOOSE["name"]):
            value = re.sub(r"\s+(barcode|id|patient\s*id)\b.*$", "", value, flags=re.I).strip()
        return value
    return None

def parse_pdf() -> Parsed:
    name = sex = None
    age = None
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
            t = re.sub(r"[^\S\r\n]+", " ", raw_text, flags=re.M)

            # Name / Sex / Age
            name = _find(STRICT["name"], t) or _find(LOOSE["name"], t)
            sex  = _find(STRICT["sex"], t) or _find(LOOSE["sex"], t)
            a    = _find(STRICT["age"], t) or _find(LOOSE["age"], t)
            try:
                age = float(a) if a else None
            except Exception:
                age = None

            # ULN AST range detection first
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

            # All other lab values (skip uln_ast if already set)
            for key in [k for k in STRICT.keys() if k not in ("name","sex","age")]:
                if key == "uln_ast" and "uln_ast" in labs:
                    continue
                m = re.search(STRICT[key], t, flags=re.I)
                if m:
                    try:
                        labs[key] = float(m.group(1))
                    except Exception:
                        pass

            # Albumin unit conversion if g/L
            if "albumin_gdl" in labs:
                m = re.search(r"Albumin[^\n]{0,40}?(\d+(?:\.\d+)?)\s*(g/?dL|g/?L)", t, flags=re.I)
                if m and "g/L" in m.group(2).replace(" ", "").lower():
                    labs["albumin_gdl"] = labs["albumin_gdl"] / 10.0

        # Show what we got
        if name or sex or age or labs:
            st.success("Parsed from PDF:")
            st.json({"name": name, "sex": sex, "age": age, **labs})
    return Parsed(name, sex, age, labs, flags)
