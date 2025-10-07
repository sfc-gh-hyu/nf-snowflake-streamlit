import streamlit as st
import pandas as pd
from datetime import datetime
import conf

@st.cache_data(ttl=60)  # Cache for 1 minute
def check_table_exists(table_name):
    """Check if a table exists in Snowflake"""
    try:
        conn = st.connection("snowflake")
        
        # First, try to get current database and schema context
        result_df = conn.query(f"select 1 from {table_name}")
        return True, f"[Check Passed] Table {table_name} exists."
        
    except Exception as e:
        error_msg = str(e)
        return False, f"Error checking table: {error_msg}"

@st.cache_data(ttl=60)  # Cache for 1 minute  
def check_stage_exists(stage_name):
    """Check if a stage exists in Snowflake"""
    try:
        conn = st.connection("snowflake")
        
        # First, try to get current database and schema context
        conn.query(f"select 1 from @{stage_name}")
        return True, f"[Check Passed] Stage {stage_name} exists."

    except Exception as e:
        error_msg = str(e)
        return False, f"Error checking stage: {error_msg}"

def check_again_button(caches_to_clear, label="🔄 Check Again", key=None):
    """
    Create a button that clears the specified cache(s) and re-runs the verification checks.
    
    Args:
        caches_to_clear (callable or list): Single cached function or list of cached functions to clear
        label (str): The button label text
        key (str): Optional unique key for the button
    
    Returns:
        bool: True if button was clicked, False otherwise
    """
    if st.button(label, key=key):
        # Handle single function or list of functions
        if callable(caches_to_clear):
            caches_to_clear.clear()
        else:
            # Clear cache for each function in the list
            for cache_func in caches_to_clear:
                cache_func.clear()
        # Update the last check timestamp
        st.session_state.last_check_time = datetime.now()
        # Rerun the app to refresh the checks
        st.rerun()
        return True
    return False

def history_table_verification():
    # Create header with refresh button
    st.markdown("### 📊 Execution History Table")
    st.caption(conf.NXF_HISTORY_TBL.description)

    # Check NXF_HISTORY_TBL
    with st.spinner("Verifying table existence..."):
        table_exists, table_message = check_table_exists(conf.NXF_HISTORY_TBL.value)

    if table_exists:
        st.success(f"✅ {table_message}")
    else:
        st.error(f"❌ {table_message}")
        
    if not table_exists:
        with st.expander("💡 Table Creation Suggestions", expanded=False):
            st.markdown(f"""
            The table `{conf.NXF_HISTORY_TBL.value}` was not found. This table is typically used to store Nextflow execution history.
            
            **Common reasons:**
            - Table hasn't been created yet
            - Table exists in a different database/schema
            - Insufficient permissions to access the table
            
            **Suggested Actions:**
            1. Check if you're connected to the correct database and schema
            2. Create the table if it doesn't exist
            3. Verify your permissions to access the table
            """)

def working_directory_stage_verification():
    # Create header with refresh button
    st.markdown("### 🗂️ Working Directory Stage")
    st.caption(conf.NXF_WORKDIR_STAGE.description)

    with st.spinner("Verifying stage existence..."):
        stage_exists, stage_message = check_stage_exists(conf.NXF_WORKDIR_STAGE.value)

    if stage_exists:
        st.success(f"✅ {stage_message}")
    else:
        st.error(f"❌ {stage_message}")

    if not stage_exists:
        # Provide suggestions for creating the stage
        with st.expander("💡 Stage Creation Suggestions", expanded=False):
            st.markdown(f"""
            The stage `{conf.NXF_WORKDIR_STAGE.value}` was not found. This stage is typically used to store Nextflow work directories and intermediate files.
            
            **Common reasons:**
            - Stage hasn't been created yet
            - Stage exists in a different database/schema
            - Insufficient permissions to access the stage
            
            **Suggested Actions:**
            1. Check if you're connected to the correct database and schema
            2. Create the stage if it doesn't exist (example below)
            3. Verify your permissions to access the stage
            
            **Example stage creation SQL:**
            ```sql
            CREATE STAGE {conf.NXF_WORKDIR_STAGE.value}
            ```
            """)

# Initialize session state for last check time
if 'last_check_time' not in st.session_state:
    st.session_state.last_check_time = datetime.now()

# Sidebar - Check Again Button
with st.sidebar:
    #st.markdown("### 🔄 Refresh")

    # Display last check timestamp
    if st.session_state.last_check_time:
        st.caption(f"Last checked: {st.session_state.last_check_time.strftime('%Y-%m-%d %H:%M:%S')}")

    check_again_button(
        caches_to_clear=[check_table_exists, check_stage_exists],
        label="refresh",
        key="check_all_configs"
    )
    
# Page header
st.title("⚙️ Configuration")
st.markdown("---")

st.markdown("""
This page helps you verify that your Nextflow pipeline settings are correctly configured in Snowflake.

It checks for the existence of required objects in your Snowflake environment.
""")

# Configuration summary
st.subheader("📋 Summary")

# Run verification checks for all configs
checks_passed = 0
checks_failed = 0

with st.spinner("Running configuration checks..."):
    # Check table
    table_exists, _ = check_table_exists(conf.NXF_HISTORY_TBL.value)
    if table_exists:
        checks_passed += 1
    else:
        checks_failed += 1
    
    # Check stage
    stage_exists, _ = check_stage_exists(conf.NXF_WORKDIR_STAGE.value)
    if stage_exists:
        checks_passed += 1
    else:
        checks_failed += 1

# Display summary metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Checks", checks_passed + checks_failed)
with col2:
    st.metric("✅ Passed", checks_passed)
with col3:
    st.metric("❌ Failed", checks_failed)

st.markdown("---")

# Settings verification section
st.subheader("🔍 Verification")

col1, col2 = st.columns(2)

with col1:
    history_table_verification()
with col2:
    working_directory_stage_verification()

# Debug section - show connection details
with st.expander("🔍 Debug Information", expanded=False):
    try:
        conn = st.connection("snowflake")
        debug_query = """
        SELECT 
            CURRENT_USER() as CURRENT_USER,
            CURRENT_DATABASE() as CURRENT_DATABASE,
            CURRENT_SCHEMA() as CURRENT_SCHEMA,
            CURRENT_WAREHOUSE() as CURRENT_WAREHOUSE,
            CURRENT_ROLE() as CURRENT_ROLE,
            CURRENT_REGION() as CURRENT_REGION
        """
        debug_df = conn.query(debug_query)
        st.markdown("**Current Snowflake Session:**")
        st.dataframe(debug_df, use_container_width=True, hide_index=True)
        
        # Show table names to check
        st.markdown("**Objects to Verify:**")
        st.code(f"Table: {conf.NXF_HISTORY_TBL.value}")
        st.code(f"Stage: {conf.NXF_WORKDIR_STAGE.value}")
        
    except Exception as debug_error:
        st.error(f"Debug connection failed: {str(debug_error)}")

# Help section
with st.expander("❓ Help & Troubleshooting", expanded=False):
    st.markdown("""
    ### Common Issues and Solutions
    
    **Connection Issues:**
    - Verify your Snowflake credentials in `.streamlit/secrets.toml`
    - Check network connectivity to Snowflake
    - Ensure your Snowflake account URL is correct
    
    **Permission Issues:**
    - Verify you have SELECT privileges on tables
    - Ensure you have USAGE privileges on stages
    - Check database and schema permissions
    
    **Object Not Found:**
    - Confirm you're connected to the correct database/schema
    - Verify object names match exactly (case sensitive)
    - Check if objects exist in different schemas
    
    **Configuration Issues:**
    - Review settings in `conf.py`
    - Ensure variable names match what Nextflow expects
    - Validate object naming conventions
    """)
