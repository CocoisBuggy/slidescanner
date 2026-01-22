import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import threading
import time
import traceback

from gi.repository import GdkPixbuf, GLib

from .application_abstract import SlideWindowAbstract
from .auto_capture import AutoCaptureManager
from .camera import queued_photo_request
from .camera_core.err import CameraException, ErrorCode
from .picture import PENDING_CASSETTE


class LiveView:
    auto_capture_manager: AutoCaptureManager | None = None

    def __init__(self, window: SlideWindowAbstract):
        self.window = window

    def start_live_view(self):
        if self.window.live_view_thread and self.window.live_view_thread.is_alive():
            return

        self.window.live_view_running = True
        self.window.live_view_thread = threading.Thread(
            target=self.live_view_loop,
            daemon=True,
        )
        self.window.live_view_thread.start()

    def stop_live_view(self):
        self.window.live_view_running = False
        self.on_auto_capture_disabled()
        if self.window.live_view_thread is not None:
            self.window.live_view_thread.join(timeout=1)
            self.window.live_view_thread = None

    def live_view_loop(self):
        global queued_photo_request

        while self.window.live_view_running and self.window.shared_state.camera:
            try:
                data = self.window.shared_state.camera_manager.download_evf_image()

                # Process for auto-capture if enabled
                if (
                    self.window.shared_state.auto_capture
                    and self.auto_capture_manager is not None
                ):
                    should_capture = self.auto_capture_manager.process_frame(data)
                    self.window.stability_graph.add_data(
                        self.auto_capture_manager.stability_history
                    )

                    if should_capture and queued_photo_request is None:
                        queued_photo_request = PENDING_CASSETTE
                        self._trigger_auto_capture()

                GLib.idle_add(self.update_live_view_image, data)
            except CameraException as e:
                if e.err_code == ErrorCode.InvalidHandle:
                    self.stop_live_view()

            except Exception as e:
                traceback.print_exception(e)
                print(f"Live view error: {e}")
                time.sleep(1)
            time.sleep(0.1)

    def _trigger_auto_capture(self):
        """Trigger an automatic capture using the same logic as manual capture."""
        print("Auto-capture: Triggering automatic photo capture")
        self.window.shortcuts_handler.capture_image()

    def update_live_view_image(self, data):
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            if pixbuf:
                self.window.live_view_image.set_pixbuf(pixbuf)
            else:
                print("Pixbuf is None")
        except Exception as e:
            print(f"Failed to load image: {e}")

    def on_auto_capture_disabled(self):
        """Called when auto-capture is disabled."""
        self.auto_capture_manager = None
