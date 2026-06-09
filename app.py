"""Streamlit UI for the copilot.  Run:  streamlit run app.py"""
import os

import streamlit as st

from ask.copilot import Copilot
from ask.demo_data import DEFAULT_DB
from ask.skills import SKILLS

st.set_page_config(page_title="Ask the Warehouse", page_icon="🔎")
st.title("🔎 Ask the Warehouse")
st.caption("Plain-English questions over a dealer-channel insurance warehouse (DuckDB). "
           "Every answer shows the SQL it ran.")

with st.sidebar:
    st.subheader("Try one of these")
    for skill in SKILLS:
        st.markdown(f"- {skill.description}")
    st.divider()
    st.caption("Open-ended questions use Claude when ANTHROPIC_API_KEY is set; "
               "otherwise the curated skills answer the examples above.")

question = st.text_input("Your question", "What is the overall lead-to-policy conversion rate?")

if st.button("Ask", type="primary") and question:
    if not os.path.exists(DEFAULT_DB):
        st.error("Warehouse not built yet. Run: python scripts/build_demo_db.py")
    else:
        answer = Copilot(DEFAULT_DB).ask(question)
        if answer.source == "error":
            st.warning(answer.message)
        else:
            st.caption(f"answered via **{answer.source}**")
            st.code(answer.sql.strip(), language="sql")
            st.dataframe(
                [dict(zip(answer.result.columns, row)) for row in answer.result.rows],
                use_container_width=True,
            )
