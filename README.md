# Streamlit Historic Runs Visualizer

A multi-page Streamlit application designed for visualizing and analyzing Streamlit application historic runs.

## 📋 Project Structure

```
nf-snowflake-streamlit/
├── streamlit_app.py          # Main application entry point
├── pages/
│   ├── 1_🏠_Home.py         # Home dashboard page
│   └── 2_📈_History.py      # Historic runs analysis page
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

### Running the Application

Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`

## 📱 Features

### Current Pages

- **🏠 Home**: Dashboard with overview metrics and quick actions
- **📈 History**: Detailed historic run analysis with filters and visualizations

### Planned Features

- Interactive charts and visualizations
- Real-time run monitoring
- Detailed run analysis
- Export functionality
- Advanced filtering and search
- Performance insights and recommendations

## 🛠️ Development

This is currently a skeleton implementation with placeholder content. The actual data integration and visualization features are ready to be implemented.

## 📝 License

See the [LICENSE](LICENSE) file for details. 