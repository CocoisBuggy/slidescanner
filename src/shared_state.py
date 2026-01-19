import pathlib

import gi
gi.require_version("GObject", "2.0")
from gi.repository import GObject

from src.camera import CameraManager
from src.camera_core import EdsCameraRef


class SharedState(GObject.Object):
    """Shared state manager with GTK signals for application-wide communication."""

    camera: EdsCameraRef | None = None
    camera_name: str | None = None
    battery_level: int | None = None  # Battery level 0-100 or None

    # Cassette context
    cassette_name: str = ""
    cassette_date: str = ""  # Year
    slide_date: str = ""  # Individual slide date (optional, overrides cassette date)
    slide_label: str = ""
    quality_rating: int = 3  # Default 3-star rating
    slide_counter: int = 0  # Sequential counter for slides within cassette
    auto_capture: bool = False  # Auto capture toggle state
    auto_capture: bool = False  # Auto capture toggle state
    auto_capture: bool = False  # Auto capture toggle state

    __gsignals__ = {
        "camera-name": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,),  # camera_name
        ),
        "battery-level-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (GObject.TYPE_PYOBJECT,),  # battery_level: int or None
        ),
        "cassette-context-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (),
        ),
        "picture-taken": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,),  # filename
        ),
        "auto-capture-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (GObject.TYPE_PYOBJECT,),  # auto_capture: bool
        ),
    }

    def __init__(self, camera_manager: CameraManager):
        super().__init__()
        self.camera_manager = camera_manager
        self.photo_location = str(pathlib.Path.home() / "Pictures")

    def set_camera(self, cam: EdsCameraRef | None):
        print(f"setting active camera {cam}")
        self.camera = cam

        if self.camera is None:
            self.camera_name = None
            self.battery_level = None
        else:
            self.camera_manager.open_session(cam)
            import time

            time.sleep(1.0)
            self.camera_manager.set_property_event_handler()
            self.camera_manager.set_object_event_handler()
            time.sleep(0.5)
            self.camera_manager.start_live_view()
            time.sleep(1.5)

            dev_info = self.camera_manager.get_device_info(cam)

            if dev_info is None:
                raise Exception("We really expected dev info")

            self.camera_name = dev_info.szDeviceDescription.decode("utf8")
            print(f"Active camera name: {self.camera_name}")

            # Get initial battery level
            try:
                from .camera_core import EdsPropertyIDEnum

                battery_level = self.camera_manager.get_property_value(
                    EdsPropertyIDEnum.BatteryLevel.value
                )
                if battery_level is not None:
                    from .camera_core.properties import battery_level_to_percentage

                    percentage = battery_level_to_percentage(battery_level)
                    self.set_battery_level(percentage)
            except Exception as e:
                print(f"Failed to get initial battery level: {e}")

        self.emit("camera-name", self.camera_name)

    def set_battery_level(self, level: int | None):
        """Set the battery level (0-100 or None for unknown/AC)."""
        self.battery_level = level
        self.emit("battery-level-changed", level)

    def set_cassette_name(self, name: str):
        """Set the current cassette name."""
        self.cassette_name = name
        self.emit("cassette-context-changed")

    def set_cassette_date(self, date: str):
        """Set the current cassette date (year)."""
        self.cassette_date = date
        self.emit("cassette-context-changed")

    def set_slide_date(self, date: str):
        """Set the current slide date (optional, overrides cassette date)."""
        self.slide_date = date
        self.emit("cassette-context-changed")

    def set_slide_label(self, label: str):
        """Set the current slide label."""
        self.slide_label = label
        self.emit("cassette-context-changed")

    def set_quality_rating(self, rating: int):
        """Set the quality rating (1-5)."""
        if 1 <= rating <= 5:
            self.quality_rating = rating
            self.emit("cassette-context-changed")

    def notify_picture_taken(self, filename: str):
        """Notify that a picture has been successfully taken."""
        self.emit("picture-taken", filename)

    def set_auto_capture(self, enabled: bool):
        """Set the auto capture toggle state."""
        self.auto_capture = enabled
        self.emit("auto-capture-changed", enabled)

    def next_cassette(self):
        """Move to the next cassette (increment cassette number and reset counter)."""
        # Reset slide counter for new cassette
        self.slide_counter = 0

        # Clear cassette name for user input
        self.cassette_name = ""

        # Reset other context
        self.cassette_date = ""
        self.slide_date = ""
        self.slide_label = ""
        self.quality_rating = 3
        self.emit("cassette-context-changed")

    def get_next_slide_filename(self, extension=".jpg"):
        """Get the next sequential filename for the current cassette."""
        self.slide_counter += 1
        cassette_name = self.cassette_name.strip()
        if not cassette_name:
            cassette_name = "Unknown"
        # Replace spaces and special characters with underscores
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_" for c in cassette_name
        )
        return f"{safe_name}_{self.slide_counter:03d}{extension}"
