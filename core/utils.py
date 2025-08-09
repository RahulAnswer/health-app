import math
import streamlit as st
from typing import Optional

PALETTE = {
    "low": "#2e7d32",
    "indeterminate": "#f9a825",
    "high": "#c62828",
    "info": "#455a64",
}

def color_box(text: str, level: str = "info"):
    col = PALETTE.get(level, "#455a64")
    st.markdown(
        f"""
        <div style=\"background:{col};padding:12px;border-radius:8px;color:white;font-weight:600;\">{text}</div>
        """,
        unsafe_allow_html=True,
    )