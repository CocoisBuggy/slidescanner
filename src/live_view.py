import gi


gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import logging
import time
import traceback
from threading import Thread

from gi.repository import GdkPixbuf, GLib, Gtk

log = logging.getLogger(__name__)

from .camera_core.download import get_current_photo_request, set_next_photo_request
from .camera_core.err import CameraException, ErrorCode
from .shared_state import SharedState
from .common_signal import SignalName


class LiveView(Gtk.Frame):
    state: SharedState
    live_view_running = False
    live_view_thread: Thread | None = None

    def __init__(self, state: SharedState):
        super().__init__()
        self.set_hexpand(True)

        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.live_view_image = Gtk.Picture()
        self.live_view_image.set_vexpand(True)
        self.live_view_image.set_hexpand(True)
        self.live_view_image.set_content_fit(Gtk.ContentFit.CONTAIN)

        self.preview_box.append(self.live_view_image)
        self.set_child(self.preview_box)

        self.state = state
        self.state.connect(
            SignalName.LiveViewStopped.name,
            lambda *_: self.stop_live_view(),
        )
        self.state.connect(
            SignalName.LiveViewRunning.name,
            lambda *_: self.start_live_view(),
        )
        self.state.connect(
            SignalName.LiveViewStarting.name,
            lambda *_: self.show_loading(),
        )

    def show_loading(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_vexpand(True)
        vbox.set_hexpand(True)
        self.set_child(vbox)
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.set_halign(Gtk.Align.CENTER)
        spinner.set_valign(Gtk.Align.CENTER)
        spinner.set_hexpand(True)
        spinner.set_vexpand(True)
        vbox.append(spinner)

    def start_live_view(self):
        if self.live_view_thread and self.live_view_thread.is_alive():
            return

        self.live_view_running = True
        self.live_view_thread = Thread(
            target=self.live_view_loop,
            daemon=True,
        )
        self.live_view_thread.start()
        self.set_child(self.preview_box)

    def stop_live_view(self):
        self.live_view_running = False
        self.on_auto_capture_disabled()
        if self.live_view_thread is not None:
            self.live_view_thread.join(timeout=1)
            self.live_view_thread = None

    def live_view_loop(self):
        while self.live_view_running and self.state.camera:
            try:
                data = self.state.camera.download_evf_image()

                # Process for auto-capture if enabled
                if (
                    self.state.auto_capture_manager.enabled
                    and self.state.auto_capture_manager is not None
                ):
                    should_capture = self.state.auto_capture_manager.process_frame(data)

                    if should_capture and get_current_photo_request() is None:
                        self._trigger_capture()

                GLib.idle_add(self.update_live_view_image, data)
            except CameraException as e:
                if e.err_code == ErrorCode.InvalidHandle:
                    self.stop_live_view()

            except Exception as e:
                traceback.print_exception(e)
                log.error(f"Live view error: {e}")
                time.sleep(1)
            time.sleep(0.1)

    def _trigger_capture(self):
        """Trigger an automatic capture using the same logic as manual capture."""
        log.info("Auto-capture: Triggering automatic photo capture")
        self.state.emit(SignalName.TakePicture.name)

    def update_live_view_image(self, data):
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            if pixbuf:
                self.live_view_image.set_pixbuf(pixbuf)
            else:
                log.warning("Pixbuf is None")
        except Exception as e:
            log.error(f"Failed to load image: {e}")

    def on_auto_capture_disabled(self):
        """Called when auto-capture is disabled."""
        self.auto_capture_manager = None
