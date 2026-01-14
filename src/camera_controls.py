import time
from threading import Thread
from gi.repository import Gtk, GLib

from .camera_core.properties import EdsPropertyIDEnum, listeners


class CameraControls:
    def __init__(self, window):
        self.window = window

        self.window.iso_spin = Gtk.SpinButton()
        self.window.iso_spin.set_sensitive(False)
        self.window.iso_spin.set_range(100, 128_000)

        self.window.shutter_spin = Gtk.SpinButton()
        self.window.shutter_spin.set_sensitive(False)
        self.window.shutter_spin.set_range(0, 100)

        self.window.aperture_spin = Gtk.SpinButton()
        self.window.aperture_spin.set_sensitive(False)
        self.window.aperture_spin.set_range(0, 50)

        # Use GLib.idle_add to update GTK widgets from background threads
        listeners[EdsPropertyIDEnum.ISOSpeed].append(
            lambda value: GLib.idle_add(self.window.iso_spin.set_value, value)
        )

        listeners[EdsPropertyIDEnum.Tv].append(
            lambda value: GLib.idle_add(self.window.shutter_spin.set_value, value)
        )

        listeners[EdsPropertyIDEnum.Av].append(
            lambda value: GLib.idle_add(self.window.aperture_spin.set_value, value)
        )

    def create_controls_box(self):
        """Create the controls frame with ISO and shutter speed settings."""
        controls_frame = Gtk.Frame(label="Controls")

        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        controls_box.set_margin_top(12)
        controls_box.set_margin_bottom(12)
        controls_box.set_margin_start(12)
        controls_box.set_margin_end(12)
        controls_frame.set_child(controls_box)

        controls_box.append(Gtk.Label(label="ISO:"))
        controls_box.append(self.window.iso_spin)

        controls_box.append(Gtk.Label(label="Shutter Speed:"))
        controls_box.append(self.window.shutter_spin)

        controls_box.append(Gtk.Label(label="Aperture:"))
        controls_box.append(self.window.aperture_spin)

        return controls_frame
