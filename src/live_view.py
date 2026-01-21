import threading
import time

from gi.repository import GdkPixbuf, GLib

from .application_abstract import SlideWindowAbstract
from .auto_capture import AutoCaptureManager
from .camera_core.err import CameraException, ErrorCode
from .camera import queued_photo_request


class LiveView:
    def __init__(self, window: SlideWindowAbstract):
        self.window = window
        self.auto_capture_manager = AutoCaptureManager(window)

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
        if self.window.live_view_thread is not None:
            self.window.live_view_thread.join(timeout=1)
            self.window.live_view_thread = None

    def live_view_loop(self):
        while self.window.live_view_running and self.window.shared_state.camera:
            try:
                data = self.window.shared_state.camera_manager.download_evf_image()

                # Process for auto-capture if enabled
                if self.window.shared_state.auto_capture:
                    should_capture = self.auto_capture_manager.process_frame(data)

                    if should_capture and queued_photo_request is None:
                        self._trigger_auto_capture()

                GLib.idle_add(self.update_live_view_image, data)
            except CameraException as e:
                if e.err_code == ErrorCode.InvalidHandle:
                    self.stop_live_view()

            except Exception as e:
                print(f"Live view error: {e}")
                time.sleep(1)
            time.sleep(0.1)

    def _trigger_auto_capture(self):
        """Trigger an automatic capture using the same logic as manual capture."""
        print("Auto-capture: Triggering automatic photo capture")
        self.window.shortcuts_handler.capture_image()
        self.auto_capture_manager.on_capture_completed()

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

    def on_auto_capture_enabled(self):
        """Called when auto-capture is enabled."""
        self.auto_capture_manager.reset()
        # Start status update timer
        if hasattr(self.window, "event_handlers"):
            self._start_status_update_timer()
        print("Auto-capture: Enabled and ready")

    def on_auto_capture_disabled(self):
        """Called when auto-capture is disabled."""
        self.auto_capture_manager.reset()
        # Stop status update timer
        if hasattr(self, "_status_update_timer_id"):
            GLib.source_remove(self._status_update_timer_id)
            self._status_update_timer_id = None
        print("Auto-capture: Disabled")

    def _start_status_update_timer(self):
        """Start a timer to periodically update auto-capture status."""

        def update_status():
            if self.window.shared_state.auto_capture:
                self.window.event_handlers.update_auto_capture_status_from_manager()
                
                # Update stability graph with recent data
                if (hasattr(self.window, 'stability_graph') and 
                    hasattr(self.auto_capture_manager, 'stability_history')):
                    stability_data = self.auto_capture_manager.stability_history
                    if stability_data:
                        # Add the latest stability point to the graph
                        latest_stability = stability_data[-1]
                        self.window.stability_graph.add_data_point(latest_stability)
                
                return True  # Continue timer
            return False  # Stop timer

        self._status_update_timer_id = GLib.timeout_add(
            100, update_status
        )  # Update every 100ms
