from gi.repository import Gtk

from .camera_core.properties import EdsPropertyIDEnum, listeners


class CameraControls:
    def __init__(self, window):
        self.window = window
        listeners[EdsPropertyIDEnum.ISOSpeed].append(self.update_iso)

    def update_iso(self, data):
        print(data)
        self.window.iso_spin.set_value(data)

    def create_controls_box(self):
        """Create the controls frame with ISO and shutter speed settings."""
        controls_frame = Gtk.Frame(label="Controls")

        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        controls_box.set_margin_top(12)
        controls_box.set_margin_bottom(12)
        controls_box.set_margin_start(12)
        controls_box.set_margin_end(12)
        controls_frame.set_child(controls_box)

        iso_label = Gtk.Label(label="ISO:")
        controls_box.append(iso_label)

        self.window.iso_spin = Gtk.SpinButton()
        self.window.iso_spin.set_range(0, 3200)
        self.window.iso_spin.set_value(400)
        controls_box.append(self.window.iso_spin)

        shutter_label = Gtk.Label(label="Shutter Speed:")
        controls_box.append(shutter_label)

        self.window.shutter_spin = Gtk.SpinButton()
        self.window.shutter_spin.set_range(1, 1000)
        self.window.shutter_spin.set_value(125)
        controls_box.append(self.window.shutter_spin)

        return controls_frame
