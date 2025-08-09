import io
import streamlit as st
from core.registry import load_enabled_modules
from core.types import PatientData
from core.pdf_parser import parse_pdf
from core.report import build_pdf

st.set_page_config(page_title="Health Analyzer (Modular)", layout="wide")
st.title("Health Analyzer — Modular")

# 1) Parse PDF once (optional)
parsed = parse_pdf()

# 2) Base patient data shared across modules
base = PatientData(
    name=parsed.name,
    sex=parsed.sex,
    age=parsed.age,
    labs=parsed.labs,
    flags=parsed.flags,
)

# 3) Load enabled modules
modules = load_enabled_modules()

all_rows = []
for mod in modules:
    with st.expander(mod.title, expanded=True):
        base = mod.inputs(base)
        results = mod.compute(base)
        mod.render(results)
        all_rows += mod.to_pdf(results)

# 4) Consolidated PDF
pdf_bytes = build_pdf(patient=base, rows=all_rows)
st.download_button("Download PDF Report", data=pdf_bytes, file_name="health_report.pdf", mime="application/pdf")

st.caption("Disclaimer: Screening & education only. Not medical advice.")
