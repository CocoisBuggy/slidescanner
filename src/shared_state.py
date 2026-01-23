import logging
from threading import Thread
import gi


gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import pathlib

log = logging.getLogger(__name__)

from gi.repository import GObject

from src.camera_core import CameraManager, EdsCameraRef

from .camera import Camera
from .camera_core import EdsPropertyIDEnum
from .camera_core.properties import battery_level_to_percentage
from .camera_core.err import CameraException
from .picture import CassetteItem
from .settings import Settings
from .common_signal import SignalName
from .auto_capture import AutoCaptureManager


class SharedState(GObject.GObject):
    """Shared state manager with GTK signals for application-wide communication."""

    _settings: Settings = Settings()
    _camera: Camera | None = None
    _battery_level: int | None = None  # Battery level 0-100 or None

    cassette = CassetteItem()
    auto_capture_manager = AutoCaptureManager()

    __gsignals__ = {
        sig.name: (GObject.SignalFlags.RUN_FIRST, None, ()) for sig in SignalName
    }

    def __init__(self):
        super().__init__()
        self.camera_manager = CameraManager(self)
        self.photo_location = str(pathlib.Path.home() / "Pictures")

        self.connect(SignalName.CameraConnected.name, self.on_camera_connected)

    @GObject.Property(type=int)
    def battery_level(self):
        return self._battery_level

    @battery_level.setter
    def battery_level(self, p):
        self._battery_level = p

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, cam: Camera | None):
        if cam is None:
            if self._camera:
                self._camera.close()

        self._camera = cam

    def on_camera_connected(self, *_):
        log.info("A camera has connected to us!")

        if self.camera is None:
            raise Exception("WHY did we connect to a camera that doesn't exist?")

        Thread(target=self.camera.start_live_view).start()

        try:
            self.battery_level = battery_level_to_percentage(
                self.camera.get_property_value(EdsPropertyIDEnum.BatteryLevel)
            )
        except CameraException as e:
            log.warning(f"Failed to get initial battery level: {e}")

    def set_camera(self, cam: EdsCameraRef | None):
        log.info(f"setting active camera {cam}")
        if self.camera is not None:
            self.camera.close()

        if cam is None:
            self.camera = cam
            self.live_view = False
            self.battery_level = None
            return

        self.camera = Camera(self.camera_manager, cam)
        Thread(target=self.camera_manager.open_session, args=(cam,)).start()
