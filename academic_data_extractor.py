import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from pathlib import Path
import numpy as np
import json


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles NumPy types
    """
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

#Clase para extraer datos académicos de un informe de semestre
class AcademicDataExtractor:
    
    def __init__(self, text_content):
        self.text_content = text_content
        self.courses_data = {}
        self.years_data = {}
        
    def extract_course_info(self):
        #Extraer información básica del curso
        course_info = {}
        
        # Extraer el año académico y el semestre
        academic_year_match = re.search(r'(\d{4}/\d{2})\s*-\s*([^\n]+)\s*Semestre', self.text_content)
        if academic_year_match:
            course_info['academic_year'] = academic_year_match.group(1)
            course_info['semester'] = academic_year_match.group(2)
        
        #Extraer el plan de estudios y el título
        plan_match = re.search(r'PLAN DE ESTUDIOS\s*\n([^\n]+)\s*-\s*([^\n]+)', self.text_content)
        if plan_match:
            course_info['plan_code'] = plan_match.group(1).strip()
            course_info['plan_title'] = plan_match.group(2).strip()
            
        return course_info
    
    def extract_subjects_basic_info(self):
        # Extraer información básica de las asignaturas
        subjects = {}
        
        # Encontrar la sección de matriculados
        matriculated_section = re.search(r'A1\.1\. Matriculados(.*?)A1\.2\.', self.text_content, re.DOTALL)
        if matriculated_section:
            section_text = matriculated_section.group(1)
            #Extraer el código de la asignatura, nombre, créditos y matriculados
            subject_pattern = r'(\d{9})\s*-\s*([^\n\d]+?)\s+(\d+)\s+(\d+)'
            for match in re.finditer(subject_pattern, section_text):
                subject_code = match.group(1)
                subject_name = match.group(2).strip()
                credits = match.group(3)
                enrolled = match.group(4)
                
                subjects[subject_code] = {
                    'code': subject_code,
                    'name': subject_name,
                    'credits': int(credits),
                    'enrolled': int(enrolled)
                }
                
        return subjects
    
    def extract_student_profile(self):
        #Extraer la seccion del perfil de los alumnos
        profile_section = re.search(r'A1\.2\. Perfil de los alumnos matriculados(.*?)ANEXO 2', self.text_content, re.DOTALL)
        if profile_section:
            section_text = profile_section.group(1)
            
            #Procesar cada asignatura
            for subject_code in self.courses_data:
                if subject_code in self.courses_data:
                    #Intentar encontrar la asignatura en la sección del perfil
                    pattern = rf'{subject_code}\s*-\s*{re.escape(self.courses_data[subject_code]["name"])}\s*(\d+)\s*(\d+)\s*(\d+)'
                    match = re.search(pattern, section_text)
                    if match:
                        self.courses_data[subject_code]["total_enrolled"] = int(match.group(1))
                        self.courses_data[subject_code]["first_time"] = int(match.group(2))
                        self.courses_data[subject_code]["partial_dedication"] = int(match.group(3))
    
    def extract_performance_rates(self):
        #Extraer la sección de tasas de rendimiento para el año actual

        #Encontrar la sección de tasas de rendimiento
        rates_section = re.search(r'A2\.1\. Tasas de resultados académicos obtenidas en el curso objeto del Informe(.*?)A2\.2\. Tasas de resultados académicos obtenidas en cursos anteriores', self.text_content, re.DOTALL)
        if rates_section:
            section_text = rates_section.group(1)
            
            #expresion regular para extraer tasas de rendimiento
            pattern = r'(\d{9})\s*-\s*([^\n]+)\s*(\d+\.\d+)\s*(\d+\.\d+)\s*(\d+\.\d+)'
            
            for match in re.finditer(pattern, section_text):
                subject_code = match.group(1)
                subject_name = match.group(2).strip()
                performance_rate = float(match.group(3))
                success_rate = float(match.group(4))
                absenteeism_rate = float(match.group(5))
                
                if subject_code in self.courses_data:
                    self.courses_data[subject_code]["performance_rate"] = performance_rate
                    self.courses_data[subject_code]["success_rate"] = success_rate
                    self.courses_data[subject_code]["absenteeism_rate"] = absenteeism_rate
    
    def extract_historical_rates(self):
        #Extraer la sección de tasas de rendimiento para años anteriores

        #Encontrar la sección de tasas de rendimiento historicas
        for rate_type in ["rendimiento", "éxito", "absentismo"]:
            section_pattern = rf'A2\.2\.\d Tasa de {rate_type}(.*?)(?:A2\.2\.\d|A2\.3\.)'
            section_match = re.search(section_pattern, self.text_content, re.DOTALL)
            
            if section_match:
                section_text = section_match.group(1)
                
                #Extraer los años
                years_pattern = r'(\d{4}-\d{2})'
                years = re.findall(years_pattern, section_text)
                
                #Extraer datos para cada asignatura
                for subject_code in self.courses_data:
                    subject_name = self.courses_data[subject_code]["name"]
                    pattern = rf'{subject_code}\s*-\s*{re.escape(subject_name)}\s*([\d\.]+)\s*([\d\.]+)\s*([\d\.]+)\s*([\d\.]+)'
                    match = re.search(pattern, section_text)
                    
                    if match:
                        if "historical" not in self.courses_data[subject_code]:
                            self.courses_data[subject_code]["historical"] = {}
                        
                        if rate_type not in self.courses_data[subject_code]["historical"]:
                            self.courses_data[subject_code]["historical"][rate_type] = {}
                        
                        for i, year in enumerate(years):
                            if i+1 <= len(match.groups()):
                                try:
                                    value = float(match.group(i+1))
                                    self.courses_data[subject_code]["historical"][rate_type][year] = value
                                except:
                                    pass
    
    def extract_all_data(self):
        #Extraer todo el contenido del informe

        course_info = self.extract_course_info()
        self.courses_data = self.extract_subjects_basic_info()
        self.extract_student_profile()
        self.extract_performance_rates()
        self.extract_historical_rates()
        
        return {
            "course_info": course_info,
            "subjects": self.courses_data
        }


class AcademicDataAnalyzer:
    # Clase para analizar datos académicos y generar visualizaciones
    
    def __init__(self, data):
        self.data = data
        self.course_info = data.get("course_info", {})
        self.subjects = data.get("subjects", {})
        
    def convert_to_dataframe(self):
        # Esto convierte los datos de las asignaturas a un DataFrame
        subjects_df = pd.DataFrame(self.subjects).T.reset_index(drop=True)
        return subjects_df
    
    def historical_rates_to_dataframe(self):
        # Convertir los datos históricos a un formato largo de df
        data_rows = []
        
        for subject_code, subject_data in self.subjects.items():
            if "historical" in subject_data:
                for rate_type, years_data in subject_data["historical"].items():
                    for year, value in years_data.items():
                        data_rows.append({
                            "subject_code": subject_code,
                            "subject_name": subject_data["name"],
                            "rate_type": rate_type,
                            "year": year,
                            "value": value
                        })
        
        if data_rows:
            return pd.DataFrame(data_rows)
        return pd.DataFrame()
    
    def plot_current_performance_rates(self, output_dir="output"):
        # Grafos de rendimiento actual para todas las asignaturas
        os.makedirs(output_dir, exist_ok=True)
        
        df = self.convert_to_dataframe()
        
        if df.empty:
            print("No hay datos disponibles para crear grafos de tasas de rendimiento.")
            return
        
        # Tasas de rendimiento, éxito y absentismo
        rate_columns = ["performance_rate", "success_rate", "absenteeism_rate"]
        for col in rate_columns:
            if col in df.columns:
                plt.figure(figsize=(12, 6))
                sns.barplot(x="name", y=col, data=df)
                plt.title(f"{col.replace('_', ' ').title()} por Asignatura")
                plt.xlabel("Asignatura")
                plt.ylabel(f"{col.replace('_', ' ').title()} (%)")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                plt.savefig(f"{output_dir}/{col}_by_subject.png")
                plt.close()
    
    def plot_historical_trends(self, output_dir="output"):
        # graficos de tendencias historicas por tasa
        os.makedirs(output_dir, exist_ok=True)
        
        df = self.historical_rates_to_dataframe()
        
        if df.empty:
            print("No hay datos historicos disponibles para exponer tendencias.")
            return
        
        # Grafico de tendencias por asignatura y tipo de tasa
        for subject_code in df["subject_code"].unique():
            subject_df = df[df["subject_code"] == subject_code]
            subject_name = subject_df["subject_name"].iloc[0]
            
            plt.figure(figsize=(12, 6))
            
            for rate_type in subject_df["rate_type"].unique():
                rate_df = subject_df[subject_df["rate_type"] == rate_type]
                plt.plot(rate_df["year"], rate_df["value"], marker='o', label=rate_type)
            
            plt.title(f"Historico de tasas para {subject_name}")
            plt.xlabel("Curso")
            plt.ylabel("Tasa (%)")
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/historical_trends_{subject_code}.png")
            plt.close()
    
    def compare_subjects(self, output_dir="output"):
        # Comparar asignaturas en base a matriculados y tasas de rendimiento
        os.makedirs(output_dir, exist_ok=True)
        
        df = self.convert_to_dataframe()
        
        if df.empty or len(df) < 2:
            print("No hay datos suficientes parwa comparar asignaturas.")
            return
        
        # Compare enrollment numbers
        plt.figure(figsize=(12, 6))
        sns.barplot(x="name", y="enrolled", data=df)
        plt.title("Nº Estudiantes matriculados por asignatura")
        plt.xlabel("Asignatura")
        plt.ylabel("Nº Estudiantes")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/enrolled_comparison.png")
        plt.close()
        
        # Compare first-time enrollment
        if "first_time" in df.columns:
            plt.figure(figsize=(12, 6))
            df["first_time_percentage"] = (df["first_time"] / df["total_enrolled"]) * 100
            sns.barplot(x="name", y="first_time_percentage", data=df)
            plt.title("Percentage of First-Time Students by Subject")
            plt.xlabel("Subject")
            plt.ylabel("Percentage (%)")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(f"{output_dir}/first_time_comparison.png")
            plt.close()
    
    def generate_summary_report(self, output_dir="output"):
        # Generar un informe resumen con analisis 
        os.makedirs(output_dir, exist_ok=True)
        
        df = self.convert_to_dataframe()
        hist_df = self.historical_rates_to_dataframe()
        
        if df.empty:
            print("No hay datos disponibles para el informe.")
            return
        
        with open(f"{output_dir}/summary_report.txt", "w") as f:
            f.write(f"INFORME ACADEMICO RESUMIDO\n")
            f.write(f"======================\n\n")
            
            f.write(f"Curso academico: {self.course_info.get('academic_year', 'N/A')}\n")
            f.write(f"Semestre: {self.course_info.get('semester', 'N/A')}\n")
            f.write(f"Plan de estudios: {self.course_info.get('plan_title', 'N/A')}\n\n")
            
            f.write(f"ESTADISTICAS DE MATRICULACION\n")
            f.write(f"--------------------\n")
            total_enrolled = df["enrolled"].sum()
            f.write(f"Numero total de estudiantes matriculados en todas las asignaturas: {total_enrolled}\n")
            f.write(f"Media de estudiantes matriculados por asignatura: {df['enrolled'].mean():.2f}\n")
            f.write(f"Asignatura con mayor numero de matriculados: {df.loc[df['enrolled'].idxmax(), 'name']} ({df['enrolled'].max()} estudiantes)\n")
            f.write(f"Asignatura con menor numero de matriculados: {df.loc[df['enrolled'].idxmin(), 'name']} ({df['enrolled'].min()} estudiantes)\n\n")
            
            if "performance_rate" in df.columns:
                f.write(f"METRICAS DE RENDIMIENTO\n")
                f.write(f"------------------\n")
                f.write(f"Tasa media de rendimiento : {df['performance_rate'].mean():.2f}%\n")
                f.write(f"Tasa media de éxito: {df['success_rate'].mean():.2f}%\n")
                f.write(f"Tasa media de absentismo: {df['absenteeism_rate'].mean():.2f}%\n\n")
                
                f.write(f"Asignatura con mayor tasa de rendimiento: {df.loc[df['performance_rate'].idxmax(), 'name']} ({df['performance_rate'].max():.2f}%)\n")
                f.write(f"Tasa con menor tasa de rendimiento: {df.loc[df['performance_rate'].idxmin(), 'name']} ({df['performance_rate'].min():.2f}%)\n\n")
                
                f.write(f"Asignatura con mayor tasa de exito: {df.loc[df['success_rate'].idxmax(), 'name']} ({df['success_rate'].max():.2f}%)\n")
                f.write(f"Asignatura con menor tasa de exito: {df.loc[df['success_rate'].idxmin(), 'name']} ({df['success_rate'].min():.2f}%)\n\n")
                
                f.write(f"Asignatura con mayor tasa de absentismo: {df.loc[df['absenteeism_rate'].idxmax(), 'name']} ({df['absenteeism_rate'].max():.2f}%)\n")
                f.write(f"Asignatura con menor tasa de absentismo: {df.loc[df['absenteeism_rate'].idxmin(), 'name']} ({df['absenteeism_rate'].min():.2f}%)\n\n")
            
            # ANALISIS DE TENDENCIA HISTORICA
            if not hist_df.empty:
                f.write(f"ANALISIS DE TENDENCIA HISTORICA\n")
                f.write(f"-------------------------\n")
                
                for subject_code in hist_df["subject_code"].unique():
                    subject_df = hist_df[hist_df["subject_code"] == subject_code]
                    subject_name = subject_df["subject_name"].iloc[0]
                    
                    f.write(f"\nSubject: {subject_name}\n")
                    
                    for rate_type in subject_df["rate_type"].unique():
                        rate_df = subject_df[subject_df["rate_type"] == rate_type]
                        
                        if len(rate_df) >= 2:
                            # Comprobar si esta mejorando o empeorando
                            values = rate_df.sort_values("year")["value"].tolist()
                            if len(values) >= 2:
                                last_value = values[-1]
                                first_value = values[0]
                                trend = "mejorado" if last_value > first_value else "empeorado" if last_value < first_value else "mantenido estable"
                                change = abs(last_value - first_value)
                                
                                f.write(f"  - Tasa de {rate_type}  ha {trend} por {change:.2f} puntos de {first_value:.2f}% a {last_value:.2f}%\n")
            
            f.write("\CONCLUSIONES\n")
            f.write("----------\n")
            
            # Add some general conclusions
            if "performance_rate" in df.columns:
                above_avg_perf = df[df["performance_rate"] > df["performance_rate"].mean()]
                below_avg_perf = df[df["performance_rate"] < df["performance_rate"].mean()]
                
                f.write(f"Asignaturas con tasas de rendimientos superiores a la media: {', '.join(above_avg_perf['name'].tolist())}\n")
                f.write(f"Asignaturas con tasas de rendimientos inferiores a la media: {', '.join(below_avg_perf['name'].tolist())}\n\n")
            
            if "absenteeism_rate" in df.columns:
                high_absence = df[df["absenteeism_rate"] > 10]
                if not high_absence.empty:
                    f.write(f"asignaturas con tasas de absentismo preocupantes (>10%): {', '.join(high_absence['name'].tolist())}\n\n")
            

            if not hist_df.empty:
                # Identificar asignaturas con mejora o empeoramiento significativo
                improved_subjects = []
                declined_subjects = []
                
                for subject_code in hist_df["subject_code"].unique():
                    subject_df = hist_df[(hist_df["subject_code"] == subject_code) & (hist_df["rate_type"] == "rendimiento")]
                    
                    if len(subject_df) >= 2:
                        values = subject_df.sort_values("year")["value"].tolist()
                        if len(values) >= 2:
                            last_value = values[-1]
                            first_value = values[0]
                            subject_name = hist_df[hist_df["subject_code"] == subject_code]["subject_name"].iloc[0]
                            
                            if last_value - first_value > 5:
                                improved_subjects.append(subject_name)
                            elif first_value - last_value > 5:
                                declined_subjects.append(subject_name)
                
                if improved_subjects:
                    f.write(f"Asignaturas que muestran una mejora significativa en el tiempo: {', '.join(improved_subjects)}\n")
                
                if declined_subjects:
                    f.write(f"Asignaturas que muestran un empeoramiento significativo en el tiempo: {', '.join(declined_subjects)}\n")
    
    def run_complete_analysis(self, output_dir="output"):
        # Ejecutar todos los metodos de analisis y generar graficos
        os.makedirs(output_dir, exist_ok=True)
        
        print("Generando la sección de tasas de rendimiento actuales...")
        self.plot_current_performance_rates(output_dir)
        
        print("Generando la sección de tasas de rendimiento historicas...")
        self.plot_historical_trends(output_dir)
        
        print("Generando la comparativa de asignaturas...")
        self.compare_subjects(output_dir)
        
        print("Generando el informe de resumen...")
        self.generate_summary_report(output_dir)
        
        print("Analisis completado. Resultados almacenados en:", output_dir)
        
    def correlate_api_changes_with_performance(self, api_analysis_results, output_dir="output"):
        

        if not hasattr(self, 'historical_df') or self.historical_df is None:
            self.historical_df = self.historical_rates_to_dataframe()
            
        if self.historical_df.empty:
            print("No hay datos historicos disponibles para analizar la correlacion")
            return pd.DataFrame()
            
        # Crear informe de la correlacion
        correlations = []
        
        for subject_code, analysis in api_analysis_results.items():
            subject_name = analysis["subject_name"]
            faculty_analysis = analysis["faculty_analysis"]
            evaluation_analysis = analysis["evaluation_analysis"]
            
            # Obtener cambios en la tasa de rendimiento para esta asignatura
            perf_data = self.historical_df[(self.historical_df["subject_code"] == subject_code) & 
                                        (self.historical_df["rate_type"] == "rendimiento")]
            
            # organizar por año
            perf_data = perf_data.sort_values("academic_year")
            
            # por cada par de años consecutivos
            for i in range(len(perf_data) - 1):
                year1 = perf_data.iloc[i]["academic_year"]
                year2 = perf_data.iloc[i + 1]["academic_year"]
                
                perf1 = perf_data.iloc[i]["value"]
                perf2 = perf_data.iloc[i + 1]["value"]
                
                perf_change = perf2 - perf1
                
                # Comprobar si tenemos cambios en profesores por el par de años
                faculty_change_info = None
                for j, (y1, y2) in enumerate(faculty_analysis.get("years_compared", [])):
                    if y1 == year1 and y2 == year2:
                        faculty_change_info = faculty_analysis["faculty_changes"].get((y1, y2))
                        break
                
                # comprobar si tenemos cambios en los metodos de evaluacion por el par de años
                eval_change_info = None
                for j, (y1, y2) in enumerate(evaluation_analysis.get("years_compared", [])):
                    if y1 == year1 and y2 == year2:
                        eval_change_info = evaluation_analysis["evaluation_changes"].get((y1, y2))
                        break
                        
                # Crear la entrada de la correlacion
                correlation = {
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "year1": year1,
                    "year2": year2,
                    "performance_change": perf_change,
                    "faculty_changed": faculty_change_info is not None and (
                        faculty_change_info.get("total_added", 0) > 0 or 
                        faculty_change_info.get("total_removed", 0) > 0
                    ),
                    "faculty_percent_changed": faculty_change_info.get("percent_changed", 0) if faculty_change_info else 0,
                    "evaluation_changed": eval_change_info is not None and eval_change_info.get("changed", False),
                    "faculty_added": faculty_change_info.get("total_added", 0) if faculty_change_info else 0,
                    "faculty_removed": faculty_change_info.get("total_removed", 0) if faculty_change_info else 0,
                    "evaluation_methods_added": len(eval_change_info.get("added", [])) if eval_change_info else 0,
                    "evaluation_methods_removed": len(eval_change_info.get("removed", [])) if eval_change_info else 0,
                }
                
                correlations.append(correlation)
        
        # crear el dataframe de la correlacion
        correlation_df = pd.DataFrame(correlations)
        
        # guardar a CSV
        if not correlation_df.empty:
            correlation_df.to_csv(f"{output_dir}/performance_faculty_correlations.csv", index=False)
            
        return correlation_df

    def export_correlation_to_json(self, correlation_df, output_dir="output"):

        if correlation_df.empty:
            print("No hay datos de correlacion disponibles para exportar")
            return False
        
        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)
        
        # Exportar a CSV
       # csv_path = os.path.join(output_dir, "performance_faculty_correlations.csv")
       # correlation_df.to_csv(csv_path, index=False)
        
        # Exportar a JSON
        json_path = os.path.join(output_dir, "performance_faculty_correlations.json")
        
        # Agrupar por asignatura
        json_data = {}
        
        for subject_code in correlation_df["subject_code"].unique():
            subject_df = correlation_df[correlation_df["subject_code"] == subject_code]
            subject_name = subject_df.iloc[0]["subject_name"]
            
            subject_data = {
                "subject_name": subject_name,
                "periods": []
            }
            
            for _, row in subject_df.iterrows():
                period = {
                    "year1": row["year1"],
                    "year2": row["year2"],
                    "performance_change": float(row["performance_change"]),
                    "faculty_changed": bool(row["faculty_changed"]),
                    "faculty_percent_changed": float(row["faculty_percent_changed"]),
                    "faculty_added": int(row["faculty_added"]),
                    "faculty_removed": int(row["faculty_removed"]),
                    "evaluation_changed": bool(row["evaluation_changed"]),
                    "evaluation_methods_added": int(row["evaluation_methods_added"]),
                    "evaluation_methods_removed": int(row["evaluation_methods_removed"])
                }
                subject_data["periods"].append(period)
            
            # Calcular estadisticas resumen
            subject_data["summary"] = {
                "avg_performance_change": float(subject_df["performance_change"].mean()),
                "total_periods_with_faculty_changes": int(subject_df["faculty_changed"].sum()),
                "total_periods_with_evaluation_changes": int(subject_df["evaluation_changed"].sum()),
                "performance_change_with_faculty_changes": float(subject_df[subject_df["faculty_changed"]]["performance_change"].mean()) 
                    if subject_df["faculty_changed"].sum() > 0 else None,
                "performance_change_without_faculty_changes": float(subject_df[~subject_df["faculty_changed"]]["performance_change"].mean()) 
                    if (~subject_df["faculty_changed"]).sum() > 0 else None,
                "performance_change_with_evaluation_changes": float(subject_df[subject_df["evaluation_changed"]]["performance_change"].mean()) 
                    if subject_df["evaluation_changed"].sum() > 0 else None,
                "performance_change_without_evaluation_changes": float(subject_df[~subject_df["evaluation_changed"]]["performance_change"].mean()) 
                    if (~subject_df["evaluation_changed"]).sum() > 0 else None
            }
            
            json_data[subject_code] = subject_data
        
        # Añadir estadisticas globales
        json_data["global_stats"] = {
            "num_subjects": int(len(correlation_df["subject_code"].unique())),
            "total_periods_analyzed": int(len(correlation_df)),
            "avg_performance_change_overall": float(correlation_df["performance_change"].mean()),
            "avg_performance_change_with_faculty_changes": float(correlation_df[correlation_df["faculty_changed"]]["performance_change"].mean()) 
                if correlation_df["faculty_changed"].sum() > 0 else None,
            "avg_performance_change_without_faculty_changes": float(correlation_df[~correlation_df["faculty_changed"]]["performance_change"].mean())
                if (~correlation_df["faculty_changed"]).sum() > 0 else None,
            "avg_performance_change_with_evaluation_changes": float(correlation_df[correlation_df["evaluation_changed"]]["performance_change"].mean()) 
                if correlation_df["evaluation_changed"].sum() > 0 else None,
            "avg_performance_change_without_evaluation_changes": float(correlation_df[~correlation_df["evaluation_changed"]]["performance_change"].mean()) 
                if (~correlation_df["evaluation_changed"]).sum() > 0 else None
        }
        
        # Escribir archivo JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        #print(f"Datos de correlacion exportados a CSV: {csv_path}")
        print(f"Datos de correlacion exportados a JSON: {json_path}")
        
        return True

    def export_enhanced_insights_to_json(self, api_results, correlation_df, output_dir="output"):

        if correlation_df.empty:
            print("No hay datos de correlación disponibles para la exportación de analisis")
            return False
        
        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)
        
        insights = {
            "subject_insights": {},
            "global_insights": {
                "faculty_impact": {},
                "evaluation_impact": {},
                "recommendations": {}
            }
        }
        
        # Procesar cada asignatura
        for subject_code in correlation_df["subject_code"].unique():
            subject_df = correlation_df[correlation_df["subject_code"] == subject_code]
            subject_name = subject_df.iloc[0]["subject_name"]
            
            # Calcular el cambio medio de rendimiento
            avg_perf_change = float(subject_df["performance_change"].mean())
            direction = "improving" if avg_perf_change > 0 else "declining" if avg_perf_change < 0 else "stable"
            
            # Obtener el impacto del profesorado
            faculty_impact = None
            if subject_df["faculty_changed"].sum() > 0:
                perf_with_changes = float(subject_df[subject_df["faculty_changed"]]["performance_change"].mean())
                perf_without_changes = None
                
                if (~subject_df["faculty_changed"]).sum() > 0:
                    perf_without_changes = float(subject_df[~subject_df["faculty_changed"]]["performance_change"].mean())
                    
                faculty_impact = {
                    "periods_with_changes": int(subject_df["faculty_changed"].sum()),
                    "performance_with_changes": perf_with_changes,
                    "performance_without_changes": perf_without_changes,
                    "impact_direction": "positive" if perf_with_changes > 0 else "negative" if perf_with_changes < 0 else "neutral"
                }
            
            # obtener el impacto de la evaluacion
            eval_impact = None
            if subject_df["evaluation_changed"].sum() > 0:
                perf_with_changes = subject_df[subject_df["evaluation_changed"]]["performance_change"].mean()
                
                eval_impact = {
                    "periods_with_changes": int(subject_df["evaluation_changed"].sum()),
                    "performance_with_changes": perf_with_changes,
                    "impact_direction": "positive" if perf_with_changes > 0 else "negative" if perf_with_changes < 0 else "neutral"
                }
            
            # Construir insights en asignaturas
            subject_insights = {
                "subject_name": subject_name,
                "average_performance_change": avg_perf_change,
                "trend_direction": direction,
                "periods_analyzed": int(len(subject_df)),
                "faculty_impact": faculty_impact,
                "evaluation_impact": eval_impact,
                "periods": []
            }
            
            # Añadir insights por cada periodo
            for _, row in subject_df.iterrows():
                period_insight = {
                    "year1": row["year1"],
                    "year2": row["year2"],
                    "performance_change": row["performance_change"],
                    "faculty_changed": bool(row["faculty_changed"]),
                    "faculty_details": {
                        "percent_changed": row["faculty_percent_changed"],
                        "added": row["faculty_added"],
                        "removed": row["faculty_removed"]
                    } if row["faculty_changed"] else None,
                    "evaluation_changed": bool(row["evaluation_changed"]),
                    "evaluation_details": {
                        "methods_added": row["evaluation_methods_added"],
                        "methods_removed": row["evaluation_methods_removed"]
                    } if row["evaluation_changed"] else None,
                    "insights": []
                }
                
                # Añadir analisis de tendencias especificos basados en patrones de datos
                insights_list = []
                
                # Analisis en el profesorado
                if row["faculty_changed"] and row["performance_change"] > 2 and row["faculty_percent_changed"] > 20:
                    insights_list.append({
                        "type": "faculty_positive",
                        "text": "La mejora significativa del rendimiento podría estar relacionada con cambios en el profesorado"
                    })
                elif row["faculty_changed"] and row["performance_change"] < -2 and row["faculty_percent_changed"] > 20:
                    insights_list.append({
                        "type": "faculty_negative",
                        "text": "El descenso del rendimiento podría estar relacionado con los cambios en el profesorado"
                    })
                elif not row["faculty_changed"] and abs(row["performance_change"]) > 5:
                    insights_list.append({
                        "type": "non_faculty",
                        "text": "Se ha producido un cambio significativo en el rendimiento sin cambios en el profesorado"
                    })
                
                # Analisis en la evalua
                if row["evaluation_changed"] and row["performance_change"] > 2:
                    insights_list.append({
                        "type": "evaluation_positive",
                        "text": "Los cambios en el método de evaluación podrían haber contribuido a mejorar los resultados"
                    })
                
                period_insight["insights"] = insights_list
                subject_insights["periods"].append(period_insight)
            
            insights["subject_insights"][subject_code] = subject_insights
        
        # Procesar impacto global
        # analisis del impacto del profesorado
        faculty_changed = correlation_df[correlation_df["faculty_changed"]]["performance_change"].mean()
        faculty_stable = correlation_df[~correlation_df["faculty_changed"]]["performance_change"].mean()
        
        faculty_impact_type = "neutral"
        if abs(faculty_changed - faculty_stable) > 2:
            faculty_impact_type = "positive" if faculty_changed > faculty_stable else "negative"
        
        insights["global_insights"]["faculty_impact"] = {
            "with_changes": faculty_changed,
            "without_changes": faculty_stable,
            "difference": faculty_changed - faculty_stable,
            "impact_type": faculty_impact_type,
            "insight": "Los cambios en el profesorado se asocian a mejoras en el rendimiento" if faculty_impact_type == "positive" else 
                    "La estabilidad del profesorado se asocia a un mejor rendimiento" if faculty_impact_type == "negative" else
                    "Los cambios en el profesorado no repercuten claramente en el rendimiento"
        }
        
        # Analisis del impacto en la evaluacion
        eval_changed = correlation_df[correlation_df["evaluation_changed"]]["performance_change"].mean()
        eval_stable = correlation_df[~correlation_df["evaluation_changed"]]["performance_change"].mean()
        
        eval_impact_type = "neutral"
        if abs(eval_changed - eval_stable) > 2:
            eval_impact_type = "positive" if eval_changed > eval_stable else "negative"
        
        insights["global_insights"]["evaluation_impact"] = {
            "with_changes": eval_changed,
            "without_changes": eval_stable,
            "difference": eval_changed - eval_stable,
            "impact_type": eval_impact_type,
            "insight": "Los cambios en los métodos de evaluación se asocian a mejoras en los resultados" if eval_impact_type == "positive" else 
                    "Los métodos de evaluación estables se asocian a mejores resultados" if eval_impact_type == "negative" else
                    "Los cambios en el método de evaluación no tienen un impacto claro en los resultados"
        }
        
        # Formato de las recomendaciones
        recommendations = {
            "faculty": [],
            "evaluation": [],
            "general": [
                "Establecer un sistema de seguimiento continuo de calidad que correlacione los cambios en el profesorado, la evaluación y los contenidos con los resultados académicos.",
                "Realizar encuestas a los estudiantes para identificar factores cualitativos de éxito o fracaso.",
                "Desarrollar un programa de intervención precoz para los sujetos que muestren tendencias negativas."
            ]
        }
        
        # Recomendaciones en el profesorado
        if faculty_impact_type == "positive":
            recommendations["faculty"] = [
                "Proseguir la renovación estratégica del profesorado en las asignaturas de bajo rendimiento",
                "Identificar y reproducir prácticas del nuevo profesorado en asignaturas de alto rendimiento",
                "Facilitar la integración del nuevo profesorado con programas de tutoría y formación"
            ]
        else:
            recommendations["faculty"] = [
                "Reforzar la continuidad del profesorado, especialmente en asignaturas clave",
                "Implantar programas de actualización pedagógica para el profesorado actual",
                "Establecer equipos docentes estables con responsabilidades a largo plazo"
            ]
        
        # Recomendaciones en la evaluacion
        if eval_impact_type == "positive":
            recommendations["evaluation"] = [
                "Promover la innovación en los métodos de evaluación, especialmente en las asignaturas con rendimiento estancado.",
                "Documentar y compartir los métodos de evaluación que han dado buenos resultados en todas las asignaturas",
                "Establecer un programa de mejora continua para la evaluación basada en los resultados académicos"
            ]
        else:
            recommendations["evaluation"] = [
                "Normalizar los métodos de evaluación más eficaces y mantener la coherencia",
                "Introducir cambios graduales en la evaluación con procesos de transición claros",
                "Comunicar claramente los criterios y métodos de evaluación a los estudiantes al inicio del curso."
            ]
        
        insights["global_insights"]["recommendations"] = recommendations
        
        # Escribir archivo JSON
        json_path = os.path.join(output_dir, "enhanced_insights.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        print(f"Analisis mejorado exportado a JSON en: {json_path}")
        
        return insights

    def run_api_integrated_analysis(self, output_dir="output", plan_code="10II", db_path="academic_data.db"):

            # eJECUTAR ANALISIS INTEGRADO DE LA API primero
            #print("Ejecutando analisis estandar...")
            #self.run_complete_analysis(output_dir)
            
            # Ejecutar analisis de la API
            print("Analizando datos de la API...")
            from academic_api_extractor import AcademicApiExtractor
            api_extractor = AcademicApiExtractor()
            
            if not hasattr(self, 'historical_df'):
                self.historical_df = self.historical_rates_to_dataframe()
            
            print("Escaneando datos de la API de la UPM...")
            api_data = {}
            api_results = {}
            
            # Comprobar is hay datos historicos disponibles
            if not self.historical_df.empty:
                # Obtener codigos de asignaturas unicos
                subject_codes = self.historical_df["subject_code"].unique()
                
                # Obtener años unicos de los datos historicos
                years = sorted(self.historical_df["academic_year"].unique())
                
                # Formatear años para la API
                api_years = [api_extractor.format_year_for_api(year) for year in years]
                
                # Obtener datos de la API para todas las asignaturas y años
                print(f"Obteniendo datos de la API de {len(subject_codes)} asignaturas en {len(api_years)} cursos ...")
                api_data = api_extractor.fetch_multi_year_data(subject_codes, api_years, plan_code)
                
                # Exportar datos de la API a JSON
                #print("Exportando datos basicos de la API a JSON...")
                #api_extractor.export_api_data_to_json(api_data, os.path.join(output_dir, "api_data"))
                

                # Analizar los cambios en cada asignatura
                print("Analizando datos de la API por cambios...")
                api_results = api_extractor.analyze_all_subjects(self.historical_df, plan_code)
                
                # Exportar resultados de analisis de la API a JSON
                print("Exportando resultados del analisis de la API a JSON...")
                api_extractor.export_analysis_results_to_json(api_results, os.path.join(output_dir, "api_analysis"))
            else:
                print("No hay datos historicos disponibles para analisis de la API")
                return
        
            #api_results = api_extractor.analyze_all_subjects(self.historical_df, plan_code)
            
            # Correlacionar los datos API con rendimiento
            print("Correlacionando cambios en la API con metricas de rendimiento...")
            correlation_df = self.correlate_api_changes_with_performance(api_results, output_dir)
            
            # Export correlacion a JSON
            print("Exportando datos de correlacion a JSON...")
            self.export_correlation_to_json(correlation_df, output_dir)

            # Generar informe de analisis mejorado
            print("Generando informe de analisis mejorado...")
            self.generate_enhanced_insights_report(api_results, correlation_df, output_dir)

            #print("Exportando analisis completos a JSON...")
            #self.export_enhanced_insights_to_json(api_results, correlation_df, output_dir)
 
            # Exportar analisis mejorados a JSON
            print("Exportando analisis mejorados a JSON...")
            enhanced_insights = self.export_enhanced_insights_to_json(api_results, correlation_df, output_dir)
    
            # Almacenar analisis en la base de datos si se solicita
            
            print("Almacenando el analisis de la API en la base de datos...")
            from academic_database import AcademicDatabase
            db = AcademicDatabase(db_path)
            analysis_id = db.add_api_analysis(api_data, api_results, correlation_df, enhanced_insights)
            api_output_dir = os.path.join(output_dir, "api_analysis")
            db.export_api_analysis_to_json(api_output_dir)
            if analysis_id:
                print(f"Analisis de la API almacenado en BD ")
            db.close()



            

            # Crear graficas de analisis con API
            print("Creando graficas de analisis de la API...")
            from academic_visualizations import AcademicVisualizer
            visualizer = AcademicVisualizer(output_dir=os.path.join(output_dir, "visualizations"))
            visualizer.create_api_insight_visualizations(correlation_df, self.historical_df)
            
    def generate_enhanced_insights_report(self, api_results, correlation_df, output_dir="output"):
        # Generar un informe de analisis mejorado
        # al final api_results no lo uso
            if correlation_df.empty:
                print("No correlation data available for enhanced report")
                return
                
            with open(f"{output_dir}/enhanced_insights_report.txt", "w", encoding='utf-8') as f:
                f.write("INFORME MEJORADO DE INSIGHTS ACADÉMICOS\n")
                f.write("=====================================\n\n")
                
                f.write("CORRELACIONES ENTRE CAMBIOS EN PROFESORADO Y RENDIMIENTO\n")
                f.write("-----------------------------------------------------\n\n")
                
                # Agrupar por asignatura
                for subject_code in correlation_df["subject_code"].unique():
                    subject_df = correlation_df[correlation_df["subject_code"] == subject_code]
                    subject_name = subject_df.iloc[0]["subject_name"]
                    
                    f.write(f"Asignatura: {subject_name} ({subject_code})\n")
                    f.write("-" * (len(subject_name) + len(subject_code) + 14) + "\n\n")
                    
                    # Analizar la transicion de cada año
                    for _, row in subject_df.iterrows():
                        f.write(f"Periodo {row['year1']} a {row['year2']}:\n")
                        
                        perf_change = row["performance_change"]
                        perf_direction = "mejorado" if perf_change > 0 else "empeorado" if perf_change < 0 else "mantenido"
                        
                        f.write(f"- Rendimiento: Ha {perf_direction} un {abs(perf_change):.2f}% (de {row['year1']} a {row['year2']})\n")
                        
                        # cambios en los profesores
                        if row["faculty_changed"]:
                
                            f.write(f"- Cambios en profesorado: Sí ({row['faculty_percent_changed']:.1f}% del claustro)\n")
                            f.write(f"  - Profesores añadidos: {row['faculty_added']}\n")
                            f.write(f"  - Profesores eliminados: {row['faculty_removed']}\n")
                            
                            # Cambios en profesores con analisis de rendimiento
                            if perf_change > 2 and row["faculty_percent_changed"] > 20:
                                f.write("  - COMENTARIO: La mejora significativa en el rendimiento podría estar relacionada ")
                                f.write("con los cambios importantes en el profesorado durante este periodo.\n")
                            elif perf_change < -2 and row["faculty_percent_changed"] > 20:
                                f.write("  - COMENTARIO: El empeoramiento en el rendimiento podría estar relacionado ")
                                f.write("con los cambios importantes en el profesorado durante este periodo. Se recomienda ")
                                f.write("revisar la transición y adaptación de los nuevos profesores.\n")
                        else:
                            f.write("- Cambios en profesorado: No\n")
                            
                            if abs(perf_change) > 5:
                                f.write(f"  - COMENTARIO: Los cambios significativos en rendimiento ({perf_direction} un {abs(perf_change):.2f}%) ")
                                f.write("ocurrieron sin cambios en el profesorado, lo que sugiere que otros factores ")
                                f.write("influyeron en este cambio de desempeño.\n")
                        
                        # Evaluation method changes
                        # Cambios en los metodos de evaluacion
                        if row["evaluation_changed"]:
                            f.write("- Cambios en métodos de evaluación: Sí\n")
                            f.write(f"  - Métodos añadidos: {row['evaluation_methods_added']}\n")
                            f.write(f"  - Métodos eliminados: {row['evaluation_methods_removed']}\n")
                            
                            # Evaluation insights
                            # analisis en la evaluacion
                            if perf_change > 2:
                                f.write("  - COMENTARIO: Los cambios en los métodos de evaluación podrían haber contribuido ")
                                f.write("a la mejora del rendimiento de los estudiantes.\n")
                        else:
                            f.write("- Cambios en métodos de evaluación: No\n")
                        
                        f.write("\n")
                    
                    # Analisis 360 de las asignaturas
                    avg_perf_change = subject_df["performance_change"].mean()
                    direction = "mejorando" if avg_perf_change > 0 else "empeorando" if avg_perf_change < 0 else "manteniéndose estable"
                    
                    f.write(f"Análisis global para {subject_name}:\n")
                    f.write(f"- Esta asignatura está {direction} con un cambio promedio de {abs(avg_perf_change):.2f}% por año.\n")
                    
                    # Comprobar si los cambios en los profesores correlaciones en cambios en el rendimiento
                    faculty_changes = subject_df["faculty_changed"].sum()
                    if faculty_changes > 0:
                        perf_with_changes = subject_df[subject_df["faculty_changed"]]["performance_change"].mean()
                        perf_without_changes = 0
                        if not subject_df[~subject_df["faculty_changed"]].empty:
                            perf_without_changes = subject_df[~subject_df["faculty_changed"]]["performance_change"].mean()
                        
                        if abs(perf_with_changes) > abs(perf_without_changes) + 2:
                            f.write(f"- ANALISIS IMPORTANTE: Los periodos con cambios en el profesorado muestran un ")
                            f.write(f"impacto promedio de {perf_with_changes:.2f}% en el rendimiento, ")
                            
                            if perf_with_changes > 0:
                                f.write("sugiriendo que los cambios de profesorado han sido beneficiosos para esta asignatura.\n")
                            else:
                                f.write("sugiriendo que los cambios de profesorado han afectado negativamente a esta asignatura. ")
                                f.write("Se recomienda revisar la continuidad del profesorado.\n")
                    
                    # Comprobar si los cambios en la evaluacion se correlacionan con cambios en el rendimiento
                    eval_changes = subject_df["evaluation_changed"].sum()
                    if eval_changes > 0:
                        perf_with_eval_changes = subject_df[subject_df["evaluation_changed"]]["performance_change"].mean()
                        
                        if abs(perf_with_eval_changes) > 3:
                            f.write(f"- ANALISIS METODOLÓGICO: Los cambios en métodos de evaluación muestran un ")
                            f.write(f"impacto promedio de {perf_with_eval_changes:.2f}% en el rendimiento, ")
                            
                            if perf_with_eval_changes > 0:
                                f.write("sugiriendo que los nuevos métodos han sido más efectivos.\n")
                            else:
                                f.write("sugiriendo que los nuevos métodos podrían necesitar revisión.\n")
                    
                    f.write("\n" + "=" * 80 + "\n\n")
                
                # Generar analisis colectivos
                f.write("Analisis COLECTIVOS\n")
                f.write("-----------------\n\n")
                
                # Asignaturas con mayor mejora
                if len(correlation_df) > 0:
                    # Calcular la media de cambios en rendimiento por asignatura
                    avg_changes = correlation_df.groupby("subject_code").agg({
                        "performance_change": "mean",
                        "subject_name": "first",
                        "faculty_changed": "sum",
                        "evaluation_changed": "sum"
                    }).reset_index()
                    
                    # Asignaturas con mayor mejora
                    most_improved = avg_changes.sort_values("performance_change", ascending=False).head(3)
                    
                    f.write("Asignaturas con mayor mejora en rendimiento:\n")
                    for _, row in most_improved.iterrows():
                        f.write(f"- {row['subject_name']}: {row['performance_change']:.2f}% promedio\n")
                        
                        if row["faculty_changed"] > 0:
                            f.write(f"  - Experimentó cambios en el profesorado en {row['faculty_changed']} períodos\n")
                        
                        if row["evaluation_changed"] > 0:
                            f.write(f"  - Experimentó cambios en métodos de evaluación en {row['evaluation_changed']} períodos\n")
                    
                    f.write("\n")
                    
                    # Asignatura con mayor declive
                    most_declined = avg_changes.sort_values("performance_change").head(3)
                    
                    f.write("Asignaturas con mayor disminución en rendimiento:\n")
                    for _, row in most_declined.iterrows():
                        if row["performance_change"] < 0:  # Solo mostrar asignaturas con cambios negativos
                            f.write(f"- {row['subject_name']}: {row['performance_change']:.2f}% promedio\n")
                            
                            if row["faculty_changed"] > 0:
                                f.write(f"  - Experimentó cambios en el profesorado en {row['faculty_changed']} períodos\n")
                            
                            if row["evaluation_changed"] > 0:
                                f.write(f"  - Experimentó cambios en métodos de evaluación en {row['evaluation_changed']} períodos\n")
                    
                    f.write("\n")
                    
                    # Correlacion entre cambios de los profes y el rendimiento
                    faculty_changed = correlation_df[correlation_df["faculty_changed"]]["performance_change"].mean()
                    faculty_stable = correlation_df[~correlation_df["faculty_changed"]]["performance_change"].mean()
                    
                    f.write("Correlación entre cambios de profesorado y rendimiento:\n")
                    f.write(f"- Períodos con cambios en profesorado: {faculty_changed:.2f}% cambio promedio\n")
                    f.write(f"- Períodos sin cambios en profesorado: {faculty_stable:.2f}% cambio promedio\n")
                    
                    if abs(faculty_changed - faculty_stable) > 2:
                        if faculty_changed > faculty_stable:
                            f.write("- ANALISIS GLOBAL: Los cambios en el profesorado están asociados con mejoras en el rendimiento. ")
                            f.write("La renovación pedagógica podría ser beneficiosa para el programa.\n")
                        else:
                            f.write("- ANALISIS GLOBAL: La estabilidad en el profesorado está asociada con mejores resultados. ")
                            f.write("Se recomienda garantizar continuidad y evitar cambios frecuentes en la plantilla docente.\n")
                    else:
                        f.write("- No se observa una correlación clara entre cambios de profesorado y rendimiento académico a nivel global.\n")
                    
                    f.write("\n")
                    
                    # Correlacion entre cambios en la evaluacion y el rendimiento
                    eval_changed = correlation_df[correlation_df["evaluation_changed"]]["performance_change"].mean()
                    eval_stable = correlation_df[~correlation_df["evaluation_changed"]]["performance_change"].mean()
                    
                    f.write("Correlación entre cambios de evaluación y rendimiento:\n")
                    f.write(f"- Períodos con cambios en métodos: {eval_changed:.2f}% cambio promedio\n")
                    f.write(f"- Períodos sin cambios en métodos: {eval_stable:.2f}% cambio promedio\n")
                    
                    if abs(eval_changed - eval_stable) > 2:
                        if eval_changed > eval_stable:
                            f.write("- ANALISIS METODOLÓGICO GLOBAL: La innovación en métodos de evaluación está asociada ")
                            f.write("con mejoras en el rendimiento. Se recomienda promover la actualización metodológica.\n")
                        else:
                            f.write("- ANALISIS METODOLÓGICO GLOBAL: La estabilidad en métodos de evaluación está asociada ")
                            f.write("con mejores resultados. Los cambios frecuentes en evaluación podrían confundir a los estudiantes.\n")
                    else:
                        f.write("- No se observa una correlación clara entre cambios de evaluación y rendimiento académico a nivel global.\n")
                
                f.write("\n")
                f.write("RECOMENDACIONES\n")
                f.write("--------------\n\n")
                
                # Generar recomendaciones basadas en los analisis
                if len(correlation_df) > 0:
                    # Recomendaciones relacionadas con los profesores
                    f.write("Relacionadas con el profesorado:\n")
                    
                    if faculty_changed > faculty_stable:
                        f.write("1. Continuar la política de renovación estratégica del profesorado en asignaturas con bajos rendimientos.\n")
                        f.write("2. Identificar y replicar las prácticas de los nuevos profesores en asignaturas de alto rendimiento.\n")
                        f.write("3. Facilitar la integración de nuevos profesores con programas de mentoría y formación.\n")
                    else:
                        f.write("1. Fortalecer la continuidad del profesorado, especialmente en asignaturas clave.\n")
                        f.write("2. Implementar programas de actualización pedagógica para profesores actuales.\n")
                        f.write("3. Establecer equipos docentes estables con responsabilidades de larga duración.\n")
                    
                    f.write("\n")
                    
                    # Recomendaciones relacionadas con la evaluacion
                    f.write("Relacionadas con la evaluación:\n")
                    
                    if eval_changed > eval_stable:
                        f.write("1. Promover la innovación en métodos de evaluación, especialmente en asignaturas con rendimiento estancado.\n")
                        f.write("2. Documentar y compartir los métodos de evaluación exitosos entre asignaturas.\n")
                        f.write("3. Establecer un programa de mejora continua de evaluación basado en resultados académicos.\n")
                    else:
                        f.write("1. Estandarizar los métodos de evaluación más efectivos y mantener consistencia.\n")
                        f.write("2. Introducir cambios graduales en evaluación con procesos de transición claros.\n")
                        f.write("3. Comunicar con claridad a los estudiantes los criterios y métodos de evaluación al inicio del curso.\n")
                    
                    f.write("\n")
                    
                    # Recomendaciones generales
                    f.write("Recomendaciones generales:\n")
                    f.write("1. Establecer un sistema de seguimiento continuo que correlacione cambios en profesorado, ")
                    f.write("evaluación y contenidos con los resultados académicos.\n")
                    f.write("2. Realizar entrevistas con estudiantes para identificar factores cualitativos de éxito o fracaso.\n")
                    f.write("3. Desarrollar un programa de intervención temprana para asignaturas que muestren tendencias ")
                    f.write("negativas en sus indicadores de rendimiento.\n")

def process_pdf_content(pdf_text):
    #Procesar el contenido del PDF
    extractor = AcademicDataExtractor(pdf_text)
    data = extractor.extract_all_data()
    
    analyzer = AcademicDataAnalyzer(data)
    analyzer.run_complete_analysis()
    
    return data


if __name__ == "__main__":
    #Ruta al contenido extraído del PDF
    pdf_content = """ """
    
    data = process_pdf_content(pdf_content)
    
    # Convertir los datos de las asignaturas a un DataFrame para analisis por errores
    subjects_df = pd.DataFrame(data["subjects"]).T
    print(subjects_df.head())
