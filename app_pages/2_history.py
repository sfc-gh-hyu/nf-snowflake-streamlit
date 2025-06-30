import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page header
st.title("🔬 Nextflow Pipeline Run Analysis")
st.markdown("---")

# Initialize session state for data
if 'pipeline_data' not in st.session_state:
    st.session_state.pipeline_data = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

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
def load_pipeline_data(days_back=1):
    """Load Nextflow pipeline data from Snowflake"""
    try:
        # Create Snowflake connection
        conn = st.connection("snowflake")
        
        # Query to get Nextflow pipeline runs
        # Note: QUERY_HISTORY_BY_USER has limitations on historical data retrieval
        query = f"""
        SELECT *
        FROM TABLE (
            INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER (
                USER_NAME => CURRENT_USER(),
                END_TIME_RANGE_START => DATEADD (day, -{days_back}, CURRENT_TIMESTAMP()),
                END_TIME_RANGE_END => CURRENT_TIMESTAMP(),
                RESULT_LIMIT => 10000
            )
        )
        WHERE 1=1 
        AND try_parse_json(query_tag):"NEXTFLOW_JOB_TYPE"::string = 'main'
        AND query_type = 'EXECUTE_JOB_SERVICE'
        ORDER BY end_time DESC
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
        if "more than 7 days ago" in error_msg or "Cannot retrieve data" in error_msg:
            st.error("⚠️ Snowflake Query History Limitation: Cannot retrieve data from more than a few days ago.")
            st.info("💡 Try reducing the time range or contact your Snowflake administrator about query history retention policies.")
        else:
            st.error(f"Error connecting to Snowflake: {error_msg}")
        return pd.DataFrame()

# Sidebar - Data Loading Section
with st.sidebar:
    st.header("📊 Data Loading")
    
    # Time range options with (value_in_hours, display_label)
    time_options = [
        (1, "Last 1 hour"),
        (2, "Last 2 hours"),
        (6, "Last 6 hours"),
        (12, "Last 12 hours"),
        (24, "Last 1 day"),
        (48, "Last 2 days"),
        (72, "Last 3 days")
    ]

    selected_option = st.selectbox(
        "📅 Load data from:",
        options=time_options,
        format_func=lambda x: x[1],
        index=4,  # Default to "Last 1 day"
        help="Snowflake query history has limitations on how far back data can be retrieved"
    )

    # Convert to decimal days for the query
    hours_back = selected_option[0]
    days_back_decimal = hours_back / 24.0

    # Refresh data button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Show current status
    if st.session_state.last_refresh:
        st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    st.info(f"📊 Loading: {selected_option[1]}")

# Load data
with st.spinner("Loading Nextflow pipeline data from Snowflake..."):
    pipeline_df = load_pipeline_data(days_back_decimal)

# Display data load status
if pipeline_df.empty:
    st.warning("⚠️ No pipeline data found. Please check your Snowflake connection and permissions.")
    st.info("💡 **Tips:**")
    st.info("• Make sure you have access to INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER")
    st.info("• Verify your Nextflow pipelines are running and tagging queries correctly")
    st.info("• Try adjusting the time range in the sidebar")
    st.info("• Snowflake query history may have retention limitations")
else:
    st.success(f"✅ Loaded {len(pipeline_df)} Nextflow pipeline runs from Snowflake")
    st.session_state.pipeline_data = pipeline_df
    st.session_state.last_refresh = datetime.now()

# Sidebar - Filters Section
with st.sidebar:
    st.markdown("---")
    st.header("🔍 Data Filters")
    
    # Only show filters if we have data
    if not pipeline_df.empty:
        try:
            # Date range filter (for filtering loaded data)
            st.subheader("📅 Date Range Filter")
            min_date = pipeline_df['END_TIME'].dt.date.min()
            max_date = pipeline_df['END_TIME'].dt.date.max()
            
            # Show available data range
            date_range_days = (max_date - min_date).days
            if date_range_days == 0:
                st.caption(f"Available: {min_date}")
            else:
                st.caption(f"Available: {min_date} to {max_date}")
            
            # Calculate safe default start date (ensure it's within valid range)
            if date_range_days == 0:
                # Only one day of data available
                default_start_date = min_date
            else:
                # Multiple days available, default to one day before max or min_date, whichever is later
                default_start_date = max(min_date, max_date - timedelta(days=1))
            
            start_date = st.date_input(
                "Start Date",
                value=default_start_date,
                min_value=min_date,
                max_value=max_date,
                key="filter_start_date"
            )
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=start_date,  # End date can't be before start date
                max_value=max_date,
                key="filter_end_date"
            )
            
            # Validate date range
            if start_date > end_date:
                st.error("Start date cannot be after end date. Please adjust your date selection.")
                # Reset to safe defaults
                start_date = min_date
                end_date = max_date
            
            # Status filter
            st.subheader("🔄 Pipeline Status")
            available_statuses = sorted(pipeline_df['EXECUTION_STATUS'].unique())
            status_filter = st.multiselect(
                "Select Status",
                options=available_statuses,
                default=available_statuses,
                key="status_filter"
            )
            
            # Execution time filter
            st.subheader("⏱️ Execution Time Filter")
            if 'EXECUTION_TIME_MINUTES' in pipeline_df.columns:
                max_minutes = int(pipeline_df['EXECUTION_TIME_MINUTES'].max()) + 1
                runtime_range = st.slider(
                    "Execution Time (minutes)",
                    min_value=0,
                    max_value=max_minutes,
                    value=(0, max_minutes),
                    step=5,
                    format="%d min",
                    key="runtime_filter"
                )
            else:
                runtime_range = (0, 2880)  # 48 hours in minutes
            
            # Apply filters
            filtered_df = pipeline_df.copy()
            
            # Apply date filter
            filtered_df = filtered_df[
                (filtered_df['END_TIME'].dt.date >= start_date) & 
                (filtered_df['END_TIME'].dt.date <= end_date)
            ]
            
            # Apply status filter
            if status_filter:
                filtered_df = filtered_df[filtered_df['EXECUTION_STATUS'].isin(status_filter)]
            
            # Apply execution time filter
            if 'EXECUTION_TIME_MINUTES' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['EXECUTION_TIME_MINUTES'] >= runtime_range[0]) & 
                    (filtered_df['EXECUTION_TIME_MINUTES'] <= runtime_range[1])
                ]
            
            st.markdown("---")
            st.success(f"✅ **Showing:** {len(filtered_df)} of {len(pipeline_df)} pipelines")
            
        except Exception as e:
            st.error(f"Error applying filters: {str(e)}")
            st.info("Using unfiltered data instead.")
            filtered_df = pipeline_df.copy()
        
    else:
        # Default values when no data
        filtered_df = pd.DataFrame()
        st.info("Load data to enable filters")

# Main content
st.subheader("🧬 Nextflow Pipeline Overview")

# Calculate metrics from filtered data
if not filtered_df.empty:
    total_runs = len(filtered_df)
    avg_execution_time_minutes = filtered_df['EXECUTION_TIME_MINUTES'].mean() if 'EXECUTION_TIME_MINUTES' in filtered_df.columns else 0
    success_rate = (len(filtered_df[filtered_df['EXECUTION_STATUS'] == 'SUCCESS']) / total_runs * 100) if total_runs > 0 else 0
    total_compute_minutes = filtered_df['EXECUTION_TIME_MINUTES'].sum() if 'EXECUTION_TIME_MINUTES' in filtered_df.columns else 0
    
    # Calculate deltas compared to previous period (simplified)
    current_period_runs = total_runs
    prev_period_runs = len(pipeline_df) - total_runs if len(pipeline_df) > total_runs else 0
    runs_delta = current_period_runs - prev_period_runs
else:
    total_runs = avg_execution_time_minutes = success_rate = total_compute_minutes = 0
    runs_delta = 0

# Metrics row
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric(
        "Pipeline Runs", 
        f"{total_runs:,}",
        delta=f"{runs_delta:+,}" if runs_delta != 0 else None
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
        
        # Execution time by status
        if len(filtered_df['EXECUTION_STATUS'].unique()) > 1:
            fig3 = px.box(
                filtered_df,
                x='EXECUTION_STATUS',
                y='EXECUTION_TIME_MINUTES',
                title="Execution Time by Status",
                color='EXECUTION_STATUS'
            )
            fig3.update_layout(
                xaxis_title="Pipeline Status",
                yaxis_title="Execution Time (minutes)",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No execution time data available")

st.markdown("---")

# Detailed table section
st.subheader("📋 Detailed Pipeline Run History")

if not filtered_df.empty:
    # Table controls
    table_col1, table_col2, table_col3 = st.columns([2, 1, 1])

    with table_col1:
        search_query = st.text_input("🔍 Search pipeline runs", placeholder="Search by query ID, database, or query text...")

    with table_col2:
        sort_column_map = {
            "End Time": "END_TIME",
            "Execution Time": "EXECUTION_TIME_MINUTES",
            "Status": "EXECUTION_STATUS",
            "Query ID": "QUERY_ID"
        }
        sort_by = st.selectbox("Sort by", list(sort_column_map.keys()))

    with table_col3:
        sort_order = st.selectbox("Order", ["Descending", "Ascending"])

    # Apply search filter
    display_df = filtered_df.copy()
    if search_query:
        search_mask = (
            display_df['QUERY_ID'].astype(str).str.contains(search_query, case=False, na=False) |
            display_df['DATABASE_NAME'].astype(str).str.contains(search_query, case=False, na=False) |
            display_df['QUERY_TEXT'].astype(str).str.contains(search_query, case=False, na=False)
        )
        display_df = display_df[search_mask]

    # Apply sorting
    sort_column = sort_column_map[sort_by]
    ascending = sort_order == "Ascending"
    if sort_column in display_df.columns:
        display_df = display_df.sort_values(sort_column, ascending=ascending)

    # Select and format columns for display
    columns_to_show = [
        'QUERY_ID', 'END_TIME', 'EXECUTION_STATUS', 'DATABASE_NAME', 
        'WAREHOUSE_NAME', 'EXECUTION_TIME_MINUTES'
    ]
    
    # Only show columns that exist in the dataframe
    available_columns = [col for col in columns_to_show if col in display_df.columns]
    table_df = display_df[available_columns].copy()
    
    # Format the display
    if 'END_TIME' in table_df.columns:
        table_df['END_TIME'] = table_df['END_TIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    if 'EXECUTION_TIME_MINUTES' in table_df.columns:
        # Apply human-readable time formatting
        table_df['EXECUTION_TIME_READABLE'] = table_df['EXECUTION_TIME_MINUTES'].apply(format_execution_time)
        # Remove the original minutes column
        table_df = table_df.drop('EXECUTION_TIME_MINUTES', axis=1)
    
    # Rename columns for better display
    column_rename = {
        'QUERY_ID': 'Query ID',
        'END_TIME': 'End Time',
        'EXECUTION_STATUS': 'Status',
        'DATABASE_NAME': 'Database',
        'WAREHOUSE_NAME': 'Warehouse',
        'EXECUTION_TIME_READABLE': 'Execution Time'
    }
    
    table_df = table_df.rename(columns=column_rename)
    
    # Display the table
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
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
    
    # Download button
    if st.button("📥 Download Results as CSV"):
        csv = table_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"nextflow_pipeline_runs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    st.info("No pipeline run data available. Please check your filters or data connection.")

# Summary section
if not filtered_df.empty:
    st.markdown("---")
    st.subheader("📊 Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Total Filtered Results", len(filtered_df))
    
    with summary_col2:
        if 'WAREHOUSE_NAME' in filtered_df.columns:
            unique_warehouses = filtered_df['WAREHOUSE_NAME'].nunique()
            st.metric("Unique Warehouses", unique_warehouses)
    
    with summary_col3:
        if 'DATABASE_NAME' in filtered_df.columns:
            unique_databases = filtered_df['DATABASE_NAME'].nunique()
            st.metric("Unique Databases", unique_databases) 