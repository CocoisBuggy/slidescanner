from gi.repository import GLib, Gtk

from .camera_core.properties import EdsPropertyIDEnum, listeners
from .constants import INNER_PADDING
from .shared_state import SharedState


class CameraControls(Gtk.Frame):
    def __init__(self, state: SharedState):
        super().__init__(label="Controls")

        self.iso_label = Gtk.Label(label="--")
        self.iso_label.set_halign(Gtk.Align.START)

        self.shutter_label = Gtk.Label(label="--")
        self.shutter_label.set_halign(Gtk.Align.START)

        self.aperture_label = Gtk.Label(label="--")
        self.aperture_label.set_halign(Gtk.Align.START)

        self.create_controls_box()

        # Use GLib.idle_add to update GTK widgets from background threads
        listeners[EdsPropertyIDEnum.ISOSpeed].append(
            lambda value: GLib.idle_add(self.iso_label.set_label, str(value))
        )

        listeners[EdsPropertyIDEnum.Tv].append(
            lambda value: GLib.idle_add(self.shutter_label.set_label, str(value))
        )

        listeners[EdsPropertyIDEnum.Av].append(
            lambda value: GLib.idle_add(self.aperture_label.set_label, str(value))
        )

    def create_controls_box(self):
        """Create the controls frame with ISO and shutter speed settings."""
        controls_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=INNER_PADDING
        )
        controls_box.set_margin_top(INNER_PADDING)
        controls_box.set_margin_bottom(INNER_PADDING)
        controls_box.set_margin_start(INNER_PADDING)
        controls_box.set_margin_end(INNER_PADDING)
        self.set_child(controls_box)

        # ISO
        iso_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        iso_box.append(Gtk.Label(label="ISO:"))
        iso_box.append(self.iso_label)
        controls_box.append(iso_box)

        # Shutter Speed
        shutter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        shutter_box.append(Gtk.Label(label="Shutter:"))
        shutter_box.append(self.shutter_label)
        controls_box.append(shutter_box)

        # Aperture
        aperture_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        aperture_box.append(Gtk.Label(label="Aperture:"))
        aperture_box.append(self.aperture_label)
        controls_box.append(aperture_box)
