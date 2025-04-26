import streamlit as st
import os

st.set_page_config(page_title="Help", layout="centered")
st.title("📖 Help & Instructions")

st.markdown("""

""")

st.caption("When setting up the TV Paper Account, DO NOT ENABLE COMMISSIONS, see below.")

st.subheader("How to set up a paper account")
st.text("Open Paper Account settings")
st.image("images/de-paper-1.png", caption="Step 1: Open Paper Account settings")

st.text("Make sure commissions (Provision) are unchecked")
st.image("images/de-paper-2.png", caption="Step 2: Paper Account settings - no commissions!")

st.divider()

st.subheader("How to export your account data")

st.text("Select export from the menu")
st.image("images/de-export-1.png", caption="Step 1: Export your data from the TV Equity app")

st.text("Select Account History (Kontoverlauf)")
st.image("images/de-export-2.png", caption="Step 2: Select the data you want to export")