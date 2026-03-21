import gi
import logging


gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import matplotlib

log = logging.getLogger(__name__)

matplotlib.use("GTK4Agg")

import numpy as np
from matplotlib.lines import Line2D

from src.auto_capture import AutoCaptureManager
from src.graphs import GraphWidget


class ExposureHist(GraphWidget):
    """A graph widget for displaying stability over time."""

    def __init__(
        self,
        auto_capture: AutoCaptureManager,
        width: int = 400,
        height: int = 90,
    ):
        super().__init__(width, height)
        self.auto_capture = auto_capture
        # Initialize empty plot
        self.update_plot()
        self.auto_capture.connect("notify::stability-history", self.update_plot)

    def update_plot(self, *_):
        """Update the plot with current data."""
        # Update line data
        self.ax.cla()  # Clear the current axes
        self.ax.hist(
            self.auto_capture._histogram_data,
            bins=10,
            range=(0, 256),
        )  # Replot with new data, using the same bins
        self.canvas.draw_idle()
