import gi
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import matplotlib

log = logging.getLogger(__name__)

matplotlib.use("GTK4Agg")

import numpy as np
from gi.repository import Gtk
from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from .auto_capture import AutoCaptureManager


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
        self.ax.set_facecolor("#2b2b2b")
        self.figure.patch.set_facecolor("#1e1e1e")

        # Adjust subplot parameters to prevent cropping
        self.figure.subplots_adjust(
            left=0.20,
            right=0.90,
            top=0.85,
            bottom=0.20,
        )

        # Style the plot
        self.ax.grid(True, alpha=0.3, linestyle="--", color="#555555")
        self.ax.tick_params(colors="#cccccc")
        for spine in self.ax.spines.values():
            spine.set_color("#555555")
            spine.set_linewidth(0.5)

        # Add canvas to the widget
        self.set_size_request(width, height)
        self.append(self.canvas)

        # Data storage
        self.max_points = 100  # Maximum number of data points to keep


class StabilityGraph(GraphWidget):
    """A graph widget for displaying stability over time."""

    lines: list[Line2D] = []
    auto_capture: AutoCaptureManager

    def __init__(
        self,
        auto_capture: AutoCaptureManager,
        width: int = 400,
        height: int = 150,
    ):
        super().__init__(width, height)
        self.auto_capture = auto_capture

        # Configure the plot for stability data with smaller fonts and padding
        self.ax.set_xlabel("Time (seconds)", fontsize=8, color="#cccccc")
        self.ax.set_ylabel("Stability", fontsize=8, color="#cccccc")
        self.ax.set_ylim(0.0, 1.2)
        self.ax.set_title(
            "Image Stability Over Time",
            fontsize=9,
            color="#cccccc",
            pad=5,
        )

        # Create the line plot
        self.lines = [
            self.ax.plot([], [], alpha=0.5)[0]
            for _ in range(self.auto_capture.stability_duration)
        ]

        (self.avg,) = self.ax.plot([], [])

        # Initialize empty plot
        self.update_plot()
        self.auto_capture.connect("notify::stability-history", self.update_data)

    def update_data(self, *_):
        """Add a new stability data point."""
        stability = self.auto_capture.stability_history
        if not stability:
            return

        if len(stability[-1]) != self.auto_capture.stability_duration:
            log.warning("INVALID data got added")
            return

        self.update_plot()

    def update_plot(self):
        """Update the plot with current data."""
        # Update line data
        stability_data = self.auto_capture.stability_history

        for series, line in enumerate(self.lines):
            line.set_data(
                list(range(len(stability_data))),
                list([x[series] for x in stability_data]),
            )

        self.avg.set_data(
            list(range(len(stability_data))),
            list([np.mean(x) for x in stability_data]),
        )
        # Auto-scale y-axis to ensure line is visible
        self.ax.relim()
        self.ax.autoscale_view()

        # Redraw canvas
        self.canvas.draw_idle()
