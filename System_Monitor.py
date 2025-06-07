import customtkinter as ctk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import time
from datetime import datetime
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
import os
import platform
import ctypes
import networkx as nx
import collections

class ThemeManager:
    def __init__(self):
        self.dark_theme = {
            "bg": "#0A1929", 
            "surface": "#132F4C", 
            "accent": "#007FFF", 
            "accent_secondary": "#00C6FF", 
            "text": "#FFFFFF",
            "text_secondary": "#B2BAC2",
            "border": "#1E4976",  
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#FF5252",
            "gradient": ["#007FFF", "#00C6FF"]  
        }
        
        self.light_theme = {
            "bg": "#F3F6F9", 
            "surface": "#FFFFFF",
            "accent": "#0059B2",  
            "accent_secondary": "#007FFF",
            "text": "#1A2027",
            "text_secondary": "#3E5060",
            "border": "#E7EBF0",
            "success": "#2E7D32",
            "warning": "#ED6C02",
            "error": "#D32F2F",
            "gradient": ["#0059B2", "#007FFF"]
        }
        
        self.current_theme = self.dark_theme
        self.is_dark = True

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.current_theme = self.dark_theme if self.is_dark else self.light_theme
        return self.current_theme

class MetricBox(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        
        main_window = self.winfo_toplevel()
        colors = main_window.colors
        
        self.configure(
            fg_color=colors["surface"],
            corner_radius=15,
            border_width=1,
            border_color=colors["border"]
        )
        
        gradient_canvas = ctk.CTkCanvas(
            self,
            height=4,
            width=self.winfo_width(),
            highlightthickness=0
        )
        gradient_canvas.pack(fill="x", side="top")
        
        def create_gradient():
            width = gradient_canvas.winfo_width()
            height = 4
            gradient_canvas.delete("gradient")
            
            for i in range(width):
                x = i / width
                r1, g1, b1 = tuple(int(colors["gradient"][0].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                r2, g2, b2 = tuple(int(colors["gradient"][1].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                r = int(r1 + (r2-r1) * x)
                g = int(g1 + (g2-g1) * x)
                b = int(b1 + (b2-b1) * x)
                color = f'#{r:02x}{g:02x}{b:02x}'
                gradient_canvas.create_line(i, 0, i, height, fill=color, tags="gradient")
        
        gradient_canvas.bind('<Configure>', lambda e: create_gradient())
        
        icons = {
            "CPU": "⚡", "Memory": "💾", "Disk": "💿",
            "Virtual Memory": "📊", "Core Count": "🔢",
            "Thread Count": "🧵", "CPU Usage": "📈",
            "CPU Frequency": "⚙️"
        }
        
        icon = icons.get(title, "📊")
        
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(15,5))
        
        icon_label = ctk.CTkLabel(
            title_frame,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="left", padx=5)
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["accent"]
        )
        self.title_label.pack(side="left", padx=5)
        
        value_frame = ctk.CTkFrame(self, fg_color="transparent")
        value_frame.pack(pady=(5,15))
        
        self.value_label = ctk.CTkLabel(
            value_frame,
            text="--",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=colors["text"]
        )
        self.value_label.pack()

class GraphFrame(ctk.CTkFrame):
    def __init__(self, master, title, ylabel, **kwargs):
        super().__init__(master, **kwargs)
        
        main_window = self.winfo_toplevel()
        colors = main_window.colors
        
        self.configure(
            fg_color=colors["surface"],
            corner_radius=15,
            border_width=1,
            border_color=colors["border"]
        )
        
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(15,5))
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors["accent"]
        )
        title_label.pack(side="left")
        
        zoom_frame = ctk.CTkFrame(header, fg_color="transparent")
        zoom_frame.pack(side="right")
        
        ranges = ["1m", "5m", "15m", "1h"]
        self.time_buttons = {}
        for r in ranges:
            btn = ctk.CTkButton(
                zoom_frame,
                text=r,
                width=45,
                height=28,
                corner_radius=8,
                fg_color=colors["surface"],
                hover_color=colors["accent"],
                text_color=colors["text"],
                font=ctk.CTkFont(size=12, weight="bold"),
                border_width=1,
                border_color=colors["border"]
            )
            btn.pack(side="left", padx=2)
            self.time_buttons[r] = btn
        
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        self.ax.set_facecolor(colors["surface"])
        self.fig.patch.set_facecolor(colors["surface"])
        
        self.ax.grid(True, linestyle='--', alpha=0.2, color=colors["border"])
        self.ax.tick_params(colors=colors["text"], labelsize=9)
        
        for spine in self.ax.spines.values():
            spine.set_color(colors["border"])
            spine.set_linewidth(0.5)

class PieChartFrame(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.title_label = ctk.CTkLabel(
            self, 
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax.axis('equal')  

    def update_chart(self, labels, sizes, colors):
        self.ax.clear()
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        self.ax.set_title("Usage Distribution")
        self.canvas.draw()

class AnalysisSection(ctk.CTkFrame):
    def __init__(self, master, colors, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.grid_columnconfigure((0, 1), weight=1)
        
        self.memory_leak_frame = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        self.memory_leak_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.graph_frame = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        self.graph_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.setup_memory_leak_detection()
        self.setup_acyclic_graph()
        
        self.memory_history = []
        self.process_graph = nx.DiGraph()
        self.update_thread = Thread(target=self.update_analysis, daemon=True)
        self.update_thread.start()

    def setup_memory_leak_detection(self):
        title = ctk.CTkLabel(
            self.memory_leak_frame,
            text="Memory Leak Detection",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(pady=10)
        
        self.memory_plot = GraphFrame(self.memory_leak_frame, "Memory Usage Trend", "Memory (MB)")
        self.memory_plot.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.leak_status = ctk.CTkLabel(
            self.memory_leak_frame,
            text="Status: Monitoring...",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text"]
        )
        self.leak_status.pack(pady=10)
        
        self.leak_details = ctk.CTkTextbox(
            self.memory_leak_frame,
            height=100,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.leak_details.pack(fill="x", padx=10, pady=10)
        
    def setup_acyclic_graph(self):
        title = ctk.CTkLabel(
            self.graph_frame,
            text="Process Dependency Graph",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(pady=10)
        
        self.graph_canvas = ctk.CTkCanvas(
            self.graph_frame,
            bg=self.colors["surface"],
            highlightthickness=0
        )
        self.graph_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.graph_controls = ctk.CTkFrame(self.graph_frame, fg_color="transparent")
        self.graph_controls.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            self.graph_controls,
            text="Refresh Graph",
            command=self.update_process_graph,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_secondary"]
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            self.graph_controls,
            text="Detect Cycles",
            command=self.detect_cycles,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_secondary"]
        ).pack(side="left", padx=5)

    def update_analysis(self):
        while True:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                current_memory = memory_info.rss / (1024 * 1024)  # Convert to MB
                
                self.memory_history.append(current_memory)
                if len(self.memory_history) > 60:
                    self.memory_history.pop(0)
                
                self.update_memory_plot()
                self.check_memory_leak()
                self.update_process_graph()
                
                time.sleep(2)
            except Exception as e:
                print(f"Error in analysis update: {e}")
                time.sleep(2)

    def update_memory_plot(self):
        self.memory_plot.ax.clear()
        self.memory_plot.ax.plot(self.memory_history, color=self.colors["accent"], linewidth=2)
        self.memory_plot.ax.set_title("Memory Usage Trend", color=self.colors["text"])
        self.memory_plot.ax.set_xlabel("Time (s)", color=self.colors["text"])
        self.memory_plot.ax.set_ylabel("Memory (MB)", color=self.colors["text"])
        self.memory_plot.ax.tick_params(colors=self.colors["text"])
        self.memory_plot.canvas.draw()

    def check_memory_leak(self):
        if len(self.memory_history) < 10:
            return
        
        recent_memory = self.memory_history[-10:]
        slope = np.polyfit(range(len(recent_memory)), recent_memory, 1)[0]
        
        if slope > 1.0:  # Memory increasing by more than 1MB per sample
            self.leak_status.configure(
                text="Status: Potential Memory Leak Detected!",
                text_color=self.colors["error"]
            )
            self.leak_details.delete("1.0", "end")
            self.leak_details.insert("1.0", 
                f"Memory growth rate: {slope:.2f} MB/sample\n"
                f"Current memory: {self.memory_history[-1]:.2f} MB\n"
                f"Total growth: {self.memory_history[-1] - self.memory_history[0]:.2f} MB"
            )
        else:
            self.leak_status.configure(
                text="Status: No Memory Leak Detected",
                text_color=self.colors["success"]
            )

    def update_process_graph(self):
        try:
            self.process_graph.clear()
            
            for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                try:
                    self.process_graph.add_node(
                        proc.info['pid'],
                        name=proc.info['name']
                    )
                    
                    if proc.info['ppid']:
                        self.process_graph.add_edge(
                            proc.info['ppid'],
                            proc.info['pid']
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.draw_graph()
        except Exception as e:
            print(f"Error updating process graph: {e}")

    def draw_graph(self):
        self.graph_canvas.delete("all")
        
        if not self.process_graph.nodes():
            return
            
        pos = nx.spring_layout(self.process_graph)
        
        # Draw edges
        for edge in self.process_graph.edges():
            x1, y1 = pos[edge[0]]
            x2, y2 = pos[edge[1]]
            
            # Scale and center the coordinates
            x1 = (x1 + 1) * self.graph_canvas.winfo_width() / 2
            y1 = (y1 + 1) * self.graph_canvas.winfo_height() / 2
            x2 = (x2 + 1) * self.graph_canvas.winfo_width() / 2
            y2 = (y2 + 1) * self.graph_canvas.winfo_height() / 2
            
            self.graph_canvas.create_line(
                x1, y1, x2, y2,
                fill=self.colors["accent"],
                width=2,
                arrow="last"
            )
        
        # Draw nodes
        for node in self.process_graph.nodes():
            x, y = pos[node]
            x = (x + 1) * self.graph_canvas.winfo_width() / 2
            y = (y + 1) * self.graph_canvas.winfo_height() / 2
            
            self.graph_canvas.create_oval(
                x-20, y-20, x+20, y+20,
                fill=self.colors["surface"],
                outline=self.colors["accent"]
            )
            
            self.graph_canvas.create_text(
                x, y,
                text=str(node),
                fill=self.colors["text"]
            )

    def detect_cycles(self):
        try:
            cycles = list(nx.simple_cycles(self.process_graph))
            if cycles:
                message = "Cycles detected in process graph!\n"
                for cycle in cycles:
                    message += f"Cycle: {' -> '.join(map(str, cycle))}\n"
            else:
                message = "No cycles detected in process graph."
            
            self.leak_details.delete("1.0", "end")
            self.leak_details.insert("1.0", message)
        except Exception as e:
            self.leak_details.delete("1.0", "end")
            self.leak_details.insert("1.0", f"Error detecting cycles: {str(e)}")

class AlgorithmSection(ctk.CTkFrame):
    def __init__(self, master, colors, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create left panel for algorithm selection and controls
        self.control_panel = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        self.control_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create right panel for visualization
        self.visualization_panel = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        self.visualization_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.setup_control_panel()
        self.setup_visualization_panel()
        
        # Initialize algorithm data
        self.current_algorithm = None
        self.animation_thread = None
        self.is_animating = False

    def setup_control_panel(self):
        # Algorithm categories
        categories = {
            "Divide and Conquer": ["Merge Sort", "Quick Sort", "Strassen's Matrix Multiplication"],
            "Decrease and Conquer": ["Insertion Sort", "DFS", "BFS", "Topological Sort"],
            "Transform and Conquer": ["Heap Sort", "Presorting"],
            "Dynamic Programming": ["Binomial Coefficient", "Floyd-Warshall", "0/1 Knapsack"],
            "Greedy Algorithms": ["Prim's MST", "Dijkstra's", "Huffman Coding"],
            "Backtracking": ["N-Queens", "Subset Sum"],
            "Branch and Bound": ["TSP", "Assignment Problem"]
        }
        
        # Create category selection
        self.category_var = ctk.StringVar(value="Divide and Conquer")
        category_label = ctk.CTkLabel(
            self.control_panel,
            text="Select Category:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        category_label.pack(pady=(10, 5))
        
        category_menu = ctk.CTkOptionMenu(
            self.control_panel,
            values=list(categories.keys()),
            variable=self.category_var,
            command=self.update_algorithm_list
        )
        category_menu.pack(pady=(0, 10))
        
        # Create algorithm selection
        self.algorithm_var = ctk.StringVar()
        algorithm_label = ctk.CTkLabel(
            self.control_panel,
            text="Select Algorithm:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        algorithm_label.pack(pady=(10, 5))
        
        self.algorithm_menu = ctk.CTkOptionMenu(
            self.control_panel,
            values=categories[self.category_var.get()],
            variable=self.algorithm_var,
            command=self.on_algorithm_select
        )
        self.algorithm_menu.pack(pady=(0, 10))
        
        # Input controls
        self.input_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=10, pady=10)
        
        self.input_label = ctk.CTkLabel(
            self.input_frame,
            text="Input:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        )
        self.input_label.pack(side="left", padx=5)
        
        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter input...",
            width=150
        )
        self.input_entry.pack(side="left", padx=5)
        
        # Control buttons
        self.button_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="Start",
            command=self.start_algorithm,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_secondary"]
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            self.button_frame,
            text="Stop",
            command=self.stop_algorithm,
            fg_color=self.colors["error"],
            hover_color=self.colors["error"]
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Speed control
        self.speed_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.speed_frame.pack(fill="x", padx=10, pady=10)
        
        self.speed_label = ctk.CTkLabel(
            self.speed_frame,
            text="Animation Speed:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        )
        self.speed_label.pack(side="left", padx=5)
        
        self.speed_slider = ctk.CTkSlider(
            self.speed_frame,
            from_=0.1,
            to=2.0,
            number_of_steps=19,
            width=150
        )
        self.speed_slider.pack(side="left", padx=5)
        self.speed_slider.set(1.0)
        
        # Status display
        self.status_text = ctk.CTkTextbox(
            self.control_panel,
            height=100,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.status_text.pack(fill="x", padx=10, pady=10)

    def setup_visualization_panel(self):
        # Create matplotlib figure for visualization
        self.fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self.visualization_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Set theme colors
        self.fig.patch.set_facecolor(self.colors["surface"])
        self.ax.set_facecolor(self.colors["surface"])
        self.ax.tick_params(colors=self.colors["text"])
        for spine in self.ax.spines.values():
            spine.set_color(self.colors["border"])

    def update_algorithm_list(self, category):
        self.algorithm_menu.configure(values=self.get_algorithms_for_category(category))
        self.algorithm_var.set(self.algorithm_menu.cget("values")[0])
        self.on_algorithm_select(self.algorithm_var.get())

    def get_algorithms_for_category(self, category):
        algorithms = {
            "Divide and Conquer": ["Merge Sort", "Quick Sort", "Strassen's Matrix Multiplication"],
            "Decrease and Conquer": ["Insertion Sort", "DFS", "BFS", "Topological Sort"],
            "Transform and Conquer": ["Heap Sort", "Presorting"],
            "Dynamic Programming": ["Binomial Coefficient", "Floyd-Warshall", "0/1 Knapsack"],
            "Greedy Algorithms": ["Prim's MST", "Dijkstra's", "Huffman Coding"],
            "Backtracking": ["N-Queens", "Subset Sum"],
            "Branch and Bound": ["TSP", "Assignment Problem"]
        }
        return algorithms.get(category, [])

    def on_algorithm_select(self, algorithm):
        self.current_algorithm = algorithm
        self.update_input_placeholder()
        self.clear_visualization()

    def update_input_placeholder(self):
        placeholders = {
            "Merge Sort": "Enter numbers (e.g., 5,3,8,1,2)",
            "Quick Sort": "Enter numbers (e.g., 5,3,8,1,2)",
            "Insertion Sort": "Enter numbers (e.g., 5,3,8,1,2)",
            "Heap Sort": "Enter numbers (e.g., 5,3,8,1,2)",
            "DFS": "Enter graph edges (e.g., 1-2,2-3,3-4)",
            "BFS": "Enter graph edges (e.g., 1-2,2-3,3-4)",
            "Topological Sort": "Enter graph edges (e.g., 1-2,2-3,3-4)",
            "Prim's MST": "Enter graph edges with weights (e.g., 1-2:5,2-3:3)",
            "Dijkstra's": "Enter graph edges with weights (e.g., 1-2:5,2-3:3)",
            "N-Queens": "Enter board size (e.g., 8)",
            "Subset Sum": "Enter numbers and target (e.g., 1,2,3,4,5;10)",
            "TSP": "Enter cities and distances (e.g., A-B:5,B-C:3,C-A:4)",
            "Assignment Problem": "Enter cost matrix (e.g., 2,3;4,1)"
        }
        self.input_entry.configure(placeholder_text=placeholders.get(self.current_algorithm, "Enter input..."))

    def clear_visualization(self):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["surface"])
        self.canvas.draw()

    def start_algorithm(self):
        if self.is_animating:
            return
            
        input_text = self.input_entry.get()
        if not input_text:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Please enter input data")
            return
            
        self.is_animating = True
        self.animation_thread = Thread(target=self.run_algorithm, args=(input_text,), daemon=True)
        self.animation_thread.start()

    def stop_algorithm(self):
        self.is_animating = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
        self.clear_visualization()

    def run_algorithm(self, input_text):
        try:
            if self.current_algorithm == "Merge Sort":
                self.visualize_merge_sort(input_text)
            elif self.current_algorithm == "Quick Sort":
                self.visualize_quick_sort(input_text)
            elif self.current_algorithm == "Insertion Sort":
                self.visualize_insertion_sort(input_text)
            elif self.current_algorithm == "Heap Sort":
                self.visualize_heap_sort(input_text)
            elif self.current_algorithm == "DFS":
                self.visualize_dfs(input_text)
            elif self.current_algorithm == "BFS":
                self.visualize_bfs(input_text)
            elif self.current_algorithm == "Topological Sort":
                self.visualize_topological_sort(input_text)
            elif self.current_algorithm == "Prim's MST":
                self.visualize_prims(input_text)
            elif self.current_algorithm == "Dijkstra's":
                self.visualize_dijkstra(input_text)
            elif self.current_algorithm == "N-Queens":
                self.visualize_n_queens(input_text)
            elif self.current_algorithm == "Subset Sum":
                self.visualize_subset_sum(input_text)
            elif self.current_algorithm == "TSP":
                self.visualize_tsp(input_text)
            elif self.current_algorithm == "Assignment Problem":
                self.visualize_assignment(input_text)
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error: {str(e)}")
        finally:
            self.is_animating = False

    def visualize_merge_sort(self, input_text):
        try:
            arr = [int(x.strip()) for x in input_text.split(",")]
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Merge Sort...")
            
            def merge_sort(arr, left, right):
                if left < right:
                    mid = (left + right) // 2
                    merge_sort(arr, left, mid)
                    merge_sort(arr, mid + 1, right)
                    merge(arr, left, mid, right)
                    
                    # Update visualization
                    self.ax.clear()
                    self.ax.bar(range(len(arr)), arr, color=self.colors["accent"])
                    self.ax.set_title("Merge Sort Visualization")
                    self.canvas.draw()
                    time.sleep(1.0 / self.speed_slider.get())
            
            def merge(arr, left, mid, right):
                temp = arr[left:right + 1]
                i, j, k = 0, mid - left + 1, left
                
                while i <= mid - left and j <= right - left:
                    if temp[i] <= temp[j]:
                        arr[k] = temp[i]
                        i += 1
                    else:
                        arr[k] = temp[j]
                        j += 1
                    k += 1
                
                while i <= mid - left:
                    arr[k] = temp[i]
                    i += 1
                    k += 1
                
                while j <= right - left:
                    arr[k] = temp[j]
                    j += 1
                    k += 1
            
            merge_sort(arr, 0, len(arr) - 1)
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Merge Sort completed!\nSorted array: {arr}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Merge Sort: {str(e)}")

    def visualize_quick_sort(self, input_text):
        try:
            arr = [int(x.strip()) for x in input_text.split(",")]
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Quick Sort...")
            
            def quick_sort(arr, low, high):
                if low < high:
                    pi = partition(arr, low, high)
                    quick_sort(arr, low, pi - 1)
                    quick_sort(arr, pi + 1, high)
            
            def partition(arr, low, high):
                pivot = arr[high]
                i = low - 1
                
                for j in range(low, high):
                    if arr[j] <= pivot:
                        i += 1
                        arr[i], arr[j] = arr[j], arr[i]
                        
                        # Update visualization
                        self.ax.clear()
                        self.ax.bar(range(len(arr)), arr, color=self.colors["accent"])
                        self.ax.set_title("Quick Sort Visualization")
                        self.canvas.draw()
                        time.sleep(1.0 / self.speed_slider.get())
                
                arr[i + 1], arr[high] = arr[high], arr[i + 1]
                return i + 1
            
            quick_sort(arr, 0, len(arr) - 1)
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Quick Sort completed!\nSorted array: {arr}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Quick Sort: {str(e)}")

    def visualize_insertion_sort(self, input_text):
        try:
            arr = [int(x.strip()) for x in input_text.split(",")]
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Insertion Sort...")
            
            for i in range(1, len(arr)):
                key = arr[i]
                j = i - 1
                
                while j >= 0 and arr[j] > key:
                    arr[j + 1] = arr[j]
                    j -= 1
                    
                    # Update visualization
                    self.ax.clear()
                    self.ax.bar(range(len(arr)), arr, color=self.colors["accent"])
                    self.ax.set_title("Insertion Sort Visualization")
                    self.canvas.draw()
                    time.sleep(1.0 / self.speed_slider.get())
                
                arr[j + 1] = key
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Insertion Sort completed!\nSorted array: {arr}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Insertion Sort: {str(e)}")

    def visualize_heap_sort(self, input_text):
        try:
            arr = [int(x.strip()) for x in input_text.split(",")]
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Heap Sort...")
            
            def heapify(arr, n, i):
                largest = i
                left = 2 * i + 1
                right = 2 * i + 2
                
                if left < n and arr[left] > arr[largest]:
                    largest = left
                
                if right < n and arr[right] > arr[largest]:
                    largest = right
                
                if largest != i:
                    arr[i], arr[largest] = arr[largest], arr[i]
                    heapify(arr, n, largest)
                    
                    # Update visualization
                    self.ax.clear()
                    self.ax.bar(range(len(arr)), arr, color=self.colors["accent"])
                    self.ax.set_title("Heap Sort Visualization")
                    self.canvas.draw()
                    time.sleep(1.0 / self.speed_slider.get())
            
            n = len(arr)
            for i in range(n // 2 - 1, -1, -1):
                heapify(arr, n, i)
            
            for i in range(n - 1, 0, -1):
                arr[i], arr[0] = arr[0], arr[i]
                heapify(arr, i, 0)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Heap Sort completed!\nSorted array: {arr}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Heap Sort: {str(e)}")

    def visualize_dfs(self, input_text):
        try:
            # Parse graph edges
            edges = [edge.strip().split("-") for edge in input_text.split(",")]
            graph = {}
            for edge in edges:
                u, v = edge
                if u not in graph:
                    graph[u] = []
                if v not in graph:
                    graph[v] = []
                graph[u].append(v)
                graph[v].append(u)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting DFS...")
            
            visited = set()
            dfs_order = []
            
            def dfs(node):
                visited.add(node)
                dfs_order.append(node)
                
                # Update visualization
                self.ax.clear()
                pos = nx.spring_layout(graph)
                nx.draw(graph, pos, with_labels=True, node_color=self.colors["accent"],
                       node_size=1000, font_size=10, font_color=self.colors["text"])
                self.ax.set_title("DFS Visualization")
                self.canvas.draw()
                time.sleep(1.0 / self.speed_slider.get())
                
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        dfs(neighbor)
            
            # Start DFS from the first node
            start_node = list(graph.keys())[0]
            dfs(start_node)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"DFS completed!\nTraversal order: {' -> '.join(dfs_order)}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in DFS: {str(e)}")

    def visualize_bfs(self, input_text):
        try:
            # Parse graph edges
            edges = [edge.strip().split("-") for edge in input_text.split(",")]
            graph = {}
            for edge in edges:
                u, v = edge
                if u not in graph:
                    graph[u] = []
                if v not in graph:
                    graph[v] = []
                graph[u].append(v)
                graph[v].append(u)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting BFS...")
            
            visited = set()
            queue = []
            bfs_order = []
            
            # Start BFS from the first node
            start_node = list(graph.keys())[0]
            visited.add(start_node)
            queue.append(start_node)
            
            while queue:
                node = queue.pop(0)
                bfs_order.append(node)
                
                # Update visualization
                self.ax.clear()
                pos = nx.spring_layout(graph)
                nx.draw(graph, pos, with_labels=True, node_color=self.colors["accent"],
                       node_size=1000, font_size=10, font_color=self.colors["text"])
                self.ax.set_title("BFS Visualization")
                self.canvas.draw()
                time.sleep(1.0 / self.speed_slider.get())
                
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"BFS completed!\nTraversal order: {' -> '.join(bfs_order)}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in BFS: {str(e)}")

    def visualize_topological_sort(self, input_text):
        try:
            # Parse graph edges
            edges = [edge.strip().split("-") for edge in input_text.split(",")]
            graph = {}
            in_degree = {}
            
            for edge in edges:
                u, v = edge
                if u not in graph:
                    graph[u] = []
                if v not in graph:
                    graph[v] = []
                graph[u].append(v)
                in_degree[v] = in_degree.get(v, 0) + 1
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Topological Sort...")
            
            queue = []
            for node in graph:
                if node not in in_degree:
                    queue.append(node)
            
            topo_order = []
            
            while queue:
                node = queue.pop(0)
                topo_order.append(node)
                
                # Update visualization
                self.ax.clear()
                pos = nx.spring_layout(graph)
                nx.draw(graph, pos, with_labels=True, node_color=self.colors["accent"],
                       node_size=1000, font_size=10, font_color=self.colors["text"])
                self.ax.set_title("Topological Sort Visualization")
                self.canvas.draw()
                time.sleep(1.0 / self.speed_slider.get())
                
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Topological Sort completed!\nOrder: {' -> '.join(topo_order)}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Topological Sort: {str(e)}")

    def visualize_prims(self, input_text):
        try:
            # Parse graph edges with weights
            edges = [edge.strip().split(":") for edge in input_text.split(",")]
            graph = {}
            for edge in edges:
                nodes, weight = edge
                u, v = nodes.split("-")
                weight = int(weight)
                if u not in graph:
                    graph[u] = {}
                if v not in graph:
                    graph[v] = {}
                graph[u][v] = weight
                graph[v][u] = weight
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Prim's Algorithm...")
            
            # Start from the first node
            start_node = list(graph.keys())[0]
            mst = {start_node}
            edges = []
            
            while len(mst) < len(graph):
                min_edge = None
                min_weight = float('inf')
                
                for node in mst:
                    for neighbor, weight in graph[node].items():
                        if neighbor not in mst and weight < min_weight:
                            min_edge = (node, neighbor)
                            min_weight = weight
                
                if min_edge:
                    u, v = min_edge
                    mst.add(v)
                    edges.append((u, v, min_weight))
                    
                    # Update visualization
                    self.ax.clear()
                    pos = nx.spring_layout(graph)
                    nx.draw(graph, pos, with_labels=True, node_color=self.colors["accent"],
                           node_size=1000, font_size=10, font_color=self.colors["text"])
                    nx.draw_networkx_edges(graph, pos, edgelist=[(u, v)], edge_color='red', width=2)
                    self.ax.set_title("Prim's Algorithm Visualization")
                    self.canvas.draw()
                    time.sleep(1.0 / self.speed_slider.get())
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Prim's Algorithm completed!\nMST edges: {edges}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Prim's Algorithm: {str(e)}")

    def visualize_dijkstra(self, input_text):
        try:
            # Parse graph edges with weights
            edges = [edge.strip().split(":") for edge in input_text.split(",")]
            graph = {}
            for edge in edges:
                nodes, weight = edge
                u, v = nodes.split("-")
                weight = int(weight)
                if u not in graph:
                    graph[u] = {}
                if v not in graph:
                    graph[v] = {}
                graph[u][v] = weight
                graph[v][u] = weight
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Dijkstra's Algorithm...")
            
            # Start from the first node
            start_node = list(graph.keys())[0]
            distances = {node: float('inf') for node in graph}
            distances[start_node] = 0
            visited = set()
            
            while len(visited) < len(graph):
                # Find unvisited node with minimum distance
                min_node = None
                min_dist = float('inf')
                for node in graph:
                    if node not in visited and distances[node] < min_dist:
                        min_node = node
                        min_dist = distances[node]
                
                if min_node is None:
                    break
                
                visited.add(min_node)
                
                # Update visualization
                self.ax.clear()
                pos = nx.spring_layout(graph)
                nx.draw(graph, pos, with_labels=True, node_color=self.colors["accent"],
                       node_size=1000, font_size=10, font_color=self.colors["text"])
                self.ax.set_title("Dijkstra's Algorithm Visualization")
                self.canvas.draw()
                time.sleep(1.0 / self.speed_slider.get())
                
                # Update distances to neighbors
                for neighbor, weight in graph[min_node].items():
                    if neighbor not in visited:
                        new_dist = distances[min_node] + weight
                        if new_dist < distances[neighbor]:
                            distances[neighbor] = new_dist
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Dijkstra's Algorithm completed!\nDistances: {distances}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Dijkstra's Algorithm: {str(e)}")

    def visualize_n_queens(self, input_text):
        try:
            n = int(input_text)
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting N-Queens...")
            
            def is_safe(board, row, col):
                # Check row
                for i in range(col):
                    if board[row][i]:
                        return False
                
                # Check upper diagonal
                for i, j in zip(range(row, -1, -1), range(col, -1, -1)):
                    if board[i][j]:
                        return False
                
                # Check lower diagonal
                for i, j in zip(range(row, n), range(col, -1, -1)):
                    if board[i][j]:
                        return False
                
                return True
            
            def solve_n_queens(board, col):
                if col >= n:
                    return True
                
                for i in range(n):
                    if is_safe(board, i, col):
                        board[i][col] = 1
                        
                        # Update visualization
                        self.ax.clear()
                        self.ax.imshow(board, cmap='binary')
                        self.ax.set_title("N-Queens Visualization")
                        self.canvas.draw()
                        time.sleep(1.0 / self.speed_slider.get())
                        
                        if solve_n_queens(board, col + 1):
                            return True
                        
                        board[i][col] = 0
                
                return False
            
            board = [[0 for _ in range(n)] for _ in range(n)]
            if solve_n_queens(board, 0):
                self.status_text.delete("1.0", "end")
                self.status_text.insert("1.0", "N-Queens solution found!")
            else:
                self.status_text.delete("1.0", "end")
                self.status_text.insert("1.0", "No solution exists!")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in N-Queens: {str(e)}")

    def visualize_subset_sum(self, input_text):
        try:
            # Parse input
            numbers_str, target_str = input_text.split(";")
            numbers = [int(x.strip()) for x in numbers_str.split(",")]
            target = int(target_str)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Subset Sum...")
            
            def subset_sum(numbers, target):
                n = len(numbers)
                dp = [[False for _ in range(target + 1)] for _ in range(n + 1)]
                
                for i in range(n + 1):
                    dp[i][0] = True
                
                for i in range(1, n + 1):
                    for j in range(1, target + 1):
                        if numbers[i-1] <= j:
                            dp[i][j] = dp[i-1][j] or dp[i-1][j-numbers[i-1]]
                        else:
                            dp[i][j] = dp[i-1][j]
                        
                        # Update visualization
                        self.ax.clear()
                        self.ax.imshow(dp, cmap='binary')
                        self.ax.set_title("Subset Sum Visualization")
                        self.canvas.draw()
                        time.sleep(1.0 / self.speed_slider.get())
                
                return dp[n][target]
            
            result = subset_sum(numbers, target)
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Subset Sum completed!\nTarget {target} {'can' if result else 'cannot'} be achieved")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Subset Sum: {str(e)}")

    def visualize_tsp(self, input_text):
        try:
            # Parse input
            edges = [edge.strip().split(":") for edge in input_text.split(",")]
            graph = {}
            for edge in edges:
                nodes, weight = edge
                u, v = nodes.split("-")
                weight = int(weight)
                if u not in graph:
                    graph[u] = {}
                if v not in graph:
                    graph[v] = {}
                graph[u][v] = weight
                graph[v][u] = weight
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting TSP...")
            
            def tsp(graph, start):
                n = len(graph)
                cities = list(graph.keys())
                min_path = float('inf')
                best_path = None
                
                def branch_and_bound(path, cost, visited):
                    nonlocal min_path, best_path
                    
                    if len(path) == n:
                        if graph[path[-1]][start] != 0:
                            total_cost = cost + graph[path[-1]][start]
                            if total_cost < min_path:
                                min_path = total_cost
                                best_path = path + [start]
                        return
                    
                    for city in cities:
                        if city not in visited and graph[path[-1]][city] != 0:
                            new_cost = cost + graph[path[-1]][city]
                            if new_cost < min_path:
                                path.append(city)
                                visited.add(city)
                                
                                # Update visualization
                                self.ax.clear()
                                pos = nx.spring_layout(graph)
                                nx.draw(graph, pos, with_labels=True, node_color=self.colors["accent"],
                                       node_size=1000, font_size=10, font_color=self.colors["text"])
                                path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
                                nx.draw_networkx_edges(graph, pos, edgelist=path_edges, edge_color='red', width=2)
                                self.ax.set_title("TSP Visualization")
                                self.canvas.draw()
                                time.sleep(1.0 / self.speed_slider.get())
                                
                                branch_and_bound(path, new_cost, visited)
                                path.pop()
                                visited.remove(city)
                
                branch_and_bound([start], 0, {start})
                return best_path, min_path
            
            start_city = list(graph.keys())[0]
            best_path, min_cost = tsp(graph, start_city)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"TSP completed!\nBest path: {' -> '.join(best_path)}\nTotal cost: {min_cost}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in TSP: {str(e)}")

    def visualize_assignment(self, input_text):
        try:
            # Parse input
            rows = [row.strip().split(",") for row in input_text.split(";")]
            cost_matrix = [[int(x) for x in row] for row in rows]
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "Starting Assignment Problem...")
            
            def assignment_problem(cost_matrix):
                n = len(cost_matrix)
                result = [-1] * n
                min_cost = float('inf')
                
                def branch_and_bound(row, assigned, cost):
                    nonlocal min_cost, result
                    
                    if row == n:
                        if cost < min_cost:
                            min_cost = cost
                            result = assigned.copy()
                        return
                    
                    for col in range(n):
                        if col not in assigned:
                            new_cost = cost + cost_matrix[row][col]
                            if new_cost < min_cost:
                                assigned[row] = col
                                
                                # Update visualization
                                self.ax.clear()
                                self.ax.imshow(cost_matrix, cmap='viridis')
                                self.ax.set_title("Assignment Problem Visualization")
                                for i in range(n):
                                    if i in assigned:
                                        self.ax.add_patch(plt.Rectangle((assigned[i]-0.5, i-0.5), 1, 1,
                                                                      fill=False, edgecolor='red', linewidth=2))
                                self.canvas.draw()
                                time.sleep(1.0 / self.speed_slider.get())
                                
                                branch_and_bound(row + 1, assigned, new_cost)
                                del assigned[row]
                
                branch_and_bound(0, {}, 0)
                return result, min_cost
            
            assignment, min_cost = assignment_problem(cost_matrix)
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Assignment Problem completed!\nAssignment: {assignment}\nTotal cost: {min_cost}")
            
        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Error in Assignment Problem: {str(e)}")

class MemoryOptimizationSection(ctk.CTkFrame):
    def __init__(self, master, colors, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        
        # Initialize data structures with optimized sizes
        self.memory_history = collections.deque(maxlen=30)  # Reduced history size
        self.process_history = {}
        self.markov_states = {}
        self.hung_processes = set()
        self.selected_processes = set()
        self.suggested_processes = set()
        
        # Performance optimization settings
        self.update_interval = 3.0  # Increased base update interval
        self.performance_threshold = 0.3  # Increased threshold
        self.last_update_time = time.time()
        self.update_counter = 0
        
        # Create sections with improved layout
        self.create_ram_usage_section()
        self.create_prediction_section()
        self.create_optimization_section()
        self.create_process_monitor_section()
        
        # Start monitoring thread with improved error handling
        self.running = True
        self.monitor_thread = Thread(target=self.update_memory_metrics, daemon=True)
        self.monitor_thread.start()

    def create_ram_usage_section(self):
        frame = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create header with controls
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        title = ctk.CTkLabel(
            header,
            text="RAM Usage",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(side="left")
        
        # Add refresh button
        refresh_btn = ctk.CTkButton(
            header,
            text="Refresh",
            command=self.refresh_ram_analysis,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_secondary"],
            width=80
        )
        refresh_btn.pack(side="right")
        
        # Create RAM graph with optimized settings
        self.ram_graph = GraphFrame(frame, "Memory Usage", "Memory (MB)")
        self.ram_graph.pack(fill="both", expand=True, padx=10, pady=10)
        self.ram_graph.fig.set_dpi(100)  # Lower DPI for better performance
        
        # Add memory leak detection status
        self.leak_status = ctk.CTkLabel(
            frame,
            text="Memory Leak Status: Monitoring...",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        )
        self.leak_status.pack(pady=5)
        
        # Add memory usage details
        self.memory_details = ctk.CTkTextbox(
            frame,
            height=60,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.memory_details.pack(fill="x", padx=10, pady=5)

    def create_prediction_section(self):
        frame = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Create header with controls
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        title = ctk.CTkLabel(
            header,
            text="Memory Prediction",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(side="left")
        
        # Add prediction interval selector
        interval_frame = ctk.CTkFrame(header, fg_color="transparent")
        interval_frame.pack(side="right")
        
        ctk.CTkLabel(
            interval_frame,
            text="Interval:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        ).pack(side="left", padx=5)
        
        self.interval_var = ctk.StringVar(value="5m")
        interval_menu = ctk.CTkOptionMenu(
            interval_frame,
            values=["5m", "15m", "30m"],
            variable=self.interval_var,
            command=self.update_prediction_interval,
            width=60
        )
        interval_menu.pack(side="left")
        
        # Create prediction graph
        self.prediction_graph = GraphFrame(frame, "Memory Prediction", "Memory (MB)")
        self.prediction_graph.pack(fill="both", expand=True, padx=10, pady=10)
        self.prediction_graph.fig.set_dpi(100)
        
        # Add prediction details
        self.prediction_details = ctk.CTkTextbox(
            frame,
            height=60,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.prediction_details.pack(fill="x", padx=10, pady=5)

    def create_optimization_section(self):
        frame = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create header with controls
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        title = ctk.CTkLabel(
            header,
            text="Memory Optimization",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(side="left")
        
        # Add optimization strategy selector
        strategy_frame = ctk.CTkFrame(header, fg_color="transparent")
        strategy_frame.pack(side="right")
        
        ctk.CTkLabel(
            strategy_frame,
            text="Strategy:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        ).pack(side="left", padx=5)
        
        self.strategy_var = ctk.StringVar(value="Balanced")
        strategy_menu = ctk.CTkOptionMenu(
            strategy_frame,
            values=["Balanced", "Performance", "Memory Saving"],
            variable=self.strategy_var,
            command=self.update_optimization_strategy,
            width=120
        )
        strategy_menu.pack(side="left")
        
        # Add apply button
        apply_btn = ctk.CTkButton(
            strategy_frame,
            text="Apply",
            command=self.apply_optimization,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_secondary"],
            width=80
        )
        apply_btn.pack(side="left", padx=5)
        
        # Add optimization details
        self.optimization_details = ctk.CTkTextbox(
            frame,
            height=200,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.optimization_details.pack(fill="both", expand=True, padx=10, pady=10)

    def create_process_monitor_section(self):
        frame = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        # Create header with process controls
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        title = ctk.CTkLabel(
            header,
            text="Process Monitor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(side="left")
        
        # Add process filter with improved responsiveness
        self.process_filter = ctk.CTkEntry(
            header,
            placeholder_text="Filter processes...",
            width=150
        )
        self.process_filter.pack(side="right")
        self.process_filter.bind("<KeyRelease>", lambda e: self.after(100, self.filter_processes))
        
        # Create process list with improved performance
        self.process_list = ctk.CTkTextbox(
            frame,
            height=200,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.process_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add process control buttons with improved layout
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.kill_button = ctk.CTkButton(
            button_frame,
            text="Kill Selected Processes",
            command=self.kill_selected_process,
            fg_color=self.colors["error"],
            hover_color=self.colors["error"]
        )
        self.kill_button.pack(side="left", padx=5)
        
        self.suggest_button = ctk.CTkButton(
            button_frame,
            text="Suggest Processes",
            command=self.suggest_processes,
            fg_color=self.colors["warning"],
            hover_color=self.colors["warning"]
        )
        self.suggest_button.pack(side="left", padx=5)
        
        self.refresh_btn = ctk.CTkButton(
            button_frame,
            text="Refresh",
            command=self.refresh_process_list,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_secondary"]
        )
        self.refresh_btn.pack(side="right", padx=5)

    def kill_selected_process(self):
        try:
            killed_count = 0
            failed_count = 0
            error_messages = []
            
            # Get a copy of selected processes to avoid modification during iteration
            processes_to_kill = list(self.selected_processes)
            
            for pid in processes_to_kill:
                try:
                    process = psutil.Process(pid)
                    # Try graceful termination first
                    process.terminate()
                    try:
                        process.wait(timeout=3)  # Wait for process to terminate
                    except psutil.TimeoutExpired:
                        # If graceful termination fails, force kill
                        process.kill()
                    killed_count += 1
                except psutil.NoSuchProcess:
                    failed_count += 1
                    error_messages.append(f"Process {pid} no longer exists")
                except psutil.AccessDenied:
                    failed_count += 1
                    error_messages.append(f"Access denied to process {pid}")
                except Exception as e:
                    failed_count += 1
                    error_messages.append(f"Error killing process {pid}: {str(e)}")
            
            # Clear selections and update UI
            self.selected_processes.clear()
            self.suggested_processes.clear()
            
            # Show results
            self.process_list.delete("1.0", "end")
            result_text = f"Process termination results:\n"
            result_text += f"Successfully killed: {killed_count}\n"
            if failed_count > 0:
                result_text += f"Failed to kill: {failed_count}\n"
                result_text += "Errors:\n"
                for msg in error_messages:
                    result_text += f"- {msg}\n"
            
            self.process_list.insert("1.0", result_text)
            
            # Refresh process list after a short delay
            self.after(1000, self.refresh_process_list)
            
        except Exception as e:
            print(f"Error in kill_selected_process: {e}")
            self.process_list.delete("1.0", "end")
            self.process_list.insert("1.0", f"Error killing processes: {str(e)}\n")

    def update_process_list_with_suggestions(self, processes):
        try:
            self.process_list.delete("1.0", "end")
            
            # Sort processes by memory usage
            processes.sort(key=lambda x: x['memory'], reverse=True)
            
            # Add header
            self.process_list.insert("end", "Suggested processes are marked with ⚠️\n\n")
            
            # Add processes with improved formatting
            for proc in processes[:20]:  # Show top 20 processes
                is_suggested = proc['pid'] in self.suggested_processes
                is_selected = proc['pid'] in self.selected_processes
                
                # Format process information with better readability
                process_info = (
                    f"[{'X' if is_selected else ' '}] "
                    f"{'⚠️ ' if is_suggested else ''}"
                    f"PID: {proc['pid']} | {proc['name']} | "
                    f"Memory: {proc['memory']:.1f}% | CPU: {proc['cpu']:.1f}% | "
                    f"Status: {proc['status']}\n"
                )
                
                # Set color based on status and suggestion
                if proc['status'] == 'zombie':
                    color = self.colors["error"]
                elif is_suggested:
                    color = self.colors["warning"]
                else:
                    color = self.colors["text"]
                
                self.process_list.insert("end", process_info, color)
            
            # Add click handling for process selection
            self.process_list.bind("<Button-1>", self.on_process_list_click)
            
        except Exception as e:
            print(f"Error updating process list: {e}")

    def on_process_list_click(self, event):
        try:
            # Get the line number clicked
            index = self.process_list.index(f"@{event.x},{event.y}")
            line = int(float(index))
            
            # Get the process information from the clicked line
            line_text = self.process_list.get(f"{line}.0", f"{line}.end")
            
            # Extract PID from the line
            if "PID:" in line_text:
                pid = int(line_text.split("PID:")[1].split("|")[0].strip())
                
                # Toggle selection
                if pid in self.selected_processes:
                    self.selected_processes.remove(pid)
                else:
                    self.selected_processes.add(pid)
                
                # Update the process list to reflect the change
                self.refresh_process_list()
                
        except Exception as e:
            print(f"Error in process list click handler: {e}")

    def suggest_processes(self):
        try:
            self.suggested_processes.clear()
            processes = []
            
            # Collect process information with improved error handling
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'status']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory': proc.info['memory_percent'],
                        'cpu': proc.info['cpu_percent'],
                        'status': proc.info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Suggest processes based on multiple criteria with improved thresholds
            for proc in processes:
                # Check for high resource usage
                if proc['memory'] > 25 or proc['cpu'] > 70:  # Lowered thresholds
                    self.suggested_processes.add(proc['pid'])
                # Check for problematic status
                elif proc['status'] in ['zombie', 'not responding']:
                    self.suggested_processes.add(proc['pid'])
                # Check for long-running processes with high memory
                elif proc['memory'] > 15 and proc['pid'] in self.process_history:  # Lowered threshold
                    self.suggested_processes.add(proc['pid'])
            
            # Update process list with suggestions
            self.update_process_list_with_suggestions(processes)
            
        except Exception as e:
            print(f"Error suggesting processes: {e}")

    def update_memory_metrics(self):
        while self.running:
            try:
                start_time = time.time()
                
                # Get current memory usage with error handling
                try:
                    memory = psutil.virtual_memory()
                    self.memory_history.append(memory.percent)
                except Exception as e:
                    print(f"Error getting memory usage: {e}")
                    time.sleep(1)
                    continue
                
                # Implement selective updates to reduce lag
                self.update_counter += 1
                
                # Update RAM graph (every other cycle)
                if self.update_counter % 2 == 0:
                    self.update_ram_graph()
                
                # Update predictions (every third cycle)
                if self.update_counter % 3 == 0:
                    self.update_predictions()
                
                # Update optimization (every fourth cycle)
                if self.update_counter % 4 == 0:
                    self.update_optimization()
                
                # Always update process info and check for hung processes
                self.refresh_process_list()
                self.check_hung_processes()
                
                # Calculate and adjust update interval based on performance
                elapsed_time = time.time() - start_time
                if elapsed_time > self.performance_threshold:
                    self.update_interval = min(3.0, self.update_interval * 1.1)
                else:
                    self.update_interval = max(1.0, self.update_interval * 0.9)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in memory metrics update: {e}")
                time.sleep(1)

    def update_ram_graph(self):
        try:
            self.ram_graph.ax.clear()
            times = list(range(len(self.memory_history)))
            self.ram_graph.ax.plot(times, list(self.memory_history), color=self.colors["accent"])
            self.ram_graph.ax.set_title("Memory Usage Trend")
            self.ram_graph.ax.grid(True, linestyle='--', alpha=0.2)
            self.ram_graph.canvas.draw()
            
            # Update memory details
            memory = psutil.virtual_memory()
            self.memory_details.delete("1.0", "end")
            self.memory_details.insert("1.0",
                f"Total: {memory.total / (1024**3):.1f} GB\n"
                f"Used: {memory.used / (1024**3):.1f} GB\n"
                f"Free: {memory.available / (1024**3):.1f} GB"
            )
            
            # Check for memory leaks
            if len(self.memory_history) > 10:
                recent_memory = list(self.memory_history)[-10:]
                slope = np.polyfit(range(len(recent_memory)), recent_memory, 1)[0]
                if slope > 1.0:
                    self.leak_status.configure(
                        text="Memory Leak Status: Potential leak detected!",
                        text_color=self.colors["error"]
                    )
                else:
                    self.leak_status.configure(
                        text="Memory Leak Status: No leaks detected",
                        text_color=self.colors["success"]
                    )
        except Exception as e:
            print(f"Error updating RAM graph: {e}")

    def update_predictions(self):
        try:
            if len(self.memory_history) < 5:
                return
                
            # Simple Markov chain prediction
            current_state = int(self.memory_history[-1] / 10)
            if current_state not in self.markov_states:
                self.markov_states[current_state] = collections.defaultdict(int)
            
            # Update transition probabilities
            for i in range(len(self.memory_history) - 1):
                from_state = int(self.memory_history[i] / 10)
                to_state = int(self.memory_history[i + 1] / 10)
                self.markov_states[from_state][to_state] += 1
            
            # Make prediction
            prediction = []
            current = current_state
            steps = 30 if self.interval_var.get() == "30m" else (15 if self.interval_var.get() == "15m" else 5)
            
            for _ in range(steps):
                if current in self.markov_states:
                    next_states = self.markov_states[current]
                    if next_states:
                        current = max(next_states.items(), key=lambda x: x[1])[0]
                prediction.append(current * 10)
            
            # Update prediction graph
            self.prediction_graph.ax.clear()
            times = list(range(len(prediction)))
            self.prediction_graph.ax.plot(times, prediction, color=self.colors["accent"])
            self.prediction_graph.ax.set_title("Memory Usage Prediction")
            self.prediction_graph.ax.grid(True, linestyle='--', alpha=0.2)
            self.prediction_graph.canvas.draw()
            
            # Update prediction details
            self.prediction_details.delete("1.0", "end")
            self.prediction_details.insert("1.0",
                f"Current: {self.memory_history[-1]:.1f}%\n"
                f"Predicted: {prediction[-1]:.1f}%\n"
                f"Change: {prediction[-1] - self.memory_history[-1]:.1f}%"
            )
        except Exception as e:
            print(f"Error updating predictions: {e}")

    def update_optimization(self):
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent()
            
            strategy = self.strategy_var.get()
            recommendations = []
            
            if strategy == "Balanced":
                if memory.percent > 70:
                    recommendations.append("Consider closing unused applications")
                if cpu > 70:
                    recommendations.append("Reduce background processes")
            elif strategy == "Performance":
                if memory.percent > 50:
                    recommendations.append("Close non-essential applications")
                if cpu > 50:
                    recommendations.append("Optimize running processes")
            else:  # Memory Saving
                if memory.percent > 30:
                    recommendations.append("Close all non-critical applications")
                if cpu > 30:
                    recommendations.append("Minimize background processes")
            
            # Update optimization details
            self.optimization_details.delete("1.0", "end")
            self.optimization_details.insert("1.0",
                f"Current Memory Usage: {memory.percent:.1f}%\n"
                f"Current CPU Usage: {cpu:.1f}%\n\n"
                f"Recommendations:\n" + "\n".join(f"- {rec}" for rec in recommendations)
            )
        except Exception as e:
            print(f"Error updating optimization: {e}")

    def check_hung_processes(self):
        try:
            self.hung_processes.clear()
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if proc.info['status'] in ['zombie', 'not responding']:
                        self.hung_processes.add(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error checking hung processes: {e}")

    def refresh_process_list(self):
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'status']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory': proc.info['memory_percent'],
                        'cpu': proc.info['cpu_percent'],
                        'status': proc.info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.update_process_list_with_suggestions(processes)
        except Exception as e:
            print(f"Error refreshing process list: {e}")

    def refresh_ram_analysis(self):
        try:
            self.update_ram_graph()
            self.update_predictions()
            self.update_optimization()
        except Exception as e:
            print(f"Error refreshing RAM analysis: {e}")

    def filter_processes(self):
        try:
            filter_text = self.process_filter.get().lower()
            if not filter_text:
                self.refresh_process_list()
                return
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'status']):
                try:
                    if filter_text in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory': proc.info['memory_percent'],
                            'cpu': proc.info['cpu_percent'],
                            'status': proc.info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.update_process_list_with_suggestions(processes)
        except Exception as e:
            print(f"Error filtering processes: {e}")

    def update_prediction_interval(self, value):
        self.update_predictions()

    def update_optimization_strategy(self, value):
        self.update_optimization()

    def apply_optimization(self):
        try:
            strategy = self.strategy_var.get()
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent()
            
            if strategy == "Memory Saving":
                # Find and kill non-essential processes
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    try:
                        if proc.info['memory_percent'] > 5 and proc.info['name'] not in ['System', 'Idle']:
                            p = psutil.Process(proc.info['pid'])
                            p.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            elif strategy == "Performance":
                # Optimize process priorities
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        if proc.info['cpu_percent'] > 50:
                            p = psutil.Process(proc.info['pid'])
                            p.nice(10)  # Lower priority
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            self.refresh_ram_analysis()
        except Exception as e:
            print(f"Error applying optimization: {e}")

class SystemMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.colors = self.theme_manager.current_theme
        
        # Configure window
        self.title("System Monitor")
        self.geometry("1200x800")
        self.configure(fg_color=self.colors["bg"])
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Initialize history data with optimized size
        self.history = {
            'time': collections.deque(maxlen=60),
            'cpu': collections.deque(maxlen=60),
            'memory': collections.deque(maxlen=60),
            'disk': collections.deque(maxlen=60),
            'network': collections.deque(maxlen=60)
        }
        
        # Initialize frames dictionary
        self.frames = {}
        
        # Performance optimization settings
        self.update_interval = 2.0  # Base update interval
        self.performance_threshold = 0.2  # Performance threshold
        self.last_update_time = time.time()
        self.update_counter = 0  # Counter for selective updates
        
        # Create main area first
        self.create_main_area()
        
        # Create sidebar
        self.create_sidebar()
        
        # Start update thread with improved error handling
        self.running = True
        self.update_thread = Thread(target=self.update_metrics, daemon=True)
        self.update_thread.start()

    def create_main_area(self):
        # Create main content area
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        
        # Create and store all frames
        self.frames['dashboard'] = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frames['memory'] = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frames['cpu'] = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frames['disk'] = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frames['analysis'] = AnalysisSection(self.main_area, self.colors)
        self.frames['algorithms'] = AlgorithmSection(self.main_area, self.colors)
        self.frames['memory_opt'] = MemoryOptimizationSection(self.main_area, self.colors)
        
        # Initialize metric boxes dictionaries
        self.overview_boxes = {}
        self.memory_boxes = {}
        self.cpu_boxes = {}
        self.disk_boxes = {}
        
        # Show dashboard by default
        self.show_dashboard()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, 
            width=200,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="ew")
        
        logo_label = ctk.CTkLabel(
            header_frame,
            text="System Monitor",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["accent"]
        )
        logo_label.pack()
        
        theme_switch = ctk.CTkSwitch(
            header_frame,
            text="🌓 Toggle Theme",
            command=self.toggle_theme,
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent"],
            text_color=self.colors["text"]
        )
        theme_switch.pack(pady=10)
        theme_switch.select() if self.theme_manager.is_dark else theme_switch.deselect()
        
        separator = ctk.CTkFrame(
            self.sidebar,
            height=2,
            fg_color=self.colors["accent"]
        )
        separator.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        sections = {
            "📊 Dashboard": self.show_dashboard,
            "💾 Memory": self.show_memory,
            "⚡ CPU": self.show_cpu,
            "💿 Disk": self.show_disk,
            "📈 Analysis": self.show_analysis,
            "🧮 Algorithms": self.show_algorithms,
            "🔧 Memory Optimization": self.show_memory_optimization
        }
        
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        for i, (section, command) in enumerate(sections.items()):
            btn = ctk.CTkButton(
                nav_frame,
                text=section,
                command=command,
                fg_color="transparent",
                hover_color=self.colors["accent"],
                height=45,
                anchor="w",
                font=ctk.CTkFont(size=14),
                corner_radius=8,
                text_color=self.colors["text"],
                border_width=1,
                border_color=self.colors["border"]
            )
            btn.pack(fill="x", pady=2)

    def show_dashboard(self):
        self.hide_all_frames()
        self.frames['dashboard'].grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.frames['dashboard'].grid_columnconfigure((0, 1), weight=1)
        self.frames['dashboard'].grid_rowconfigure((0, 1), weight=1)
        
        # Create overview boxes with improved layout
        metrics = [
            ("CPU", "CPU Usage"),
            ("Memory", "Memory Usage"),
            ("Disk", "Disk Usage"),
            ("Network", "Network I/O")
        ]
        
        for i, (key, title) in enumerate(metrics):
            row = i // 2
            col = i % 2
            box = MetricBox(self.frames['dashboard'], title)
            box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.overview_boxes[key] = box
        
        # Add performance graph with optimized settings
        self.performance_graph = GraphFrame(self.frames['dashboard'], "System Performance", "Usage (%)")
        self.performance_graph.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Configure graph for better performance
        self.performance_graph.fig.set_dpi(100)  # Lower DPI for better performance
        self.performance_graph.ax.grid(True, linestyle='--', alpha=0.2)
        self.performance_graph.canvas.draw()

    def show_memory(self):
        self.hide_all_frames()
        self.frames['memory'].grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.frames['memory'].grid_columnconfigure((0, 1), weight=1)
        self.frames['memory'].grid_rowconfigure((0, 1), weight=1)
        
        # Create memory boxes with improved layout
        metrics = [
            ("Total", "Total Memory"),
            ("Used", "Used Memory"),
            ("Available", "Available Memory"),
            ("Percent", "Memory Usage")
        ]
        
        for i, (key, title) in enumerate(metrics):
            row = i // 2
            col = i % 2
            box = MetricBox(self.frames['memory'], title)
            box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.memory_boxes[key] = box
        
        # Add memory graph with optimized settings
        self.memory_graph = GraphFrame(self.frames['memory'], "Memory Usage Trend", "Memory (MB)")
        self.memory_graph.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Configure graph for better performance
        self.memory_graph.fig.set_dpi(100)  # Lower DPI for better performance
        self.memory_graph.ax.grid(True, linestyle='--', alpha=0.2)
        self.memory_graph.canvas.draw()
        
        # Add memory pie chart with optimized settings
        self.memory_pie = PieChartFrame(self.frames['memory'], "Memory Distribution")
        self.memory_pie.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.memory_pie.fig.set_dpi(100)  # Lower DPI for better performance

    def show_cpu(self):
        self.hide_all_frames()
        self.frames['cpu'].grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.frames['cpu'].grid_columnconfigure((0, 1), weight=1)
        self.frames['cpu'].grid_rowconfigure((0, 1), weight=1)
        
        # Create CPU boxes with improved layout
        metrics = [
            ("Usage", "CPU Usage"),
            ("Freq", "CPU Frequency"),
            ("Cores", "Core Count"),
            ("Threads", "Thread Count")
        ]
        
        for i, (key, title) in enumerate(metrics):
            row = i // 2
            col = i % 2
            box = MetricBox(self.frames['cpu'], title)
            box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.cpu_boxes[key] = box
        
        # Add CPU graph with optimized settings
        self.cpu_graph = GraphFrame(self.frames['cpu'], "CPU Usage Trend", "Usage (%)")
        self.cpu_graph.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Configure graph for better performance
        self.cpu_graph.fig.set_dpi(100)  # Lower DPI for better performance
        self.cpu_graph.ax.grid(True, linestyle='--', alpha=0.2)
        self.cpu_graph.canvas.draw()
        
        # Add CPU pie chart with optimized settings
        self.cpu_pie = PieChartFrame(self.frames['cpu'], "CPU Usage Distribution")
        self.cpu_pie.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.cpu_pie.fig.set_dpi(100)  # Lower DPI for better performance

    def show_disk(self):
        self.hide_all_frames()
        self.frames['disk'].grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.frames['disk'].grid_columnconfigure((0, 1), weight=1)
        self.frames['disk'].grid_rowconfigure((0, 1), weight=1)
        
        # Create disk boxes with improved layout
        metrics = [
            ("Total", "Total Space"),
            ("Used", "Used Space"),
            ("Free", "Free Space"),
            ("Percent", "Disk Usage")
        ]
        
        for i, (key, title) in enumerate(metrics):
            row = i // 2
            col = i % 2
            box = MetricBox(self.frames['disk'], title)
            box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.disk_boxes[key] = box
        
        # Add disk graph with optimized settings
        self.disk_graph = GraphFrame(self.frames['disk'], "Disk Usage Trend", "Usage (%)")
        self.disk_graph.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Configure graph for better performance
        self.disk_graph.fig.set_dpi(100)  # Lower DPI for better performance
        self.disk_graph.ax.grid(True, linestyle='--', alpha=0.2)
        self.disk_graph.canvas.draw()
        
        # Add disk pie chart with optimized settings
        self.disk_pie = PieChartFrame(self.frames['disk'], "Disk Space Distribution")
        self.disk_pie.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.disk_pie.fig.set_dpi(100)  # Lower DPI for better performance

    def show_analysis(self):
        self.hide_all_frames()
        self.frames['analysis'].grid(row=0, column=0, sticky="nsew")

    def show_algorithms(self):
        self.hide_all_frames()
        self.frames['algorithms'].grid(row=0, column=0, sticky="nsew")

    def show_memory_optimization(self):
        self.hide_all_frames()
        self.frames['memory_opt'].grid(row=0, column=0, sticky="nsew")

    def hide_all_frames(self):
        for frame in self.frames.values():
            frame.grid_remove()

    def update_metrics(self):
        while self.running:
            try:
                start_time = time.time()
                
                # Get current time
                current_time = datetime.now()
                
                # Get system metrics with error handling
                try:
                    cpu_percent = psutil.cpu_percent()
                    cpu_freq = psutil.cpu_freq().current
                    core_count = psutil.cpu_count(logical=False)
                    thread_count = psutil.cpu_count(logical=True)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    net_io = psutil.net_io_counters()
                except Exception as e:
                    print(f"Error getting system metrics: {e}")
                    time.sleep(1)
                    continue
                
                # Update history with optimized data structures
                self.history['time'].append(current_time)
                self.history['cpu'].append(cpu_percent)
                self.history['memory'].append(memory.percent)
                self.history['disk'].append(disk.percent)
                self.history['network'].append(net_io.bytes_sent + net_io.bytes_recv)
                
                # Implement selective updates to reduce lag
                self.update_counter += 1
                
                # Update dashboard (every cycle)
                if hasattr(self, 'overview_boxes'):
                    self.update_dashboard_metrics(cpu_percent, memory, disk, net_io)
                
                # Update memory page (every other cycle)
                if self.update_counter % 2 == 0 and hasattr(self, 'memory_boxes'):
                    self.update_memory_metrics(memory)
                
                # Update CPU page (every third cycle)
                if self.update_counter % 3 == 0 and hasattr(self, 'cpu_boxes'):
                    self.update_cpu_metrics(cpu_percent, cpu_freq, core_count, thread_count)
                
                # Update disk page (every fourth cycle)
                if self.update_counter % 4 == 0 and hasattr(self, 'disk_boxes'):
                    self.update_disk_metrics(disk)
                
                # Calculate and adjust update interval based on performance
                elapsed_time = time.time() - start_time
                if elapsed_time > self.performance_threshold:
                    self.update_interval = min(3.0, self.update_interval * 1.1)
                else:
                    self.update_interval = max(1.0, self.update_interval * 0.9)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in metrics update: {e}")
                time.sleep(1)

    def update_dashboard_metrics(self, cpu_percent, memory, disk, net_io):
        try:
            # Update overview boxes
            self.overview_boxes["CPU"].value_label.configure(text=f"{cpu_percent:.1f}%")
            self.overview_boxes["Memory"].value_label.configure(text=f"{memory.percent:.1f}%")
            self.overview_boxes["Disk"].value_label.configure(text=f"{disk.percent:.1f}%")
            self.overview_boxes["Network"].value_label.configure(
                text=f"{(net_io.bytes_sent + net_io.bytes_recv) / 1024:.1f} KB/s"
            )
            
            # Update performance graph with optimized plotting
            self.performance_graph.ax.clear()
            times = list(self.history['time'])
            self.performance_graph.ax.plot(
                times, list(self.history['cpu']),
                label="CPU", color=self.colors["accent"]
            )
            self.performance_graph.ax.plot(
                times, list(self.history['memory']),
                label="Memory", color=self.colors["accent_secondary"]
            )
            self.performance_graph.ax.plot(
                times, list(self.history['disk']),
                label="Disk", color=self.colors["success"]
            )
            self.performance_graph.ax.legend()
            self.performance_graph.canvas.draw()
        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def update_memory_metrics(self, memory):
        try:
            # Update memory boxes
            self.memory_boxes["Total"].value_label.configure(
                text=f"{memory.total / (1024**3):.1f} GB"
            )
            self.memory_boxes["Used"].value_label.configure(
                text=f"{memory.used / (1024**3):.1f} GB"
            )
            self.memory_boxes["Available"].value_label.configure(
                text=f"{memory.available / (1024**3):.1f} GB"
            )
            self.memory_boxes["Percent"].value_label.configure(
                text=f"{memory.percent:.1f}%"
            )
            
            # Update memory graph with optimized plotting
            self.memory_graph.ax.clear()
            times = list(self.history['time'])
            self.memory_graph.ax.plot(
                times, list(self.history['memory']),
                color=self.colors["accent"]
            )
            self.memory_graph.canvas.draw()
            
            # Update memory pie chart
            self.memory_pie.update_chart(
                ["Used", "Free"],
                [memory.percent, 100 - memory.percent],
                [self.colors["accent"], self.colors["success"]]
            )
        except Exception as e:
            print(f"Error updating memory metrics: {e}")

    def update_cpu_metrics(self, cpu_percent, cpu_freq, core_count, thread_count):
        try:
            # Update CPU boxes
            self.cpu_boxes["Usage"].value_label.configure(text=f"{cpu_percent:.1f}%")
            self.cpu_boxes["Freq"].value_label.configure(text=f"{cpu_freq:.1f} MHz")
            self.cpu_boxes["Cores"].value_label.configure(text=str(core_count))
            self.cpu_boxes["Threads"].value_label.configure(text=str(thread_count))
            
            # Update CPU graph with optimized plotting
            self.cpu_graph.ax.clear()
            times = list(self.history['time'])
            self.cpu_graph.ax.plot(
                times, list(self.history['cpu']),
                color=self.colors["accent"]
            )
            self.cpu_graph.canvas.draw()
            
            # Update CPU pie chart
            self.cpu_pie.update_chart(
                ["Used", "Idle"],
                [cpu_percent, 100 - cpu_percent],
                [self.colors["accent"], self.colors["success"]]
            )
        except Exception as e:
            print(f"Error updating CPU metrics: {e}")

    def update_disk_metrics(self, disk):
        try:
            # Update disk boxes
            self.disk_boxes["Total"].value_label.configure(
                text=f"{disk.total / (1024**3):.1f} GB"
            )
            self.disk_boxes["Used"].value_label.configure(
                text=f"{disk.used / (1024**3):.1f} GB"
            )
            self.disk_boxes["Free"].value_label.configure(
                text=f"{disk.free / (1024**3):.1f} GB"
            )
            self.disk_boxes["Percent"].value_label.configure(
                text=f"{disk.percent:.1f}%"
            )
            
            # Update disk graph with optimized plotting
            self.disk_graph.ax.clear()
            times = list(self.history['time'])
            self.disk_graph.ax.plot(
                times, list(self.history['disk']),
                color=self.colors["accent"]
            )
            self.disk_graph.canvas.draw()
            
            # Update disk pie chart
            self.disk_pie.update_chart(
                ["Used", "Free"],
                [disk.percent, 100 - disk.percent],
                [self.colors["accent"], self.colors["success"]]
            )
        except Exception as e:
            print(f"Error updating disk metrics: {e}")

    def toggle_theme(self):
        self.colors = self.theme_manager.toggle_theme()
        self.configure(fg_color=self.colors["bg"])
        self.update_widget_colors()

    def update_widget_colors(self):
        for widget in self.winfo_children():
            if isinstance(widget, (ctk.CTkFrame, ctk.CTkButton, ctk.CTkLabel)):
                widget.configure(fg_color=self.colors["surface"])
                if isinstance(widget, (ctk.CTkButton, ctk.CTkLabel)):
                    widget.configure(text_color=self.colors["text"])

    def on_closing(self):
        self.running = False
        self.quit()

    def create_status_bar(self):
        self.status_bar = ctk.CTkFrame(
            self,
            height=30,
            fg_color=self.colors["surface"]
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        sys_info = ctk.CTkLabel(
            self.status_bar,
            text=f"OS: {os.name.upper()} | CPU: {psutil.cpu_count()} Cores",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        sys_info.pack(side="left", padx=15)
        
        self.clock_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        self.clock_label.pack(side="right", padx=15)
        self.update_clock()

    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.after(1000, self.update_clock)

if __name__ == "__main__":
    app = SystemMonitor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()