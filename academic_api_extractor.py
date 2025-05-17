import requests
import json
from urllib.parse import quote
import time
import os
from pathlib import Path
import pandas as pd

class AcademicApiExtractor:
    def __init__(self, base_url="https://www.upm.es/comun_gauss/publico/api"):
        self.base_url = base_url
        self.cache_dir = Path("api_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    def get_subject_api_data(self, academic_year, semester, plan_code, subject_code, force_refresh=False):

        # Asegurarse de que existe el directorio
        cache_path = self.cache_dir / f"{academic_year}_{semester}"
        cache_path.mkdir(exist_ok=True)
        
        # Probar si lo tenemos en cache
        file_path = cache_path / f"{plan_code}_{subject_code}.json"
        if file_path.exists() and not force_refresh:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                # Si falla la carga, vamos a hacer fetch
                pass
                
        # Construir URL
        url = f"{self.base_url}/{academic_year}/{semester}/{plan_code}_{subject_code}.json"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Que los errores HTTP salten excepcioness
            
            # Parsear JSON
            data = response.json()
            
            # Cachear la respuesta
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"datos escaneados exitosamente para la asignatura con codigo {subject_code} en el curso {academic_year}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"error escaneando datos para la asignatura de codigo {subject_code}: {e}")
            return None
    
    def fetch_multi_year_data(self, subjects, years_list, plan_code, semester="2S"):

        all_data = {}
        
        for subject_code in subjects:
            all_data[subject_code] = {}
            for year in years_list:
                time.sleep(0.5)  
                data = self.get_subject_api_data(year, semester, plan_code, subject_code)
                if data:
                    all_data[subject_code][year] = data
                    
        return all_data
    
    def analyze_faculty_changes(self, subject_data):

        years = sorted(subject_data.keys())
        result = {"years_compared": [], "faculty_changes": {}}
        
        # Se necesitan al menos dos años para comparar
        if len(years) < 2:
            return result
            
        for i in range(len(years) - 1):
            year1 = years[i]
            year2 = years[i+1]
            
            # Extraer listas de profes
            faculty1 = set()
            faculty2 = set()
            
            # Extraer nombres de profes del primer año
            if "profesores" in subject_data[year1]:
                for prof in subject_data[year1]["profesores"]:
                    if "nombre" in prof:
                        faculty1.add(prof["nombre"])
            
            # Extraer nombres de profes del segundo año
            if "profesores" in subject_data[year2]:
                for prof in subject_data[year2]["profesores"]:
                    if "nombre" in prof:
                        faculty2.add(prof["nombre"])
            
            # calcular diferencias
            added = faculty2 - faculty1
            removed = faculty1 - faculty2
            
            result["years_compared"].append((year1, year2))
            result["faculty_changes"][(year1, year2)] = {
                "added": list(added),
                "removed": list(removed),
                "total_added": len(added),
                "total_removed": len(removed),
                "percent_changed": (len(added) + len(removed)) / max(1, len(faculty1)) * 100
            }
            
        return result
    
    def analyze_evaluation_changes(self, subject_data):

        years = sorted(subject_data.keys())
        result = {"years_compared": [], "evaluation_changes": {}}
        
        # Necesitas al menos 2 años para comparar
        if len(years) < 2:
            return result
            
        for i in range(len(years) - 1):
            year1 = years[i]
            year2 = years[i+1]
            
            # Extraer metodos de evaluacion
            eval_methods1 = set()
            eval_methods2 = set()
            
            # Extraer metodos de evaluacion del año 1
            if "actividades_evaluacion" in subject_data[year1]:
                for eval_act in subject_data[year1]["actividades_evaluacion"]:
                    if "tipo" in eval_act:
                        eval_methods1.add(eval_act["tipo"])
            
            # 
            # Extraer metodos de evaluacion del año 2
            if "actividades_evaluacion" in subject_data[year2]:
                for eval_act in subject_data[year2]["actividades_evaluacion"]:
                    if "tipo" in eval_act:
                        eval_methods2.add(eval_act["tipo"])
            
            # Calcular diferencias
            added = eval_methods2 - eval_methods1
            removed = eval_methods1 - eval_methods2
            
            result["years_compared"].append((year1, year2))
            result["evaluation_changes"][(year1, year2)] = {
                "added": list(added),
                "removed": list(removed),
                "changed": len(added) > 0 or len(removed) > 0
            }
            
        return result
        
    def get_years_from_historical_data(self, historical_df):
        # Extraer cursos academicos unicos del dataframe historico
        if historical_df is not None and not historical_df.empty:
            return sorted(historical_df["academic_year"].unique())
        return []
    
    def format_year_for_api(self, academic_year):
        # Convertir el formato del curso academico de la db a formato de la API porque lo nesecita en fin
        # de"2021-22" a "2021-22"
        # Puede que necesite ajustes
        return academic_year

    def export_api_data_to_json(self, all_api_data, output_dir="output/api_data"):
        #este no se usa
        # Crear directorio de salida
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Exportar los datos de cada asignatura
        for subject_code, years_data in all_api_data.items():
            subject_dir = Path(output_dir) / subject_code
            subject_dir.mkdir(exist_ok=True)
            
            # Iterar sobre los años y guardar los datos
        #    for year, api_data in years_data.items():
        #        file_path = subject_dir / f"{year}.json"
        #        with open(file_path, 'w', encoding='utf-8') as f:
        #            json.dump(api_data, f, ensure_ascii=False, indent=2)
            
            # Crear un resumen de los datos con la info clave
            summary = {
                "subject_code": subject_code,
                "years": list(years_data.keys()),
                "faculty_by_year": {},
                "evaluation_methods_by_year": {}
            }
            
            for year, api_data in years_data.items():
                # Extraer nombres de profes del año
                faculty = []
                if "profesores" in api_data:
                    for prof in api_data["profesores"]:
                        if "nombre" in prof:
                            faculty.append(prof["nombre"])
                
                summary["faculty_by_year"][year] = faculty
                
                # Extraer metodos de evaluacion del año
                eval_methods = []
                if "actividades_evaluacion" in api_data:
                    for eval_act in api_data["actividades_evaluacion"]:
                        if "tipo" in eval_act:
                            eval_methods.append(eval_act["tipo"])
                
                summary["evaluation_methods_by_year"][year] = eval_methods
            
            # Guardar el resumen en un archivo JSON
            summary_path = subject_dir / "summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"Datos de la API exportados a JSON en {output_dir}")
        return True

    def export_analysis_results_to_json(self, analysis_results, output_dir="output/api_analysis"):
    # Exportar resultados de analisis a JSON

        # Crear directorio de salida
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Guardar los resultados completos del analisis
        with open(Path(output_dir) / "complete_analysis.json", 'w', encoding='utf-8') as f:
            # Convertir claves de tupla a cadenas string para la serializacion JSON
            serializable_results = {}
            
            for subject_code, subject_data in analysis_results.items():
                serializable_results[subject_code] = {
                    "subject_name": subject_data["subject_name"],
                    "faculty_analysis": {
                        "years_compared": subject_data["faculty_analysis"].get("years_compared", []),
                        "faculty_changes": {}
                    },
                    "evaluation_analysis": {
                        "years_compared": subject_data["evaluation_analysis"].get("years_compared", []),
                        "evaluation_changes": {}
                    }
                }
                
                # Convertir claves de tupla a cadenas de str
                for year_pair, change_data in subject_data["faculty_analysis"].get("faculty_changes", {}).items():
                    year_key = f"{year_pair[0]}_to_{year_pair[1]}"
                    serializable_results[subject_code]["faculty_analysis"]["faculty_changes"][year_key] = change_data
                
                for year_pair, change_data in subject_data["evaluation_analysis"].get("evaluation_changes", {}).items():
                    year_key = f"{year_pair[0]}_to_{year_pair[1]}"
                    serializable_results[subject_code]["evaluation_analysis"]["evaluation_changes"][year_key] = change_data
            
            from academic_data_extractor import NumpyEncoder
            json.dump(serializable_results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        print(f"Resultados del analisis de la API exportados a JSON en {output_dir}/complete_analysis.json")
        return True

    def analyze_all_subjects(self, historical_df, plan_code="10II", semester="2S"):

        if historical_df is None or historical_df.empty:
            return {}
            
        # Obtener asignaturas unicas y años
        subject_codes = historical_df["subject_code"].unique()
        years = self.get_years_from_historical_data(historical_df)
        
        # formatear años para la API
        api_years = [self.format_year_for_api(year) for year in years]
        
        # Hacer fetch de los datos de la API para todas las asignaturas y años
        all_api_data = self.fetch_multi_year_data(subject_codes, api_years, plan_code, semester)
        
        # Analizar cambios para cada asigntura
        results = {}
        for subject_code in subject_codes:
            subject_data = all_api_data.get(subject_code, {})
            
            if subject_data:
                subject_name = historical_df[historical_df["subject_code"] == subject_code]["subject_name"].iloc[0]
                
                results[subject_code] = {
                    "subject_name": subject_name,
                    "faculty_analysis": self.analyze_faculty_changes(subject_data),
                    "evaluation_analysis": self.analyze_evaluation_changes(subject_data)
                }
                
        return results