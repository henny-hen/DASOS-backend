import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
from pathlib import Path

class AdvancedStatisticalAnalysis:
    """
    Clase para realizar análisis estadísticos avanzados en datos académicos.
    Esta clase amplía las capacidades de análisis de la clase AcademicDataAnalyzer
    """
    
    def __init__(self, historical_df=None, correlation_df=None):
        """        

        Inicializa con DataFrames opcionales de datos históricos y de correlación.

        Parameters:
        - historical_df: DataFrame con datos históricos de rendimiento académico
        - correlation_df: DataFrame con correlaciones entre cambios de facultad/evaluación y rendimiento
        """
        self.historical_df = historical_df
        self.correlation_df = correlation_df
    
    def load_data(self, historical_df=None, correlation_df=None):
        """
        Carga los datos históricos y de correlación para el análisis.
        
        Parameters:
        - historical_df: Dataframe con datos históricos de rendimiento académico
        - correlation_df: Dataframe con correlaciones entre cambios de facultad/evaluación y rendimiento
        """
        if historical_df is not None:
            self.historical_df = historical_df
        
        if correlation_df is not None:
            self.correlation_df = correlation_df
    
    def perform_statistical_significance_tests(self):
        """
        Realiza pruebas t para determinar si las diferencias en el rendimiento
        entre períodos con y sin cambios son estadísticamente significativas.

        Esta función también calcula tamaños del efecto utilizando d de Cohen.
    
        
        Returns:
        - DataFrame con resultados de pruebas de significancia estadística
        """
        if self.correlation_df is None or self.correlation_df.empty:
            print("No hay datos de correlación disponibles para análisis")
            return pd.DataFrame()
        
        results = []
        
        # Agrupar por código de asignatura
        for subject_code in self.correlation_df["subject_code"].unique():
            subject_df = self.correlation_df[self.correlation_df["subject_code"] == subject_code]
            subject_name = subject_df.iloc[0]["subject_name"]
            
            # Analizar impacto de cambios de profesorado
            self._analyze_change_significance(
                subject_df, 
                subject_code, 
                subject_name, 
                "faculty_changed", 
                "Faculty Change Impact", 
                results
            )
            
            # Analizar impacto de cambios en la evaluación
            self._analyze_change_significance(
                subject_df, 
                subject_code, 
                subject_name, 
                "evaluation_changed", 
                "Evaluation Change Impact", 
                results
            )
        
        # También realizar análisis global para todos las asignaturas
        all_subjects_faculty = self._analyze_change_significance(
            self.correlation_df, 
            "ALL", 
            "All Subjects", 
            "faculty_changed", 
            "Faculty Change Impact (Global)", 
            results
        )
        
        all_subjects_eval = self._analyze_change_significance(
            self.correlation_df, 
            "ALL", 
            "All Subjects", 
            "evaluation_changed", 
            "Evaluation Change Impact (Global)", 
            results
        )
        
        return pd.DataFrame(results)
    
    def _analyze_change_significance(self, df, subject_code, subject_name, change_column, impact_type, results):
        """
        Función auxiliar para analizar la significancia de los cambios.
        
        Parameters:
        - df: DataFrame que contiene los datos de rendimiento
        - subject_code: Codigo de la asignatura
        - subject_name: Nombre de la asignatura
        - change_column: Columna que indica el cambio (e.g., "faculty_changed" o "evaluation_changed")
        - impact_type: Descripción del tipo de impacto (e.g., "Faculty Change Impact")
        - results: Lista para almacenar los resultados del análisis
        
        Returns:
        - Diccionario con el resultado del análisis para este cambio
        """
        # Obtener cambios de rendimiento con y sin el cambio especificado
        perf_with_change = df[df[change_column]]["performance_change"]
        perf_without_change = df[~df[change_column]]["performance_change"]
        
        # Valores predeterminados para el resultado
        result = {
            "subject_code": subject_code,
            "subject_name": subject_name,
            "impact_type": impact_type,
            "periods_with_change": len(perf_with_change),
            "periods_without_change": len(perf_without_change),
            "mean_with_change": perf_with_change.mean() if len(perf_with_change) > 0 else None,
            "mean_without_change": perf_without_change.mean() if len(perf_without_change) > 0 else None,
            "difference": None,
            "t_statistic": None,
            "p_value": None,
            "statistically_significant": None,
            "cohens_d": None,
            "effect_size_category": None
        }
        
        # Calcular la diferencia solo si ambos grupos tienen datos
        if len(perf_with_change) > 0 and len(perf_without_change) > 0:
            result["difference"] = result["mean_with_change"] - result["mean_without_change"]
        
        # Realizar la prueba t solo si ambos grupos tienen al menos 2 puntos de datos
        if len(perf_with_change) >= 2 and len(perf_without_change) >= 2:
            t_stat, p_value = stats.ttest_ind(perf_with_change, perf_without_change)
            
            # Calcular desviación estándar de ambos grupos
            std1, std2 = perf_with_change.std(), perf_without_change.std()
            n1, n2 = len(perf_with_change), len(perf_without_change)
            
            # Deviación estándar agrupada
            pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
            
            # Evitar división por cero
            if pooled_std > 0:
                cohens_d = (result["mean_with_change"] - result["mean_without_change"]) / pooled_std
            else:
                cohens_d = 0
            
            result.update({
                "t_statistic": t_stat,
                "p_value": p_value,
                "statistically_significant": p_value < 0.05,
                "cohens_d": cohens_d,
                "effect_size_category": self._categorize_effect_size(cohens_d)
            })
        
        results.append(result)
        return result
    
    def _categorize_effect_size(self, d):
        """
        Categorize effect size based on Cohen's d value.
        
        Parameters:
        - d: Cohen's d value
        
        Returns:
        - String describing effect size category
        """
        if d is None:
            return None
        
        abs_d = abs(d)
        if abs_d >= 0.8:
            return "Large"
        elif abs_d >= 0.5:
            return "Medium"
        elif abs_d >= 0.2:
            return "Small"
        else:
            return "Negligible"
    
    def perform_trend_analysis(self):
        """
        Perform advanced trend analysis on historical data.
        
        This function conducts formal tests for trend detection, including:
        - Linear regression with p-values and R-squared
        - Mann-Kendall test for consistent trend direction
        - Theil-Sen estimator for robust trend line fitting
        
        Returns:
        - DataFrame with trend analysis results
        """
        if self.historical_df is None or self.historical_df.empty:
            print("No historical data available for trend analysis")
            return pd.DataFrame()
        
        try:
            # Try to import pymannkendall, but handle gracefully if not available
            import pymannkendall as mk
            has_mk = True
        except ImportError:
            print("Warning: pymannkendall package not available, skipping Mann-Kendall test")
            has_mk = False
        
        results = []
        
        for subject_code in self.historical_df["subject_code"].unique():
            # Get performance data for this subject
            subject_data = self.historical_df[(self.historical_df["subject_code"] == subject_code) & 
                                           (self.historical_df["rate_type"] == "rendimiento")]
            
            if len(subject_data) >= 3:  # Need at least 3 points for meaningful trend analysis
                subject_data = subject_data.sort_values("academic_year")
                subject_name = subject_data.iloc[0]["subject_name"]
                
                # Convert years to numeric indices for regression
                years = list(range(len(subject_data)))
                values = subject_data["value"].values
                
                # Basic trend info
                result = {
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "num_years": len(subject_data),
                    "first_year": subject_data["academic_year"].iloc[0],
                    "last_year": subject_data["academic_year"].iloc[-1],
                    "first_value": values[0],
                    "last_value": values[-1],
                    "total_change": values[-1] - values[0],
                    "average_annual_change": (values[-1] - values[0]) / (len(values) - 1)
                }
                
                # Linear regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
                
                result.update({
                    "linear_slope": slope,
                    "r_squared": r_value**2,
                    "regression_p_value": p_value,
                    "slope_significant": p_value < 0.05
                })
                
                # Mann-Kendall test if available
                if has_mk:
                    try:
                        mk_result = mk.original_test(values)
                        result.update({
                            "mk_trend": mk_result.trend,
                            "mk_p_value": mk_result.p,
                            "mk_significant": mk_result.p < 0.05,
                            "mk_slope": mk_result.slope
                        })
                    except Exception as e:
                        print(f"Error performing Mann-Kendall test: {e}")
                
                # Theil-Sen estimator (more robust to outliers)
                try:
                    ts_result = stats.theilslopes(values, years)
                    result.update({
                        "ts_slope": ts_result[0],
                        "ts_intercept": ts_result[1],
                        "ts_low_slope": ts_result[2],
                        "ts_high_slope": ts_result[3]
                    })
                except Exception as e:
                    print(f"Error calculating Theil-Sen estimator: {e}")
                
                # Determine overall trend direction using multiple methods
                trend_direction = self._determine_trend_direction(result)
                result["trend_direction"] = trend_direction
                
                results.append(result)
        
        return pd.DataFrame(results)
    
    def _determine_trend_direction(self, result):
        """
        Determine overall trend direction using multiple methods.
        
        Parameters:
        - result: Dictionary containing various trend measurements
        
        Returns:
        - String indicating trend direction
        """
        # Check if we have Mann-Kendall results
        if "mk_trend" in result and result["mk_significant"]:
            # Use Mann-Kendall if it's statistically significant
            if result["mk_trend"] == "increasing":
                return "Improving"
            elif result["mk_trend"] == "decreasing":
                return "Declining"
            else:
                return "Stable"
        
        # Fall back to linear regression if significant
        if "slope_significant" in result and result["slope_significant"]:
            if result["linear_slope"] > 0:
                return "Improving"
            elif result["linear_slope"] < 0:
                return "Declining"
        
        # If no test is significant, use simple thresholds on average annual change
        if "average_annual_change" in result:
            if result["average_annual_change"] > 1:
                return "Improving"
            elif result["average_annual_change"] < -1:
                return "Declining"
        
        # Default if no clear trend
        return "Stable"
    
    def generate_trend_visualizations(self, output_dir="output/advanced_analysis"):
        """
        Generate advanced trend visualizations based on formal trend analysis.
        
        Parameters:
        - output_dir: Directory to save visualization files
        
        Returns:
        - Boolean indicating success
        """
        if self.historical_df is None or self.historical_df.empty:
            print("No historical data available for trend visualizations")
            return False
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get trend analysis results
        trend_results = self.perform_trend_analysis()
        
        if trend_results.empty:
            print("No trend analysis results available for visualization")
            return False
        
        # Generate visualizations for subjects with significant trends
        significant_trends = trend_results[
            (trend_results["slope_significant"] == True) | 
            (trend_results.get("mk_significant", False) == True)
        ]
        
        for _, row in significant_trends.iterrows():
            subject_code = row["subject_code"]
            subject_name = row["subject_name"]
            
            # Get historical data for this subject
            subject_data = self.historical_df[
                (self.historical_df["subject_code"] == subject_code) & 
                (self.historical_df["rate_type"] == "rendimiento")
            ].sort_values("academic_year")
            
            if len(subject_data) < 3:
                continue
            
            # Create the visualization
            plt.figure(figsize=(10, 6))
            
            # Plot actual data points
            years = list(range(len(subject_data)))
            values = subject_data["value"].values
            academic_years = subject_data["academic_year"].values
            
            plt.plot(years, values, 'o-', linewidth=2, color='#3498db', label='Actual Values')
            
            # Plot linear regression line
            slope = row["linear_slope"]
            intercept = row.get("linear_intercept", 0)
            if "linear_slope" in row:
                # Generate y values using the regression line
                reg_y = [slope * x + intercept for x in years]
                plt.plot(years, reg_y, '--', color='#e74c3c', linewidth=2, 
                         label=f'Linear Trend (slope={slope:.2f})')
            
            # Plot Theil-Sen line if available
            if "ts_slope" in row and "ts_intercept" in row:
                ts_slope = row["ts_slope"]
                ts_intercept = row["ts_intercept"]
                ts_y = [ts_slope * x + ts_intercept for x in years]
                plt.plot(years, ts_y, '-.', color='#2ecc71', linewidth=2, 
                         label=f'Theil-Sen Trend (slope={ts_slope:.2f})')
                
                # Add confidence interval for Theil-Sen
                if "ts_low_slope" in row and "ts_high_slope" in row:
                    low_slope = row["ts_low_slope"]
                    high_slope = row["ts_high_slope"]
                    plt.fill_between(
                        years,
                        [low_slope * x + ts_intercept for x in years],
                        [high_slope * x + ts_intercept for x in years],
                        color='#2ecc71', alpha=0.2, label='95% Confidence Interval'
                    )
            
            # Add trend direction and p-value annotations
            trend_text = f"Trend Direction: {row['trend_direction']}"
            if "r_squared" in row:
                trend_text += f"\nR² = {row['r_squared']:.3f}"
            if "regression_p_value" in row:
                trend_text += f"\np-value = {row['regression_p_value']:.3f}"
            if "mk_p_value" in row:
                trend_text += f"\nMann-Kendall p-value = {row['mk_p_value']:.3f}"
                
            plt.annotate(
                trend_text, 
                xy=(0.02, 0.02), 
                xycoords='axes fraction',
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8)
            )
            
            # Set chart properties
            plt.title(f'Advanced Trend Analysis: {subject_name}', fontsize=14)
            plt.xlabel('Year Index')
            plt.ylabel('Performance Rate (%)')
            
            # Set x-tick labels to actual academic years
            plt.xticks(years, academic_years, rotation=45)
            
            # Add grid and legend
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            
            # Save the figure
            plt.savefig(f"{output_dir}/trend_analysis_{subject_code}.png", dpi=300)
            print(f"Trend visualization for {subject_name} saved as trend_analysis_{subject_code}.png")
            plt.close()
        
        # Create summary visualization of trends across subjects
        self._create_trend_summary_visualization(trend_results, output_dir)
        
        return True
    
    def _create_trend_summary_visualization(self, trend_results, output_dir):
        """
        Create a summary visualization of trends across all subjects.
        
        Parameters:
        - trend_results: DataFrame with trend analysis results
        - output_dir: Directory to save the visualization
        """
        if trend_results.empty:
            print("No trend results available for summary visualization")
            return
            
        plt.figure(figsize=(12, 8))
        
        # Sort results by trend direction and slope magnitude
        trend_results['abs_slope'] = trend_results['linear_slope'].abs()
        sorted_results = trend_results.sort_values(['trend_direction', 'abs_slope'], ascending=[False, False])
        
        # Create bar chart of slopes
        subject_names = sorted_results['subject_name']
        slopes = sorted_results['linear_slope']
        
        # Define colors based on trend direction
        colors = ['#3498db' if direction == 'Improving' else 
                 '#e74c3c' if direction == 'Declining' else 
                 '#95a5a6' for direction in sorted_results['trend_direction']]
        
        # Create horizontal bar chart
        bars = plt.barh(subject_names, slopes, color=colors)
        
        # Add vertical line at x=0
        plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        
        # Add annotations for significant trends
        for i, (is_significant, slope) in enumerate(zip(sorted_results['slope_significant'], slopes)):
            if is_significant:
                plt.text(
                    slope + (0.2 if slope > 0 else -0.2), 
                    i, 
                    '*', 
                    ha='center', 
                    va='center', 
                    fontsize=14, 
                    fontweight='bold'
                )
        
        # Add a legend explaining the colors
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3498db', edgecolor='#3498db', label='Improving'),
            Patch(facecolor='#e74c3c', edgecolor='#e74c3c', label='Declining'),
            Patch(facecolor='#95a5a6', edgecolor='#95a5a6', label='Stable')
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        
        # Add annotations explaining the significance
        plt.annotate(
            '* Statistically significant trend (p < 0.05)',
            xy=(0.02, 0.02),
            xycoords='figure fraction',
            fontsize=10
        )
        
        # Set chart properties
        plt.title('Performance Trends Across Subjects', fontsize=14)
        plt.xlabel('Annual Rate of Change (percentage points per year)')
        plt.grid(True, axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f"{output_dir}/trend_summary.png", dpi=300)
        print("Trend summary visualization saved as trend_summary.png")
        plt.close()
    
    def generate_correlation_visualizations(self, output_dir="output/advanced_analysis"):
        """
        Generate advanced visualizations of correlation analysis with statistical indicators.
        
        Parameters:
        - output_dir: Directory to save visualization files
        
        Returns:
        - Boolean indicating success
        """
        if self.correlation_df is None or self.correlation_df.empty:
            print("No correlation data available for visualizations")
            return False
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get significance test results
        significance_results = self.perform_statistical_significance_tests()
        
        if significance_results.empty:
            print("No significance test results available for visualization")
            return False
        
        # Create global correlation visualization
        self._create_global_correlation_visualization(significance_results, output_dir)
        
        # Create faculty impact visualizations
        faculty_results = significance_results[significance_results['impact_type'].str.contains('Faculty')]
        self._create_impact_comparison_visualization(faculty_results, 'Faculty Change Impact', output_dir)
        
        # Create evaluation impact visualizations
        eval_results = significance_results[significance_results['impact_type'].str.contains('Evaluation')]
        self._create_impact_comparison_visualization(eval_results, 'Evaluation Change Impact', output_dir)
        
        # Create effect size visualization
        self._create_effect_size_visualization(significance_results, output_dir)
        
        return True
    
    def _create_global_correlation_visualization(self, significance_results, output_dir):
        """
        Create a visualization showing global correlation between changes and performance.
        
        Parameters:
        - significance_results: DataFrame with significance test results
        - output_dir: Directory to save the visualization
        """
        # Filter for global results
        global_results = significance_results[significance_results['subject_code'] == 'ALL']
        
        if global_results.empty:
            print("No global results available for visualization")
            return
        
        plt.figure(figsize=(10, 6))
        
        # Extract data for the visualization
        impact_types = global_results['impact_type'].str.replace(' (Global)', '')
        with_change = global_results['mean_with_change']
        without_change = global_results['mean_without_change']
        
        # Set up bar positions
        x = np.arange(len(impact_types))
        width = 0.35
        
        # Create grouped bar chart
        bars1 = plt.bar(x - width/2, with_change, width, label='With Changes', color='#3498db')
        bars2 = plt.bar(x + width/2, without_change, width, label='Without Changes', color='#95a5a6')
        
        # Add statistical significance markers
        for i, is_significant in enumerate(global_results['statistically_significant']):
            if is_significant:
                plt.text(i, max(with_change.iloc[i], without_change.iloc[i]) + 0.2, 
                         '*', ha='center', fontsize=16, fontweight='bold')
        
        # Add data labels on bars
        def add_labels(bars):
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=9)
        
        add_labels(bars1)
        add_labels(bars2)
        
        # Add horizontal line at y=0
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Set chart properties
        plt.title('Global Impact of Changes on Performance', fontsize=14)
        plt.xlabel('Type of Change')
        plt.ylabel('Average Performance Change (%)')
        plt.xticks(x, impact_types)
        plt.legend()
        
        # Add p-value annotations
        for i, row in global_results.iterrows():
            if pd.notnull(row['p_value']):
                plt.annotate(
                    f"p-value: {row['p_value']:.3f}\nEffect size: {row['effect_size_category']}",
                    xy=(i, -0.5),
                    ha='center',
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
                )
        
        # Add annotation explaining the significance marker
        plt.annotate(
            '* Statistically significant (p < 0.05)',
            xy=(0.02, 0.02),
            xycoords='figure fraction',
            fontsize=10
        )
        
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f"{output_dir}/global_correlation_impact.png", dpi=300)
        print("Global correlation visualization saved as global_correlation_impact.png")
        plt.close()
    
    def _create_impact_comparison_visualization(self, results, impact_type, output_dir):
        """
        Create a visualization comparing impact across subjects.
        
        Parameters:
        - results: DataFrame with significance test results
        - impact_type: String describing the type of impact
        - output_dir: Directory to save the visualization
        """
        # Filter out global results and those with the wrong impact type
        subject_results = results[
            (results['subject_code'] != 'ALL') & 
            (results['impact_type'].str.contains(impact_type.split()[0]))
        ]
        
        if subject_results.empty:
            print(f"No subject-specific results available for {impact_type} visualization")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Sort by difference magnitude
        subject_results['abs_difference'] = subject_results['difference'].abs()
        sorted_results = subject_results.sort_values('abs_difference', ascending=False)
        
        # Extract data for the visualization
        subject_names = sorted_results['subject_name']
        differences = sorted_results['difference']
        
        # Define colors based on significance and effect direction
        colors = []
        for _, row in sorted_results.iterrows():
            if pd.isnull(row['difference']):
                colors.append('#95a5a6')  # gray for null values
            elif row['statistically_significant']:
                colors.append('#3498db' if row['difference'] > 0 else '#e74c3c')  # blue/red for significant
            else:
                colors.append('#aed6f1' if row['difference'] > 0 else '#f5b7b1')  # light blue/red for non-significant
        
        # Create horizontal bar chart
        bars = plt.barh(subject_names, differences, color=colors)
        
        # Add vertical line at x=0
        plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        
        # Add effect size markers
        for i, row in enumerate(sorted_results.itertuples()):
            if pd.notnull(row.effect_size_category) and row.effect_size_category != 'Negligible':
                marker = '*' if row.effect_size_category == 'Small' else '**' if row.effect_size_category == 'Medium' else '***'
                plt.text(
                    row.difference + (0.2 if row.difference > 0 else -0.2), 
                    i, 
                    marker, 
                    ha='center', 
                    va='center', 
                    fontsize=10
                )
        
# Add a legend explaining the colors
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3498db', edgecolor='#3498db', label='Positive Impact (Significant)'),
            Patch(facecolor='#aed6f1', edgecolor='#aed6f1', label='Positive Impact (Not Significant)'),
            Patch(facecolor='#e74c3c', edgecolor='#e74c3c', label='Negative Impact (Significant)'),
            Patch(facecolor='#f5b7b1', edgecolor='#f5b7b1', label='Negative Impact (Not Significant)'),
            Patch(facecolor='#95a5a6', edgecolor='#95a5a6', label='Insufficient Data')
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        
        # Add annotations explaining the significance markers
        plt.annotate(
            '* Small Effect Size\n** Medium Effect Size\n*** Large Effect Size',
            xy=(0.02, 0.02),
            xycoords='figure fraction',
            fontsize=10
        )
        
        # Set chart properties
        clean_impact_type = impact_type.replace(" Change Impact", "")
        plt.title(f'Impact of {clean_impact_type} Changes on Performance by Subject', fontsize=14)
        plt.xlabel('Difference in Performance Change (percentage points)')
        plt.grid(True, axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the figure
        file_name = f"{clean_impact_type.lower().replace(' ', '_')}_impact_comparison.png"
        plt.savefig(f"{output_dir}/{file_name}", dpi=300)
        print(f"{impact_type} visualization saved as {file_name}")
        plt.close()
    
    def _create_effect_size_visualization(self, significance_results, output_dir):
        """
        Create a visualization showing effect sizes for both faculty and evaluation impacts.
        
        Parameters:
        - significance_results: DataFrame with significance test results
        - output_dir: Directory to save the visualization
        """
        # Filter for subject-specific results (not global) and where effect size is calculated
        subject_results = significance_results[
            (significance_results['subject_code'] != 'ALL') & 
            pd.notnull(significance_results['cohens_d'])
        ]
        
        if subject_results.empty:
            print("No subject-specific results available for effect size visualization")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Extract data for faculty and evaluation impacts
        faculty_results = subject_results[subject_results['impact_type'].str.contains('Faculty')]
        eval_results = subject_results[subject_results['impact_type'].str.contains('Evaluation')]
        
        # Set up scatter plot
        faculty_d = faculty_results['cohens_d']
        eval_d = eval_results['cohens_d']
        
        subjects = faculty_results['subject_name']
        
        # Define the scatter plot size based on number of data points
        s = 100
        
        # Create scatter plot
        sc = plt.scatter(faculty_d, eval_d, s=s, c=faculty_d*eval_d, cmap='RdYlGn', alpha=0.7)
        
        # Add vertical and horizontal lines at x=0 and y=0
        plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add quadrant labels
        plt.text(0.75*max(faculty_d), 0.75*max(eval_d), "Both Positive", 
                 ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5))
        plt.text(0.75*min(faculty_d), 0.75*max(eval_d), "Faculty Negative\nEvaluation Positive", 
                 ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5))
        plt.text(0.75*max(faculty_d), 0.75*min(eval_d), "Faculty Positive\nEvaluation Negative", 
                 ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5))
        plt.text(0.75*min(faculty_d), 0.75*min(eval_d), "Both Negative", 
                 ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5))
        
        # Add subject labels to the points
        for i, subj in enumerate(subjects):
            plt.annotate(subj, (faculty_d.iloc[i], eval_d.iloc[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Add effect size threshold lines
        for val in [0.2, 0.5, 0.8, -0.2, -0.5, -0.8]:
            if val > 0:
                label = f"Small (+{val})" if val == 0.2 else f"Medium (+{val})" if val == 0.5 else f"Large (+{val})"
            else:
                label = f"Small ({val})" if val == -0.2 else f"Medium ({val})" if val == -0.5 else f"Large ({val})"
            
            plt.axvline(x=val, color='gray', linestyle='--', alpha=0.5)
            plt.text(val, plt.ylim()[0], label, rotation=90, va='bottom', ha='center', fontsize=8)
            
            plt.axhline(y=val, color='gray', linestyle='--', alpha=0.5)
            plt.text(plt.xlim()[0], val, label, va='center', ha='left', fontsize=8)
        
        # Add color bar
        cbar = plt.colorbar(sc)
        cbar.set_label("Combined Effect (Faculty × Evaluation)")
        
        # Set chart properties
        plt.title('Comparison of Faculty and Evaluation Effect Sizes (Cohen\'s d)', fontsize=14)
        plt.xlabel('Faculty Change Effect Size')
        plt.ylabel('Evaluation Change Effect Size')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f"{output_dir}/effect_size_comparison.png", dpi=300)
        print("Effect size visualization saved.")
        plt.close()
    
    def run_complete_analysis(self, output_dir="output/advanced_analysis"):
        """
        Run a complete advanced statistical analysis.
        
        This function performs all available analyses and generates 
        reports and visualizations.
        
        Parameters:
        - output_dir: Directory to save analysis outputs
        
        Returns:
        - Boolean indicating success
        """
        # Check if we have the required data
        if self.historical_df is None or self.historical_df.empty:
            print("No historical data available for analysis")
            return False
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Perform trend analysis
        print("Performing advanced trend analysis...")
        trend_results = self.perform_trend_analysis()
        if not trend_results.empty:
            trend_results.to_csv(f"{output_dir}/trend_analysis_results.csv", index=False)
        
        # Generate trend visualizations
        print("Generating trend visualizations...")
        self.generate_trend_visualizations(output_dir)
        
        # If correlation data is available, analyze it too
        print(self.correlation_df)
        if self.correlation_df is not None and not self.correlation_df.empty:
            print("Performing statistical significance tests...")
            significance_results = self.perform_statistical_significance_tests()
            if not significance_results.empty:
                significance_results.to_csv(f"{output_dir}/significance_test_results.csv", index=False)
            
            print("Generating correlation visualizations...")
            self.generate_correlation_visualizations(output_dir)
            
            # Generate combined report
            self._generate_statistical_report(trend_results, significance_results, output_dir)
        else:
            # Generate only trend report
            self._generate_trend_report(trend_results, output_dir)
        
        print(f"Advanced statistical analysis completed. Results stored in: {output_dir}")
        return True
    
    def _generate_trend_report(self, trend_results, output_dir):
        """
        Generate a report focusing on trend analysis results.
        
        Parameters:
        - trend_results: DataFrame with trend analysis results
        - output_dir: Directory to save the report
        """
        if trend_results.empty:
            print("No trend analysis results available for report")
            return
        
        with open(f"{output_dir}/trend_analysis_report.txt", "w") as f:
            f.write("ADVANCED TREND ANALYSIS REPORT\n")
            f.write("==============================\n\n")
            
            # Overall statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-----------------\n\n")
            
            total_subjects = len(trend_results)
            improving = len(trend_results[trend_results['trend_direction'] == 'Improving'])
            declining = len(trend_results[trend_results['trend_direction'] == 'Declining'])
            stable = len(trend_results[trend_results['trend_direction'] == 'Stable'])
            
            sig_trends = len(trend_results[trend_results['slope_significant'] == True])
            
            f.write(f"Total subjects analyzed: {total_subjects}\n")
            f.write(f"Subjects with improving trends: {improving} ({improving/total_subjects*100:.1f}%)\n")
            f.write(f"Subjects with declining trends: {declining} ({declining/total_subjects*100:.1f}%)\n")
            f.write(f"Subjects with stable trends: {stable} ({stable/total_subjects*100:.1f}%)\n")
            f.write(f"Subjects with statistically significant trends: {sig_trends} ({sig_trends/total_subjects*100:.1f}%)\n\n")
            
            # Subjects with significant trends
            f.write("SIGNIFICANT TRENDS\n")
            f.write("-----------------\n\n")
            
            sig_df = trend_results[trend_results['slope_significant'] == True].sort_values('linear_slope', ascending=False)
            
            if not sig_df.empty:
                for i, row in sig_df.iterrows():
                    f.write(f"Subject: {row['subject_name']}\n")
                    f.write(f"  - Trend direction: {row['trend_direction']}\n")
                    f.write(f"  - Annual rate of change: {row['linear_slope']:.2f} percentage points\n")
                    f.write(f"  - Total change ({row['first_year']} to {row['last_year']}): {row['total_change']:.2f} percentage points\n")
                    f.write(f"  - Statistical confidence: R² = {row['r_squared']:.3f}, p-value = {row['regression_p_value']:.3f}\n")
                    if 'mk_trend' in row and pd.notnull(row['mk_trend']):
                        f.write(f"  - Mann-Kendall test: {row['mk_trend']} trend, p-value = {row['mk_p_value']:.3f}\n")
                    f.write("\n")
            else:
                f.write("No subjects show statistically significant trends.\n\n")
            
            # Most substantial changes (even if not statistically significant)
            f.write("SUBJECTS WITH LARGEST CHANGES\n")
            f.write("----------------------------\n\n")
            
            # Sort by absolute total change
            trend_results['abs_total_change'] = trend_results['total_change'].abs()
            largest_changes = trend_results.sort_values('abs_total_change', ascending=False).head(5)
            
            for i, row in largest_changes.iterrows():
                f.write(f"Subject: {row['subject_name']}\n")
                f.write(f"  - Total change ({row['first_year']} to {row['last_year']}): {row['total_change']:.2f} percentage points\n")
                f.write(f"  - Statistically significant: {'Yes' if row['slope_significant'] else 'No'}\n")
                f.write("\n")
            
            # Recommendations based on trend analysis
            f.write("RECOMMENDATIONS\n")
            f.write("--------------\n\n")
            
            # For improving subjects
            significant_improving = sig_df[sig_df['trend_direction'] == 'Improving']
            if not significant_improving.empty:
                f.write("1. Subjects with significant improvement:\n")
                for _, row in significant_improving.iterrows():
                    f.write(f"   - {row['subject_name']}: Identify and document successful practices for potential application to other subjects\n")
                f.write("\n")
            
            # For declining subjects
            significant_declining = sig_df[sig_df['trend_direction'] == 'Declining']
            if not significant_declining.empty:
                f.write("2. Subjects with significant decline:\n")
                for _, row in significant_declining.iterrows():
                    f.write(f"   - {row['subject_name']}: Conduct detailed review to identify causes and implement targeted interventions\n")
                f.write("\n")
            
            f.write("3. General recommendations:\n")
            f.write("   - For subjects with consistent trends, use forecasting to project future performance\n")
            f.write("   - For subjects with unstable trends, identify potential external factors influencing performance\n")
            f.write("   - Consider implementing threshold alerts for subjects approaching critical performance levels\n")
    
    def _generate_statistical_report(self, trend_results, significance_results, output_dir):
        """
        Genera un informe completo que combina los análisis de tendencias y correlaciones.
        
        Parameters:
        - trend_results: DataFrame con resultados del análisis de tendencias
        - significance_results: DataFrame con resultados de pruebas de significancia estadística
        - output_dir: Directory para guardar el informe
        """
        if trend_results.empty and significance_results.empty:
            print("No results available for comprehensive report")
            return
        
        with open(f"{output_dir}/comprehensive_statistical_report.txt", "w") as f:
            f.write("COMPREHENSIVE STATISTICAL ANALYSIS REPORT\n")
            f.write("=======================================\n\n")
            
            # Include trend analysis if available
            if not trend_results.empty:
                f.write("PART 1: TREND ANALYSIS\n")
                f.write("=====================\n\n")
                
                # Overall statistics
                f.write("Summary Statistics\n")
                f.write("-----------------\n\n")
                
                total_subjects = len(trend_results)
                improving = len(trend_results[trend_results['trend_direction'] == 'Improving'])
                declining = len(trend_results[trend_results['trend_direction'] == 'Declining'])
                stable = len(trend_results[trend_results['trend_direction'] == 'Stable'])
                
                sig_trends = len(trend_results[trend_results['slope_significant'] == True])
                
                f.write(f"Total subjects analyzed: {total_subjects}\n")
                f.write(f"Subjects with improving trends: {improving} ({improving/total_subjects*100:.1f}%)\n")
                f.write(f"Subjects with declining trends: {declining} ({declining/total_subjects*100:.1f}%)\n")
                f.write(f"Subjects with stable trends: {stable} ({stable/total_subjects*100:.1f}%)\n")
                f.write(f"Subjects with statistically significant trends: {sig_trends} ({sig_trends/total_subjects*100:.1f}%)\n\n")
                
                # Top significant trends
                sig_df = trend_results[trend_results['slope_significant'] == True].sort_values('linear_slope', ascending=False)
                
                if not sig_df.empty:
                    f.write("Key Significant Trends\n")
                    f.write("---------------------\n\n")
                    
                    # Top 3 improving
                    improving_sig = sig_df[sig_df['linear_slope'] > 0].head(3)
                    if not improving_sig.empty:
                        f.write("Most significantly improving subjects:\n")
                        for i, row in improving_sig.iterrows():
                            f.write(f"- {row['subject_name']}: +{row['linear_slope']:.2f} percentage points/year (p={row['regression_p_value']:.3f})\n")
                        f.write("\n")
                    
                    # Top 3 declining
                    declining_sig = sig_df[sig_df['linear_slope'] < 0].sort_values('linear_slope').head(3)
                    if not declining_sig.empty:
                        f.write("Most significantly declining subjects:\n")
                        for i, row in declining_sig.iterrows():
                            f.write(f"- {row['subject_name']}: {row['linear_slope']:.2f} percentage points/year (p={row['regression_p_value']:.3f})\n")
                        f.write("\n")
            
            # Include correlation analysis if available
            if not significance_results.empty:
                f.write("\nPART 2: CORRELATION ANALYSIS\n")
                f.write("==========================\n\n")
                
                # Global impact analysis
                global_results = significance_results[significance_results['subject_code'] == 'ALL']
                
                if not global_results.empty:
                    f.write("Global Impact Analysis\n")
                    f.write("---------------------\n\n")
                    
                    for i, row in global_results.iterrows():
                        impact_type = row['impact_type'].replace(" (Global)", "")
                        
                        f.write(f"{impact_type}:\n")
                        if pd.notnull(row['mean_with_change']) and pd.notnull(row['mean_without_change']):
                            f.write(f"- Performance with changes: {row['mean_with_change']:.2f}%\n")
                            f.write(f"- Performance without changes: {row['mean_without_change']:.2f}%\n")
                            
                            if pd.notnull(row['difference']):
                                f.write(f"- Difference: {row['difference']:.2f} percentage points\n")
                            
                            if pd.notnull(row['p_value']):
                                significance = "Statistically significant" if row['statistically_significant'] else "Not statistically significant"
                                f.write(f"- Statistical significance: {significance} (p-value = {row['p_value']:.3f})\n")
                            
                            if pd.notnull(row['cohens_d']) and pd.notnull(row['effect_size_category']):
                                f.write(f"- Effect size: {row['effect_size_category']} (Cohen's d = {row['cohens_d']:.3f})\n")
                                
                            f.write("\n")
                
                # Subjects with significant correlations
                subject_results = significance_results[
                    (significance_results['subject_code'] != 'ALL') & 
                    (significance_results['statistically_significant'] == True)
                ]
                
                if not subject_results.empty:
                    f.write("Subjects with Significant Correlations\n")
                    f.write("------------------------------------\n\n")
                    
                    for i, row in subject_results.iterrows():
                        f.write(f"Subject: {row['subject_name']}\n")
                        f.write(f"- Impact type: {row['impact_type']}\n")
                        f.write(f"- Difference: {row['difference']:.2f} percentage points\n")
                        f.write(f"- Statistical significance: p-value = {row['p_value']:.3f}\n")
                        f.write(f"- Effect size: {row['effect_size_category']} (Cohen's d = {row['cohens_d']:.3f})\n")
                        f.write("\n")
            
            # Combined insights if both analyses are available
            if not trend_results.empty and not significance_results.empty:
                f.write("\nPART 3: COMBINED INSIGHTS\n")
                f.write("========================\n\n")
                
                # Find subjects with both significant trends and correlations
                trend_subjects = set(trend_results[trend_results['slope_significant'] == True]['subject_code'])
                correlation_subjects = set(subject_results['subject_code'])
                
                dual_significant = trend_subjects.intersection(correlation_subjects)
                
                if dual_significant:
                    f.write("Subjects with Both Significant Trends and Correlations\n")
                    f.write("---------------------------------------------------\n\n")
                    
                    for subject_code in dual_significant:
                        trend_row = trend_results[trend_results['subject_code'] == subject_code].iloc[0]
                        corr_rows = subject_results[subject_results['subject_code'] == subject_code]
                        
                        f.write(f"Subject: {trend_row['subject_name']}\n")
                        f.write(f"- Trend: {trend_row['trend_direction']} at {trend_row['linear_slope']:.2f} points/year (p={trend_row['regression_p_value']:.3f})\n")
                        
                        for i, row in corr_rows.iterrows():
                            f.write(f"- {row['impact_type']}: {row['difference']:.2f} percentage points (p={row['p_value']:.3f})\n")
                        
                        f.write(f"- COMBINED INSIGHT: Changes in {', '.join(corr_rows['impact_type'])} may be driving the {trend_row['trend_direction'].lower()} trend\n")
                        f.write("\n")
                
                # Generate comprehensive recommendations
                f.write("Comprehensive Recommendations\n")
                f.write("----------------------------\n\n")
                
                # Get global impact results
                try:
                    faculty_global = global_results[global_results['impact_type'].str.contains('Faculty')].iloc[0]
                    faculty_positive = faculty_global['difference'] > 0 if pd.notnull(faculty_global['difference']) else False
                except (IndexError, KeyError):
                    faculty_positive = None
                
                try:
                    eval_global = global_results[global_results['impact_type'].str.contains('Evaluation')].iloc[0]
                    eval_positive = eval_global['difference'] > 0 if pd.notnull(eval_global['difference']) else False
                except (IndexError, KeyError):
                    eval_positive = None
                
                # Faculty recommendations
                if faculty_positive is not None:
                    if faculty_positive:
                        f.write("1. Faculty Management:\n")
                        f.write("   - Consider strategic faculty renewal in subjects with declining performance\n")
                        f.write("   - Implement knowledge transfer protocols to preserve institutional knowledge during transitions\n")
                        f.write("   - Analyze which faculty changes were most beneficial to replicate success factors\n")
                    else:
                        f.write("1. Faculty Management:\n")
                        f.write("   - Prioritize faculty stability and continuity in teaching assignments\n")
                        f.write("   - Invest in professional development for existing faculty rather than replacement\n")
                        f.write("   - Implement mentoring programs to support new faculty during transition periods\n")
                    f.write("\n")
                
                # Evaluation recommendations
                if eval_positive is not None:
                    if eval_positive:
                        f.write("2. Evaluation Methods:\n")
                        f.write("   - Encourage innovation in evaluation approaches, particularly in stagnant subjects\n")
                        f.write("   - Document and share successful evaluation practices across departments\n")
                        f.write("   - Consider a systematic review of evaluation methods in declining subjects\n")
                    else:
                        f.write("2. Evaluation Methods:\n")
                        f.write("   - Standardize effective evaluation methods across similar subjects\n")
                        f.write("   - Introduce changes gradually with careful monitoring of impact\n")
                        f.write("   - Ensure consistent communication of evaluation criteria to students\n")
                    f.write("\n")
                
                # Recommendations for specific subject categories
                f.write("3. Targeted Interventions:\n")
                
                # For subjects with significant positive trends
                if 'improving_sig' in locals() and not improving_sig.empty:
                    f.write("   a. For significantly improving subjects:\n")
                    f.write("      - Document and analyze success factors that could be transferred\n")
                    f.write("      - Set stretch goals to maintain momentum\n")
                    f.write("\n")
                
                # For subjects with significant negative trends
                if 'declining_sig' in locals() and not declining_sig.empty:
                    f.write("   b. For significantly declining subjects:\n")
                    f.write("      - Implement immediate intervention strategies\n")
                    f.write("      - Consider structural changes informed by correlation analysis\n")
                    f.write("\n")
                
                # For subjects with both significant trends and correlations
                if dual_significant:
                    f.write("   c. For subjects with both significant trends and correlations:\n")
                    f.write("      - Leverage identified correlations to amplify positive trends or reverse negative trends\n")
                    f.write("      - Develop customized improvement plans based on statistical findings\n")
                    f.write("\n")