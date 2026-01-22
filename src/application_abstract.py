from threading import Event, Thread

from gi.repository import Gtk

from .camera import CameraManager
from .settings import Settings
from .shared_state import SharedState


class SlideScannerAbstract(Gtk.Application):
    running: Event
    state: SharedState
    camera_manager: CameraManager
    camera_watcher: Thread | None
    settings: Settings


class SlideWindowAbstract(Gtk.ApplicationWindow):
    state: SharedState
    live_view_running: bool
    live_view_thread: Thread | None
