import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
#Clase para crear las graficas 
class AcademicVisualizer:
    #crear prim las gráficas
    #Inicializar el visualizador con una conexión a la base de datos o dataframes
    #Cargar datos de un dataframe o la base de datos
    #Crear un dashboard de rendimiento
    #Crear visualizaciones de tendencias históricas
    #Crear visualizaciones de tasas de rendimiento
    #Crear un mapa de calor de tasas de rendimiento
    #Crear un gráfico de dispersión de rendimiento vs. absentismo
    #Crear un resumen de dashboard
    #Crear un resumen de dashboard con métricas clave
    #Crear un gráfico de distribución de rendimiento
    #Crear un gráfico de tendencias comparativas
    #Correr todas las visualizaciones
    
    def __init__(self, db_connection=None, output_dir="visualizations"):
        # Inicializar el visualizador con una conexión a la base de datos o dataframes
        self.db = db_connection
        self.output_dir = output_dir
        Path(output_dir).mkdir(exist_ok=True)
        
        # Configurar el estilo de visualización
        self.setup_style()
    

    #Configurar el estilo de las graficas
    def setup_style(self):
        sns.set_theme(style="whitegrid")
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        
        # Crear paletas de colores personalizadas
        self.performance_cmap = LinearSegmentedColormap.from_list("performance_cmap", ["#FF5A5F", "#FFDA6A", "#33CC66"])

        #Fix colors gammut (revisar colores)
        self.trend_colors = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC"]
    
    #Cargar datos de un dataframe o la database
    def load_data(self, subjects_df=None, historical_df=None):
        if subjects_df is not None:
            self.subjects_df = subjects_df
        elif self.db is not None:
            self.subjects_df = self.db.get_subjects()
        else:
            raise ValueError("No data source provided")
        
        if historical_df is not None:
            self.historical_df = historical_df
        elif self.db is not None:
            self.historical_df = self.db.get_historical_rates()
        else:
            self.historical_df = pd.DataFrame()
    

    def create_performance_dashboard(self):
        # Crear un dashboard de rendimiento
        if not hasattr(self, 'subjects_df'):
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Crear un canvas grande para el dashboard
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(2, 2, figure=fig, wspace=0.3, hspace=0.4)
        
        # Gráfico de tasas de rendimiento
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_performance_rates(ax1)
        
        # Gráfico de tasas de éxito
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_success_rates(ax2)
        
        # Gráfico de tasas de absentismo
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_absenteeism_rates(ax3)
        
        # Gráfico de distribución de matriculados
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_enrollment_distribution(ax4)
        
        # Añadir un título al dashboard
        fig.suptitle("Academic Performance Dashboard", fontsize=20, y=0.98)
        
        # Almacenar el dashboard
        plt.savefig(f"{self.output_dir}/performance_dashboard.png", dpi=300, bbox_inches="tight")
        plt.close()
    
    def _plot_performance_rates(self, ax):
        #Gráfica de tasas de rendimiento de todas las asignaturas
        if 'performance_rate' in self.subjects_df.columns:
            # Ordenar por tasa de rendimiento
            sorted_df = self.subjects_df.sort_values('performance_rate', ascending=False)
            
            # Grafica de barras horizontales (escala de color)
            bars = ax.barh(sorted_df['subject_name'], sorted_df['performance_rate'], 
                     color=plt.cm.RdYlGn(sorted_df['performance_rate']/100))
            
            # Añadir etiquetas de porcentaje
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                        f"{width:.1f}%", ha='left', va='center')
            
            ax.set_title("Tasas de rendimiento por asignatura", fontsize=14)
            ax.set_xlabel("Tasa de rendimiento  (%)")
            ax.set_xlim(0, 100)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    def _plot_success_rates(self, ax):
        # Gráfica de tasas de éxito de todas las asignaturas
        if 'success_rate' in self.subjects_df.columns:
            # Ordenar por tasa de exito
            sorted_df = self.subjects_df.sort_values('success_rate', ascending=False)
            
            # Grafica de barras horizontales (escala de color)
            bars = ax.barh(sorted_df['subject_name'], sorted_df['success_rate'], 
                     color=plt.cm.RdYlGn(sorted_df['success_rate']/100))
            
            # Añadir etiquetas de porcentaje
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                        f"{width:.1f}%", ha='left', va='center')
            
            ax.set_title("Tasa de exito por asignatura", fontsize=14)
            ax.set_xlabel("Tasa de exito (%)")
            ax.set_xlim(0, 100)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    def _plot_absenteeism_rates(self, ax):
        # Gráfica de tasas de absentismo de todas las asignaturas
        if 'absenteeism_rate' in self.subjects_df.columns:
            # Ordenar por tasa de absentismo (mayor es peor)
            sorted_df = self.subjects_df.sort_values('absenteeism_rate', ascending=False)
            
            # Grafica de barras horizontales (escala de color invertida ya que mayor es peor)
            bars = ax.barh(sorted_df['subject_name'], sorted_df['absenteeism_rate'], 
                     color=plt.cm.RdYlGn_r(sorted_df['absenteeism_rate']/20))  # Escalado a max 20%
            
            # Añadir etiquetas de porcentaje
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 0.2, bar.get_y() + bar.get_height()/2, 
                        f"{width:.1f}%", ha='left', va='center')
            
            ax.set_title("Tasas de absentismo por asignatura", fontsize=14)
            ax.set_xlabel("Tasa de absentismo (%)")
            ax.set_xlim(0, max(sorted_df['absenteeism_rate']) * 1.2)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    def _plot_enrollment_distribution(self, ax):
        # Gráfica de distribución de matriculados
        if 'enrolled' in self.subjects_df.columns:
            # Crear gráfica de tarta con la distribución de matriculados
            labels = self.subjects_df['subject_name']
            sizes = self.subjects_df['enrolled']
            
            # Calcular porcentajes
            percentages = [100 * size / sum(sizes) for size in sizes]
            
            # Crear gráfica de tarta
            wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct='%1.1f%%', 
                                             startangle=90, colors=plt.cm.tab10.colors)
            
            # Crear etiquetas de leyenda
            legend_labels = [f"{label} ({size} estudiantes)" for label, size in zip(labels, sizes)]
            ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            ax.set_title("Distribución de matriculación", fontsize=14)
            plt.setp(autotexts, size=10, weight="bold")
    
    # Crear graficas de tendencias historicas
    def create_historical_trends(self):
        if not hasattr(self, 'historical_df') or self.historical_df.empty:
            print("No hay datos historicos disponibles para dar grafica.")
            return
        
        # Tendencias historicas para cada asignatura y tipo de tasa
        for subject_code in self.historical_df['subject_code'].unique():
            self.plot_subject_trend(subject_code)
        
        # Crear un gráfico de tendencias comparativas
        self.plot_comparative_trends()
    

    # Grafica de tendencias historicas para una asignatura
    def plot_subject_trend(self, subject_code):
        subject_data = self.historical_df[self.historical_df['subject_code'] == subject_code]
        
        if subject_data.empty:
            return
        
        subject_name = subject_data['subject_name'].iloc[0]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for i, rate_type in enumerate(subject_data['rate_type'].unique()):
            rate_data = subject_data[subject_data['rate_type'] == rate_type].sort_values('academic_year')
            
            # Línea de trazado con marcadores
            line = ax.plot(rate_data['academic_year'], rate_data['value'], 
                    marker='o', linestyle='-', linewidth=2, 
                    color=self.trend_colors[i % len(self.trend_colors)],
                    label=rate_type)
            
            # añadir etiquetas de valor
            for x, y in zip(rate_data['academic_year'], rate_data['value']):
                ax.text(x, y + 1, f"{y:.1f}%", ha='center', va='bottom', fontsize=9)
        
        ax.set_title(f"Tendencia historica para {subject_name}", fontsize=16)
        ax.set_xlabel("Curso", fontsize=12)
        ax.set_ylabel("Tasa (%)", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Configurar limites del eje y
        min_val = max(0, subject_data['value'].min() - 5)
        max_val = min(100, subject_data['value'].max() + 5)
        ax.set_ylim(min_val, max_val)
        
        #Rotar etiquetas del eje x
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/trend_{subject_code}.png", dpi=300)
        plt.close()


    #Grafica de tendencias comparativas de todas las asignaturas por cada tipo de asignatura
    def plot_comparative_trends(self):
    
        if self.historical_df.empty:
            return
        
        # Obtener tipos de tasas
        rate_types = self.historical_df['rate_type'].unique()
        
        for rate_type in rate_types:
            # Enfocar los datos en el tipo de tasa
            rate_data = self.historical_df[self.historical_df['rate_type'] == rate_type]
            
            # Crear una tabla dinámica para facilitar el trazado
            pivot_data = rate_data.pivot_table(
                index='academic_year', 
                columns='subject_name', 
                values='value'
            )
            
            # Crear la gráfica de líneas
            fig, ax = plt.subplots(figsize=(14, 8))
            
            for i, column in enumerate(pivot_data.columns):
                ax.plot(pivot_data.index, pivot_data[column], 
                        marker='o', linestyle='-', linewidth=2,
                        color=self.trend_colors[i % len(self.trend_colors)],
                        label=column)
            
            ax.set_title(f"Comparativa de Tasas de {rate_type} entre asignaturas", fontsize=16)
            ax.set_xlabel("Curso", fontsize=12)
            ax.set_ylabel(f"Tasa de {rate_type} (%)", fontsize=12)
            ax.legend(fontsize=10, bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Configurar limites del eje y
            min_val = max(0, pivot_data.min().min() - 5)
            max_val = min(100, pivot_data.max().max() + 5)
            ax.set_ylim(min_val, max_val)
            
            # Rotar etiquetas del eje x
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/comparative_{rate_type}_trends.png", dpi=300)
            plt.close()
    
    def create_heatmap_visualization(self):
        if self.historical_df.empty:
            return
        
        # Obtener tipos de tasas
        rate_types = self.historical_df['rate_type'].unique()
        
        for rate_type in rate_types:
            # Filtrar datos para este tipo de tasa
            rate_data = self.historical_df[self.historical_df['rate_type'] == rate_type]
            
            # Crear una tabla dinámica para facilitar el trazado
            pivot_data = rate_data.pivot_table(
                index='subject_name', 
                columns='academic_year', 
                values='value'
            )
            
            # Ordenar por el año más reciente si hay datos
            if len(pivot_data.columns) > 0:
                latest_year = pivot_data.columns[-1]
                pivot_data = pivot_data.sort_values(by=latest_year, ascending=False)
            
            # Configurar el tamaño de la figura
            plt.figure(figsize=(12, len(pivot_data) * 0.5 + 2))
            
            # Elegir el mapa de colores apropiado
            # (RdYlGn para rendimiento/exito, RdYlGn_r para absentismo)
            cmap = plt.cm.RdYlGn_r if rate_type == 'absentismo' else plt.cm.RdYlGn
            
            #Crear el mapa de calor
            ax = sns.heatmap(pivot_data, annot=True, fmt=".1f", cmap=cmap, 
                        linewidths=0.5, cbar_kws={'label': f' tasa de {rate_type}  (%)'})
            
            ax.set_title(f"Mapa de calor de las tasas de {rate_type} A través de los años", fontsize=16)
            ax.set_ylabel("Asignatura")
            ax.set_xlabel("Curso")
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/heatmap_{rate_type}.png", dpi=300)
            plt.close()
    
    def create_performance_vs_absenteeism(self):
        # Crear un gráfico de dispersión de rendimiento vs. absentismo
        if not hasattr(self, 'subjects_df'):
            return
            
        if 'performance_rate' in self.subjects_df.columns and 'absenteeism_rate' in self.subjects_df.columns:
            plt.figure(figsize=(10, 8))
            
            # Crear un gráfico de dispersión
            ax = plt.scatter(self.subjects_df['absenteeism_rate'], 
                        self.subjects_df['performance_rate'],
                        s=self.subjects_df['enrolled'] / 5,  # Tamaño proporcional a matriculados
                        c=self.subjects_df['performance_rate'], 
                        cmap='RdYlGn',
                        alpha=0.7)
            
            # Añadir etiquetas de asignaturas
            for idx, row in self.subjects_df.iterrows():
                plt.annotate(row['subject_name'], 
                         xy=(row['absenteeism_rate'], row['performance_rate']),
                         xytext=(5, 5), textcoords='offset points')
            
            # Añadir líneas de referencia
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
            plt.axvline(x=10, color='gray', linestyle='--', alpha=0.5)
            
            # Añadir etiquetas de cuadrantes
            plt.text(max(self.subjects_df['absenteeism_rate'])*0.75, 75, 
                 "Rendimiento alto\nAbsentismo alto", 
                 ha='center', bbox=dict(facecolor='white', alpha=0.5))
            
            plt.text(max(self.subjects_df['absenteeism_rate'])*0.75, 25, 
                 "Rendimiento bajo\nAbsentismo alto", 
                 ha='center', bbox=dict(facecolor='white', alpha=0.5))
            
            plt.text(5, 75, 
                 "Rendimiento alto\nAbsentismo bajo", 
                 ha='center', bbox=dict(facecolor='white', alpha=0.5))
            
            plt.text(5, 25, 
                 " Rendimiento bajo\nAbsentismo bajo", 
                 ha='center', bbox=dict(facecolor='white', alpha=0.5))
            
            # Añadir etiquetas y título
            plt.xlabel("Tasa de Absentismo (%)")
            plt.ylabel("Tasa de Rendimiento (%)")
            plt.title("Rendimiento vs. Absentismo por Asignatura", fontsize=16)
            
            # Añadir barra de color
            cbar = plt.colorbar()
            cbar.set_label("Tasa de rendimiento (%)")
            
            # Añadir leyenda de tamaños
            sizes = [50, 100, 200, 400]
            labels = [str(size*5) for size in sizes]
            
            # Crear puntos de dispersión ficticios para la leyenda
            for size, label in zip(sizes, labels):
                plt.scatter([], [], s=size/5, c='gray', alpha=0.7, label=f'{label} students')
            
            plt.legend(title="Matriculacion", loc='upper right')
            
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            plt.savefig(f"{self.output_dir}/performance_vs_absenteeism.png", dpi=300)
            plt.close()


    # Crear un dashboard de resumen 
    def create_summary_dashboard(self):
        if not hasattr(self, 'subjects_df') or self.subjects_df.empty:
            return
            
        # Crear un canvas grande para el dashboard
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle("Dashboard de rendimiento academico", fontsize=20, y=0.98)
        
        # Crear una cuadrícula para el dashboard
        gs = gridspec.GridSpec(3, 4, figure=fig, wspace=0.3, hspace=0.4)
        
        # 1. Resumen de metricas clave
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_metrics_overview(ax1)
        
        # 2. Mejores y peores rendimientos
        ax2 = fig.add_subplot(gs[0, 2:])
        self._plot_top_bottom_performers(ax2)
        
        # 3. Resumen de rendimiento historico
        ax3 = fig.add_subplot(gs[1, :2])
        self._plot_historical_summary(ax3)
        
        # 4. Crear un gráfico de distribución de tasas de rendimiento
        ax4 = fig.add_subplot(gs[1, 2:])
        self._plot_performance_distribution(ax4)
        
        #5. Crear un cuadro de texto para puntos clave
        ax5 = fig.add_subplot(gs[2, :])
        self._add_key_insights(ax5)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # Ajustar el layout para incluir el título
        plt.savefig(f"{self.output_dir}/summary_dashboard.png", dpi=300)
        plt.close()
    
    def create_faculty_performance_correlation_plot(self, correlation_df):
        """
        Create visualization showing correlation between faculty changes and performance changes
        
        Parameters:
        - correlation_df: DataFrame with correlation data from API analysis
        """
        if correlation_df.empty:
            print("No hay datos disponibles para una correlación")
            return
        
        # Create scatter plot of faculty change vs performance change
        plt.figure(figsize=(12, 8))
        
        # Create a scatter plot with size based on enrolled students
        scatter = plt.scatter(
            correlation_df["faculty_percent_changed"], 
            correlation_df["performance_change"],
            s=100,  # Size of dots
            c=correlation_df["performance_change"],  # Color based on performance change
            cmap="RdYlGn",  # Red-Yellow-Green color map
            alpha=0.7
        )
        
        # Add labels for each point (subject name)
        for i, row in correlation_df.iterrows():
            plt.annotate(
                row["subject_name"], 
                (row["faculty_percent_changed"], row["performance_change"]),
                xytext=(5, 5),
                textcoords='offset points'
            )
        
        # Add a horizontal line at y=0
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # Add a vertical line at x=0
        plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        
        # Add quadrant labels
        plt.text(max(correlation_df["faculty_percent_changed"])*0.75, 
                max(correlation_df["performance_change"])*0.75,
                "Cambios en profesorado\nMejora rendimiento", 
                ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.5))
        
        plt.text(max(correlation_df["faculty_percent_changed"])*0.75, 
                min(correlation_df["performance_change"])*0.75,
                "Cambios en profesorado\nEmpeora rendimiento", 
                ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.5))
        
        plt.text(0, max(correlation_df["performance_change"])*0.75,
                "Sin cambios en profesorado\nMejora rendimiento", 
                ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.5))
        
        plt.text(0, min(correlation_df["performance_change"])*0.75,
                "Sin cambios en profesorado\nEmpeora rendimiento", 
                ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.5))
        
        # Add labels and title
        plt.xlabel("Porcentaje de cambio en profesorado (%)")
        plt.ylabel("Cambio en tasa de rendimiento (%)")
        plt.title("Correlación entre cambios en profesorado y rendimiento académico", fontsize=16)
        
        # Add color bar
        cbar = plt.colorbar(scatter)
        cbar.set_label("Cambio en rendimiento (%)")
        
        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/faculty_performance_correlation.png", dpi=300)
        plt.close()

    def create_evaluation_performance_correlation_plot(self, correlation_df):
        """
        Create visualization showing correlation between evaluation method changes and performance changes
        
        Parameters:
        - correlation_df: DataFrame with correlation data from API analysis
        """
        if correlation_df.empty:
            print("No hay datos de corrrelación disponibles para creacion de grafos")
            return
        
        # Group by evaluation changed flag and calculate mean performance change
        eval_group = correlation_df.groupby("evaluation_changed")["performance_change"].mean().reset_index()
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        
        bars = plt.bar(
            ["Sin cambios en evaluación", "Con cambios en evaluación"],
            eval_group["performance_change"],
            color=["skyblue", "coral"]
        )
        
        # Add data labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + (0.1 if height > 0 else -0.1),
                f'{height:.2f}%',
                ha='center', va='bottom' if height > 0 else 'top'
            )
        
        # Add horizontal line at y=0
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # Add labels and title
        plt.ylabel("Cambio promedio en rendimiento (%)")
        plt.title("Impacto de cambios en métodos de evaluación sobre el rendimiento", fontsize=16)
        
        # Add grid
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/evaluation_performance_correlation.png", dpi=300)
        plt.close()

    def create_subject_comparison_with_api_insights(self, correlation_df, historical_df):
        """
        Create an enhanced subject comparison with insights from API analysis
        
        Parameters:
        - correlation_df: DataFrame with correlation data from API analysis
        - historical_df: DataFrame with historical performance data
        """
        if correlation_df.empty or historical_df.empty:
            print("No hay datos disponibles para hacer comparacion de asignaturas")
            return
        
        # Calculate average performance change by subject
        avg_changes = correlation_df.groupby("subject_code").agg({
            "performance_change": "mean",
            "subject_name": "first",
            "faculty_changed": "sum",
            "evaluation_changed": "sum"
        }).reset_index()
        
        # Sort by performance change
        avg_changes = avg_changes.sort_values("performance_change", ascending=False)
        
        # Create bar chart
        plt.figure(figsize=(14, 8))
        
        # Create bars with colors based on faculty changes
        colors = ['coral' if fc > 0 else 'skyblue' for fc in avg_changes["faculty_changed"]]
        
        bars = plt.barh(
            avg_changes["subject_name"],
            avg_changes["performance_change"],
            color=colors
        )
        
        # Add data labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            label_text = f"{width:.2f}%"
            
            # Add faculty change info
            if avg_changes.iloc[i]["faculty_changed"] > 0:
                label_text += f" | 👨‍🏫"
            
            # Add evaluation change info
            if avg_changes.iloc[i]["evaluation_changed"] > 0:
                label_text += f" | 📝"
                
            plt.text(
                width + 0.1,
                bar.get_y() + bar.get_height()/2,
                label_text,
                va='center'
            )
        
        # Add vertical line at x=0
        plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        
        # Add labels and title
        plt.xlabel("Cambio promedio en rendimiento (%)")
        plt.title("Cambios en rendimiento por asignatura con insights de profesorado y evaluación", fontsize=16)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='coral', label='Con cambios en profesorado'),
            Patch(facecolor='skyblue', label='Sin cambios en profesorado'),
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        
        # Add grid
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/subject_comparison_with_insights.png", dpi=300)
        plt.close()

    # Funcion para crear las graficas basadas en el analisis de la API
    def create_api_insight_visualizations(self, correlation_df, historical_df):

        if correlation_df.empty:
            print("No hay datos de correlacion disponibles para las graficas de puntos de la API")
            return
        
        print("Creando visualizaciones de insights basados en la API...")
        
        # Create directory for API visualizations
        # Directorio para guardar las graficas de la API
        api_viz_dir = os.path.join(self.output_dir, "api_insights")
        os.makedirs(api_viz_dir, exist_ok=True)
        
        # Crear un visualizador temporal para las graficas de la API
        temp_visualizer = AcademicVisualizer(output_dir=api_viz_dir)
        
        # Crear grafica de correlacion entre profesorado y rendimiento
        temp_visualizer.create_faculty_performance_correlation_plot(correlation_df)
        
        # Crear grafica de correlacion entre evaluacion y rendimiento
        temp_visualizer.create_evaluation_performance_correlation_plot(correlation_df)
        
        # Crear comparacion de asignaturas con insights
        temp_visualizer.create_subject_comparison_with_api_insights(correlation_df, historical_df)
        
        print(f"Visualizaciones de insights guardadas en: {api_viz_dir}")

    # Grafico de resumen de metricas clave
    def _plot_metrics_overview(self, ax):
            if 'performance_rate' not in self.subjects_df.columns:
                return
                
            # Calcular metricas clave
            metrics = {
                'Rendimiento medio': self.subjects_df['performance_rate'].mean(),
                'Exito medio': self.subjects_df['success_rate'].mean() if 'success_rate' in self.subjects_df.columns else 0,
                'Absentismo medio': self.subjects_df['absenteeism_rate'].mean() if 'absenteeism_rate' in self.subjects_df.columns else 0,
                'MAtriculados totales': self.subjects_df['enrolled'].sum() if 'enrolled' in self.subjects_df.columns else 0
            }
            
            # Crear grafica de barras horizontales
            y_pos = range(len(metrics))
            values = list(metrics.values())
            labels = list(metrics.keys())
            
            bars = ax.barh(y_pos, values, align='center', 
                    color=['#33CC66', '#3399FF', '#FF5A5F', '#FFCC33'])
            
            # Añadir etiquetas de valor
            for i, bar in enumerate(bars):
                width = bar.get_width()
                if labels[i] == 'Matriculados totales':
                    ax.text(width * 1.02, bar.get_y() + bar.get_height()/2, 
                        f"{int(width):,}", ha='left', va='center', fontweight='bold')
                else:
                    ax.text(width * 1.02, bar.get_y() + bar.get_height()/2, 
                        f"{width:.1f}%", ha='left', va='center', fontweight='bold')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels)
            ax.invert_yaxis()  # Etiquetas invertidas
            ax.set_title("Resumen de metricas clave", fontsize=14)
            ax.set_xlabel("Valor")
            
            # Configurar limites del eje x basado en el valor maximo
            ax.set_xlim(0, max(values) * 1.3)
        
    # Grafica de los mejores y peores rendimientos
    def _plot_top_bottom_performers(self, ax):
            if 'performance_rate' not in self.subjects_df.columns or len(self.subjects_df) < 4:
                return
                
            # Ordenar por tasa de rendimiento
            sorted_df = self.subjects_df.sort_values('performance_rate')
            
            # Obtener los mejores y peores rendimientos (top 2)
            bottom_2 = sorted_df.head(2)
            top_2 = sorted_df.tail(2).iloc[::-1]  # Invertir para que el mejor rendimiento esté arriba
            
            # Combinar en un solo dataframe
            plot_df = pd.concat([top_2, bottom_2])
            plot_df['Category'] = ['Top 1', 'Top 2', '2º peor',  'Peor']
            
            # Crear la gráfica de barras horizontales
            bars = ax.barh(plot_df['Category'], plot_df['performance_rate'], 
                    color=['#33CC66', '#66CC99', '#FF9999', '#FF5A5F'])
            
            # añadir etiquetas de rendimiento
            for i, bar in enumerate(bars):
                width = bar.get_width()
                subject = plot_df.iloc[i]['subject_name']
                
                # Añadir nombre de la asignatura dentro de la barra si cabe, sino fuera
                if width > 15:  # Si la barra es suficientemente ancha
                    ax.text(width/2, bar.get_y() + bar.get_height()/2, 
                        f"{subject}\n{width:.1f}%", ha='center', va='center', color='white', fontweight='bold')
                else:
                    ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                        f"{subject} ({width:.1f}%)", ha='left', va='center')
            
            ax.set_title("Mejores y peores rendimientos", fontsize=14)
            ax.set_xlabel("Tasa de rendimiento (%)")
            ax.set_xlim(0, 100)
                

    # Grafico de tendencia de rendimiento historico
    def _plot_historical_summary(self, ax):
            if not hasattr(self, 'historical_df') or self.historical_df.empty:
                ax.text(0.5, 0.5, "No hay datos historicos disponibles", ha='center', va='center')
                return
                
            # Filtrar datos de rendimiento
            perf_data = self.historical_df[self.historical_df['rate_type'] == 'rendimiento']
            
            if perf_data.empty:
                ax.text(0.5, 0.5, "No hay datos historicos de rendimiento disponibles", ha='center', va='center')
                return
            
            # Calcular la tasa media de rendimiento por año
            yearly_avg = perf_data.groupby('academic_year')['value'].mean().reset_index()
            
            # Create line chart of average performance over time
            # Crear la gráfica de puntos de tasa media a traves de los años
            ax.plot(yearly_avg['academic_year'], yearly_avg['value'], 'o-', linewidth=2, color='#3399FF')
            
            # añadir etiquetas de valor
            for x, y in zip(yearly_avg['academic_year'], yearly_avg['value']):
                ax.text(x, y + 1, f"{y:.1f}%", ha='center', va='bottom')
            
            # añadir una línea horizontal para la media del último año
            latest_avg = yearly_avg['value'].iloc[-1] if not yearly_avg.empty else 0
            ax.axhline(y=latest_avg, color='gray', linestyle='--', alpha=0.5)
            
            ax.set_title("Tendencia de tasa de rendimiento media", fontsize=14)
            ax.set_xlabel("Curso")
            ax.set_ylabel("Tasa media de rendimiento (%)")
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Configurar limites del eje y
            ax.set_ylim(0, 100)
            
            # Rotar etiquetas del eje x
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
    # Crear un gráfico de distribución de tasas de rendimiento
    def _plot_performance_distribution(self, ax):

            if 'performance_rate' not in self.subjects_df.columns:
                return
                
            # Definir categorias de rendimiento
            performance_bins = [0, 30, 50, 70, 90, 100]
            performance_labels = ['Very Low (0-30%)', 'Low (30-50%)', 'Average (50-70%)', 
                                'High (70-90%)', 'Excellent (90-100%)']
            
            # Contar asignaturas en cada categoria
            self.subjects_df['category'] = pd.cut(
                self.subjects_df['performance_rate'], 
                bins=performance_bins, 
                labels=performance_labels, 
                include_lowest=True
            )
            
            category_counts = self.subjects_df['category'].value_counts().reindex(performance_labels).fillna(0)
            
            # Obtener colores de la paleta basado en categorias de rojo a verde
            colors = plt.cm.RdYlGn(np.linspace(0.1, 0.9, len(category_counts)))
            
            # Crear gráfica de tarta
            wedges, texts, autotexts = ax.pie(
                category_counts, 
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors
            )
            
            # Añadir etiquetas
            legend_labels = [f"{label} ({count:,.0f} subjects)" for label, count in zip(category_counts.index, category_counts)]
            ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            ax.set_title("Distribucion de tasas de rendimiento", fontsize=14)

    # añadir cuadro de texto de puntos clave
    def _add_key_insights(self, ax):

            # Esconder ejes
            ax.axis('off')
            
            # Calcular perspectivas
            if 'performance_rate' in self.subjects_df.columns:
                avg_performance = self.subjects_df['performance_rate'].mean()
                max_perf_subject = self.subjects_df.loc[self.subjects_df['performance_rate'].idxmax(), 'subject_name']
                max_performance = self.subjects_df['performance_rate'].max()
                min_perf_subject = self.subjects_df.loc[self.subjects_df['performance_rate'].idxmin(), 'subject_name']
                min_performance = self.subjects_df['performance_rate'].min()
                
                # Calcular tendencias si hay datos historicos disponibles
                trend_text = ""
                if hasattr(self, 'historical_df') and not self.historical_df.empty:
                    perf_data = self.historical_df[self.historical_df['rate_type'] == 'rendimiento']
                    if not perf_data.empty:
                        yearly_avg = perf_data.groupby('academic_year')['value'].mean()
                        if len(yearly_avg) >= 2:
                            latest_year = yearly_avg.index[-1]
                            previous_year = yearly_avg.index[-2]
                            change = yearly_avg[latest_year] - yearly_avg[previous_year]
                            trend_text = f"• Overall performance has {'increased' if change > 0 else 'decreased'} by {abs(change):.1f} percentage points compared to the previous year.\n"
                
                # Contar asignaturas con bajo rendimiento
                low_perf_count = len(self.subjects_df[self.subjects_df['performance_rate'] < 50])
                low_perf_percentage = (low_perf_count / len(self.subjects_df)) * 100 if len(self.subjects_df) > 0 else 0
                
                # generar texto de analisis
                insights_text = (
                    "PUNTOS CLAVE\n\n"
                    f"• Tasa de rendimiento media conjunta: {avg_performance:.1f}%\n"
                    f"• Asignatura con mejor rendimiento: {max_perf_subject} ({max_performance:.1f}%)\n"
                    f"• Asignatura que requiere atencion: {min_perf_subject} ({min_performance:.1f}%)\n"
                    f"• {low_perf_count} asignaturas ({low_perf_percentage:.1f}%) tienen tasa de rendimientos menores al 50%\n"
                    f"{trend_text}"
                )
                
                # anadir recomendaciones si datos de la tasa de absentismo estan disponibles
                if 'absenteeism_rate' in self.subjects_df.columns:
                    high_absence_subjects = self.subjects_df[self.subjects_df['absenteeism_rate'] > 10]
                    if not high_absence_subjects.empty:
                        highest_absence = high_absence_subjects['absenteeism_rate'].max()
                        highest_absence_subject = high_absence_subjects.loc[high_absence_subjects['absenteeism_rate'].idxmax(), 'subject_name']
                        
                        insights_text += (
                            f"• {len(high_absence_subjects)} asignaturas tienen tasa de absentismo elevadas (>10%)\n"
                            f"• Absentismo mas alto: {highest_absence_subject} ({highest_absence:.1f}%)\n"
                        )
                
                # Anadir recomendaciones
                insights_text += (
                    "\RECOMENDACIONES\n\n"
                    "1. Consider curriculum revisions or additional support for subjects with performance rates below 50%\n"
                    "2. Investigate causes of high absenteeism in problematic subjects\n"
                    "3. Share best practices from top-performing subjects across the department\n"
                    "4. Regularly monitor trends to identify early warning signs\n"
                )
                
                # anadir cuadro de texto
                props = dict(boxstyle='round', facecolor='white', alpha=0.9)
                ax.text(0.5, 0.5, insights_text, ha='center', va='center', 
                    fontsize=12, bbox=props, transform=ax.transAxes)


    #Generar todas las graficas        
    def run_all_visualizations(self):
            print("Generando dashboard de rendimiento...")
            self.create_performance_dashboard()
            
            print("Generando visualizaciones de tendencias historicas...")
            self.create_historical_trends()
            
            print("Generando visualizaciones de tabla de calor...")
            self.create_heatmap_visualization()
            
            #print("Generating performance vs. absenteeism plot...")
            #print("Generating performance vs. absenteeism plot...")
            #self.create_performance_vs_absenteeism()
            
            print("Generando dashboard resumen...")
            self.create_summary_dashboard()
            
            print("Visualizaciones creadas y guardadas en:", self.output_dir)



if __name__ == "__main__":
    # Datos de prueba de las asignaturas
    subjects_data = {
        'subject_code': ['105000005', '105000007', '105000012', '105000015', '105000159'],
        'subject_name': ['Cálculo', 'Probabilidades y Estadística I', 'Sistemas Digitales', 'Programación II', 'Interacción Persona - Ordenador'],
        'credits': [6, 6, 6, 6, 6],
        'enrolled': [455, 267, 313, 370, 259],
        'performance_rate': [31.94, 89.14, 63.26, 47.70, 94.21],
        'success_rate': [36.52, 92.97, 67.58, 53.50, 97.60],
        'absenteeism_rate': [12.56, 4.12, 6.39, 10.84, 3.47]
    }
    
    subjects_df = pd.DataFrame(subjects_data)
    
    # Datos de prueba sobre históricos
    historical_data = []
    for subject_code, subject_name in zip(subjects_data['subject_code'], subjects_data['subject_name']):
        for year in ['2020-21', '2021-22', '2022-23', '2023-24']:
            # Crea datos de prueba aleat
            perf_base = subjects_data['performance_rate'][subjects_data['subject_code'].index(subject_code)]
            success_base = subjects_data['success_rate'][subjects_data['subject_code'].index(subject_code)]
            absence_base = subjects_data['absenteeism_rate'][subjects_data['subject_code'].index(subject_code)]
            
            perf_variation = np.random.uniform(-5, 5)
            success_variation = np.random.uniform(-5, 5)
            absence_variation = np.random.uniform(-2, 2)
            
            # Tasa de rendimiento
            historical_data.append({
                'subject_code': subject_code,
                'subject_name': subject_name,
                'academic_year': year,
                'rate_type': 'rendimiento',
                'value': max(0, min(100, perf_base + perf_variation))
            })
            
            # Tasa de exito
            historical_data.append({
                'subject_code': subject_code,
                'subject_name': subject_name,
                'academic_year': year,
                'rate_type': 'éxito',
                'value': max(0, min(100, success_base + success_variation))
            })
            
            # Tasa de absentismo
            historical_data.append({
                'subject_code': subject_code,
                'subject_name': subject_name,
                'academic_year': year,
                'rate_type': 'absentismo',
                'value': max(0, min(20, absence_base + absence_variation))
            })
    
    historical_df = pd.DataFrame(historical_data)
    
    # Crear visualizador y generar visualizaciones
    visualizer = AcademicVisualizer(output_dir="visualization_examples")
    visualizer.load_data(subjects_df, historical_df)
    visualizer.run_all_visualizations()