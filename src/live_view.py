from enum import Enum, auto
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import logging
import time
import traceback
from threading import Thread

import cv2
import numpy as np
from gi.repository import GdkPixbuf, GLib, Gtk

log = logging.getLogger(__name__)

from .camera_core.download import get_current_photo_request
from .camera_core.err import CameraException, ErrorCode
from .common_signal import SignalName
from .shared_state import SharedState


class LiveViewState(Enum):
    Idle = auto()
    Focusing = auto()
    ShutterDown = auto()


class LiveView(Gtk.Frame):
    state: SharedState
    live_view_running = False
    live_view_thread: Thread | None = None
    live_view_state = LiveViewState.Idle

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

        self.state_hoc(SignalName.TakePictureError, LiveViewState.Idle)
        self.state_hoc(SignalName.ImageDownloaded, LiveViewState.Idle)
        self.state_hoc(SignalName.ShutterRelease, LiveViewState.ShutterDown)
        self.state_hoc(SignalName.Focusing, LiveViewState.Focusing)

        # Add CSS provider for focusing animation
        self.css_provider = Gtk.CssProvider()
        self.style_context = self.get_style_context()
        self.style_context.add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def state_hoc(self, signal: SignalName, state: LiveViewState):
        def cb(_):
            self.live_view_state = state
            self.update_focusing_style()

        self.state.connect(signal.name, cb)

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
                should_capture = self.state.auto_capture_manager.process_frame(data)

                if (
                    self.state.auto_capture_manager.enabled
                    and should_capture
                    and get_current_photo_request() is None
                ):
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
                # Highlight pure white pixels with red to show clipping
                if self.state.show_zebra:
                    pixbuf = self._highlight_clipped_pixels(pixbuf)

                self.live_view_image.set_pixbuf(pixbuf)
            else:
                log.warning("Pixbuf is None")
        except Exception as e:
            log.exception(e)
            log.error(f"Failed to load image: {e}")

    def _highlight_clipped_pixels(self, pixbuf: GdkPixbuf.Pixbuf):
        """Create a new pixbuf with pure white pixels highlighted in red."""
        # --- 1. PIXBUF TO NUMPY (OPENCV COMPATIBLE) ---

        width = pixbuf.get_width()
        height = pixbuf.get_height()
        channels = pixbuf.get_n_channels()
        rowstride = pixbuf.get_rowstride()

        # Get pixels and create a mutable copy
        raw_data = pixbuf.get_pixels()
        # We use np.frombuffer + .copy() to solve the read-only error
        arr = np.frombuffer(raw_data, dtype=np.uint8).copy()
        # Reshape and handle rowstride (strips padding bytes if they exist)
        arr = arr.reshape((height, rowstride))
        img_rgb = arr[:, : width * channels].reshape((height, width, channels))

        # Convert RGB (GDK) to BGR (OpenCV)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        # Define "pure white" in BGR
        # We can use cv2.inRange for speed if we ever want to do a "range" (e.g. 250-255)
        lower_white = np.array([255, 255, 255])
        upper_white = np.array([255, 255, 255])
        mask = cv2.inRange(img_bgr, lower_white, upper_white)
        img_bgr[mask > 0] = [0, 0, 255]

        # Convert back to RGB for GTK
        processed_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        data_bytes = processed_rgb.tobytes()

        return GdkPixbuf.Pixbuf.new_from_data(
            data_bytes,  # type: ignore
            GdkPixbuf.Colorspace.RGB,
            pixbuf.get_has_alpha(),
            8,
            width,
            height,
            width * channels,  # New rowstride (no padding needed here)
            destroy_fn=None,
        )

    def update_focusing_style(self):
        """Update CSS styling based on focusing state."""
        if self.live_view_state == LiveViewState.Focusing:
            css_data = """
                frame {
                    outline: 3px solid #ff6b35;
                    outline-offset: 2px;
                    border-radius: 4px;
                    animation: pulse 1.5s ease-in-out infinite, fadeIn 0.3s ease-out;
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
                }
                
                @keyframes pulse {
                    0% { 
                        box-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
                        outline-color: #ff6b35;
                    }
                    50% { 
                        box-shadow: 0 0 30px rgba(255, 107, 53, 0.9);
                        outline-color: #ff8c5a;
                    }
                    100% { 
                        box-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
                        outline-color: #ff6b35;
                    }
                }
                
                @keyframes fadeIn {
                    0% {
                        outline-color: rgba(255, 107, 53, 0);
                        box-shadow: 0 0 0 rgba(255, 107, 53, 0);
                    }
                    100% {
                        outline-color: rgba(255, 107, 53, 1);
                        box-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
                    }
                }
            """
            self.css_provider.load_from_data(css_data.encode())
        else:
            # Remove the focusing animation when not focusing
            css_data = """
                frame {
                    outline: none;
                    box-shadow: none;
                    animation: none;
                }
            """
            self.css_provider.load_from_data(css_data.encode())

    def on_auto_capture_disabled(self):
        """Called when auto-capture is disabled."""
        self.auto_capture_manager = None
