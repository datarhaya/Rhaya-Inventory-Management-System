import streamlit as st
from st_pages import add_page_title, get_nav_from_toml, hide_pages
import pathlib
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(initial_sidebar_state="collapsed", layout="wide", page_icon="🎬", page_title="Knowledge Management Database")

with open( pathlib.Path("app/styles.css") ) as f:
    st.markdown(f'<style>{f.read()}</style>' , unsafe_allow_html= True)

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(
    worksheet="STREAMLIT DATA",
    ttl="10m",
)

st.session_state['data'] = df

nav = get_nav_from_toml(".streamlit/pages.toml")

# st.logo("logo.png")

pg = st.navigation(nav)

add_page_title(pg)

pg.run()