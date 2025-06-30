import streamlit as st

# Define pages using st.Page
home_page = st.Page(
    "app_pages/1_home.py", 
    title="Dashboard", 
    icon="🧬",
    default=True
)

history_page = st.Page(
    "app_pages/2_history.py", 
    title="Pipeline Runs", 
    icon="🔬"
)

# Navigation without sections
pg = st.navigation([home_page, history_page])

# Global page configuration
st.set_page_config(
    page_title="Nextflow Pipeline Analytics - Snowflake",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Run the selected page
pg.run() 