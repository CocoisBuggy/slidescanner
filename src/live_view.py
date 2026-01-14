import threading
import time
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import GLib, GdkPixbuf


class LiveView:
    def __init__(self, window):
        self.window = window

    def start_live_view(self):
        if self.window.live_view_thread and self.window.live_view_thread.is_alive():
            return
        self.window.live_view_running = True
        self.window.live_view_thread = threading.Thread(
            target=self.live_view_loop, daemon=True
        )
        self.window.live_view_thread.start()

    def stop_live_view(self):
        self.window.live_view_running = False
        if self.window.live_view_thread:
            self.window.live_view_thread.join(timeout=1)
            self.window.live_view_thread = None

    def live_view_loop(self):
        while self.window.live_view_running and self.window.shared_state.camera:
            try:
                data = self.window.shared_state.camera_manager.download_evf_image()
                GLib.idle_add(self.update_live_view_image, data)
            except Exception as e:
                print(f"Live view error: {e}")
                time.sleep(1)
            time.sleep(0.1)

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