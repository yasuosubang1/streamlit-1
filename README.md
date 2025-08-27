# Instance Application Dashboard

A simple, local, web-based dashboard for analyzing and visualizing instance application data. Built with Streamlit for quick prototyping and demo purposes.

## 🚀 Features

### Data Ingestion
- **Multiple JSON File Upload**: Upload one or more JSON files containing instance data
- **Basic Validation**: Automatic validation of JSON structure and required fields
- **In-Memory Processing**: Fast data processing without persistent storage

### Data Processing
- **Array Flattening**: Automatically flattens nested application arrays
- **Metric Aggregation**: Calculates summary statistics and distributions
- **Data Transformation**: Converts raw JSON into structured tabular format

### Dashboard Visualization
- **Interactive Charts**: Bar and pie charts for application type and status distribution
- **Hover Details**: Rich tooltips with additional information
- **Single-Page View**: All visualizations and data in one convenient interface

### Data Tables
- **Instance/Application Listing**: Comprehensive table view of all applications
- **Sorting & Search**: Built-in sorting and text search functionality
- **CSV Export**: Download processed data as CSV files

### Filtering
- **Dropdown Filters**: Filter by application type, status, and instance
- **Text Search**: Search applications by name
- **Real-time Updates**: Filters update visualizations and tables instantly

## 📋 Requirements

- Python 3.8+
- Streamlit 1.29.0+
- Pandas 2.2.0+
- Plotly 5.17.0+
- NumPy 2.0.0+

## 🛠️ Installation

1. **Clone or download the project files**
   ```bash
   # Ensure you have the following files:
   # - app.py
   # - requirements.txt
   # - README.md
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser**
   - Navigate to `http://localhost:8501`
   - The dashboard will open automatically

3. **Upload JSON files**
   - Use the sidebar file uploader
   - Select one or more JSON files
   - Files are validated and processed automatically

4. **Explore your data**
   - View summary metrics at the top
   - Interact with charts and visualizations
   - Use filters to drill down into specific data
   - Search for specific applications
   - Export data as CSV when needed

## 📊 Expected JSON Format

The dashboard expects JSON files with the following structure:

```json
{
  "instance_id": "i-1234567890abcdef0",
  "instance_name": "web-server-01",
  "collection_timestamp": "2024-01-15T10:30:00Z",
  "script_version": "1.0.0",
  "applications": [
    {
      "name": "nginx",
      "type": "container",
      "image": "nginx:latest",
      "status": "running",
      "ports": [80, 443],
      "pids": [1234],
      "container_id": "abc123def456"
    },
    {
      "name": "python-app",
      "type": "process",
      "status": "running",
      "ports": [8000],
      "pids": [5678],
      "process_name": "python app.py"
    }
  ],
  "total_applications": 2
}
```

### Required Fields
- `instance_id`: Unique identifier for the instance
- `instance_name`: Human-readable name for the instance
- `applications`: Array of application objects

### Application Object Fields
- `name`: Application name
- `type`: Application type (e.g., "container", "process")
- `status`: Current status (e.g., "running", "stopped")
- `ports`: Array of port numbers
- `pids`: Array of process IDs
- `container_id`: Container ID (for container applications)
- `process_name`: Process name (for process applications)

## 🎯 Use Cases

- **System Monitoring**: Visualize application status across multiple instances
- **Capacity Planning**: Analyze application distribution and resource usage
- **Troubleshooting**: Quickly identify stopped or problematic applications
- **Reporting**: Generate reports and export data for further analysis
- **Demos**: Present system state to stakeholders

## 🔧 Customization

The dashboard is designed to be easily customizable:

- **Styling**: Modify the CSS in the `st.markdown()` sections
- **Visualizations**: Add new chart types using Plotly
- **Filters**: Extend filtering logic in the sidebar
- **Data Processing**: Modify the `process_instance_data()` function
- **Validation**: Update the `load_and_validate_json()` function

## 🚨 Limitations

- **No Persistent Storage**: Data is only stored in memory during the session
- **No Authentication**: Designed for local/demo use only
- **No Cloud Dependencies**: Runs entirely locally
- **Single Session**: Each browser session maintains its own data

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid JSON format" error**
   - Ensure your JSON files are properly formatted
   - Check for missing commas or brackets
   - Validate JSON using an online validator

2. **"Missing required field" error**
   - Ensure your JSON includes `instance_id`, `instance_name`, and `applications`
   - Check field names for typos

3. **Empty visualizations**
   - Ensure your applications have `type` and `status` fields
   - Check that the applications array is not empty

4. **Performance issues**
   - Large files (>10MB) may cause slow loading
   - Consider splitting large datasets into smaller files

### Getting Help

If you encounter issues:
1. Check the Streamlit console for error messages
2. Verify your JSON file format
3. Ensure all dependencies are installed correctly
4. Try with the provided sample data first

## 📝 Version History

- **v1.0.0** - Initial release with core functionality
  - JSON file upload and validation
  - Interactive visualizations
  - Data tables with filtering
  - CSV export functionality

## 🤝 Contributing

This is a demo application designed for specific use cases. For enhancements:
1. Fork the project
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is provided as-is for demonstration purposes. Feel free to modify and use according to your needs.