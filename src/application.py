import time
import ctypes
from threading import Event, Thread
import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, Gtk  # noqa: E402

from .camera import CameraManager  # noqa: E402
from .shared_state import SharedState  # noqa: E402
from .slide_scanner_window import SlideScannerWindow  # noqa: E402


class SlideScannerApplication(Gtk.Application):
    running: Event
    state: SharedState

    def __init__(self):
        super().__init__(
            application_id="com.example.slidescanner",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        self.running = Event()
        self.running.set()

        self.camera_manager = CameraManager()
        self.state = SharedState(self.camera_manager)
        self.camera_watcher = None

        # Load settings
        from .settings import Settings
        self.settings = Settings()
        self.state.photo_location = self.settings.photo_location

    def do_activate(self):
        # Initialize camera manager
        camera_status = "Initializing EDSDK..."
        print(camera_status)

        if not self.camera_manager.initialize():
            raise Exception("EDSDK initialization failed")

        camera_status = "EDSDK initialized, waiting for camera..."
        print(camera_status)

        # Set global references for callbacks
        from src.camera import _global_shared_state

        _global_shared_state = self.state

        def camera_watcher():
            print("Starting camera watcher")

            while self.camera_manager.initialized.is_set() and self.running.is_set():
                time.sleep(0.05)

                if self.state.camera is not None:
                    # We have a camera, process events and chill
                    # Need to call EdsGetEvent regularly to process camera events
                    from src.camera_core import edsdk, EdsUInt32

                    if edsdk:
                        event = EdsUInt32()
                        edsdk.EdsGetEvent(self.state.camera, ctypes.byref(event))
                        # Process events - the event callbacks should be triggered
                    continue

                if not self.camera_manager.get_camera_count():
                    continue

                print("Camera count > 0")
                camera = self.camera_manager.get_camera(0)

                if not camera:
                    print("Camera count was positive but we couldn't get the camera")
                    continue

                self.state.set_camera(camera)

        win = SlideScannerWindow(self.state, application=self)

        self.camera_watcher = Thread(target=camera_watcher, daemon=True)
        self.camera_watcher.start()

        if win.camera_info_label:
            win.camera_info_label.set_text(camera_status)

        win.present()

    def do_shutdown(self):
        self.running.clear()
        if self.camera_watcher is not None:
            self.camera_watcher.join(timeout=3)

        self.camera_manager.terminate()
        self.quit()
