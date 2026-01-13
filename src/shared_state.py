from gi.repository import GObject

from src.camera import CameraManager
from src.camera_core import EdsCameraRef


class SharedState(GObject.Object):
    """Shared state manager with GTK signals for application-wide communication."""

    camera: EdsCameraRef | None = None
    camera_name: str | None = None

    __gsignals__ = {
        "camera-name": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,),  # camera_name
        ),
    }

    def __init__(self, camera_manager: CameraManager):
        super().__init__()
        self.camera_manager = camera_manager

    def set_camera(self, cam: EdsCameraRef | None):
        print(f"setting active camera {cam}")
        self.camera = cam

        if self.camera is None:
            self.camera_name = None
            return

        dev_info = self.camera_manager.get_device_info(cam)

        if dev_info is None:
            raise Exception("We really expected dev info")

        self.camera_name = dev_info.szDeviceDescription.decode("utf8")
        print(f"Active camera name: {self.camera_name}")
