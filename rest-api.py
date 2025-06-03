"""
Academic Data REST API - Production Version

This module provides a REST API to access the academic data stored in the SQLite database.
It allows external applications like websites to retrieve analysis results, performance data,
and insights through HTTP requests.

Usage:
    python academic_api.py --db path/to/academic_data.db --port 5000
"""

import os
import argparse
import json
import sqlite3
import pandas as pd
from flask import Flask, jsonify, request, g, abort
from flask_cors import CORS
import numpy as np
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure Flask application
app = Flask(__name__)

# Production configurations
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    # Use ProxyFix for deployment behind reverse proxies (like Railway, Render)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
else:
    app.config['DEBUG'] = True

# Enable CORS for production with specific origins
if os.environ.get('FLASK_ENV') == 'production':
    # Add your frontend URLs here
    allowed_origins = [
        "https://*.vercel.app",
        "https://your-frontend-domain.com"
    ]
    CORS(app, origins=allowed_origins)
else:
    CORS(app)  # Allow all origins in development

# Configuration - Use environment variables for production
DATABASE = os.environ.get('DATABASE_PATH', 'academic_data.db')
API_PREFIX = '/api/v1'
PORT = int(os.environ.get('PORT', 5000))

# Custom JSON encoder to handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return json.JSONEncoder.default(self, obj)

# Configure app to use custom JSON encoder
app.json_encoder = NumpyEncoder

# Health check endpoint for deployment platforms
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if os.path.exists(app.config.get('DATABASE', DATABASE)) else 'not_found'
    })

# Root endpoint
@app.route('/')
def root():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'Academic Data API',
        'version': '1.0.0',
        'endpoints': {
            'subjects': f'{API_PREFIX}/subjects',
            'stats': f'{API_PREFIX}/stats',
            'health': '/health'
        }
    })

# Database connection handling
def get_db():
    """Get database connection for the current request"""
    if not hasattr(g, 'db'):
        db_path = app.config.get('DATABASE', DATABASE)
        if not os.path.exists(db_path):
            abort(500, description=f"Database file not found: {db_path}")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row  # Return rows as dictionaries
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection at the end of the request"""
    if hasattr(g, 'db'):
        g.db.close()

# Helper functions
def dict_factory(cursor, row):
    """Convert database row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def query_db(query, args=(), one=False):
    """Query the database and return results as dictionaries"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        app.logger.error(f"Database query error: {str(e)}")
        abort(500, description="Database query failed")

def get_dataframe_from_query(query, params=()):
    """Execute a query and return results as a pandas DataFrame"""
    try:
        conn = get_db()
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        app.logger.error(f"DataFrame query error: {str(e)}")
        return pd.DataFrame()

# API Endpoints
@app.route(f'{API_PREFIX}/subjects', methods=['GET'])
def get_subjects():
    """
    Get all subjects or filter by academic year
    
    Query Parameters:
    - academic_year: Filter by academic year (e.g., "2023-24")
    - semester: Filter by semester
    
    Returns:
    - JSON array of subjects with their basic information
    """
    academic_year = request.args.get('academic_year')
    semester = request.args.get('semester')
    
    query = """
    SELECT s.subject_code, s.subject_name, s.credits, s.academic_year, s.semester,
           e.total_enrolled, e.first_time, e.partial_dedication,
           p.performance_rate, p.success_rate, p.absenteeism_rate
    FROM subjects s
    LEFT JOIN enrollment e ON s.subject_code = e.subject_code AND s.academic_year = e.academic_year AND s.semester = e.semester
    LEFT JOIN performance_rates p ON s.subject_code = p.subject_code AND s.academic_year = p.academic_year AND s.semester = p.semester
    """
    
    conditions = []
    params = []
    
    if academic_year:
        conditions.append("s.academic_year = ?")
        params.append(academic_year)
    
    if semester:
        conditions.append("s.semester = ?")
        params.append(semester)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY s.subject_name"
    
    results = query_db(query, params)
    return jsonify(results)

@app.route(f'{API_PREFIX}/subjects/<subject_code>', methods=['GET'])
def get_subject(subject_code):
    """
    Get detailed information about a specific subject
    
    Parameters:
    - subject_code: The code of the subject
    
    Query Parameters:
    - academic_year: Filter by academic year (optional)
    
    Returns:
    - JSON object with subject details including performance metrics
    """
    academic_year = request.args.get('academic_year')
    
    # Get basic subject info
    query = """
    SELECT s.subject_code, s.subject_name, s.credits, s.academic_year, s.semester,
           e.total_enrolled, e.first_time, e.partial_dedication,
           p.performance_rate, p.success_rate, p.absenteeism_rate
    FROM subjects s
    LEFT JOIN enrollment e ON s.subject_code = e.subject_code AND s.academic_year = e.academic_year AND s.semester = e.semester
    LEFT JOIN performance_rates p ON s.subject_code = p.subject_code AND s.academic_year = p.academic_year AND s.semester = p.semester
    WHERE s.subject_code = ?
    """
    
    params = [subject_code]
    
    if academic_year:
        query += " AND s.academic_year = ?"
        params.append(academic_year)
    
    result = query_db(query, params, one=True)
    
    if not result:
        abort(404, description=f"Subject with code {subject_code} not found")
    
    return jsonify(result)

@app.route(f'{API_PREFIX}/subjects/<subject_code>/historical', methods=['GET'])
def get_subject_historical(subject_code):
    """
    Get historical performance data for a specific subject
    
    Parameters:
    - subject_code: The code of the subject
    
    Query Parameters:
    - rate_type: Filter by rate type (e.g., "rendimiento", "éxito", "absentismo")
    
    Returns:
    - JSON array with historical performance data
    """
    rate_type = request.args.get('rate_type')
    
    query = """
    SELECT subject_code, academic_year, rate_type, value
    FROM historical_rates
    WHERE subject_code = ?
    """
    
    params = [subject_code]
    
    if rate_type:
        query += " AND rate_type = ?"
        params.append(rate_type)
    
    query += " ORDER BY academic_year"
    
    results = query_db(query, params)
    return jsonify(results)

@app.route(f'{API_PREFIX}/faculty/changes', methods=['GET'])
def get_faculty_changes():
    """
    Get faculty changes data
    
    Query Parameters:
    - subject_code: Filter by subject code (optional)
    
    Returns:
    - JSON array with faculty change data
    """
    subject_code = request.args.get('subject_code')
    
    query = """
    SELECT f.subject_code, s.subject_name, f.year1, f.year2, 
           f.faculty_added, f.faculty_removed, f.percent_changed
    FROM faculty_changes f
    LEFT JOIN subjects s ON f.subject_code = s.subject_code
    """
    
    params = []
    if subject_code:
        query += " WHERE f.subject_code = ?"
        params.append(subject_code)
    
    results = query_db(query, params)
    return jsonify(results)

@app.route(f'{API_PREFIX}/evaluation/changes', methods=['GET'])
def get_evaluation_changes():
    """
    Get evaluation method changes data
    
    Query Parameters:
    - subject_code: Filter by subject code (optional)
    
    Returns:
    - JSON array with evaluation method change data
    """
    subject_code = request.args.get('subject_code')
    
    query = """
    SELECT e.subject_code, s.subject_name, e.year1, e.year2, 
           e.methods_added, e.methods_removed
    FROM evaluation_changes e
    LEFT JOIN subjects s ON e.subject_code = s.subject_code
    """
    
    params = []
    if subject_code:
        query += " WHERE e.subject_code = ?"
        params.append(subject_code)
    
    results = query_db(query, params)
    return jsonify(results)

@app.route(f'{API_PREFIX}/correlations', methods=['GET'])
def get_correlations():
    """
    Get correlations between faculty/evaluation changes and performance
    
    Query Parameters:
    - subject_code: Filter by subject code (optional)
    
    Returns:
    - JSON array with correlation data
    """
    subject_code = request.args.get('subject_code')
    
    query = """
    SELECT *
    FROM performance_correlations
    """
    
    params = []
    if subject_code:
        query += " WHERE subject_code = ?"
        params.append(subject_code)
    
    results = query_db(query, params)
    return jsonify(results)

@app.route(f'{API_PREFIX}/insights/subjects', methods=['GET'])
def get_subject_insights():
    """
    Get subject-specific insights
    
    Query Parameters:
    - subject_code: Filter by subject code (optional)
    
    Returns:
    - JSON array with subject insights
    """
    subject_code = request.args.get('subject_code')
    
    # Mock insights for now - replace with actual database query
    insights = []
    if subject_code:
        insights = [{
            'subject_code': subject_code,
            'insight_type': 'performance',
            'message': 'This subject shows stable performance over time',
            'confidence': 0.85
        }]
    
    return jsonify(insights)

@app.route(f'{API_PREFIX}/stats', methods=['GET'])
def get_database_stats():
    """
    Get database statistics
    
    Returns:
    - JSON object with database statistics
    """
    stats = {}
    
    # Count subjects
    subjects_query = "SELECT COUNT(*) as count FROM subjects"
    subjects_result = query_db(subjects_query, one=True)
    stats['total_subjects'] = subjects_result['count'] if subjects_result else 0
    
    # Count unique academic years
    years_query = "SELECT COUNT(DISTINCT academic_year) as count FROM subjects"
    years_result = query_db(years_query, one=True)
    stats['total_academic_years'] = years_result['count'] if years_result else 0
    
    # Get distinct academic years
    years_list_query = "SELECT DISTINCT academic_year FROM subjects ORDER BY academic_year"
    years_list_result = query_db(years_list_query)
    stats['academic_years'] = [year['academic_year'] for year in years_list_result]
    
    # Count historical rates
    hist_query = "SELECT COUNT(*) as count FROM historical_rates"
    hist_result = query_db(hist_query, one=True)
    stats['total_historical_rates'] = hist_result['count'] if hist_result else 0
    
    # Check if API analysis data exists
    try:
        faculty_query = "SELECT COUNT(*) as count FROM faculty_changes"
        faculty_result = query_db(faculty_query, one=True)
        stats['has_api_analysis'] = (faculty_result['count'] > 0) if faculty_result else False
    except:
        stats['has_api_analysis'] = False
    
    return jsonify(stats)

@app.route(f'{API_PREFIX}/search', methods=['GET'])
def search_subjects():
    """
    Search subjects by name or code
    
    Query Parameters:
    - q: Search query
    
    Returns:
    - JSON array of matching subjects
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    search_query = """
    SELECT s.subject_code, s.subject_name, s.credits, s.academic_year, s.semester
    FROM subjects s
    WHERE s.subject_name LIKE ? OR s.subject_code LIKE ?
    ORDER BY s.subject_name
    LIMIT 20
    """
    
    search_pattern = f"%{query}%"
    results = query_db(search_query, [search_pattern, search_pattern])
    
    return jsonify(results)

# Error handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e.description)), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error=str(e.description)), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error="Internal server error"), 500

# Main entry point
def main():
    parser = argparse.ArgumentParser(description='Academic Data REST API')
    parser.add_argument('--db', type=str, default=DATABASE, 
                        help=f'Path to SQLite database (default: {DATABASE})')
    parser.add_argument('--port', type=int, default=PORT, 
                        help=f'Port to run the API server on (default: {PORT})')
    parser.add_argument('--host', type=str, default='0.0.0.0', 
                        help='Host to run the API server on (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Set database path
    app.config['DATABASE'] = args.db
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file '{args.db}' not found.")
        return 1
    
    print(f"Starting Academic Data API server on http://{args.host}:{args.port}")
    print(f"Using database: {args.db}")
    
    # Use production WSGI server if available
    try:
        from waitress import serve
        print("Using Waitress WSGI server for production")
        serve(app, host=args.host, port=args.port)
    except ImportError:
        print("Waitress not available, using Flask development server")
        app.run(host=args.host, port=args.port, debug=(os.environ.get('FLASK_ENV') != 'production'))
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())