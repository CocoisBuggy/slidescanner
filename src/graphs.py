import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GdkPixbuf, GLib
import matplotlib
matplotlib.use('GTK4Agg')
from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from collections import deque
from typing import List, Optional
import time


class GraphWidget(Gtk.Box):
    """A reusable GTK widget that hosts a matplotlib graph."""
    
    def __init__(self, width: int = 400, height: int = 200, dpi: int = 100):
        """
        Initialize the graph widget.
        
        Args:
            width: Widget width in pixels
            height: Widget height in pixels
            dpi: DPI for the matplotlib figure
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create matplotlib figure and canvas with tight layout disabled
        self.figure = Figure(figsize=(width/dpi, height/dpi), dpi=dpi, constrained_layout=False)
        self.canvas = FigureCanvas(self.figure)
        
        # Set up the plot with proper margins
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#f8f9fa')
        self.figure.patch.set_facecolor('#ffffff')
        
        # Adjust subplot parameters to prevent cropping
        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.15)
        
        # Style the plot
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.tick_params(colors='#666666')
        for spine in self.ax.spines.values():
            spine.set_color('#cccccc')
            spine.set_linewidth(0.5)
        
        # Add canvas to the widget
        self.set_size_request(width, height)
        self.append(self.canvas)
        
        # Data storage
        self.max_points = 100  # Maximum number of data points to keep


class StabilityGraph(GraphWidget):
    """A graph widget for displaying stability over time."""
    
    def __init__(self, width: int = 400, height: int = 150):
        super().__init__(width, height)
        
        # Data storage
        self.time_data = deque(maxlen=self.max_points)
        self.stability_data = deque(maxlen=self.max_points)
        self.start_time = time.time()
        
        # Configure the plot for stability data with smaller fonts and padding
        self.ax.set_xlabel('Time (seconds)', fontsize=8, color='#333333')
        self.ax.set_ylabel('Stability', fontsize=8, color='#333333')
        self.ax.set_title('Image Stability Over Time', fontsize=9, color='#333333', pad=5)
        self.ax.set_ylim(0.0, 1.0)
        
        # Create the line plot
        self.line, = self.ax.plot([], [], 'b-', linewidth=1.5, alpha=0.8)
        self.stability_threshold_line = None
        
        # Add reference line for stability threshold
        self.add_stability_threshold(0.98)
        
        # Initialize empty plot
        self.update_plot()
    
    def add_stability_threshold(self, threshold: float):
        """Add a horizontal line showing the stability threshold."""
        if self.stability_threshold_line:
            self.stability_threshold_line.remove()
        
        self.stability_threshold_line = self.ax.axhline(
            y=threshold, color='red', linestyle='--', alpha=0.7, linewidth=1,
            label=f'Threshold ({threshold:.2f})'
        )
        self.ax.legend(loc='upper right', fontsize=8)
    
    def add_data_point(self, stability: float):
        """Add a new stability data point."""
        current_time = time.time() - self.start_time
        self.time_data.append(current_time)
        self.stability_data.append(stability)
        
        # Update plot periodically
        if len(self.time_data) % 5 == 0:  # Update every 5 points to reduce overhead
            self.update_plot()
    
    def update_plot(self):
        """Update the plot with current data."""
        if not self.time_data:
            return
        
        # Update line data
        self.line.set_data(list(self.time_data), list(self.stability_data))
        
        # Adjust x-axis limits to show recent data
        if self.time_data:
            max_time = max(self.time_data)
            min_time = max(0, max_time - 30)  # Show last 30 seconds
            self.ax.set_xlim(min_time, max_time + 1)
        
        # Redraw canvas
        self.canvas.draw_idle()
    
    def reset(self):
        """Reset the graph data."""
        self.time_data.clear()
        self.stability_data.clear()
        self.start_time = time.time()
        self.update_plot()


class GraphManager:
    """Manager class for handling multiple graph widgets."""
    
    def __init__(self):
        self.graphs = {}
    
    def create_stability_graph(self, name: str, width: int = 400, height: int = 150) -> StabilityGraph:
        """Create and register a stability graph."""
        graph = StabilityGraph(width, height)
        self.graphs[name] = graph
        return graph
    
    def get_graph(self, name: str) -> Optional[GraphWidget]:
        """Get a registered graph by name."""
        return self.graphs.get(name)
    
    def update_graph(self, name: str, *args, **kwargs):
        """Update a specific graph."""
        graph = self.get_graph(name)
        if graph and hasattr(graph, 'add_data_point'):
            graph.add_data_point(*args, **kwargs)
    
    def reset_graph(self, name: str):
        """Reset a specific graph."""
        graph = self.get_graph(name)
        if graph and hasattr(graph, 'reset'):
            graph.reset()
    
    def reset_all_graphs(self):
        """Reset all registered graphs."""
        for graph in self.graphs.values():
            if hasattr(graph, 'reset'):
                graph.reset()