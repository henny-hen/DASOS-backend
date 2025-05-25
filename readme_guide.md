# Academic Data Analysis Project

This project provides a comprehensive solution for extracting, analyzing, and visualizing academic performance data from semester reports. It's specifically designed to work with PDF reports containing course information, student enrollment statistics, and performance metrics.

## Features

- **Data Extraction**: Extract structured data from semester report PDFs
- **API Integration**: Fetch and analyze data from the UPM academic API
- **Correlation Analysis**: Identify relationships between faculty changes, evaluation methods, and performance metrics
- **Data Storage**: Store extracted data in SQLite database for easy querying and analysis
- **Data Analysis**: Generate comprehensive analysis of academic performance
- **Visualization**: Create insightful plots and visuals of academic data
- **Trend Analysis**: Track performance trends across multiple semesters
- **Comparative Analysis**: Compare subjects based on various performance metrics
- **Report Generation**: Generate detailed summary reports with insights and recommendations

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - pandas
  - matplotlib
  - seaborn
  - PyMuPDF
  - textract 
  - numpy
  - sqlite3 
  - requests
  - flask
  - flask-cors
  - scipy (for advanced statistical analysis)
  - pymannkendall (optional, for advanced trend analysis)

## Installation

1. Install required packages:

```bash
pip install pandas matplotlib seaborn PyMuPDF textract numpy requests flask flask-cors scipy
```

## Project Structure

```
academic_analysis/
├── academic_data_extractor.py  # Extract data from PDF text
├── academic_database.py        # SQLite database functionality
├── academic_api_extractor.py   # Fetch and analyze data from UPM API
├── academic_visualizations.py  # Advanced visualization functions
├── academic_api.py               # REST API for web integration
├── main.py                     # Main program and CLI interface
└── README.md                   # This documentation file
```

## Usage

### Command Line Interface

The project provides a command-line interface for usage:

```bash
python main.py --pdf path/to/report.pdf --output results
```

#### Command Line Options

- `--pdf PATH`: Process a single PDF report
- `--dir PATH`: Process all PDF reports in a directory
- `--output PATH`: Specify output directory (default: "output")
- `--db PATH`: Specify SQLite database path (default: "academic_data.db")
- `--no-viz`: Skip generating visualizations
- `--analyze-only`: Only perform analysis on existing database
-  `--api-analysis`: Perform analysis with API integration
-  `--plan-code CODE`: Specify the academic plan code for API requests (default: "10II")

### Examples

#### Process a single report

```bash
python main.py --pdf reports/IS_10II_2023-24.pdf --output results/2023-24
```


#### Perform API-integrated analysis using the processed data of the reports

```bash
python main.py --api-analysis --db academic_data.db --output api_results --plan-code 10II
```

#### Process multiple reports

```bash
python main.py --dir reports/ --output all_results
```

#### Analyze existing database without processing PDFs

```bash
python main.py --analyze-only --db academic_data.db --output analysis_results
```

### Starting the REST API Server

To make your academic data available through a REST API for web applications:

```bash
python rest-api.py --db academic_data.db --port 5000
```

#### API Server Options

- `--db PATH`: Path to SQLite database (default: "academic_data.db")
- `--port PORT`: Port to run the API server on (default: 5000)
- `--host HOST`: Host to run the API server on (default: 127.0.0.1)
- `--debug`: Run in debug mode

## REST API Endpoints

The REST API provides access to all analysis data stored in the database. All endpoints are prefixed with `/api/v1`.

### Basic Data Endpoints

- **GET /api/v1/subjects**: Get all subjects
  - Query parameters: `academic_year`, `semester`

- **GET /api/v1/subjects/{subject_code}**: Get detailed information about a specific subject
  - Query parameters: `academic_year`

- **GET /api/v1/subjects/{subject_code}/historical**: Get historical performance data for a subject
  - Query parameters: `rate_type`

- **GET /api/v1/performance/summary**: Get summary of performance metrics
  - Query parameters: `academic_year`

### API Analysis Endpoints

- **GET /api/v1/faculty/changes**: Get faculty changes data
  - Query parameters: `subject_code`

- **GET /api/v1/evaluation/changes**: Get evaluation method changes data
  - Query parameters: `subject_code`

- **GET /api/v1/correlations**: Get correlations between changes and performance
  - Query parameters: `subject_code`, `faculty_changed`, `evaluation_changed`

### Insights Endpoints

- **GET /api/v1/insights/global**: Get global insights from the most recent analysis

- **GET /api/v1/insights/subjects**: Get subject-specific insights
  - Query parameters: `subject_code`, `analysis_id`

### Advanced Analysis Endpoints

- **GET /api/v1/advanced/trend-analysis**: Get results from advanced trend analysis
  - Query parameters: `subject_code`, `significant_only`

### Utility Endpoints

- **GET /api/v1/stats**: Get database statistics

## Example API Requests

### Get all subjects from a specific academic year

```
GET http://localhost:5000/api/v1/subjects?academic_year=2023-24
```

### Get historical data for a specific subject

```
GET http://localhost:5000/api/v1/subjects/105000005/historical
```

### Get performance correlation data for subjects with faculty changes

```
GET http://localhost:5000/api/v1/correlations?faculty_changed=true
```

### Get global insights from the latest analysis

```
GET http://localhost:5000/api/v1/insights/global


## Output

The tool generates various outputs organized in directories:

- **CSV and JSON Files**: Extracted data in structured formats
- **Analysis Reports**: Text reports with insights and observations
- **Visualizations**: Charts and graphs visualizing performance metrics:
  - Performance rates comparison
  - Success rates comparison
  - Absenteeism rates analysis
  - Historical trends
  - Subject comparisons
  - Performance dashboards
  - Faculty-performance correlation visualizations
  - Evaluation-performance correlation visualizations
  
- **Enhanced Reports**: API-integrated analysis reports:
  - Faculty change impact analysis
  - Evaluation methods impact analysis
  - Correlation between academic changes and performance

## Example Workflow

1. **Extract Data**: Process PDF reports to extract academic performance data
2. **Store Data**: Save extracted data in SQLite database
3. **Fetch API Data**: Retrieve faculty and evaluation information from the UPM API
4. **Correlate Changes**: Identify relationships between faculty/evaluation changes and performance trends
5. **Analyze Data**: Generate comprehensive analysis of performance metrics
6. **Visualize Results**: Create charts and dashboards to visualize insights
7. **Generate Reports**: Produce detailed reports with recommendations
8. **Track Trends**: Monitor performance trends across semesters


## API Integration Details

The new API integration component connects to the UPM academic API to fetch detailed information about subjects, including:

- Faculty information (professors teaching each subject)
- Evaluation methods and activities
- Curriculum details

The system analyzes changes in these elements across academic years and correlates them with performance metrics to identify potential causative relationships.

### API Endpoint Format

The toolkit accesses the UPM API using the following URL pattern:
```
https://www.upm.es/comun_gauss/publico/api/{academic_year}/{semester}/{plan_code}_{subject_code}.json
```

For example:
```
https://www.upm.es/comun_gauss/publico/api/2022-23/2S/10II_105000005.json
```

### Correlation Analysis

The toolkit performs the following correlation analyses:

1. **Faculty Change Impact**: Evaluates how changes in teaching staff correlate with changes in performance metrics
2. **Evaluation Method Impact**: Assesses the relationship between changes in evaluation methods and student performance
3. **Trend Analysis**: Identifies patterns across subjects where similar changes produce similar outcomes

## Enhanced Insights

The API-integrated analysis generates enhanced insights such as:

- Identification of potential causative factors for performance changes
- Recommendations for faculty assignments based on historical performance
- Evaluation method effectiveness analysis
- Identification of best practices that could be applied across courses
