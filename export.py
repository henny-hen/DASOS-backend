import os
import re
import ast
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

class CodeAnalyzer:
    def __init__(self, directory="."):
        self.directory = directory
        self.modules = {}
        self.function_calls = {}
        self.function_purposes = {}
        self.module_classes = {}
        self.class_methods = {}
    
    def analyze_files(self):
        """Analyze Python files in the directory"""
        for filename in os.listdir(self.directory):
            if filename.endswith('.py'):
                file_path = os.path.join(self.directory, filename)
                self._analyze_file(file_path, os.path.splitext(filename)[0])
    
    def _analyze_file(self, file_path, module_name):
        """Analyze a Python file to extract functions, classes, and function calls"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        try:
            tree = ast.parse(content)
            
            # Extract functions and classes in this module
            self.modules[module_name] = []
            self.module_classes[module_name] = []
            
            for node in ast.walk(tree):
                # Get function definitions
                if isinstance(node, ast.FunctionDef):
                    # Store function in module
                    self.modules[module_name].append(node.name)
                    
                    # Extract function docstring for purpose
                    docstring = ast.get_docstring(node)
                    if docstring:
                        first_line = docstring.split('\n')[0].strip()
                        self.function_purposes[f"{module_name}.{node.name}"] = first_line
                    
                    # Extract function calls within this function
                    self.function_calls[f"{module_name}.{node.name}"] = []
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            if isinstance(subnode.func, ast.Name):
                                called_func = subnode.func.id
                                self.function_calls[f"{module_name}.{node.name}"].append(called_func)
                            elif isinstance(subnode.func, ast.Attribute):
                                if isinstance(subnode.func.value, ast.Name):
                                    # This handles calls like module.function()
                                    called_module = subnode.func.value.id
                                    called_func = subnode.func.attr
                                    self.function_calls[f"{module_name}.{node.name}"].append(
                                        f"{called_module}.{called_func}")
                
                # Get class definitions
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    self.module_classes[module_name].append(class_name)
                    self.class_methods[f"{module_name}.{class_name}"] = []
                    
                    # Extract methods of this class
                    for subnode in node.body:
                        if isinstance(subnode, ast.FunctionDef):
                            method_name = subnode.name
                            self.class_methods[f"{module_name}.{class_name}"].append(method_name)
                            
                            # Extract function docstring for purpose
                            docstring = ast.get_docstring(subnode)
                            if docstring:
                                first_line = docstring.split('\n')[0].strip()
                                self.function_purposes[f"{module_name}.{class_name}.{method_name}"] = first_line
                            
                            # Extract function calls within this method
                            self.function_calls[f"{module_name}.{class_name}.{method_name}"] = []
                            for method_subnode in ast.walk(subnode):
                                if isinstance(method_subnode, ast.Call):
                                    if isinstance(method_subnode.func, ast.Name):
                                        called_func = method_subnode.func.id
                                        self.function_calls[f"{module_name}.{class_name}.{method_name}"].append(called_func)
                                    elif isinstance(method_subnode.func, ast.Attribute):
                                        if isinstance(method_subnode.func.value, ast.Name):
                                            called_obj = method_subnode.func.value.id
                                            called_method = method_subnode.func.attr
                                            self.function_calls[f"{module_name}.{class_name}.{method_name}"].append(
                                                f"{called_obj}.{called_method}")
        
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
    
    def generate_module_graph(self, output_file="module_graph.png"):
        """Generate a graph showing module dependencies"""
        G = nx.DiGraph()
        
        # Add all modules as nodes
        for module in self.modules:
            G.add_node(module)
        
        # Add edges for module dependencies
        for caller_module, functions in self.modules.items():
            for function in functions:
                if f"{caller_module}.{function}" in self.function_calls:
                    for called in self.function_calls[f"{caller_module}.{function}"]:
                        if '.' in called:
                            called_parts = called.split('.')
                            called_module = called_parts[0]
                            
                            if called_module in self.modules and called_module != caller_module:
                                G.add_edge(caller_module, called_module)
        
        # Draw the graph
        plt.figure(figsize=(12, 9))
        pos = graphviz_layout(G, prog="dot")
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=2000, arrows=True, arrowsize=20, 
                font_size=10, font_weight='bold')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Module graph saved to {output_file}")
    
    def generate_function_graph(self, output_file="function_graph.png"):
        """Generate a graph showing function calls"""
        G = nx.DiGraph()
        
        # Add nodes for all functions and methods
        for module, functions in self.modules.items():
            for function in functions:
                function_id = f"{module}.{function}"
                G.add_node(function_id, 
                          label=f"{function}\n({module})\n{self.function_purposes.get(function_id, '')}")
        
        # Add nodes for all class methods
        for class_id, methods in self.class_methods.items():
            module, class_name = class_id.split('.')
            for method in methods:
                method_id = f"{class_id}.{method}"
                G.add_node(method_id, 
                         label=f"{method}\n({class_name})\n{self.function_purposes.get(method_id, '')}")
        
        # Add edges for function calls
        for caller, called_list in self.function_calls.items():
            for called in called_list:
                if '.' in called:
                    # This is a call to a specific function or method
                    G.add_edge(caller, called)
                else:
                    # This is a call to a function in the same module or a built-in
                    for node in G.nodes():
                        if node.endswith(f".{called}"):
                            G.add_edge(caller, node)
        
        # Draw the graph (this will be large and complex)
        plt.figure(figsize=(24, 18))
        pos = graphviz_layout(G, prog="dot")
        
        # Draw nodes with labels showing function purpose
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1500)
        nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=15)
        
        # Draw labels with function purpose
        node_labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Function graph saved to {output_file}")
    
    def generate_simplified_flow_chart(self, output_file="flow_chart.png"):
        """Generate a simplified flow chart showing key functions and their purposes"""
        G = nx.DiGraph()
        
        # Map of main modules and their primary classes/functions
        key_components = {
            "main": ["main", "process_academic_report", "batch_process_directory", "perform_comparative_analysis", "perform_api_integrated_analysis"],
            "academic_data_extractor": ["AcademicDataExtractor", "AcademicDataAnalyzer"],
            "academic_database": ["AcademicDatabase"],
            "academic_visualizations": ["AcademicVisualizer"],
            "academic_api_extractor": ["AcademicApiExtractor"]
        }
        
        # Add nodes for key components
        for module, components in key_components.items():
            for component in components:
                node_id = f"{module}.{component}"
                
                # Check if it's a class or function
                is_class = False
                for class_id in self.class_methods:
                    if class_id == node_id:
                        is_class = True
                        break
                
                # Get label based on component type and purpose
                if is_class:
                    # For classes, add key methods
                    G.add_node(node_id, 
                             label=f"{component}\n({module})\nClass",
                             shape="box")
                    
                    # Add class methods as separate nodes
                    if node_id in self.class_methods:
                        for method in self.class_methods[node_id]:
                            method_id = f"{node_id}.{method}"
                            purpose = self.function_purposes.get(method_id, '')
                            
                            # Filter out common Python magic methods
                            if not method.startswith('__'):
                                G.add_node(method_id, 
                                        label=f"{method}\n{purpose}",
                                        shape="ellipse")
                                G.add_edge(node_id, method_id)
                else:
                    # For functions, add purpose
                    purpose = self.function_purposes.get(node_id, '')
                    G.add_node(node_id, 
                             label=f"{component}\n({module})\n{purpose}",
                             shape="ellipse")
        
        # Add edges for key function calls
        for caller, called_list in self.function_calls.items():
            if caller in G:
                for called in called_list:
                    if called in G:
                        G.add_edge(caller, called)
        
        # Create a pydot graph
        dot_graph = nx.nx_pydot.to_pydot(G)
        
        # Set node attributes
        for node in dot_graph.get_nodes():
            node_id = node.get_name().strip('"')
            if node_id in G:
                shape = G.nodes[node_id].get('shape', 'ellipse')
                node.set('shape', shape)
                
                label = G.nodes[node_id].get('label', node_id)
                node.set('label', label)
                
                # Set different colors for different modules
                module = node_id.split('.')[0]
                if module == "main":
                    node.set('fillcolor', 'lightblue')
                elif module == "academic_data_extractor":
                    node.set('fillcolor', 'lightgreen')
                elif module == "academic_database":
                    node.set('fillcolor', 'lightyellow')
                elif module == "academic_visualizations":
                    node.set('fillcolor', 'lightpink')
                elif module == "academic_api_extractor":
                    node.set('fillcolor', 'lightcoral')
                
                node.set('style', 'filled')
        
        # Save the graph
        dot_graph.write_png(output_file)
        print(f"Flow chart saved to {output_file}")

# Usage
analyzer = CodeAnalyzer()
analyzer.analyze_files()
analyzer.generate_module_graph("module_dependencies.png")
analyzer.generate_simplified_flow_chart("academic_toolkit_flow.png")