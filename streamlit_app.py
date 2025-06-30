import streamlit as st

# Define pages using st.Page
home_page = st.Page(
    "pages/home.py", 
    title="Home", 
    icon="🏠",
    default=True
)

history_page = st.Page(
    "pages/history.py", 
    title="History", 
    icon="📈"
)

# Navigation with sections
pg = st.navigation({
    "Dashboard": [home_page],
    "Analytics": [history_page]
})

# Global page configuration
st.set_page_config(
    page_title="Streamlit Historic Runs Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Run the selected page
pg.run() 