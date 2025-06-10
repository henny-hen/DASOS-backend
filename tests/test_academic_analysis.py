import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

# Import modules to test
from academic_data_extractor import AcademicDataExtractor, AcademicDataAnalyzer
from academic_api_extractor import AcademicApiExtractor
from academic_database import AcademicDatabase


class TestAcademicDataExtractor:
    """Test suite for academic data extraction functionality"""
    
    @pytest.fixture
    def sample_pdf_text(self):
        """Sample PDF text content for testing"""
        return """
        2023/24 - Segundo Semestre
        PLAN DE ESTUDIOS
        10II - Grado en Ingeniería Informática
        
        A1.1. Matriculados
        105000005 - Cálculo
        6
        455
        105000007 - Probabilidades y Estadística I
        6
        267

        A1.2. Perfil de los alumnos matriculados

        
        A2.1. Tasas de resultados académicos obtenidas en el curso objeto del Informe
        105000005 - Cálculo 
        31.94 
        36.52 
        12.56
        105000007 - Probabilidades y Estadística I 
        89.14 
        92.97 
        4.12

        A2.2. Tasas de resultados académicos obtenidas en cursos anteriores

        """
    
    def test_extract_course_info(self, sample_pdf_text):
        """Test course information extraction"""
        extractor = AcademicDataExtractor(sample_pdf_text)
        course_info = extractor.extract_course_info()
        
        assert course_info['academic_year'] == '2023/24'
        assert course_info['semester'].strip() == 'Segundo'
        assert course_info['plan_code'] == '10II'
        assert course_info['plan_title'] == 'Grado en Ingeniería Informática'
    
    def test_extract_subjects_basic_info(self, sample_pdf_text):
        """Test subject basic information extraction"""
        extractor = AcademicDataExtractor(sample_pdf_text)
        subjects = extractor.extract_subjects_basic_info()
        
        assert len(subjects) == 2
        assert '105000005' in subjects
        assert subjects['105000005']['name'] == 'Cálculo'
        assert subjects['105000005']['credits'] == 6
        assert subjects['105000005']['enrolled'] == 455
    
    def test_extract_performance_rates(self, sample_pdf_text):
        """Test performance rates extraction"""
        extractor = AcademicDataExtractor(sample_pdf_text)
        extractor.courses_data = extractor.extract_subjects_basic_info()
        extractor.extract_performance_rates()
        
        calc_data = extractor.courses_data['105000005']
        assert calc_data['performance_rate'] == 31.94
        assert calc_data['success_rate'] == 36.52
        assert calc_data['absenteeism_rate'] == 12.56


class TestAcademicDataAnalyzer:
    """Test suite for academic data analysis functionality"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing analysis"""
        return {
            "course_info": {
                "academic_year": "2023/24",
                "semester": "Segundo",
                "plan_code": "10II",
                "plan_title": "Grado en Ingeniería Informática"
            },
            "subjects": {
                "105000005": {
                    "name": "Cálculo",
                    "credits": 6,
                    "enrolled": 455,
                    "performance_rate": 31.94,
                    "success_rate": 36.52,
                    "absenteeism_rate": 12.56,
                    "historical": {
                        "rendimiento": {
                            "2020-21": 31.32,
                            "2021-22": 35.12,
                            "2022-23": 32.49,
                            "2023-24": 31.94
                        }
                    }
                }
            }
        }
    
    def test_convert_to_dataframe(self, sample_data):
        """Test conversion to pandas DataFrame"""
        analyzer = AcademicDataAnalyzer(sample_data)
        df = analyzer.convert_to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['name'] == 'Cálculo'
        assert df.iloc[0]['performance_rate'] == 31.94
    
    def test_historical_rates_to_dataframe(self, sample_data):
        """Test historical rates DataFrame conversion"""
        analyzer = AcademicDataAnalyzer(sample_data)
        hist_df = analyzer.historical_rates_to_dataframe()
        
        assert isinstance(hist_df, pd.DataFrame)
        assert len(hist_df) == 4  # 4 years of data
        assert 'subject_code' in hist_df.columns
        assert 'rate_type' in hist_df.columns
        assert 'value' in hist_df.columns
    
    def test_correlation_analysis(self, sample_data):
        """Test correlation analysis with API data"""
        analyzer = AcademicDataAnalyzer(sample_data)
        current_folder_path = Path(__file__).parent
        # Mock API analysis results
        api_results = {
            "105000005": {
                "subject_name": "Cálculo",
                "faculty_analysis": {
                    "years_compared": [("2022-23", "2023-24")],
                    "faculty_changes": {
                        ("2022-23", "2023-24"): {
                            "added": ["Prof. New"],
                            "removed": ["Prof. Old"],
                            "total_added": 1,
                            "total_removed": 1,
                            "percent_changed": 25.0
                        }
                    }
                },
                "evaluation_analysis": {
                    "years_compared": [("2022-23", "2023-24")],
                    "evaluation_changes": {
                        ("2022-23", "2023-24"): {
                            "added": ["Online Quiz"],
                            "removed": [],
                            "changed": True
                        }
                    }
                }
            }
        }
        
        # Test correlation analysis
        correlation_df = analyzer.correlate_api_changes_with_performance(api_results, current_folder_path)
        
        assert not correlation_df.empty
        assert 'performance_change' in correlation_df.columns
        assert 'faculty_changed' in correlation_df.columns
        assert correlation_df.iloc[2]['faculty_changed'] == True


class TestAcademicDatabase:
    """Test suite for database operations"""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a test database"""
        db_path = tmp_path / "test_academic.db"
        return AcademicDatabase(str(db_path))
    
    def test_database_setup(self, test_db):
        """Test database table creation"""
        # Check if tables exist
        cursor = test_db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'course_info', 'subjects', 'enrollment', 
            'performance_rates', 'historical_rates',
            'faculty_changes', 'evaluation_changes',
            'performance_correlations', 'global_insights',
            'subject_insights'
        ]
        
        for table in expected_tables:
            assert table in tables
    
    def test_store_and_retrieve_data(self, test_db):
        """Test storing and retrieving data"""
        # Sample data
        data = {
            "course_info": {
                "academic_year": "2023/24",
                "semester": "Segundo",
                "plan_code": "10II",
                "plan_title": "Test Plan"
            },
            "subjects": {
                "TEST001": {
                    "name": "Test Subject",
                    "credits": 6,
                    "enrolled": 100,
                    "performance_rate": 75.0,
                    "success_rate": 85.0,
                    "absenteeism_rate": 5.0
                }
            }
        }
        
        # Store data
        test_db.store_data(data)
        
        # Retrieve and verify
        subjects_df = test_db.get_subjects()
        assert len(subjects_df) == 1
        assert subjects_df.iloc[0]['subject_code'] == 'TEST001'
        assert subjects_df.iloc[0]['subject_name'] == 'Test Subject'
        assert subjects_df.iloc[0]['performance_rate'] == 75.0
    
    def test_performance_correlations(self, test_db):
        """Test storing and retrieving performance correlations"""
        # Create correlation data
        

        correlation_data = pd.DataFrame([{
            "subject_code": "TEST001",
            "subject_name": "Test Subject",
            "year1": "2022-23",
            "year2": "2023-24",
            "performance_change": -2.5,
            "faculty_changed": True,
            "faculty_percent_changed": 25.0,
            "faculty_added": 2,
            "faculty_removed": 1,
            "evaluation_changed": False,
            "evaluation_methods_added": 0,
            "evaluation_methods_removed": 0
        }])
        
        # Store correlations
        test_db.store_performance_correlations(correlation_data)
        
        # Retrieve and verify
        retrieved = test_db.get_performance_correlations("TEST001")
        assert len(retrieved) == 1
        assert retrieved.iloc[0]['performance_change'] == -2.5
        assert retrieved.iloc[0]['faculty_changed'] == True


class TestAcademicApiExtractor:
    """Test suite for API data extraction"""
    
    @pytest.fixture
    def api_extractor(self, tmp_path):
        """Create API extractor with test cache directory"""
        extractor = AcademicApiExtractor()
        extractor.cache_dir = tmp_path / "api_cache"
        extractor.cache_dir.mkdir(exist_ok=True)
        return extractor
    
    def test_analyze_faculty_changes(self, api_extractor):
        """Test faculty change analysis"""
        # Mock subject data
        subject_data = {
            "2022-23": {
                "profesores": [
                    {"nombre": "Prof. A"},
                    {"nombre": "Prof. B"}
                ]
            },
            "2023-24": {
                "profesores": [
                    {"nombre": "Prof. B"},
                    {"nombre": "Prof. C"},
                    {"nombre": "Prof. D"}
                ]
            }
        }
        
        result = api_extractor.analyze_faculty_changes(subject_data)
        
        assert len(result["years_compared"]) == 1
        changes = result["faculty_changes"][("2022-23", "2023-24")]
        assert len(changes["added"]) == 2  # Prof. C and D
        assert len(changes["removed"]) == 1  # Prof. A
        assert changes["percent_changed"] == 150.0  # 3 changes out of 5 total
    
    def test_analyze_evaluation_changes(self, api_extractor):
        """Test evaluation method change analysis"""
        subject_data = {
            "2022-23": {
                "actividades_evaluacion": [
                    {"tipo": "Examen parcial"},
                    {"tipo": "Trabajo práctico"}
                ]
            },
            "2023-24": {
                "actividades_evaluacion": [
                    {"tipo": "Examen parcial"},
                    {"tipo": "Quiz online"},
                    {"tipo": "Presentación"}
                ]
            }
        }
        
        result = api_extractor.analyze_evaluation_changes(subject_data)
        
        assert len(result["years_compared"]) == 1
        changes = result["evaluation_changes"][("2022-23", "2023-24")]
        assert len(changes["added"]) == 2  # Quiz and Presentación
        assert len(changes["removed"]) == 1  # Trabajo práctico
        assert changes["changed"] == True


if __name__ == "__main__":
    pytest.main(["-v", __file__])