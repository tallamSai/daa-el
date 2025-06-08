import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import networkx as nx
import threading
import time
from datetime import datetime
import collections
from scipy import stats

# Configure matplotlib for tkinter
plt.style.use('dark_background')
plt.rcParams.update({
    'axes.facecolor': '#1e1e2e',
    'figure.facecolor': '#1e1e2e',
    'savefig.facecolor': '#1e1e2e',
    'text.color': '#cdd6f4',
    'axes.labelcolor': '#cdd6f4',
    'xtick.color': '#cdd6f4',
    'ytick.color': '#cdd6f4'
})

class SystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced System Monitor")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e2e')
        
        # Configure matplotlib
        plt.style.use('dark_background')
        
        # Data storage
        self.memory_history = collections.deque(maxlen=50)
        self.cpu_history = collections.deque(maxlen=50)
        self.time_stamps = collections.deque(maxlen=50)
        self.process_graph = nx.DiGraph()
        self.graph_pos = None
        self.anomaly_threshold = 2.5
        self.monitoring = True
        
        # Initialize matplotlib figures
        self.setup_matplotlib_figures()
        self.setup_styles()
        self.create_widgets()
        
        # Start monitoring thread
        self.monitor_thread = None
        
        # Initial data update
        self.update_initial_data()
        
        # Start monitoring
        self.start_monitoring()
    
    def setup_matplotlib_figures(self):
        """Initialize all matplotlib figures with proper configuration"""
        # Memory usage figure
        self.memory_fig = Figure(figsize=(6, 4), dpi=100, facecolor='#1e1e2e')
        self.memory_ax = self.memory_fig.add_subplot(111)
        self.memory_ax.set_facecolor('#1e1e2e')
        
        # CPU usage figure
        self.cpu_fig = Figure(figsize=(6, 4), dpi=100, facecolor='#1e1e2e')
        self.cpu_ax = self.cpu_fig.add_subplot(111)
        self.cpu_ax.set_facecolor('#1e1e2e')
        
        # Process graph figure
        self.graph_fig = Figure(figsize=(8, 6), dpi=100, facecolor='#1e1e2e')
        self.graph_ax = self.graph_fig.add_subplot(111)
        self.graph_ax.set_facecolor('#1e1e2e')
        
        # Memory prediction figure
        self.prediction_fig = Figure(figsize=(10, 4), dpi=100, facecolor='#1e1e2e')
        self.prediction_ax = self.prediction_fig.add_subplot(111)
        self.prediction_ax.set_facecolor('#1e1e2e')
        
        # Configure all figures
        for fig in [self.memory_fig, self.cpu_fig, self.graph_fig, self.prediction_fig]:
            fig.patch.set_facecolor('#1e1e2e')
    
    def setup_styles(self):
        """Setup custom styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for dark theme
        style.configure('Dark.TFrame', background='#1e1e2e')
        style.configure('Dark.TLabel', background='#1e1e2e', foreground='#cdd6f4')
        style.configure('Dark.TButton', background='#313244', foreground='#cdd6f4')
        style.configure('Danger.TButton', background='#f38ba8', foreground='#11111b')
        style.configure('Success.TButton', background='#a6e3a1', foreground='#11111b')
        
    def create_widgets(self):
        """Create the main UI components with enhanced styling"""
        # Apply modern styling
        self.root.configure(bg='#1e1e2e')
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Modern.TFrame', background='#1e1e2e')
        style.configure('Modern.TLabel', 
                       background='#1e1e2e', 
                       foreground='#cdd6f4',
                       font=('Segoe UI', 10))
        style.configure('Modern.TButton',
                       background='#313244',
                       foreground='#cdd6f4',
                       padding=10)
        style.configure('Header.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       foreground='#89b4fa')
        
        # Create main container with padding
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add application header
        header_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, 
                 text="System Process Monitor",
                 style='Header.TLabel').pack(side=tk.LEFT)
        
        # Add quick action buttons
        action_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        action_frame.pack(side=tk.RIGHT)
        
        ttk.Button(action_frame,
                  text="🔄 Refresh",
                  style='Modern.TButton',
                  command=self.refresh_all).pack(side=tk.LEFT, padx=5)
        
        # Create notebook with custom styling
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Add tabs with enhanced visuals
        self.create_dashboard_tab()
        self.create_process_graph_tab()
        self.create_memory_analysis_tab()
        self.create_process_manager_tab()
    
    def create_dashboard_tab(self):
        """Create the main dashboard tab with graphs"""
        dashboard_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Top row - Memory and CPU usage
        top_frame = ttk.Frame(dashboard_frame, style='Modern.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Memory usage chart
        memory_frame = ttk.LabelFrame(top_frame, text="Memory Usage", style='Modern.TFrame')
        memory_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.memory_canvas = FigureCanvasTkAgg(self.memory_fig, memory_frame)
        self.memory_canvas.draw()
        self.memory_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        memory_toolbar = NavigationToolbar2Tk(self.memory_canvas, memory_frame)
        memory_toolbar.update()
        
        # CPU usage chart
        cpu_frame = ttk.LabelFrame(top_frame, text="CPU Usage", style='Modern.TFrame')
        cpu_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_fig, cpu_frame)
        self.cpu_canvas.draw()
        self.cpu_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        cpu_toolbar = NavigationToolbar2Tk(self.cpu_canvas, cpu_frame)
        cpu_toolbar.update()
        
        # System info
        info_frame = ttk.LabelFrame(dashboard_frame, text="System Information", style='Modern.TFrame')
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.system_info_label = ttk.Label(info_frame, text="", style='Modern.TLabel')
        self.system_info_label.pack(padx=10, pady=10)
    
    def create_process_graph_tab(self):
        """Create the process dependency graph tab"""
        # Create main frame
        graph_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(graph_frame, text="Process Graph")
        
        # Controls frame
        control_frame = ttk.Frame(graph_frame, style='Modern.TFrame')
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add refresh button
        ttk.Button(control_frame, 
                  text="🔄 Refresh Graph",
                  style='Modern.TButton',
                  command=self.update_process_graph).pack(side=tk.LEFT, padx=5)
        
        # Create canvas frame
        canvas_frame = ttk.Frame(graph_frame, style='Modern.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create canvas
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, canvas_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.graph_canvas, canvas_frame)
        toolbar.update()
        
        # Schedule initial graph update
        self.root.after(1000, self.update_process_graph)
    
    def update_process_graph(self):
        """Update the process dependency graph focusing on high memory processes"""
        try:
            # Clear the graph
            self.graph_ax.clear()
            
            # Create new directed graph
            G = nx.DiGraph()
            
            # Get processes with focus on memory usage
            processes = {}
            high_memory_pids = set()  # Track high memory processes
            
            # First pass: identify high memory processes
            for proc in psutil.process_iter(['pid', 'name', 'ppid', 'memory_percent', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    if not pinfo:
                        continue
                    
                    # Get memory usage
                    memory_percent = pinfo.get('memory_percent', 0) or 0
                    cpu_percent = pinfo.get('cpu_percent', 0) or 0
                    
                    # Store process info if it uses significant memory
                    if memory_percent > 0.5:  # Increased threshold for clearer graph
                        pid = pinfo['pid']
                        high_memory_pids.add(pid)
                        processes[pid] = {
                            'name': pinfo.get('name', 'Unknown'),
                            'ppid': pinfo.get('ppid', 0),
                            'memory_percent': memory_percent,
                            'cpu_percent': cpu_percent
                        }
                except:
                    continue
            
            # Second pass: add parent processes of high memory processes
            for pid in list(high_memory_pids):
                try:
                    proc = psutil.Process(pid)
                    parent = proc.parent()
                    if parent and parent.pid not in processes:
                        pinfo = parent.info
                        processes[parent.pid] = {
                            'name': pinfo['name'],
                            'ppid': pinfo.get('ppid', 0),
                            'memory_percent': pinfo.get('memory_percent', 0) or 0,
                            'cpu_percent': pinfo.get('cpu_percent', 0) or 0
                        }
                except:
                    continue
            
            # Build graph
            for pid, data in processes.items():
                # Add node
                G.add_node(pid, **data)
                
                # Add edge to parent if exists
                ppid = data['ppid']
                if ppid in processes and ppid != pid:
                    G.add_edge(ppid, pid)
            
            if len(G.nodes()) == 0:
                self.graph_ax.text(0.5, 0.5, 'No high memory processes found\n(>0.5% memory usage)',
                                 ha='center', va='center',
                                 transform=self.graph_ax.transAxes,
                                 color='#cdd6f4')
            else:
                # Calculate layout with more spacing
                pos = nx.spring_layout(G, k=2.0, iterations=50)
                
                # Draw edges
                nx.draw_networkx_edges(G, pos,
                                     edge_color='#6c7086',
                                     arrows=True,
                                     arrowsize=20,
                                     ax=self.graph_ax,
                                     width=2)
                
                # Draw nodes with size based on memory usage
                node_sizes = []
                node_colors = []
                for node in G.nodes():
                    memory_pct = G.nodes[node]['memory_percent']
                    # Make high memory processes more prominent
                    size = 2000 + (memory_pct * 100)  # Increased base size
                    color = '#f38ba8' if node in high_memory_pids else '#89b4fa'
                    node_sizes.append(size)
                    node_colors.append(color)
                
                nx.draw_networkx_nodes(G, pos,
                                     node_size=node_sizes,
                                     node_color=node_colors,
                                     ax=self.graph_ax)
                
                # Add labels with memory percentage
                labels = {}
                for node in G.nodes():
                    data = G.nodes[node]
                    # Format label to emphasize memory usage
                    if node in high_memory_pids:
                        labels[node] = f"{data['name']}\n⚠️ {data['memory_percent']:.1f}% MEM\n{data['cpu_percent']:.1f}% CPU"
                    else:
                        labels[node] = f"{data['name']}\n{data['memory_percent']:.1f}% MEM"
                
                nx.draw_networkx_labels(G, pos, labels,
                                      font_size=9,  # Slightly larger font
                                      font_color='#cdd6f4',
                                      bbox=dict(facecolor='#313244',
                                              alpha=0.8,
                                              pad=0.7,
                                              edgecolor='none'),
                                      ax=self.graph_ax)
                
                # Add legend
                legend_elements = [
                    plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor='#f38ba8', markersize=15,
                              label='High Memory (>0.5%)'),
                    plt.Line2D([0], [0], marker='o', color='w',
                              markerfacecolor='#89b4fa', markersize=15,
                              label='Parent Process')
                ]
                self.graph_ax.legend(handles=legend_elements,
                                   loc='upper right',
                                   facecolor='#313244',
                                   edgecolor='#6c7086')
            
            # Set title and style
            self.graph_ax.set_title('High Memory Process Graph',
                                  color='#cdd6f4',
                                  pad=20)
            self.graph_ax.set_facecolor('#1e1e2e')
            self.graph_ax.axis('off')
            
            # Update display
            self.graph_fig.tight_layout()
            self.graph_canvas.draw()
            
        except Exception as e:
            print(f"Error updating graph: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error in graph
            self.graph_ax.clear()
            self.graph_ax.text(0.5, 0.5,
                             f"Error updating graph:\n{str(e)}",
                             ha='center', va='center',
                             color='#f38ba8',
                             transform=self.graph_ax.transAxes)
            self.graph_canvas.draw()
    
    def categorize_process(self, name, cmdline):
        """Categorize process based on name and command line"""
        name = name.lower()
        cmdline = ' '.join(cmdline).lower() if cmdline else ''
        
        categories = {
            'Browser': ['chrome', 'firefox', 'edge', 'opera', 'safari'],
            'Development': ['python', 'node', 'npm', 'java', 'code', 'git'],
            'System': ['system', 'svchost', 'service', 'registry', 'wininit'],
            'Security': ['antivirus', 'defender', 'firewall'],
            'Office': ['word', 'excel', 'powerpoint', 'outlook', 'teams'],
            'Media': ['vlc', 'spotify', 'music', 'video', 'media'],
            'Gaming': ['steam', 'game', 'unity', 'unreal'],
            'Background': ['updater', 'scheduler', 'helper']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name or keyword in cmdline for keyword in keywords):
                return category
        return 'Other'
    
    def show_all_process_trees(self):
        """Show complete process trees with enhanced visualization"""
        try:
            self.update_process_graph()
            
            # Add interactive tooltips
            self.add_graph_tooltips()
            
            # Add process grouping
            self.group_similar_processes(self.process_graph.nodes())
            
            # Add performance metrics
            self.add_performance_indicators()
            
            messagebox.showinfo("Process Trees", 
                              "Graph updated with enhanced visualization:\n" +
                              "• Interactive tooltips added\n" +
                              "• Process groups identified\n" +
                              "• Performance metrics displayed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show process trees: {e}")
    
    def focus_high_memory_processes(self):
        """Focus on high memory consuming processes and their trees"""
        try:
            # Get processes with high memory usage
            high_memory_processes = []
            for node in self.process_graph.nodes():
                node_data = self.process_graph.nodes[node]
                memory_pct = node_data.get('memory_percent', 0)
                memory_mb = node_data.get('memory_mb', 0)
                if memory_pct > 3.0 or memory_mb > 200:  # > 3% or > 200MB
                    high_memory_processes.append(node)
            
            if not high_memory_processes:
                messagebox.showinfo("High Memory Focus", "No high memory processes found")
                return
            
            # Include their parent and child processes
            focus_nodes = set(high_memory_processes)
            for proc in high_memory_processes:
                # Add parents
                for pred in self.process_graph.predecessors(proc):
                    focus_nodes.add(pred)
                # Add children
                for succ in self.process_graph.successors(proc):
                    focus_nodes.add(succ)
            
            # Create focused subgraph
            focused_subgraph = self.process_graph.subgraph(focus_nodes)
            
            # Show information about focused processes
            info_text = f"Focusing on {len(high_memory_processes)} high-memory processes and their trees:\n\n"
            for proc in sorted(high_memory_processes, 
                             key=lambda x: self.process_graph.nodes[x].get('memory_percent', 0), 
                             reverse=True)[:10]:
                node_data = self.process_graph.nodes[proc]
                info_text += f"• {node_data.get('name', 'Unknown')} (PID: {proc})\n"
                info_text += f"  Memory: {node_data.get('memory_percent', 0):.1f}% ({node_data.get('memory_mb', 0):.0f}MB)\n"
                info_text += f"  CPU: {node_data.get('cpu_percent', 0):.1f}%\n\n"
            
            messagebox.showinfo("High Memory Processes", info_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to focus on high memory processes: {e}")
    
    def create_memory_analysis_tab(self):
        """Create memory analysis tab with prediction graph and optimization suggestions"""
        analysis_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(analysis_frame, text="Memory Analysis")
        
        # Memory prediction graph
        prediction_frame = ttk.LabelFrame(analysis_frame, text="Memory Usage Prediction", 
                                        style='Modern.TFrame')
        prediction_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create canvas for prediction graph
        self.prediction_canvas = FigureCanvasTkAgg(self.prediction_fig, prediction_frame)
        self.prediction_canvas.draw()
        self.prediction_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        prediction_toolbar = NavigationToolbar2Tk(self.prediction_canvas, prediction_frame)
        prediction_toolbar.update()
        
        # Memory optimization suggestions
        optimization_frame = ttk.LabelFrame(analysis_frame, text="Memory Optimization", 
                                          style='Modern.TFrame')
        optimization_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar
        self.optimization_text = tk.Text(optimization_frame, 
                                       bg='#313244', 
                                       fg='#cdd6f4',
                                       font=('Consolas', 10),
                                       wrap=tk.WORD,
                                       insertbackground='#cdd6f4')
        
        optimization_scrollbar = ttk.Scrollbar(optimization_frame, 
                                             orient=tk.VERTICAL,
                                             command=self.optimization_text.yview)
        
        self.optimization_text.configure(yscrollcommand=optimization_scrollbar.set)
        
        # Pack text widget and scrollbar
        self.optimization_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        optimization_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Add control buttons
        control_frame = ttk.Frame(optimization_frame, style='Modern.TFrame')
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(control_frame,
                  text="🔄 Update Analysis",
                  style='Modern.TButton',
                  command=self.update_memory_analysis).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame,
                  text="📊 Show Detailed Stats",
                  style='Modern.TButton',
                  command=self.show_detailed_memory_stats).pack(side=tk.LEFT, padx=5)

    def create_process_manager_tab(self):
        """Create process manager tab with process list and controls"""
        manager_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(manager_frame, text="Process Manager")
        
        # Process list
        list_frame = ttk.LabelFrame(manager_frame, text="Running Processes", 
                                  style='Modern.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Search and filter frame
        filter_frame = ttk.Frame(list_frame, style='Modern.TFrame')
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="🔍 Filter:", 
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, 
                               textvariable=self.filter_var,
                               width=40)
        filter_entry.pack(side=tk.LEFT, padx=5)
        filter_entry.bind('<KeyRelease>', self.filter_processes)
        
        # Sort options
        ttk.Label(filter_frame, text="Sort by:", 
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        
        self.sort_var = tk.StringVar(value="memory")
        sort_options = ttk.OptionMenu(filter_frame, self.sort_var, 
                                    "memory", "memory", "cpu", "name", "pid",
                                    command=self.refresh_process_list)
        sort_options.pack(side=tk.LEFT, padx=5)
        
        # Treeview for processes
        tree_frame = ttk.Frame(list_frame, style='Modern.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Create columns
        columns = ('PID', 'Name', 'CPU%', 'Memory%', 'Memory MB', 'Threads', 'Status')
        self.process_tree = ttk.Treeview(tree_frame, 
                                       columns=columns, 
                                       show='headings', 
                                       height=15)
        
        # Configure columns
        for col in columns:
            self.process_tree.heading(col, text=col, 
                                    command=lambda c=col: self.sort_processes_by(c))
            width = 70 if col in ('PID', 'CPU%', 'Memory%', 'Threads') else 200
            self.process_tree.column(col, width=width, minwidth=50)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, 
                                  orient=tk.VERTICAL, 
                                  command=self.process_tree.yview)
        x_scrollbar = ttk.Scrollbar(tree_frame, 
                                  orient=tk.HORIZONTAL, 
                                  command=self.process_tree.xview)
        
        self.process_tree.configure(yscrollcommand=y_scrollbar.set,
                                  xscrollcommand=x_scrollbar.set)
        
        # Pack scrollbars and treeview
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Control buttons frame
        button_frame = ttk.Frame(manager_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Process control buttons
        ttk.Button(button_frame, 
                  text="⚠️ Kill Process",
                  style='Danger.TButton',
                  command=self.kill_selected_process).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame,
                  text="🛑 Terminate Process",
                  style='Danger.TButton',
                  command=self.terminate_selected_process).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame,
                  text="🔄 Refresh List",
                  style='Success.TButton',
                  command=self.refresh_process_list).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(manager_frame, style='Modern.TFrame')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, 
                                    text="Ready", 
                                    style='Modern.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        # Add right-click menu
        self.create_context_menu()
        
        # Initial process list update
        self.refresh_process_list()
    
    def show_detailed_memory_stats(self):
        """Show detailed memory statistics"""
        try:
            # Get detailed memory info
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Format detailed stats
            stats = [
                "=== DETAILED MEMORY STATISTICS ===\n",
                f"Total Memory: {self.bytes_to_gb(memory.total):.2f} GB\n",
                f"Available: {self.bytes_to_gb(memory.available):.2f} GB\n",
                f"Used: {self.bytes_to_gb(memory.used):.2f} GB ({memory.percent}%)\n",
                f"Free: {self.bytes_to_gb(memory.free):.2f} GB\n",
                f"Active: {self.bytes_to_gb(memory.active):.2f} GB\n",
                f"Inactive: {self.bytes_to_gb(getattr(memory, 'inactive', 0)):.2f} GB\n",
                f"Buffers: {self.bytes_to_gb(getattr(memory, 'buffers', 0)):.2f} GB\n",
                f"Cached: {self.bytes_to_gb(getattr(memory, 'cached', 0)):.2f} GB\n",
                f"Shared: {self.bytes_to_gb(getattr(memory, 'shared', 0)):.2f} GB\n",
                "\n=== SWAP MEMORY ===\n",
                f"Total Swap: {self.bytes_to_gb(swap.total):.2f} GB\n",
                f"Used Swap: {self.bytes_to_gb(swap.used):.2f} GB ({swap.percent}%)\n",
                f"Free Swap: {self.bytes_to_gb(swap.free):.2f} GB\n",
                f"Swapped in: {self.bytes_to_gb(swap.sin):.2f} GB\n",
                f"Swapped out: {self.bytes_to_gb(swap.sout):.2f} GB\n"
            ]
            
            # Show in message box
            messagebox.showinfo("Detailed Memory Statistics", "".join(stats))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get detailed stats: {e}")
    
    def update_memory_analysis(self):
        """Update memory analysis and predictions"""
        try:
            if len(self.memory_history) < 5:
                return
            
            # Clear previous prediction
            self.prediction_ax.clear()
            
            # Prepare data for prediction
            x = np.arange(len(self.memory_history))
            y = np.array(list(self.memory_history))
            
            # Fit polynomial for better prediction
            degree = min(3, len(self.memory_history) - 1)
            coeffs = np.polyfit(x, y, degree)
            
            # Generate prediction points
            future_points = 10
            future_x = np.arange(len(self.memory_history), len(self.memory_history) + future_points)
            predictions = np.polyval(coeffs, future_x)
            
            # Ensure predictions stay within reasonable bounds
            predictions = np.clip(predictions, 0, 100)
            
            # Plot historical data with confidence interval
            self.prediction_ax.plot(x, y, 'o-', color='#89b4fa', label='Historical',
                                  linewidth=2, markersize=4)
            
            # Add confidence interval
            if len(self.memory_history) > 10:
                std_dev = np.std(y)
                self.prediction_ax.fill_between(x, 
                                             np.clip(y - std_dev, 0, 100),
                                             np.clip(y + std_dev, 0, 100),
                                             color='#89b4fa', alpha=0.2)
            
            # Plot predictions with uncertainty cone
            self.prediction_ax.plot(future_x, predictions, '--', color='#a6e3a1',
                                  label='Predicted', linewidth=2, alpha=0.7)
            
            # Add prediction uncertainty cone
            std_dev_future = np.std(y) * np.sqrt(np.arange(1, future_points + 1) / len(y))
            self.prediction_ax.fill_between(future_x,
                                         np.clip(predictions - 2*std_dev_future, 0, 100),
                                         np.clip(predictions + 2*std_dev_future, 0, 100),
                                         color='#a6e3a1', alpha=0.2)
            
            # Add current time marker
            self.prediction_ax.axvline(x=len(self.memory_history)-1, color='#f38ba8',
                                     linestyle=':', alpha=0.7, label='Current')
            
            # Add warning threshold
            self.prediction_ax.axhline(y=80, color='#f38ba8', linestyle='--',
                                     alpha=0.5, label='Warning Threshold')
            
            # Customize appearance
            self.prediction_ax.set_title('Memory Usage Prediction', color='#cdd6f4', pad=20)
            self.prediction_ax.set_ylabel('Memory Usage %', color='#cdd6f4')
            self.prediction_ax.set_xlabel('Time (intervals)', color='#cdd6f4')
            self.prediction_ax.tick_params(colors='#cdd6f4')
            self.prediction_ax.grid(True, alpha=0.3)
            self.prediction_ax.set_ylim(0, 100)
            self.prediction_ax.legend(loc='upper left')
            
            # Draw prediction graph
            self.prediction_canvas.draw()
            
            # Update optimization suggestions
            self.update_optimization_suggestions()
            
        except Exception as e:
            print(f"Memory analysis update error: {e}")
    
    def update_optimization_suggestions(self):
        """Update memory optimization suggestions"""
        try:
            suggestions = []
            
            # Get top memory consumers
            high_memory_procs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['memory_percent'] and pinfo['memory_percent'] > 2.0:
                        high_memory_procs.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            high_memory_procs.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            suggestions.append("=== MEMORY OPTIMIZATION SUGGESTIONS ===\n")
            
            if len(self.memory_history) > 0 and self.memory_history[-1] > 80:
                suggestions.append("⚠️  HIGH MEMORY USAGE DETECTED!\n")
                suggestions.append("Consider the following actions:\n")
            
            suggestions.append(f"Current Memory Usage: {self.memory_history[-1] if self.memory_history else 'N/A'}%\n")
            suggestions.append("\nTop Memory Consumers:\n")
            
            for i, proc in enumerate(high_memory_procs[:10]):
                suggestions.append(f"{i+1:2d}. {proc['name']:<20} - {proc['memory_percent']:.2f}%\n")
            
            suggestions.append("\nRecommendations:\n")
            suggestions.append("• Close unnecessary applications\n")
            suggestions.append("• Clear browser cache and tabs\n")
            suggestions.append("• Restart high-memory processes\n")
            suggestions.append("• Check for memory leaks in running applications\n")
            suggestions.append("• Consider upgrading RAM if consistently high usage\n")
            
            # System recommendations
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                suggestions.append("\n🔴 CRITICAL: Memory usage critically high!\n")
                suggestions.append("• Immediately close non-essential applications\n")
                suggestions.append("• Consider restarting the system\n")
            elif memory.percent > 75:
                suggestions.append("\n🟡 WARNING: Memory usage high\n")
                suggestions.append("• Monitor running processes closely\n")
            else:
                suggestions.append("\n🟢 Memory usage is within normal limits\n")
            
            # Update text widget
            self.optimization_text.delete(1.0, tk.END)
            self.optimization_text.insert(1.0, ''.join(suggestions))
            
        except Exception as e:
            print(f"Optimization suggestions update error: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        self.monitoring = False
        self.root.quit()

    def refresh_all(self):
        """Refresh all components of the application"""
        try:
            self.update_process_graph()
            self.refresh_process_list()
            self.update_memory_analysis()
            self.update_charts()
            messagebox.showinfo("Refresh", "All components updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh: {e}")

    def update_initial_data(self):
        """Perform initial data update"""
        try:
            # Get initial system stats
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            current_time = datetime.now()
            
            # Initialize histories
            self.memory_history.append(memory.percent)
            self.cpu_history.append(cpu_percent)
            self.time_stamps.append(current_time)
            
            # Initial process graph
            self.update_process_graph()
            
            # Initial charts
            self.update_charts()
            
            # Initial system info
            self.update_system_info()
            
        except Exception as e:
            print(f"Initial data update error: {e}")
            import traceback
            traceback.print_exc()

    def update_gui(self):
        """Update GUI elements with proper error handling"""
        try:
            if not self.monitoring:
                return
                
            # Update charts first
            self.update_charts()
            
            # Update system info
            self.update_system_info()
            
            # Update process list if visible
            if self.notebook.select() == self.notebook.tabs()[-1]:  # Process Manager tab
                self.refresh_process_list()
            
            # Update process graph if visible
            if self.notebook.select() == self.notebook.tabs()[1]:  # Process Graph tab
                self.update_process_graph()
            
            # Update memory analysis if visible
            if self.notebook.select() == self.notebook.tabs()[2]:  # Memory Analysis tab
                self.update_memory_analysis()
            
        except Exception as e:
            print(f"GUI update error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Schedule next update if still monitoring
            if self.monitoring:
                self.root.after(3000, self.update_gui)

    def start_monitoring(self):
        """Start the monitoring thread and GUI updates"""
        try:
            # Start monitoring thread
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
                self.monitor_thread.start()
            
            # Initial graph update
            self.update_process_graph()
            
            # Start GUI updates
            self.root.after(100, self.update_gui)
            
        except Exception as e:
            print(f"Failed to start monitoring: {e}")
            import traceback
            traceback.print_exc()
    
    def monitor_system(self):
        """Monitor system resources in background thread"""
        while self.monitoring:
            try:
                # Get system stats
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                current_time = datetime.now()
                
                # Update histories
                self.memory_history.append(memory.percent)
                self.cpu_history.append(cpu_percent)
                self.time_stamps.append(current_time)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(2)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)  # Longer delay on error
    
    def update_charts(self):
        """Update memory and CPU usage charts"""
        try:
            if len(self.memory_history) > 0:
                # Memory chart
                self.memory_ax.clear()
                self.memory_ax.plot(list(range(len(self.memory_history))), 
                                  list(self.memory_history), 
                                  color='#89b4fa', 
                                  linewidth=2,
                                  marker='o',
                                  markersize=4)
                
                # Add fill below the line
                self.memory_ax.fill_between(range(len(self.memory_history)), 
                                          list(self.memory_history), 
                                          color='#89b4fa', 
                                          alpha=0.2)
                
                # Add warning threshold
                self.memory_ax.axhline(y=80, color='#f38ba8', 
                                     linestyle='--', alpha=0.5,
                                     label='Warning Threshold')
                
                # Customize appearance
                self.memory_ax.set_title('Memory Usage Over Time', 
                                       color='#cdd6f4', pad=20)
                self.memory_ax.set_ylabel('Usage %', color='#cdd6f4')
                self.memory_ax.set_xlabel('Time (s)', color='#cdd6f4')
                self.memory_ax.tick_params(colors='#cdd6f4')
                self.memory_ax.grid(True, alpha=0.3)
                self.memory_ax.set_ylim(0, 100)
                
                # Add legend
                self.memory_ax.legend(['Memory Usage', 'Warning (80%)'],
                                    loc='upper right',
                                    facecolor='#313244',
                                    edgecolor='#6c7086')
                
                self.memory_canvas.draw()
                
                # CPU chart
                self.cpu_ax.clear()
                self.cpu_ax.plot(list(range(len(self.cpu_history))), 
                               list(self.cpu_history), 
                               color='#a6e3a1', 
                               linewidth=2,
                               marker='o',
                               markersize=4)
                
                # Add fill below the line
                self.cpu_ax.fill_between(range(len(self.cpu_history)), 
                                       list(self.cpu_history), 
                                       color='#a6e3a1', 
                                       alpha=0.2)
                
                # Add warning threshold
                self.cpu_ax.axhline(y=80, color='#f38ba8', 
                                  linestyle='--', alpha=0.5,
                                  label='Warning Threshold')
                
                # Customize appearance
                self.cpu_ax.set_title('CPU Usage Over Time', 
                                    color='#cdd6f4', pad=20)
                self.cpu_ax.set_ylabel('Usage %', color='#cdd6f4')
                self.cpu_ax.set_xlabel('Time (s)', color='#cdd6f4')
                self.cpu_ax.tick_params(colors='#cdd6f4')
                self.cpu_ax.grid(True, alpha=0.3)
                self.cpu_ax.set_ylim(0, 100)
                
                # Add legend
                self.cpu_ax.legend(['CPU Usage', 'Warning (80%)'],
                                 loc='upper right',
                                 facecolor='#313244',
                                 edgecolor='#6c7086')
                
                self.cpu_canvas.draw()
                
        except Exception as e:
            print(f"Chart update error: {e}")
    
    def filter_processes(self, event=None):
        """Filter processes based on search text"""
        try:
            search_text = self.filter_var.get().lower()
            self.refresh_process_list(search_text)
        except Exception as e:
            print(f"Filter error: {e}")

    def refresh_process_list(self, filter_text=None):
        """Refresh the process list with optional filtering"""
        try:
            # Clear existing items
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            
            # Get all processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 
                                           'memory_percent', 'memory_info',
                                           'num_threads', 'status']):
                try:
                    pinfo = proc.info
                    
                    # Skip if filtered out
                    if filter_text and filter_text not in pinfo['name'].lower():
                        continue
                    
                    memory_mb = pinfo['memory_info'].rss / (1024 * 1024) if pinfo['memory_info'] else 0
                    
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'] or 0,
                        'memory_percent': pinfo['memory_percent'] or 0,
                        'memory_mb': memory_mb,
                        'threads': pinfo['num_threads'],
                        'status': pinfo['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort processes based on selected criterion
            sort_by = self.sort_var.get()
            if sort_by == 'memory':
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            elif sort_by == 'cpu':
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == 'name':
                processes.sort(key=lambda x: x['name'].lower())
            elif sort_by == 'pid':
                processes.sort(key=lambda x: x['pid'])
            
            # Add to treeview
            for proc in processes[:100]:  # Limit to 100 for performance
                self.process_tree.insert('', 'end', values=(
                    proc['pid'],
                    proc['name'][:50],
                    f"{proc['cpu_percent']:.1f}",
                    f"{proc['memory_percent']:.1f}",
                    f"{proc['memory_mb']:.1f}",
                    proc['threads'],
                    proc['status']
                ))
            
            # Update status
            total = len(processes)
            shown = min(100, total)
            self.status_label.config(
                text=f"Showing {shown} of {total} processes" +
                     (f" (filtered from {total})" if filter_text else "")
            )
            
        except Exception as e:
            print(f"Process list refresh error: {e}")
            self.status_label.config(text=f"Error: {str(e)}")

    def sort_processes_by(self, column):
        """Sort process list by column"""
        try:
            items = [(self.process_tree.set(item, column), item) 
                    for item in self.process_tree.get_children('')]
            
            # Convert values for proper sorting
            if column in ('CPU%', 'Memory%', 'Memory MB', 'Threads', 'PID'):
                items = [(float(value.replace('%', '')), item) 
                        if value else (0, item) for value, item in items]
            
            # Sort items
            items.sort(reverse=True)
            
            # Rearrange items in sorted positions
            for index, (_, item) in enumerate(items):
                self.process_tree.move(item, '', index)
            
            # Update status
            self.status_label.config(text=f"Sorted by {column}")
            
        except Exception as e:
            print(f"Sort error: {e}")

    def create_context_menu(self):
        """Create right-click context menu for process tree"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#313244', fg='#cdd6f4')
        self.context_menu.add_command(label="Kill Process", 
                                    command=self.kill_selected_process)
        self.context_menu.add_command(label="Terminate Process",
                                    command=self.terminate_selected_process)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show Details",
                                    command=self.show_process_details)
        
        self.process_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            item = self.process_tree.identify_row(event.y)
            if item:
                self.process_tree.selection_set(item)
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def kill_selected_process(self):
        """Kill the selected process"""
        self.manage_process('kill')

    def terminate_selected_process(self):
        """Terminate the selected process"""
        self.manage_process('terminate')

    def manage_process(self, action):
        """Kill or terminate a selected process"""
        try:
            selection = self.process_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a process first")
                return
            
            # Get PID from selection
            item = self.process_tree.item(selection[0])
            pid = int(item['values'][0])
            process_name = item['values'][1]
            
            # Confirm action
            if not messagebox.askyesno("Confirm Action", 
                                     f"Are you sure you want to {action} process '{process_name}' (PID: {pid})?"):
                return
            
            # Perform action
            try:
                proc = psutil.Process(pid)
                if action == 'kill':
                    proc.kill()
                elif action == 'terminate':
                    proc.terminate()
                
                messagebox.showinfo("Success", f"Process {action}ed successfully")
                self.refresh_process_list()
                
            except psutil.NoSuchProcess:
                messagebox.showerror("Error", "Process no longer exists")
            except psutil.AccessDenied:
                messagebox.showerror("Error", "Access denied. Try running as administrator")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to {action} process: {e}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to manage process: {e}")

    def show_process_details(self):
        """Show detailed information about selected process"""
        try:
            selection = self.process_tree.selection()
            if not selection:
                return
            
            item = self.process_tree.item(selection[0])
            pid = int(item['values'][0])
            
            try:
                proc = psutil.Process(pid)
                info = proc.as_dict(attrs=[
                    'name', 'exe', 'status', 'cpu_percent', 'memory_percent',
                    'memory_info', 'num_threads', 'connections', 'create_time',
                    'username', 'nice', 'cmdline'
                ])
                
                details = [
                    "=== PROCESS DETAILS ===\n",
                    f"Name: {info['name']}\n",
                    f"PID: {pid}\n",
                    f"Executable: {info['exe']}\n",
                    f"Status: {info['status']}\n",
                    f"CPU Usage: {info['cpu_percent']}%\n",
                    f"Memory Usage: {info['memory_percent']:.1f}%\n",
                    f"Memory (RSS): {info['memory_info'].rss / (1024*1024):.1f} MB\n",
                    f"Threads: {info['num_threads']}\n",
                    f"User: {info['username']}\n",
                    f"Started: {datetime.fromtimestamp(info['create_time']).strftime('%Y-%m-%d %H:%M:%S')}\n",
                    f"Nice Value: {info['nice']}\n",
                    "\nCommand Line:\n",
                    " ".join(info['cmdline'] or []),
                    "\n\nNetwork Connections:\n"
                ]
                
                if info['connections']:
                    for conn in info['connections']:
                        details.append(
                            f"- {conn.laddr.ip}:{conn.laddr.port} -> "
                            f"{conn.raddr.ip if conn.raddr else '*'}:"
                            f"{conn.raddr.port if conn.raddr else '*'} "
                            f"({conn.status})\n"
                        )
                else:
                    details.append("No active connections\n")
                
                messagebox.showinfo("Process Details", "".join(details))
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                messagebox.showerror("Error", str(e))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get process details: {e}")

    def update_system_info(self):
        """Update system information display"""
        try:
            # Get system information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            cpu_freq = psutil.cpu_freq()
            disk = psutil.disk_usage('/')
            
            # Format information
            info = [
                "=== SYSTEM INFORMATION ===\n",
                f"CPU Usage: {psutil.cpu_percent()}%\n",
                f"CPU Frequency: {cpu_freq.current:.1f} MHz\n",
                f"Memory Usage: {memory.percent}% of {self.bytes_to_gb(memory.total):.1f} GB\n",
                f"Swap Usage: {swap.percent}% of {self.bytes_to_gb(swap.total):.1f} GB\n",
                f"Disk Usage: {disk.percent}% of {self.bytes_to_gb(disk.total):.1f} GB\n",
                f"Running Processes: {len(psutil.pids())}\n",
                f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
            ]
            
            # Update label
            self.system_info_label.config(text=''.join(info))
            
        except Exception as e:
            print(f"System info update error: {e}")
    
    def bytes_to_gb(self, bytes_value):
        """Convert bytes to gigabytes"""
        return bytes_value / (1024 * 1024 * 1024)

    def detect_anomalies(self):
        """Detect anomalous processes based on resource usage"""
        try:
            anomalies = []
            
            # Get current process stats
            memory_values = []
            cpu_values = []
            process_data = []
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['memory_percent'] and pinfo['cpu_percent']:
                        memory_values.append(pinfo['memory_percent'])
                        cpu_values.append(pinfo['cpu_percent'])
                        process_data.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if len(memory_values) < 3:
                messagebox.showinfo("Anomaly Detection", "Not enough data for anomaly detection")
                return
            
            # Calculate Z-scores
            memory_z_scores = np.abs(stats.zscore(memory_values))
            cpu_z_scores = np.abs(stats.zscore(cpu_values))
            
            # Find anomalies
            for i, (mem_z, cpu_z) in enumerate(zip(memory_z_scores, cpu_z_scores)):
                if mem_z > self.anomaly_threshold or cpu_z > self.anomaly_threshold:
                    anomalies.append({
                        'process': process_data[i],
                        'memory_z': mem_z,
                        'cpu_z': cpu_z
                    })
            
            # Display results
            if anomalies:
                result = "Anomalous Processes Detected:\n\n"
                for anomaly in anomalies[:10]:  # Limit to top 10
                    proc = anomaly['process']
                    result += f"PID: {proc['pid']}, Name: {proc['name']}\n"
                    result += f"  Memory: {proc['memory_percent']:.2f}% (Z-score: {anomaly['memory_z']:.2f})\n"
                    result += f"  CPU: {proc['cpu_percent']:.2f}% (Z-score: {anomaly['cpu_z']:.2f})\n\n"
                
                messagebox.showwarning("Anomaly Detection Results", result)
            else:
                messagebox.showinfo("Anomaly Detection", "No anomalous processes detected")
                
        except Exception as e:
            messagebox.showerror("Error", f"Anomaly detection failed: {e}")

def main():
    """Main application entry point"""
    # Check if required modules are available
    try:
        import psutil
        import matplotlib
        import networkx
        import scipy
    except ImportError as e:
        print(f"Missing required module: {e}")
        print("Please install required packages:")
        print("pip install psutil matplotlib networkx scipy numpy")
        return
    
    # Create and run application
    root = tk.Tk()
    app = SystemMonitor(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        app.monitoring = False

if __name__ == "__main__":
    main()