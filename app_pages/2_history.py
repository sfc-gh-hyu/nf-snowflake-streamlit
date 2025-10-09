import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from conf import NXF_HISTORY_TBL

# Page header
st.title("🔬 Nextflow Pipeline Run Analysis")
st.markdown("---")

# Initialize session state for applied filters
if 'applied_filters' not in st.session_state:
    st.session_state.applied_filters = {
        'start_date': None,
        'end_date': None,
        'statuses': None,
        'limit': 50
    }

def format_execution_time(minutes):
    """Format execution time in human-readable format like 1hr2min30sec"""
    if pd.isna(minutes) or minutes == 0:
        return "0sec"
    
    total_seconds = int(minutes * 60)
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    mins = remaining_seconds // 60
    secs = remaining_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}hr")
    if mins > 0:
        parts.append(f"{mins}min")
    if secs > 0 or len(parts) == 0:
        parts.append(f"{secs}sec")
    
    return "".join(parts)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_pipeline_data(start_date=None, end_date=None, statuses=None, limit=50):
    """Load Nextflow pipeline data from Snowflake with SQL-level filtering"""
    try:
        # Create Snowflake connection
        conn = st.connection("snowflake")
        
        # Build WHERE clause conditions
        where_conditions = []
        
        if start_date:
            where_conditions.append(f"run_end_time >= '{start_date}'")
        if end_date:
            # Add one day to end_date to make it inclusive
            end_date_inclusive = pd.to_datetime(end_date) + timedelta(days=1)
            where_conditions.append(f"run_end_time < '{end_date_inclusive}'")
        if statuses and len(statuses) > 0:
            status_list = "', '".join(statuses)
            where_conditions.append(f"run_status IN ('{status_list}')")
        
        # Construct WHERE clause
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Query to get Nextflow pipeline runs from execution history table
        query = f"""
        SELECT 
            run_id AS QUERY_ID,
            run_name AS QUERY_TEXT,
            run_start_time AS START_TIME,
            run_end_time AS END_TIME,
            run_session_id AS SESSION_ID,
            run_status AS EXECUTION_STATUS,
            submitted_by AS USER_NAME
        FROM {NXF_HISTORY_TBL.value}
        WHERE {where_clause}
        ORDER BY run_start_time DESC
        LIMIT {limit}
        """
        
        # Execute query
        df = conn.query(query)
        
        # Add derived columns if data exists
        if not df.empty:
            # Ensure datetime columns are properly typed
            df['START_TIME'] = pd.to_datetime(df['START_TIME'])
            df['END_TIME'] = pd.to_datetime(df['END_TIME'])
            
            # Calculate execution time in minutes
            df['EXECUTION_TIME_MINUTES'] = (df['END_TIME'] - df['START_TIME']).dt.total_seconds() / 60
            df['DATE'] = df['END_TIME'].dt.date
        
        return df
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"Error querying execution history table: {error_msg}")
        st.info("💡 Please ensure the execution history table exists and you have the necessary permissions.")
        return pd.DataFrame()

# Sidebar - Filters Section
with st.sidebar:
    st.header("🔍 Query Filters")
    st.markdown("Configure filters and click 'Apply' to run the query")
    
    # Date range filter
    st.subheader("📅 Date Range")
    
    # Calculate default date range (last 7 days)
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=7)
    
    use_date_filter = st.checkbox("Filter by date range", value=False, key="use_date_filter")
    
    if use_date_filter:
        start_date = st.date_input(
            "Start Date",
            value=default_start_date,
            key="filter_start_date"
        )
        end_date = st.date_input(
            "End Date",
            value=default_end_date,
            min_value=start_date,
            key="filter_end_date"
        )
    else:
        start_date = None
        end_date = None
    
    # Status filter
    st.subheader("🔄 Pipeline Status")
    status_filter = st.multiselect(
        "Select Status (leave empty for all)",
        options=['SUCCESS', 'ERROR', 'RUNNING', 'ABORTED'],
        default=None,
        key="status_filter",
        help="Select one or more statuses to filter. Leave empty to show all statuses."
    )
    
    # Convert empty list to None for SQL query
    if not status_filter:
        status_filter = None
    
    # Result limit
    st.subheader("📊 Result Limit")
    limit = st.number_input(
        "Max number of runs to retrieve",
        min_value=1,
        max_value=1000,
        value=50,
        step=10,
        help="Limit the number of results returned from the database",
        key="result_limit"
    )
    
    # Apply button - updates session state with current filter values
    if st.button("🔄 Apply", use_container_width=True, type="primary"):
        st.session_state.applied_filters = {
            'start_date': start_date,
            'end_date': end_date,
            'statuses': status_filter,
            'limit': limit
        }
        st.cache_data.clear()
        st.rerun()
    
    # Show currently applied filters
    st.caption("**Currently Applied:**")
    if st.session_state.applied_filters['start_date'] or st.session_state.applied_filters['end_date']:
        st.caption(f"📅 Date: {st.session_state.applied_filters['start_date'] or 'All'} to {st.session_state.applied_filters['end_date'] or 'All'}")
    else:
        st.caption("📅 Date: All")
    if st.session_state.applied_filters['statuses']:
        st.caption(f"🔄 Status: {', '.join(st.session_state.applied_filters['statuses'])}")
    else:
        st.caption("🔄 Status: All")
    st.caption(f"📊 Limit: {st.session_state.applied_filters['limit']} runs")

# Load data with APPLIED filters from session state
with st.spinner("Loading Nextflow pipeline data from Snowflake..."):
    filtered_df = load_pipeline_data(
        start_date=st.session_state.applied_filters['start_date'],
        end_date=st.session_state.applied_filters['end_date'],
        statuses=st.session_state.applied_filters['statuses'],
        limit=st.session_state.applied_filters['limit']
    )

# Display data load status
if filtered_df.empty:
    st.warning("⚠️ No pipeline data found. Please check your Snowflake connection and permissions.")
    with st.expander("💡 Tips", expanded=True):
        st.markdown(f"""
        - Make sure you have access to the **{NXF_HISTORY_TBL.value}** table
        - Verify your Nextflow pipelines are running and logging execution history
        - Try adjusting the filters in the sidebar
        - Check that the execution history table contains recent data
        """)
else:
    st.success(f"✅ Loaded {len(filtered_df)} Nextflow pipeline runs from Snowflake")

# Main content
st.subheader("🧬 Nextflow Pipeline Overview")

# Calculate metrics from filtered data
if not filtered_df.empty:
    total_runs = len(filtered_df)
    avg_execution_time_minutes = filtered_df['EXECUTION_TIME_MINUTES'].mean() if 'EXECUTION_TIME_MINUTES' in filtered_df.columns else 0
    success_rate = (len(filtered_df[filtered_df['EXECUTION_STATUS'] == 'SUCCESS']) / total_runs * 100) if total_runs > 0 else 0
    total_compute_minutes = filtered_df['EXECUTION_TIME_MINUTES'].sum() if 'EXECUTION_TIME_MINUTES' in filtered_df.columns else 0
else:
    total_runs = avg_execution_time_minutes = success_rate = total_compute_minutes = 0

# Metrics row
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric(
        "Pipeline Runs", 
        f"{total_runs:,}"
    )

with metric_col2:
    st.metric(
        "Avg Execution Time", 
        format_execution_time(avg_execution_time_minutes) if avg_execution_time_minutes > 0 else "0sec"
    )

with metric_col3:
    st.metric(
        "Success Rate", 
        f"{success_rate:.1f}%" if not filtered_df.empty else "0%"
    )

with metric_col4:
    st.metric(
        "Total Compute Time", 
        format_execution_time(total_compute_minutes) if total_compute_minutes > 0 else "0sec"
    )

st.markdown("---")

# Detailed table section
st.subheader("📋 Detailed Pipeline Run History")
st.caption("💡 Click on any row to select it, then click 'View Details' to see full run information")

if not filtered_df.empty:
    # Select and format columns for display
    display_df = filtered_df.copy()
    columns_to_show = [
        'SESSION_ID', 'QUERY_TEXT', 'START_TIME', 'END_TIME', 'EXECUTION_STATUS', 
        'USER_NAME', 'EXECUTION_TIME_MINUTES'
    ]
    
    # Only show columns that exist in the dataframe
    available_columns = [col for col in columns_to_show if col in display_df.columns]
    table_df = display_df[available_columns].copy()
    
    # Format the display
    if 'START_TIME' in table_df.columns:
        table_df['START_TIME'] = table_df['START_TIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    if 'END_TIME' in table_df.columns:
        table_df['END_TIME'] = table_df['END_TIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    if 'EXECUTION_TIME_MINUTES' in table_df.columns:
        # Apply human-readable time formatting
        table_df['EXECUTION_TIME_READABLE'] = table_df['EXECUTION_TIME_MINUTES'].apply(format_execution_time)
        # Remove the original minutes column
        table_df = table_df.drop('EXECUTION_TIME_MINUTES', axis=1)
    
    # Rename columns for better display
    column_rename = {
        'SESSION_ID': 'Session ID',
        'QUERY_TEXT': 'Run Name',
        'START_TIME': 'Start Time',
        'END_TIME': 'End Time',
        'EXECUTION_STATUS': 'Status',
        'USER_NAME': 'User',
        'EXECUTION_TIME_READABLE': 'Execution Time'
    }
    
    table_df = table_df.rename(columns=column_rename)
    
    # Display the table with selection enabled
    event = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Pipeline execution status",
                width="small"
            ),
            "Execution Time": st.column_config.TextColumn(
                "Execution Time",
                help="Total execution time in human-readable format",
                width="medium"
            )
        }
    )
    
    # Show button to view details if a row is selected
    if len(event.selection.rows) > 0:
        selected_idx = event.selection.rows[0]
        selected_run_name = table_df.iloc[selected_idx]['Run Name']
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"Selected run: **{selected_run_name}**")
        with col2:
            if st.button("🔍 View Details", type="primary", use_container_width=True):
                # Store run name in session state to pass between pages
                st.session_state["selected_run_name"] = selected_run_name
                # Navigate to detail page
                st.switch_page("app_pages/3_detail.py")
    
else:
    st.info("No pipeline run data available. Please check your filters or data connection.")

st.markdown("---")

# Charts section
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Pipeline Execution Trends")
    
    if not filtered_df.empty:
        # Create daily aggregation
        daily_stats = filtered_df.groupby(['DATE', 'EXECUTION_STATUS']).size().reset_index(name='COUNT')
        
        # Create timeline chart
        fig = px.bar(
            daily_stats, 
            x='DATE', 
            y='COUNT', 
            color='EXECUTION_STATUS',
            title="Daily Pipeline Executions by Status",
            color_discrete_map={
                'SUCCESS': '#00CC96',
                'FAILED': '#EF553B',
                'RUNNING': '#FFA15A',
                'CANCELLED': '#AB63FA'
            }
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Pipelines",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected filters")

with chart_col2:
    st.subheader("⏱️ Execution Time Distribution")
    
    if not filtered_df.empty and 'EXECUTION_TIME_MINUTES' in filtered_df.columns:
        # Execution time histogram
        fig = px.histogram(
            filtered_df,
            x='EXECUTION_TIME_MINUTES',
            nbins=20,
            title="Pipeline Execution Time Distribution",
            labels={'EXECUTION_TIME_MINUTES': 'Execution Time (minutes)', 'count': 'Number of Pipelines'}
        )
        fig.update_layout(
            xaxis_title="Execution Time (minutes)",
            yaxis_title="Number of Pipelines",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
       
    else:
        st.info("No execution time data available")
