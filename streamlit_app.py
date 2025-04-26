import streamlit as st

pg = st.navigation([
    st.Page("pages/challenge.py", title="Equity Analyzer", icon="📈"),
    st.Page("pages/help.py", title="Help", icon="ℹ️"),
    ])
pg.run()