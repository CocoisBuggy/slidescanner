from gi.repository import Gtk, GLib

from .camera_core.properties import EdsPropertyIDEnum, listeners


class CameraControls:
    def __init__(self, window):
        self.window = window

        self.window.iso_label = Gtk.Label(label="--")
        self.window.iso_label.set_halign(Gtk.Align.START)

        self.window.shutter_label = Gtk.Label(label="--")
        self.window.shutter_label.set_halign(Gtk.Align.START)

        self.window.aperture_label = Gtk.Label(label="--")
        self.window.aperture_label.set_halign(Gtk.Align.START)

        # Use GLib.idle_add to update GTK widgets from background threads
        listeners[EdsPropertyIDEnum.ISOSpeed].append(
            lambda value: GLib.idle_add(self.window.iso_label.set_label, str(value))
        )

        listeners[EdsPropertyIDEnum.Tv].append(
            lambda value: GLib.idle_add(self.window.shutter_label.set_label, str(value))
        )

        listeners[EdsPropertyIDEnum.Av].append(
            lambda value: GLib.idle_add(
                self.window.aperture_label.set_label, str(value)
            )
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

        # ISO
        iso_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        iso_box.append(Gtk.Label(label="ISO:"))
        iso_box.append(self.window.iso_label)
        controls_box.append(iso_box)

        # Shutter Speed
        shutter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        shutter_box.append(Gtk.Label(label="Shutter:"))
        shutter_box.append(self.window.shutter_label)
        controls_box.append(shutter_box)

        # Aperture
        aperture_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        aperture_box.append(Gtk.Label(label="Aperture:"))
        aperture_box.append(self.window.aperture_label)
        controls_box.append(aperture_box)

        return controls_frame
