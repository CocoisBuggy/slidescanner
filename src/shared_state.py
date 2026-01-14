from gi.repository import GObject

from src.camera import CameraManager
from src.camera_core import EdsCameraRef


class SharedState(GObject.Object):
    """Shared state manager with GTK signals for application-wide communication."""

    camera: EdsCameraRef | None = None
    camera_name: str | None = None

    # Cassette context
    cassette_name: str = ""
    cassette_date: str = ""  # Year
    slide_label: str = ""
    quality_rating: int = 3  # Default 3-star rating
    slide_counter: int = 0  # Sequential counter for slides within cassette

    __gsignals__ = {
        "camera-name": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,),  # camera_name
        ),
        "cassette-context-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (),  # No parameters - just notification
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
        else:
            self.camera_manager.open_session(cam)
            import time

            time.sleep(1.0)
            # self.camera_manager.set_property_event_handler()
            time.sleep(0.5)
            self.camera_manager.start_live_view()
            time.sleep(1.5)

            dev_info = self.camera_manager.get_device_info(cam)

            if dev_info is None:
                raise Exception("We really expected dev info")

            self.camera_name = dev_info.szDeviceDescription.decode("utf8")
            print(f"Active camera name: {self.camera_name}")

        self.emit("camera-name", self.camera_name)

    def set_cassette_name(self, name: str):
        """Set the current cassette name."""
        self.cassette_name = name
        self.emit("cassette-context-changed")

    def set_cassette_date(self, date: str):
        """Set the current cassette date (year)."""
        self.cassette_date = date
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

    def next_cassette(self):
        """Move to the next cassette (increment cassette number and reset counter)."""
        # Reset slide counter for new cassette
        self.slide_counter = 0

        # If no custom cassette name is set, use a default
        if not self.cassette_name or self.cassette_name.startswith("Cassette "):
            if not hasattr(self, "cassette_number"):
                self.cassette_number = 1
            else:
                self.cassette_number += 1
            self.cassette_name = f"Cassette {self.cassette_number}"

        # Reset other context but keep the cassette name
        self.cassette_date = ""
        self.slide_label = ""
        self.quality_rating = 3
        self.emit("cassette-context-changed")

    def get_next_slide_filename(self):
        """Get the next sequential filename for the current cassette."""
        self.slide_counter += 1
        cassette_name = self.cassette_name.strip()
        if not cassette_name:
            cassette_name = "Unknown"
        # Replace spaces and special characters with underscores
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_" for c in cassette_name
        )
        return f"{safe_name}_{self.slide_counter:03d}.jpg"
