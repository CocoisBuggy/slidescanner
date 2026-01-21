import gi

from typing import Optional
import time

from matplotlib.lines import Line2D

from .auto_capture import AutoCaptureManager

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk
import matplotlib

matplotlib.use("GTK4Agg")
from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg as FigureCanvas
from matplotlib.figure import Figure


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
        self.figure = Figure(
            figsize=(width / dpi, height / dpi),
            dpi=dpi,
            constrained_layout=False,
        )
        self.canvas = FigureCanvas(self.figure)

        # Set up the plot with proper margins
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#f8f9fa")
        self.figure.patch.set_facecolor("#ffffff")

        # Adjust subplot parameters to prevent cropping
        self.figure.subplots_adjust(
            left=0.20,
            right=0.90,
            top=0.85,
            bottom=0.20,
        )

        # Style the plot
        self.ax.grid(True, alpha=0.3, linestyle="--")
        self.ax.tick_params(colors="#666666")
        for spine in self.ax.spines.values():
            spine.set_color("#cccccc")
            spine.set_linewidth(0.5)

        # Add canvas to the widget
        self.set_size_request(width, height)
        self.append(self.canvas)

        # Data storage
        self.max_points = 100  # Maximum number of data points to keep


class StabilityGraph(GraphWidget):
    """A graph widget for displaying stability over time."""

    stability_data: list[list[float]] = []
    lines: list[Line2D] = []

    def __init__(self, width: int = 400, height: int = 150):
        super().__init__(width, height)

        # Configure the plot for stability data with smaller fonts and padding
        self.ax.set_xlabel("Time (seconds)", fontsize=8, color="#333333")
        self.ax.set_ylabel("Stability", fontsize=8, color="#333333")
        self.ax.set_ylim(0.0, 1.2)
        self.ax.set_title(
            "Image Stability Over Time",
            fontsize=9,
            color="#333333",
            pad=5,
        )

        # Create the line plot
        self.lines = [self.ax.plot([], [])[0] for x in range(7)]
        print(self.lines)

        # Initialize empty plot
        self.update_plot()

    def add_data(self, stability: list[float]):
        """Add a new stability data point."""
        if len(stability) != AutoCaptureManager.stability_duration:
            print("INVALID data got added")
            return

        self.stability_data.append(stability)

        if len(self.stability_data) > self.max_points:
            self.stability_data.pop(0)

        self.update_plot()

    def update_plot(self):
        """Update the plot with current data."""
        # Update line data
        for series, line in enumerate(self.lines):
            line.set_data(
                list(range(len(self.stability_data))),
                list([x[series] for x in self.stability_data]),
            )

        # Auto-scale y-axis to ensure line is visible
        self.ax.relim()
        self.ax.autoscale_view()

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

    def create_stability_graph(
        self, name: str, width: int = 400, height: int = 150
    ) -> StabilityGraph:
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
        if graph and hasattr(graph, "add_data_point"):
            graph.add_data_point(*args, **kwargs)

    def reset_graph(self, name: str):
        """Reset a specific graph."""
        graph = self.get_graph(name)
        if graph and hasattr(graph, "reset"):
            graph.reset()

    def reset_all_graphs(self):
        """Reset all registered graphs."""
        for graph in self.graphs.values():
            if hasattr(graph, "reset"):
                graph.reset()
