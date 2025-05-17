import sqlite3
import pandas as pd
import json
from pathlib import Path
import os

# boom
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


#clase para almacenar  y recuperar datos académicos en una base de datos SQLite
class AcademicDatabase:
    
    def __init__(self, db_path="academic_data.db"):
        #inicializa la conexión a la base de datos SQLite
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.setup_database()
    
    def setup_database(self):
        #Crear las tablas necesarias en la base de datos si no existen
        cursor = self.conn.cursor()
        
        # Crear tabla para información del curso
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_info (
            academic_year TEXT,
            semester TEXT,
            plan_code TEXT,
            plan_title TEXT,
            report_date TEXT,
            PRIMARY KEY (academic_year, semester)
        )
        ''')
        
        # Crear tabla para asignaturas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            subject_code TEXT,
            subject_name TEXT,
            credits INTEGER,
            academic_year TEXT,
            semester TEXT,
            PRIMARY KEY (subject_code, academic_year, semester),
            FOREIGN KEY (academic_year, semester) REFERENCES course_info (academic_year, semester)
        )
        ''')
        
        # Crear tabla para datos de matrícula
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollment (
            subject_code TEXT,
            academic_year TEXT,
            semester TEXT,
            total_enrolled INTEGER,
            first_time INTEGER,
            partial_dedication INTEGER,
            PRIMARY KEY (subject_code, academic_year, semester),
            FOREIGN KEY (subject_code, academic_year, semester) REFERENCES subjects (subject_code, academic_year, semester)
        )
        ''')
        
        # Crear tabla para tasas de rendimiento
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_rates (
            subject_code TEXT,
            academic_year TEXT,
            semester TEXT,
            performance_rate REAL,
            success_rate REAL,
            absenteeism_rate REAL,
            PRIMARY KEY (subject_code, academic_year, semester),
            FOREIGN KEY (subject_code, academic_year, semester) REFERENCES subjects (subject_code, academic_year, semester)
        )
        ''')
        
        # Crear tabla para tasas históricas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_rates (
            subject_code TEXT,
            academic_year TEXT,
            rate_type TEXT,
            value REAL,
            PRIMARY KEY (subject_code, academic_year, rate_type)
        )
        ''')
        # Tabla para cambios en profesorado
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty_changes (
            subject_code TEXT,
            year1 TEXT,
            year2 TEXT,
            faculty_added INTEGER,
            faculty_removed INTEGER,
            percent_changed REAL,
            PRIMARY KEY (subject_code, year1, year2)
        )
        ''')
        
        # Tabla para cambios en métodos de evaluación
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_changes (
            subject_code TEXT,
            year1 TEXT,
            year2 TEXT,
            methods_added INTEGER,
            methods_removed INTEGER,
            PRIMARY KEY (subject_code, year1, year2)
        )
        ''')


        # Tabla para correlaciones entre cambios y rendimiento
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_correlations (
            subject_code TEXT,
            subject_name TEXT,
            year1 TEXT,
            year2 TEXT,
            performance_change REAL,
            faculty_changed BOOLEAN,
            faculty_percent_changed REAL,
            faculty_added INTEGER,
            faculty_removed INTEGER,
            evaluation_changed BOOLEAN,
            evaluation_methods_added INTEGER,
            evaluation_methods_removed INTEGER,
            PRIMARY KEY (subject_code, year1, year2)
        )
        ''')
        
        # Tabla para almacenar insights globales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_insights (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date TEXT,
            faculty_impact_type TEXT,
            faculty_change_performance REAL,
            faculty_stable_performance REAL,
            evaluation_impact_type TEXT,
            evaluation_change_performance REAL,
            evaluation_stable_performance REAL,
            insights_json TEXT
        )
        ''')

        # Tabla para almacenar insights por asignatura
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_insights (
            subject_code TEXT,
            analysis_id INTEGER,
            subject_name TEXT,
            avg_performance_change REAL,
            trend_direction TEXT,
            faculty_impact_type TEXT,
            evaluation_impact_type TEXT,
            insights_json TEXT,
            PRIMARY KEY (subject_code, analysis_id),
            FOREIGN KEY (analysis_id) REFERENCES global_insights (analysis_id)
        )
        ''')
        
        
        self.conn.commit()
    
    def store_data(self, data):
        # Almacenar datos extraídos en la base de datos
        cursor = self.conn.cursor()
        
        # Almacenar información del curso
        course_info = data.get("course_info", {})
        if course_info:
            cursor.execute('''
            INSERT OR REPLACE INTO course_info (academic_year, semester, plan_code, plan_title, report_date)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                course_info.get("academic_year"),
                course_info.get("semester"),
                course_info.get("plan_code"),
                course_info.get("plan_title"),
                course_info.get("report_date", "")
            ))
        
        # Almacenar información de asignaturas
        subjects = data.get("subjects", {})
        academic_year = course_info.get("academic_year")
        semester = course_info.get("semester")
        
        for subject_code, subject_data in subjects.items():
            # Almacenar información básica de la asignatura
            cursor.execute('''
            INSERT OR REPLACE INTO subjects (subject_code, subject_name, credits, academic_year, semester)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                subject_code,
                subject_data.get("name"),
                subject_data.get("credits"),
                academic_year,
                semester
            ))
            
            # Almacenar datos de matrícula
            if "total_enrolled" in subject_data:
                cursor.execute('''
                INSERT OR REPLACE INTO enrollment (subject_code, academic_year, semester, total_enrolled, first_time, partial_dedication)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    subject_code,
                    academic_year,
                    semester,
                    subject_data.get("total_enrolled"),
                    subject_data.get("first_time", 0),
                    subject_data.get("partial_dedication", 0)
                ))
            
            # Almacenar tasas de rendimiento, éxito y absentismo
            if "performance_rate" in subject_data:
                cursor.execute('''
                INSERT OR REPLACE INTO performance_rates (subject_code, academic_year, semester, performance_rate, success_rate, absenteeism_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    subject_code,
                    academic_year,
                    semester,
                    subject_data.get("performance_rate"),
                    subject_data.get("success_rate"),
                    subject_data.get("absenteeism_rate")
                ))
            
            # Almacenar tasas históricas
            if "historical" in subject_data:
                for rate_type, years_data in subject_data["historical"].items():
                    for year, value in years_data.items():
                        cursor.execute('''
                        INSERT OR REPLACE INTO historical_rates (subject_code, academic_year, rate_type, value)
                        VALUES (?, ?, ?, ?)
                        ''', (
                            subject_code,
                            year,
                            rate_type,
                            value
                        ))
        
        self.conn.commit()

    def store_faculty_changes(self, analysis_results):

        cursor = self.conn.cursor()
        
        for subject_code, subject_data in analysis_results.items():
            faculty_analysis = subject_data.get("faculty_analysis", {})
            
            for i, (year1, year2) in enumerate(faculty_analysis.get("years_compared", [])):
                # Obtener los datos de cambio para este par de años
                changes = None
                for year_pair, change_data in faculty_analysis.get("faculty_changes", {}).items():
                    if year_pair == (year1, year2):
                        changes = change_data
                        break
                # Almacenar los cambios en la base de datos
                if changes:
                    cursor.execute('''
                    INSERT OR REPLACE INTO faculty_changes 
                    (subject_code, year1, year2, faculty_added, faculty_removed, percent_changed)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        subject_code,
                        year1,
                        year2,
                        changes.get("total_added", 0),
                        changes.get("total_removed", 0),
                        changes.get("percent_changed", 0)
                    ))
        
        self.conn.commit()
    
    def store_evaluation_changes(self, analysis_results):

        cursor = self.conn.cursor()
        
        for subject_code, subject_data in analysis_results.items():
            evaluation_analysis = subject_data.get("evaluation_analysis", {})
            
            for i, (year1, year2) in enumerate(evaluation_analysis.get("years_compared", [])):
                # Obtener los datos de cambio para este par de años
                changes = None
                for year_pair, change_data in evaluation_analysis.get("evaluation_changes", {}).items():
                    if year_pair == (year1, year2):
                        changes = change_data
                        break
                # Almacenar los cambios en la base de datos
                if changes:
                    cursor.execute('''
                    INSERT OR REPLACE INTO evaluation_changes 
                    (subject_code, year1, year2, methods_added, methods_removed)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        subject_code,
                        year1,
                        year2,
                        len(changes.get("added", [])),
                        len(changes.get("removed", []))
                    ))
        
        self.conn.commit()
    
    def store_performance_correlations(self, correlation_df):

        if correlation_df.empty:
            return False
        
        # Convertir DataFrame a lista de tuplas para inserción masiva
        records = []
        for _, row in correlation_df.iterrows():
            record = (
                row["subject_code"],
                row["subject_name"],
                row["year1"],
                row["year2"],
                float(row["performance_change"]),
                bool(row["faculty_changed"]),
                float(row["faculty_percent_changed"]),
                int(row["faculty_added"]),
                int(row["faculty_removed"]),
                bool(row["evaluation_changed"]),
                int(row["evaluation_methods_added"]),
                int(row["evaluation_methods_removed"])
            )
            records.append(record)

        # Insertar registros
        cursor = self.conn.cursor()
        cursor.executemany('''
        INSERT OR REPLACE INTO performance_correlations 
        (subject_code, subject_name, year1, year2, performance_change, 
         faculty_changed, faculty_percent_changed, faculty_added, faculty_removed,
         evaluation_changed, evaluation_methods_added, evaluation_methods_removed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        
        self.conn.commit()
        return True
    
    def store_insights(self, insights_data, analysis_date=None):
        import datetime
        
        if analysis_date is None:
            analysis_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extraer insights globales
        global_insights = insights_data.get("global_insights", {})
        faculty_impact = global_insights.get("faculty_impact", {})
        evaluation_impact = global_insights.get("evaluation_impact", {})
        # Insertar registro de insights globales
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO global_insights 
        (analysis_date, faculty_impact_type, faculty_change_performance, faculty_stable_performance,
         evaluation_impact_type, evaluation_change_performance, evaluation_stable_performance, insights_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_date,
            faculty_impact.get("impact_type", "neutral"),
            faculty_impact.get("with_changes", 0),
            faculty_impact.get("without_changes", 0),
            evaluation_impact.get("impact_type", "neutral"),
            evaluation_impact.get("with_changes", 0),
            evaluation_impact.get("without_changes", 0),
            json.dumps(global_insights, ensure_ascii=False, cls=NumpyEncoder)
        ))
        # Obtener el ID del análisis global insertado
        analysis_id = cursor.lastrowid
        # Insertar insights por asignatura
        subject_insights = insights_data.get("subject_insights", {})
        for subject_code, subject_insight in subject_insights.items():
            faculty_impact = subject_insight.get("faculty_impact", {})
            evaluation_impact = subject_insight.get("evaluation_impact", {})
            
            cursor.execute('''
            INSERT INTO subject_insights
            (subject_code, analysis_id, subject_name, avg_performance_change, trend_direction,
             faculty_impact_type, evaluation_impact_type, insights_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                subject_code,
                analysis_id,
                subject_insight.get("subject_name", ""),
                subject_insight.get("average_performance_change", 0),
                subject_insight.get("trend_direction", "stable"),
                faculty_impact.get("impact_direction", "neutral") if faculty_impact else "neutral",
                evaluation_impact.get("impact_direction", "neutral") if evaluation_impact else "neutral",
                json.dumps(subject_insight, ensure_ascii=False, cls=NumpyEncoder)
            ))
        
        self.conn.commit()
        return analysis_id
    
    def store_api_analysis(self, api_data, analysis_results, correlation_df, insights_data):

        try:
            # Almacenar datos de profesorado y evaluación
            #self.store_faculty_data(api_data)
            #self.store_evaluation_methods(api_data)
            
            # Almacenar análisis de cambios
            self.store_faculty_changes(analysis_results)
            self.store_evaluation_changes(analysis_results)
            # Almacenar correlaciones
            self.store_performance_correlations(correlation_df)
            
            # Almacenar insights
            self.store_insights(insights_data)
            return analysis_results

        except Exception as e:
            print(f"Error al almacenar análisis de API: {e}")
            return None



    def get_subjects(self):
        # Obtener todas las asignaturas de la base de datos
        query = '''
        SELECT s.subject_code, s.subject_name, s.credits, s.academic_year, s.semester, 
               e.total_enrolled, e.first_time, e.partial_dedication,
               p.performance_rate, p.success_rate, p.absenteeism_rate
        FROM subjects s
        LEFT JOIN enrollment e ON s.subject_code = e.subject_code AND s.academic_year = e.academic_year AND s.semester = e.semester
        LEFT JOIN performance_rates p ON s.subject_code = p.subject_code AND s.academic_year = p.academic_year AND s.semester = p.semester
        '''
        
        return pd.read_sql_query(query, self.conn)
    
    def get_historical_rates(self, subject_code=None):
        # Obtener tasas históricas de rendimiento, éxito y absentismo
        # para una asignatura específica o todas las asignaturas

        query = '''
        SELECT h.subject_code, s.subject_name, h.academic_year, h.rate_type, h.value
        FROM historical_rates h
        JOIN subjects s ON h.subject_code = s.subject_code
        '''
        
        if subject_code:
            query += ' WHERE h.subject_code = ?'
            return pd.read_sql_query(query, self.conn, params=(subject_code,))
        else:
            return pd.read_sql_query(query, self.conn)
    
    def get_subject_trend(self, subject_code, rate_type="performance_rate"):
        # Obtener la tendencia de una tasa específica para una asignatura a lo largo de los años
        query = '''
        SELECT academic_year, value
        FROM historical_rates
        WHERE subject_code = ? AND rate_type = ?
        ORDER BY academic_year
        '''
        
        return pd.read_sql_query(query, self.conn, params=(subject_code, rate_type))
    
    def get_latest_rates(self):
        # Obtener la tasa de rendimiento más reciente para cada asignatura
        query = '''
        SELECT s.subject_code, s.subject_name, p.performance_rate, p.success_rate, p.absenteeism_rate
        FROM subjects s
        JOIN performance_rates p ON s.subject_code = p.subject_code AND s.academic_year = p.academic_year AND s.semester = p.semester
        JOIN course_info c ON s.academic_year = c.academic_year AND s.semester = c.semester
        ORDER BY p.performance_rate DESC
        '''
        
        return pd.read_sql_query(query, self.conn)

    def get_faculty_changes(self, subject_code=None):

        query = '''
        SELECT f.subject_code, s.subject_name, f.year1, f.year2, 
               f.faculty_added, f.faculty_removed, f.percent_changed
        FROM faculty_changes f
        JOIN subjects s ON f.subject_code = s.subject_code
        '''
        
        if subject_code:
            query += ' WHERE f.subject_code = ?'
            return pd.read_sql_query(query, self.conn, params=(subject_code,))
        else:
            return pd.read_sql_query(query, self.conn)
    
    def get_evaluation_changes(self, subject_code=None):
        
        query = '''
        SELECT e.subject_code, s.subject_name, e.year1, e.year2, 
               e.methods_added, e.methods_removed
        FROM evaluation_changes e
        JOIN subjects s ON e.subject_code = s.subject_code
        '''
        
        if subject_code:
            query += ' WHERE e.subject_code = ?'
            return pd.read_sql_query(query, self.conn, params=(subject_code,))
        else:
            return pd.read_sql_query(query, self.conn)
    
    def get_performance_correlations(self, subject_code=None):
   
        query = '''
        SELECT *
        FROM performance_correlations
        '''
        
        if subject_code:
            query += ' WHERE subject_code = ?'
            return pd.read_sql_query(query, self.conn, params=(subject_code,))
        else:
            return pd.read_sql_query(query, self.conn)
    
    def get_global_insights(self, analysis_id=None):
     
        query = '''
        SELECT *
        FROM global_insights
        '''
        
        if analysis_id:
            query += ' WHERE analysis_id = ?'
            return pd.read_sql_query(query, self.conn, params=(analysis_id,))
        else:
            query += ' ORDER BY analysis_id DESC LIMIT 1'
            return pd.read_sql_query(query, self.conn)
    
    def get_subject_insights(self, analysis_id=None, subject_code=None):
      
        # Si no se proporciona analysis_id, obtener el más reciente
        if analysis_id is None:
            latest_analysis = self.get_global_insights()
            if not latest_analysis.empty:
                analysis_id = latest_analysis.iloc[0]["analysis_id"]
            else:
                return pd.DataFrame()  # No hay análisis disponibles
        
        query = '''
        SELECT *
        FROM subject_insights
        WHERE analysis_id = ?
        '''
        
        params = [analysis_id]
        
        if subject_code:
            query += ' AND subject_code = ?'
            params.append(subject_code)
        
        return pd.read_sql_query(query, self.conn, params=params)

    def export_api_analysis_to_json(self, output_dir="output/api_analysis"):

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Exportar cambios en profesorado
        #faculty_changes_df = self.get_faculty_changes()
        #if not faculty_changes_df.empty:
        #    faculty_changes_df.to_json(f"{output_dir}/faculty_changes.json", orient="records")
        #else:
        #    print("No hay cambios en profesorado para exportar.")

        # Exportar cambios en evaluación
        #evaluation_changes_df = self.get_evaluation_changes()
        #if not evaluation_changes_df.empty:
        #    evaluation_changes_df.to_json(f"{output_dir}/evaluation_changes.json", orient="records")
        #else:
        #    print("No hay cambios en evaluación para exportar.")
        # Exportar correlaciones
        correlations_df = self.get_performance_correlations()
        if not correlations_df.empty:
            correlations_df.to_json(f"{output_dir}/performance_correlations.json", orient="records")
        else:
            print("No hay correlaciones de rendimiento para exportar.")
        # Obtener insights globales y por asignatura
        global_insights_df = self.get_global_insights()
        
        if not global_insights_df.empty:
            analysis_id = global_insights_df.iloc[0]["analysis_id"]
            subject_insights_df = self.get_subject_insights(analysis_id)
            
            # Crear una estructura jerárquica para JSON
            insights_json = {}
            
            # Procesar insights globales
            global_row = global_insights_df.iloc[0]
            insights_json["global_insights"] = {
                "analysis_id": int(global_row["analysis_id"]),
                "analysis_date": global_row["analysis_date"],
                "faculty_impact": {
                    "impact_type": global_row["faculty_impact_type"],
                    "with_changes": float(global_row["faculty_change_performance"]),
                    "without_changes": float(global_row["faculty_stable_performance"])
                },
                "evaluation_impact": {
                    "impact_type": global_row["evaluation_impact_type"],
                    "with_changes": float(global_row["evaluation_change_performance"]) if global_row["evaluation_change_performance"] else 0,
                    "without_changes": float(global_row["evaluation_stable_performance"])
                }
            }
            
            # Añadir datos detallados si están disponibles en JSON
            try:
                global_json = json.loads(global_row["insights_json"])
                insights_json["global_insights"].update(global_json)
            except:
                pass
            
            # Procesar insights por asignatura
            insights_json["subject_insights"] = {}
            
            for _, row in subject_insights_df.iterrows():
                subject_code = row["subject_code"]
                subject_data = {
                    "subject_name": row["subject_name"],
                    "avg_performance_change": float(row["avg_performance_change"]),
                    "trend_direction": row["trend_direction"],
                    "faculty_impact_type": row["faculty_impact_type"],
                    "evaluation_impact_type": row["evaluation_impact_type"]
                }
                
                # Añadir datos detallados si están disponibles en JSON
                try:
                    subject_json = json.loads(row["insights_json"])
                    subject_data.update(subject_json)
                except:
                    pass
                
                insights_json["subject_insights"][subject_code] = subject_data
            
            # Guardar el archivo JSON con todos los insights
            with open(f"{output_dir}/insights.json", 'w', encoding='utf-8') as f:
                json.dump(insights_json, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        # Exportar datos de profesorado
        #faculty_df = self.get_faculty_data()
        #if not faculty_df.empty:
            # Crear una estructura jerárquica para JSON
            #faculty_json = {}
            
            #for subject_code in faculty_df["subject_code"].unique():
                #subject_faculty = faculty_df[faculty_df["subject_code"] == subject_code]
                #subject_name = subject_faculty.iloc[0]["subject_name"]
                
                #faculty_json[subject_code] = {
                    #"subject_name": subject_name,
                    #"faculty_by_year": {}
                #}
                
                #for year in subject_faculty["academic_year"].unique():
                    #year_faculty = subject_faculty[subject_faculty["academic_year"] == year]
                    #faculty_json[subject_code]["faculty_by_year"][year] = year_faculty["faculty_name"].tolist()
            
            #with open(f"{output_dir}/faculty_data.json", 'w', encoding='utf-8') as f:
                #json.dump(faculty_json, f, ensure_ascii=False, indent=2)
        
        # Exportar datos de métodos de evaluación
        #evaluation_methods_df = self.get_evaluation_methods_data()
        #if not evaluation_methods_df.empty:
            # Crear una estructura jerárquica para JSON
            #eval_json = {}
            
            #for subject_code in evaluation_methods_df["subject_code"].unique():
                #subject_eval = evaluation_methods_df[evaluation_methods_df["subject_code"] == subject_code]
                #subject_name = subject_eval.iloc[0]["subject_name"]
                
                #eval_json[subject_code] = {
                    #"subject_name": subject_name,
                    #"evaluation_methods_by_year": {}
                #}
                
                #for year in subject_eval["academic_year"].unique():
                    #year_eval = subject_eval[subject_eval["academic_year"] == year]
                    #eval_json[subject_code]["evaluation_methods_by_year"][year] = year_eval["evaluation_method"].tolist()
            
            #with open(f"{output_dir}/evaluation_methods_data.json", 'w', encoding='utf-8') as f:
                #json.dump(eval_json, f, ensure_ascii=False, indent=2)
        
        print(f"Datos del analisis de la API exportados a archivos JSON en el directorio {output_dir} ")

    def export_to_csv(self, output_dir="output"):
        # Exportar todas las tablas a CSV
        Path(output_dir).mkdir(exist_ok=True)
        
        # Exportar asignaturas
        subjects_df = self.get_subjects()
        subjects_df.to_csv(f"{output_dir}/subjects.csv", index=False)
        
        # Exportar tasas históricas
        historical_df = self.get_historical_rates()
        historical_df.to_csv(f"{output_dir}/historical_rates.csv", index=False)
        
        # Exportar tasas más recientes
        latest_rates_df = self.get_latest_rates()
        latest_rates_df.to_csv(f"{output_dir}/latest_rates.csv", index=False)
        
        print(f"Datos exportados a CSV en el directorio {output_dir} ")
    
    def export_to_json(self, output_dir="output"):
        #exportar todas las tablas a JSON
        Path(output_dir).mkdir(exist_ok=True)
        
        # Exportar asignaturas
        subjects_df = self.get_subjects()
        subjects_df.to_json(f"{output_dir}/subjects.json", orient="records")
        
        # Exportar tasas históricas
        historical_df = self.get_historical_rates()
        historical_df.to_json(f"{output_dir}/historical_rates.json", orient="records")
        
        # Exportar tasas más recientes
        latest_rates_df = self.get_latest_rates()
        latest_rates_df.to_json(f"{output_dir}/latest_rates.json", orient="records")
        
        print(f"Datos exportados a JSON en el directorio {output_dir} ")

#    def export_to_csv_json(self, output_dir="output"):

        # Crear directorio de salida
        #Path(output_dir).mkdir(exist_ok=True)
        
        # Exportar tablas originales a CSV
        #self.export_to_csv(output_dir)
        
        # Exportar tablas originales a JSON
        #self.export_to_json(output_dir)
        
        # Exportar análisis de API si se solicita
        #api_output_dir = os.path.join(output_dir, "api_analysis")
        #self.export_api_analysis_to_json(api_output_dir)
            
        #print(f"Todos los datos exportados a archivos JSON en el diretorio {output_dir}")

    def add_api_analysis(self, api_data, analysis_results, correlation_df, insights_data):
        #Funcion auxiliar para hacer el try de store_api_analysis a la db
        try:
            return self.store_api_analysis(api_data, analysis_results, correlation_df, insights_data)
        except Exception as e:
            print(f"Error anadiendo analisis de la API a la BD: {e}")
            import traceback
            traceback.print_exc()
            return None

    def close(self):
        # Cierra la conexión a la base de datos
        if self.conn:
            self.conn.close()
            
    def __del__(self):
        #Destructor para asegurarse de que la conexión se cierre
        # al eliminar la instancia de la clase
        self.close()


if __name__ == "__main__":
    db = AcademicDatabase()
    
    # Datos de muestra para usar como ejemplosss
    sample_data = {
        "course_info": {
            "academic_year": "2023/24",
            "semester": "Segundo",
            "plan_code": "10II",
            "plan_title": "Grado en Ingenieria Informatica"
        },
        "subjects": {
            "105000005": {
                "name": "Cálculo",
                "credits": 6,
                "enrolled": 455,
                "total_enrolled": 455,
                "first_time": 248,
                "partial_dedication": 0,
                "performance_rate": 31.94,
                "success_rate": 36.52,
                "absenteeism_rate": 12.56,
                "historical": {
                    "rendimiento": {
                        "2020-21": 31.32,
                        "2021-22": 35.12,
                        "2022-23": 32.49,
                        "2023-24": 31.94
                    },
                    "éxito": {
                        "2020-21": 41.80,
                        "2021-22": 42.30,
                        "2022-23": 37.90,
                        "2023-24": 36.52
                    },
                    "absentismo": {
                        "2020-21": 25.06,
                        "2021-22": 16.98,
                        "2022-23": 14.29,
                        "2023-24": 12.56
                    }
                }
            }
        }
    }
    
    # Guardar los datos de muestra en la base de datos
    db.store_data(sample_data)
    
    # Exportar los datos a CSV y JSON
    db.export_to_csv()
    db.export_to_json()
    
    # Cerrar la conexión a la base de datos
    db.close()