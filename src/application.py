import ctypes
import time
from threading import Event, Thread

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gio

from .settings import Settings
from .application_abstract import SlideScannerAbstract
from .camera import CameraManager
from .shared_state import SharedState
from .slide_scanner_window import SlideScannerWindow


class SlideScannerApplication(SlideScannerAbstract):
    def __init__(self):
        super().__init__(
            application_id="com.coco.slidescanner",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        self.running = Event()
        self.running.set()

        self.camera_manager = CameraManager()
        self.state = SharedState(self.camera_manager)
        self.camera_watcher = None

        self.settings = Settings()
        self.state.photo_location = self.settings.photo_location

    def do_activate(self):
        global _global_shared_state
        # Initialize camera manager
        camera_status = "Initializing EDSDK..."
        print(camera_status)

        if not self.camera_manager.initialize():
            raise Exception("EDSDK initialization failed")

        camera_status = "EDSDK initialized, waiting for camera..."
        print(camera_status)

        # Set global references for callbacks

        _global_shared_state = self.state

        def camera_watcher():
            print("Starting camera watcher")

            if not self.camera_manager.initialized.wait(3):
                print("CAMERA MANAGER DID NOT INITIALIZE")
            else:
                print("We are initialized nicely")
                time.sleep(0.4)

            try:
                while (
                    self.camera_manager.initialized.is_set() and self.running.is_set()
                ):
                    time.sleep(0.05)
                    if self.state.camera is not None:
                        # We have a camera, process events and chill
                        # Need to call EdsGetEvent regularly to process camera events
                        from src.camera_core import EdsUInt32, edsdk

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
                        print(
                            "Camera count was positive but we couldn't get the camera"
                        )
                        continue

                    self.state.set_camera(camera)
            except Exception as e:
                print(e)

            print("Leaving camera watcher routine")

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
