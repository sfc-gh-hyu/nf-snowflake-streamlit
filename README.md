# Nextflow Pipeline Analytics - Snowflake

A multi-page Streamlit application designed for visualizing and analyzing Nextflow genomics pipeline runs stored in Snowflake.

## 📋 Project Structure

```
nf-snowflake-streamlit/
├── streamlit_app.py          # Main application entry point with navigation
├── app_pages/
│   ├── 1_home.py            # Nextflow pipeline dashboard page
│   └── 2_history.py         # Pipeline run analysis and history page
├── requirements.txt          # Python dependencies
├── README.md
└── LICENSE
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository (if not already done):
   ```bash
   git clone <repository-url>
   cd nf-snowflake-streamlit
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Snowflake connection:
   - Update `.streamlit/secrets.toml` with your Snowflake credentials
   - Ensure your Snowflake user has access to `INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER`
   - Make sure your Nextflow pipelines are tagging queries with `NEXTFLOW_JOB_TYPE` metadata

### Snowflake Setup

The application queries Snowflake's `INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER` function to retrieve Nextflow pipeline execution data. 

**Important Notes:**
- Snowflake query history has limitations on how far back data can be retrieved (typically a few days)
- The application provides time range options from 1 hour to 3 days to work within these limitations
- If you encounter "Cannot retrieve data from more than X days ago" errors, reduce the time range

Your Nextflow pipelines should tag their Snowflake queries with:

```json
{
  "NEXTFLOW_JOB_TYPE": "main"
}
```

### Running the Application

Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Features Overview

- **Real-time Data**: Connects directly to Snowflake to fetch live pipeline execution data
- **Interactive Filtering**: Filter by date range, execution status, and execution time (minutes)
- **Human-readable Time Format**: Displays execution times in easy-to-read format (e.g., "1hr25min30sec")
- **Visualizations**: Charts showing execution trends and performance distributions
- **Detailed Analysis**: Searchable table with execution details and CSV export
- **Performance Metrics**: Success rates, execution times, and resource utilization

## 🧬 Features

### Current Pages

- **🧬 Dashboard**: Nextflow pipeline overview with performance metrics and quick actions
- **🔬 Pipeline Runs**: Detailed genomics workflow analysis with advanced filtering and visualizations

### Key Features

- **Human-readable Execution Times**: Times displayed as "2hr15min30sec" instead of raw numbers
- **Real-time Snowflake Integration**: Live data from your pipeline executions
- **Interactive Filtering**: Date range, status, and execution time filters
- **Visual Analytics**: Charts and graphs for trend analysis
- **Data Export**: CSV download capability for further analysis

### Planned Features

- Interactive genomics pipeline performance charts
- Real-time Nextflow workflow monitoring
- Resource utilization analysis (CPU, memory, storage)
- Task-level bottleneck identification
- Sample throughput tracking
- Workflow-specific performance insights
- Snowflake data integration for pipeline metadata
- Export functionality for genomics reports
- Advanced filtering by execution time and genomics workflows

## 🛠️ Development

This is currently a skeleton implementation with placeholder content designed specifically for Nextflow genomics pipeline analytics. The actual Snowflake data integration and genomics visualization features are ready to be implemented.

## 📝 License

See the [LICENSE](LICENSE) file for details. 