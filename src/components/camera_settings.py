from gi.repository import Gtk
from typing_extensions import Callable

from src.camera import Camera
from src.camera_core.properties import (
    EdsPropertyIDEnum,
    av_to_human_readable,
    tv_to_human_readable,
    iso_to_human_readable,
    listeners,
)
from src.constants import INNER_PADDING
from src.shared_state import SharedState


def uses_camera(wrapped) -> Callable[["CameraSettings"], None]:
    def inner(self):
        if self.state._camera is None:
            print("This class member needs state._camera to be ascociated")
            return

        wrapped(self, self.state._camera)

    return inner


class CameraSettings(Gtk.Frame):
    def __init__(self, state: SharedState):
        super().__init__(label="Controls")
        self.state = state

        self.iso_label = Gtk.Label(label="--")
        self.iso_label.set_halign(Gtk.Align.START)

        self.shutter_label = Gtk.Label(label="--")
        self.shutter_label.set_halign(Gtk.Align.START)

        self.aperture_label = Gtk.Label(label="--")
        self.aperture_label.set_halign(Gtk.Align.START)

        self.create_controls_box()

        # Use GLib.idle_add to update GTK widgets from background threads
        listeners[EdsPropertyIDEnum.ISOSpeed].append(self.on_iso_change)
        listeners[EdsPropertyIDEnum.Tv].append(self.on_tv_change)
        listeners[EdsPropertyIDEnum.Av].append(self.on_av_change)

    @uses_camera
    def on_av_change(self, camera: Camera):
        av = camera.get_property_value(EdsPropertyIDEnum.Av)
        self.aperture_label.set_label(av_to_human_readable(av))

    @uses_camera
    def on_tv_change(self, camera: Camera):
        self.shutter_label.set_label(
            tv_to_human_readable(camera.get_property_value(EdsPropertyIDEnum.Tv))
        )

    @uses_camera
    def on_iso_change(self, camera: Camera):
        self.iso_label.set_label(
            iso_to_human_readable(camera.get_property_value(EdsPropertyIDEnum.ISOSpeed))
        )

    def create_controls_box(self):
        """Create the controls frame with ISO and shutter speed settings."""
        controls_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=INNER_PADDING
        )
        controls_box.set_margin_top(INNER_PADDING)
        controls_box.set_margin_bottom(INNER_PADDING)
        controls_box.set_margin_start(INNER_PADDING)
        controls_box.set_margin_end(INNER_PADDING)
        self.set_child(controls_box)

        # ISO
        iso_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        iso_box.append(Gtk.Label(label="ISO:"))
        iso_box.append(self.iso_label)
        controls_box.append(iso_box)

        # Shutter Speed
        shutter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        shutter_box.append(Gtk.Label(label="Shutter:"))
        shutter_box.append(self.shutter_label)
        controls_box.append(shutter_box)

        # Aperture
        aperture_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        aperture_box.append(Gtk.Label(label="Aperture:"))
        aperture_box.append(self.aperture_label)
        controls_box.append(aperture_box)
