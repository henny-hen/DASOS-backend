import sys
import os
from pathlib import Path
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import warnings
import fitz

# Suppress warnings
warnings.filterwarnings("ignore")


# Primero: Extract text from PDF file
def extract_text_from_pdf(pdf_path):
    # Extraer texto del PDF
    text = ""
    try:
        with fitz.open(pdf_path) as pdf_document:
            for page_number in range(len(pdf_document)):
                page = pdf_document[page_number]
                text += page.get_text() + "\n"
#        with open("Output.txt", "w") as text_file:
#           text_file.write(text)
        return text
    except Exception as e:
        print(f"Error extrayendo texto del archivo PDF: {e}")
        return None

# Función principal para procesar un archivo PDF
def process_academic_report(pdf_path, output_dir="output", db_path="academic_data.db", visualize=True):
    # Procesar un archivo PDF de informe académico y generar análisis
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer texto del PDF
    print(f"Extrayendo texto de {pdf_path}...")
    pdf_text = extract_text_from_pdf(pdf_path)
    
    if not pdf_text:
        print("Fallo al extraer texto del PDF. Comprueba el archivo.")
        return False
    
    # Extraer datos de rendimiento académico del texto procesao
    print("Extrayendo datos académicos...")
    # Aquí se asume que AcademicDataExtractor es una clase que extrae datos del texto
    from academic_data_extractor import AcademicDataExtractor
    extractor = AcademicDataExtractor(pdf_text)
    data = extractor.extract_all_data()
    
    # Guardar datos en la base de datos
    print(f"Almacenando datos en la baase de datos: {db_path}")
    from academic_database import AcademicDatabase
    db = AcademicDatabase(db_path)
    db.store_data(data)
    
    # Exportar datos a CSV y JSON
    print(f"Exportando datos en ficheros JSON y CSV en directorio {output_dir}")
    db.export_to_csv(output_dir)
    db.export_to_json(output_dir)
    
    # Analizar datos y generar informes
    # Este paso puede incluir análisis estadísticos, generación de gráficos, etc. mi mi mi
    print("Generando análisis de datos...")
    from academic_data_extractor import AcademicDataAnalyzer
    analyzer = AcademicDataAnalyzer(data)
    analyzer.run_complete_analysis(output_dir)
    
    # Generar visualizaciones analíticas
    if visualize:
        print("Generando visualizaciones...")
        # Obtener dataframes de la base de datos para visualización
        subjects_df = db.get_subjects()
        historical_df = db.get_historical_rates()
        
        from academic_visualizations import AcademicVisualizer
        visualizer = AcademicVisualizer(output_dir=os.path.join(output_dir, "visualizations"))
        visualizer.load_data(subjects_df, historical_df)
        visualizer.run_all_visualizations()
    
    print(f"\nAnalisis completado. Resultados almacenados en: {output_dir}")
    print(f"Base de datos guardada en: {db_path}")
    
    return True

# Procesar múltiples archivos PDF en un directorio (opcional, no se si va bien tod)
def batch_process_directory(dir_path, output_dir="output", db_path="academic_data.db", visualize=True):
    # Procesar todos los archivos PDF en un directorio
    pdf_files = list(Path(dir_path).glob("*.pdf"))
    
    if not pdf_files:
        print(f"Ningún archivo PDF encontrado en {dir_path}")
        return False
    
    print(f"Se han encontrado los ficheros PDF {len(pdf_files)} en {dir_path}")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\nProcesando fichero {i} de {len(pdf_files)}: {pdf_file.name}")
        file_output_dir = os.path.join(output_dir, pdf_file.stem)
        process_academic_report(pdf_file, file_output_dir, db_path, visualize)
    
    # Despues de procesar todos los archivos, generar un análisis comparativo
    print("\nGenerando análisis comparativo entre los informes procesados...")
    perform_comparative_analysis(db_path, os.path.join(output_dir, "comparative_analysis"))
    
    return True

# Realizar un análisis comparativo entre los informes procesados
def perform_comparative_analysis(db_path, output_dir):
    # Generar analisis comparativo a partir de la base de datos
    os.makedirs(output_dir, exist_ok=True)
    
    # Conectar a la base de datos
    from academic_database import AcademicDatabase
    db = AcademicDatabase(db_path)
    
    # Obtener datos para análisis
    #print("Coger datos para su analisis...")
    subjects_df = db.get_subjects()
    historical_df = db.get_historical_rates()
    
    if historical_df.empty:
        print("No se han encontrado datos históricos suficientes para el análisis comparativo.")
        return
    
    # Generate comparative charts
    print("Generando gráficos comparativos...")
    from academic_visualizations import AcademicVisualizer
    visualizer = AcademicVisualizer(output_dir=output_dir)
    visualizer.load_data(subjects_df, historical_df)
    
    # Crear visualizaciones comparativas
    # print("Creando visualizaciones comparativas...")
    visualizer.create_heatmap_visualization()
    visualizer.plot_comparative_trends()
    visualizer.create_summary_dashboard()
    
    # Generar informe comparativo
    #print("Generando informe comparativo...")
    print("Generando informe comparativo...")
    generate_comparative_report(historical_df, output_dir)
    
    print(f"Analisis comparativo completado! Resultados almacenados en: {output_dir}")

# Realizar un análisis integrado con la API
def perform_api_integrated_analysis(db_path, output_dir, plan_code="10II"):

    # Crear Directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Connect to the database
    from academic_database import AcademicDatabase
    db = AcademicDatabase(db_path)
    
    # Obtener datos para analisis
    subjects_df = db.get_subjects()
    historical_df = db.get_historical_rates()
    
    if historical_df.empty:
        print("No se han encontrado datos historicos para el analisis integrado de la API.")
        return
    
    # Inicializar analizador con los datos
    from academic_data_extractor import AcademicDataAnalyzer
    analyzer = AcademicDataAnalyzer({"subjects": {}})  # Datos para empezar (vacios claramente)
    
    # Configurar dataframes directamente
    analyzer.historical_df = historical_df
    
    # Ejectuar analisis integrado con la API
    analyzer.run_api_integrated_analysis(output_dir, plan_code, db_path)


    print(f"Analisis integrado de la API completado. Resultados almacenados en: {output_dir}")


# Generar un informe comparativo (lo de IA analítico)
def generate_comparative_report(historical_df, output_dir):
    # Generar un informe comparativo detallado
    with open(os.path.join(output_dir, "comparative_report.txt"), "w") as f:
        f.write("ANALISIS COMPARATIVO DE RENDIMIENTO ACADEMICO\n")
        f.write("=======================================\n\n")
        
        # Analizar tendencias para cada asignatura
        f.write("TENDENCIAS DE RENDIMIENTO EN ASIGNATURAS\n")
        f.write("-------------------------\n\n")
        
        for subject_code in historical_df['subject_code'].unique():
            subject_data = historical_df[historical_df['subject_code'] == subject_code]
            if subject_data.empty:
                continue
                
            subject_name = subject_data['subject_name'].iloc[0]
            f.write(f"Asignatura: {subject_name}\n")
            
            # Analizar cada tipo de tasa
            for rate_type in subject_data['rate_type'].unique():
                rate_data = subject_data[(subject_data['rate_type'] == rate_type)].sort_values('academic_year')
                
                if len(rate_data) >= 2:
                    # Calcular tendencia
                    first_year = rate_data['academic_year'].iloc[0]
                    last_year = rate_data['academic_year'].iloc[-1]
                    first_value = rate_data['value'].iloc[0]
                    last_value = rate_data['value'].iloc[-1]
                    change = last_value - first_value
                    
                    # Determinar la descripción de la tendencia
                    if abs(change) < 1:
                        trend = "mantenido estable"
                    elif change > 0:
                        trend = "mejorado"
                    else:
                        trend = "empeorado"
                    
                    # Formatea la descripción según el tipo de tasa
                    if rate_type == "rendimiento":
                        rate_name = "LA TASA DE RENDIMIENTO"
                    elif rate_type == "éxito":
                        rate_name = "LA TASA DE EXITO"
                    elif rate_type == "absentismo":
                        rate_name = "LA TASA DE ABSENTISMO"
                    else:
                        rate_name = f"LA TASA  DE {rate_type}"
                    
                    f.write(f"  - {rate_name} ha {trend} de {first_value:.2f}% a {last_value:.2f}% ")
                    f.write(f"({abs(change):.2f} percentage points) entre los cursos {first_year} y {last_year}\n")
            
            f.write("\n")
        
        # Identificar las asignaturas con mayor mejora y declive
        f.write("CAMBIOS MAS SIGNIFICATIVOS\n")
        f.write("-----------------------\n\n")
        
        # Enfoque en las tasas de rendimiento
        perf_data = historical_df[historical_df['rate_type'] == 'rendimiento']
        
        if not perf_data.empty:
            # Calcular cambios para cada asignatura
            changes = []
            for subject_code in perf_data['subject_code'].unique():
                subject_perf = perf_data[perf_data['subject_code'] == subject_code].sort_values('academic_year')
                
                if len(subject_perf) >= 2:
                    first_value = subject_perf['value'].iloc[0]
                    last_value = subject_perf['value'].iloc[-1]
                    change = last_value - first_value
                    subject_name = subject_perf['subject_name'].iloc[0]
                    first_year = subject_perf['academic_year'].iloc[0]
                    last_year = subject_perf['academic_year'].iloc[-1]
                    
                    changes.append({
                        'subject_code': subject_code,
                        'subject_name': subject_name,
                        'change': change,
                        'first_value': first_value,
                        'last_value': last_value,
                        'first_year': first_year,
                        'last_year': last_year
                    })
            
            if changes:
                # Filtrar cambios significativos
                changes.sort(key=lambda x: abs(x['change']), reverse=True)
                
                # Motrar los 3 cambios más significativos
                for i, change_data in enumerate(changes[:3]):
                    direction = "mejora" if change_data['change'] > 0 else "declive"
                    f.write(f"{i+1}. {change_data['subject_name']}: {abs(change_data['change']):.2f} percentage point {direction}\n")
                    f.write(f"   De {change_data['first_value']:.2f}% en el curso {change_data['first_year']} a {change_data['last_value']:.2f}% en el curso {change_data['last_year']}\n\n")
        
        # Identificar asignaturas problemáticas (pondre con alto absentismo, bajo rendimiento)
        f.write("ASIGNATURAS QUE REQUIEREN REVISION\n")
        f.write("--------------------------\n\n")
        
        problematic_subjects = []
        for subject_code in historical_df['subject_code'].unique():
            # Obtener los datos más recientes de cada asignatura
            latest_perf = historical_df[(historical_df['subject_code'] == subject_code) & 
                                       (historical_df['rate_type'] == 'rendimiento')].sort_values('academic_year')
            
            latest_abs = historical_df[(historical_df['subject_code'] == subject_code) & 
                                      (historical_df['rate_type'] == 'absentismo')].sort_values('academic_year')
            
            if not latest_perf.empty and not latest_abs.empty:
                perf_value = latest_perf['value'].iloc[-1]
                abs_value = latest_abs['value'].iloc[-1]
                subject_name = latest_perf['subject_name'].iloc[0]
                
                # Definir criterios para asignaturas problemáticas
                # Consideramos problemáticas las asignaturas con rendimiento bajo o absentismo alto
                # Rendimiento bajo: menos del 50%
                # Absentismo alto: más del 10%
                # Si el rendimiento es bajo o el absentismo es alto, añadir a la lista
                if perf_value < 50 or abs_value > 10:
                    problematic_subjects.append({
                        'subject_name': subject_name,
                        'performance': perf_value,
                        'absenteeism': abs_value
                    })
        
        if problematic_subjects:
            for i, subject in enumerate(problematic_subjects):
                f.write(f"{i+1}. {subject['subject_name']}:\n")
                f.write(f"   Tasa de rendimiento: {subject['performance']:.2f}%\n")
                f.write(f"   Tasa de absentismo: {subject['absenteeism']:.2f}%\n")
                
                # Anadir preocupaciones específicas
                concerns = []
                if subject['performance'] < 50:
                    concerns.append("Tasa de rendimiento baja")
                if subject['absenteeism'] > 10:
                    concerns.append("Tasa de absentismo alta")
                
                f.write(f"   Problemas: {', '.join(concerns)}\n\n")
        else:
            f.write("No hay asignaturas con problemas criticos identificados.\n\n")
        
        # Generar recomendaciones generales
        f.write("RECOMENDACIONES\n")
        f.write("--------------\n\n")
        
        f.write("A partir del analisis de los datos, se recomienda los siguiente:\n\n")
        # Generar recomendaciones específicas basadas en los datos (ESTO es para probar con realizar recomendaciones insitu)
        if problematic_subjects:
            f.write("1. Address subjects with high absenteeism:\n")
            f.write("   - Investigate reasons for non-attendance\n")
            f.write("   - Consider revising teaching methodologies to increase engagement\n")
            f.write("   - Implement attendance monitoring and early intervention systems\n\n")
        

        f.write("2. Support subjects with low performance rates:\n")
        f.write("   - Provide additional teaching resources and support materials\n")
        f.write("   - Consider offering supplementary classes or tutorials\n")
        f.write("   - Review assessment methods and difficulty levels\n\n")
        
        f.write("3. Learn from successful subjects:\n")
        f.write("   - Identify and share best practices from high-performing subjects\n")
        f.write("   - Organize knowledge-sharing sessions between instructors\n")
        f.write("   - Document effective teaching strategies\n\n")
        
        f.write("4. Continuous monitoring and improvement:\n")
        f.write("   - Establish regular analysis of performance metrics\n")
        f.write("   - Set improvement targets for specific subjects\n")
        f.write("   - Implement feedback mechanisms for both students and instructors\n\n")
        
        f.write("5. Curriculum development:\n")
        f.write("   - Review prerequisites for challenging subjects\n")
        f.write("   - Consider sequencing adjustments to better prepare students\n")
        f.write("   - Evaluate workload distribution across the semester\n")

# Interfaz de línea de comandos
def main():
    # Interfaz principal de línea de comandos para el toolkit de análisis de datos académicos
    parser = argparse.ArgumentParser(description="Herramienta para análisis de datos académicos")
    
    # Defino los argumentos de la línea de comandos
    parser.add_argument("--pdf", type=str, help="Ruta al archivo PDF a procesar")
    parser.add_argument("--dir", type=str, help="Directorio contenedor de múltiples archivos PDF")
    parser.add_argument("--output", type=str, default="output", help="Directorio de salida para los resultados")
    parser.add_argument("--db", type=str, default="academic_data.db", help="Ruta a la base de datos SQLite")
    parser.add_argument("--no-viz", action="store_true", help="Saltar la generación de visualizaciones y gráficas")
    parser.add_argument("--analyze-only", action="store_true", help="Realizar solo análisis comparativo sin procesar archivos PDF con base de datos existente")
    parser.add_argument("--api-analysis", action="store_true", help="Realizar análisis integrado con datos de la API de la UPM")
    parser.add_argument("--plan-code", type=str, default="10II", help="Código del plan de estudios para consultas API")
    

    args = parser.parse_args()
    
    # Comprobar si se ha proporcionado al menos una de las opciones requeridas
    if not any([args.pdf, args.dir, args.analyze_only, args.api_analysis]):
        parser.print_help()
        print("\nError: Debes especificar al menos un archivo PDF o un directorio, o la opción de análisis .")
        return 1
    

    # Procesar un solo archivo PDF
    if args.pdf:
        process_academic_report(args.pdf, args.output, args.db, not args.no_viz)
    
    # Procesar varios archivos PDF
    if args.dir:
        batch_process_directory(args.dir, args.output, args.db, not args.no_viz)
    
    # Solo realizar análisis
    if args.analyze_only:
        if not os.path.exists(args.db):
            print(f"Error: Archivo de la base de datos {args.db} no encontrado. Por favor, procesa los archivos PDF primero.")
            return 1
        
        perform_comparative_analysis(args.db, os.path.join(args.output, "comparative_analysis"))

    #solo realizar analisis de la API
    if args.api_analysis:
        if not os.path.exists(args.db):
            print(f"Error: Archivo de la base de datos {args.db} no encontrado. Por favor, procesa los archivos PDF primero.")
            return 1
        
        print(f"Realizando análisis integrado con datos de la API de la UPM (Plan: {args.plan_code})...")
        perform_api_integrated_analysis(args.db, os.path.join(args.output, "api_integrated_analysis"), args.plan_code)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())