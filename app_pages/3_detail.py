import streamlit as st
import pandas as pd
from conf import NXF_WORKDIR_STAGE
import streamlit.components.v1 as components

# Page header
st.title("🔍 Nextflow Run Details")
st.markdown("---")

@st.cache_resource
def get_snowflake_session():
    """Get and cache the Snowflake session to avoid multiple session issues"""
    conn = st.connection("snowflake")
    return conn.session()

def download_file_from_stage(session, run_name, file_name):
    """
    Download a file from Snowflake stage for a specific run using Snowpark.
    
    Args:
        session: Snowpark session object
        run_name (str): The name of the Nextflow run
        file_name (str): The name of the file to download (e.g., 'report.html', 'trace.txt')
    
    Returns:
        tuple: (success: bool, content: str or error_message: str)
    """
    try:
        # Construct the file path in the stage
        # Format: @stage_name/path/to/file
        stage_file_path = f"@{NXF_WORKDIR_STAGE.value}/{run_name}/{file_name}"
        
        try:
            # Use SnowflakeFile to read file directly into memory
            from snowflake.snowpark.files import SnowflakeFile
            
            # Open and read the file from the stage
            with SnowflakeFile.open(stage_file_path, 'r', require_scoped_url=False) as f:
                file_content = f.read()
            
            return True, file_content
            
        except Exception as download_error:
            error_msg = str(download_error)
            return False, f"Error reading file from stage: {error_msg}"
            
    except Exception as e:
        error_msg = str(e)
        return False, f"Error accessing file: {error_msg}"

# Get run name from session state (when navigating from history) or query parameters
# Check session state first (from history page navigation)
if "selected_run_name" in st.session_state and st.session_state["selected_run_name"]:
    default_run_name = st.session_state["selected_run_name"]
    # Set query params to match
    st.query_params["run_name"] = default_run_name
    # Clear session state after reading
    st.session_state["selected_run_name"] = None
# Otherwise check query parameters (from direct URL or manual entry)
elif "run_name" in st.query_params:
    default_run_name = str(st.query_params["run_name"])
else:
    default_run_name = ""

# Sidebar - Run Name Input
with st.sidebar:
    st.header("🔍 Run Selection")
    st.markdown("Enter the name of the Nextflow run to view details")
    
    run_name_input = st.text_input(
        "Run Name",
        value=default_run_name,
        placeholder="e.g., r017n26s",
        help="Enter the exact run name (e.g., r017n26s)",
        key="run_name_input"
    )
    
    # Add a button to load the run and update URL
    load_button = st.button("📊 Load Run Details", type="primary", use_container_width=True)
    
    # Determine which run name to use
    if load_button and run_name_input:
        # Update query params when button is clicked manually
        st.query_params["run_name"] = run_name_input
        run_name = run_name_input
    else:
        # Use query param value if it exists (e.g., when navigating from history)
        # Otherwise fall back to the input value
        run_name = default_run_name if default_run_name else ""
    
    st.markdown("---")
    
    if run_name:
        st.info(f"📊 Viewing details for: **{run_name}**")
        # Show debug info in expander
        with st.expander("🔍 Debug Info", expanded=False):
            st.caption(f"Query param: `{default_run_name}`")
            st.caption(f"Input value: `{run_name_input}`")
            st.caption(f"Active run: `{run_name}`")
    else:
        st.warning("⚠️ Please enter a run name to view details")

# Main content
if not run_name:
    st.info("👈 Please enter a run name in the sidebar to view run details")
    
    with st.expander("💡 How to use this page", expanded=True):
        st.markdown("""
        ### Instructions
        
        1. **Enter Run Name**: Type or paste the Nextflow run name in the sidebar
        2. **View Details**: The page will load and display various statistics and reports for that run
        3. **Navigate Tabs**: Switch between different tabs to see different aspects of the run
        
        ### Example
        
        If your run name is `r017n26s`, enter it in the sidebar and the page will display:
        - Report HTML with execution statistics
        - Additional tabs (coming soon) with more detailed information
        
        ### File Location
        
        Files are loaded from the Snowflake stage at:
        ```
        @{NXF_WORKDIR_STAGE.value}/<run_name>/<file_name>
        ```
        """)
else:
    st.subheader(f"📊 Run Details: {run_name}")
    
    # Get cached Snowpark session to reuse for all tabs (avoids multiple session issues)
    try:
        session = get_snowflake_session()
    except Exception as e:
        st.error(f"❌ Failed to connect to Snowflake: {str(e)}")
        st.stop()
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📄 Report", "📈 Timeline", "🔍 Trace"])
    
    with tab1:
        st.markdown("### Nextflow Execution Report")
        
        with st.spinner(f"Loading report.html for run {run_name}..."):
            success, content = download_file_from_stage(session, run_name, "report.html")
        
        if success:
            st.success("✅ Report loaded successfully")
            
            # Display the HTML content in an iframe-like component
            # Use a container with scrolling
            st.markdown("---")
            
            # Display the HTML content
            # Note: streamlit.components.v1.html() allows rendering arbitrary HTML
            components.html(
                content,
                height=800,
                scrolling=True
            )
            
            # Add download button for the raw HTML
            st.download_button(
                label="⬇️ Download Report HTML",
                data=content,
                file_name=f"{run_name}_report.html",
                mime="text/html",
                help="Download the raw HTML report file"
            )
        else:
            st.error(f"❌ Failed to load report: {content}")
            
            with st.expander("🔍 Troubleshooting", expanded=True):
                st.markdown(f"""
                ### Possible Issues
                
                - **File doesn't exist**: Verify that `report.html` exists for run `{run_name}`
                - **Wrong path**: Check that the file is located at `@{NXF_WORKDIR_STAGE.value}/{run_name}/report.html`
                - **Permissions**: Ensure you have READ access to the stage
                - **Stage configuration**: Verify the stage `{NXF_WORKDIR_STAGE.value}` is correctly configured
                
                ### Expected Path
                ```
                @{NXF_WORKDIR_STAGE.value}/{run_name}/report.html
                ```
                
                ### Debug Information
                {content}
                """)
    
    with tab2:
        st.markdown("### Nextflow Execution Timeline")
        
        with st.spinner(f"Loading timeline.html for run {run_name}..."):
            success, content = download_file_from_stage(session, run_name, "timeline.html")
        
        if success:
            st.success("✅ Timeline loaded successfully")
            
            # Display the HTML content
            st.markdown("---")
            
            components.html(
                content,
                height=800,
                scrolling=True
            )
            
            # Add download button for the raw HTML
            st.download_button(
                label="⬇️ Download Timeline HTML",
                data=content,
                file_name=f"{run_name}_timeline.html",
                mime="text/html",
                help="Download the raw HTML timeline file"
            )
        else:
            st.error(f"❌ Failed to load timeline: {content}")
            
            with st.expander("🔍 Troubleshooting", expanded=True):
                st.markdown(f"""
                ### Possible Issues
                
                - **File doesn't exist**: Verify that `timeline.html` exists for run `{run_name}`
                - **Wrong path**: Check that the file is located at `@{NXF_WORKDIR_STAGE.value}/{run_name}/timeline.html`
                - **Permissions**: Ensure you have READ access to the stage
                - **Stage configuration**: Verify the stage `{NXF_WORKDIR_STAGE.value}` is correctly configured
                
                ### Expected Path
                ```
                @{NXF_WORKDIR_STAGE.value}/{run_name}/timeline.html
                ```
                
                ### Debug Information
                {content}
                """)
    
    with tab3:
        st.markdown("### Nextflow Execution Trace")
        
        with st.spinner(f"Loading trace.txt for run {run_name}..."):
            success, content = download_file_from_stage(session, run_name, "trace.txt")
        
        if success:
            st.success("✅ Trace loaded successfully")
            
            # Display the text content
            st.markdown("---")
            
            # Display trace file in a code block for better readability
            st.text_area(
                "Trace Content",
                content,
                height=600,
                help="Nextflow execution trace file showing task-level details"
            )
            
            # Add download button for the trace file
            st.download_button(
                label="⬇️ Download Trace File",
                data=content,
                file_name=f"{run_name}_trace.txt",
                mime="text/plain",
                help="Download the raw trace file"
            )
        else:
            st.error(f"❌ Failed to load trace: {content}")
            
            with st.expander("🔍 Troubleshooting", expanded=True):
                st.markdown(f"""
                ### Possible Issues
                
                - **File doesn't exist**: Verify that `trace.txt` exists for run `{run_name}`
                - **Wrong path**: Check that the file is located at `@{NXF_WORKDIR_STAGE.value}/{run_name}/trace.txt`
                - **Permissions**: Ensure you have READ access to the stage
                - **Stage configuration**: Verify the stage `{NXF_WORKDIR_STAGE.value}` is correctly configured
                
                ### Expected Path
                ```
                @{NXF_WORKDIR_STAGE.value}/{run_name}/trace.txt
                ```
                
                ### Debug Information
                {content}
                """)

