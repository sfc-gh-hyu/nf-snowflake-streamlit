import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Streamlit Historic Runs Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page content
st.title("📊 Streamlit Historic Runs Visualizer")
st.markdown("---")

st.markdown("""
Welcome to the Streamlit Historic Runs Visualizer! 

This application helps you visualize and analyze your Streamlit application's historic runs.

### Available Pages:
- **🏠 Home**: Overview and dashboard
- **📈 History**: Detailed historic run analysis

Use the sidebar navigation to explore different pages.
""")

# Sidebar
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("Use the pages above to navigate through the app.")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app visualizes Streamlit historic runs and provides insights into your application's performance.") 