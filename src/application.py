import ctypes
import logging
import threading
import time
import traceback
from threading import Event, Thread

import gi

log = logging.getLogger(__name__)

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gio, Gtk

from .camera_core import EdsUInt32, edsdk
from .shared_state import SharedState
from .slide_scanner_window import SlideScannerWindow


class SlideScannerApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="com.coco.slidescanner",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        self.running = Event()
        self.running.set()

        self.state = SharedState()
        self.camera_watcher = None

    def do_activate(self):
        # Initialize camera manager
        camera_status = "Initializing EDSDK..."
        log.info(camera_status)

        if not self.state.camera_manager.initialize():
            raise Exception("EDSDK initialization failed")

        camera_status = "EDSDK initialized, waiting for camera..."
        log.info(camera_status)

        def edsdk_subsystem():
            log.info("Starting camera watcher")

            if not self.state.camera_manager.initialized.wait(3):
                log.error("CAMERA MANAGER DID NOT INITIALIZE")
            else:
                log.info("We are initialized nicely")
                time.sleep(0.4)

            try:
                while (
                    self.state.camera_manager.initialized.is_set()
                    and self.running.is_set()
                ):
                    time.sleep(0.05)
                    if self.state.camera is not None:
                        # We have a camera, process events and chill
                        # Need to call EdsGetEvent regularly to process camera events

                        if edsdk:
                            event = EdsUInt32()
                            edsdk.EdsGetEvent(
                                self.state.camera.ref,
                                ctypes.byref(event),
                            )
                        continue

                    if not self.state.camera_manager.get_camera_count():
                        continue

                    log.info("Camera count > 0")
                    camera = self.state.camera_manager.get_camera(0)

                    if not camera:
                        log.warning(
                            "Camera count was positive but we couldn't get camera"
                        )
                        continue

                    self.state.set_camera(camera)
            except Exception as e:
                traceback.print_exception(e)
                log.error(e)

            log.info("Leaving camera watcher routine")

        win = SlideScannerWindow(self.state, application=self)

        self.camera_watcher = Thread(target=edsdk_subsystem, daemon=True)
        self.camera_watcher.start()

        win.present()

    def do_shutdown(self):
        self.running.clear()
        if self.camera_watcher is not None:
            self.camera_watcher.join(timeout=3)

        if self.state.camera:
            self.state.camera.close()

        self.state.camera_manager.terminate()
        self.quit()
