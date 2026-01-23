import gi


gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from src.constants import INNER_PADDING

from .camera_controls import CameraControls
from .components.auto_capture import AutoCapture
from .components.cassette_info import CassetteInfo
from .shared_state import SharedState
from .shortcuts import ShortcutsHandler
from .tool_bar import create_toolbar
from .live_view import LiveView


class MainContent(Gtk.Box):
    camera_info_label = Gtk.Label(label="No camera connected")

    def __init__(self, state: SharedState, shortcuts: ShortcutsHandler):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.state = state
        self.shortcuts = shortcuts

        self.append(create_toolbar(state, shortcuts))
        self.append(self.create_content_area())
        self.append(self.create_status_bar())
        self.state.connect("notify::camera", self.on_camera_changed)

    def on_camera_changed(self, instance, param):
        cam = instance.get_property(param.name)

        if cam is None:
            self.camera_info_label.set_label("No camera connected")
            return

        self.camera_info_label = cam.details.szDeviceDescription.decode()

    def create_content_area(self):
        content_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_area.set_hexpand(True)
        content_area.set_vexpand(True)

        content_area.append(self.create_left_panel())
        content_area.append(self.create_right_panel())
        return content_area

    def create_left_panel(self):
        # Create a scrolled window for the left panel
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(200, -1)
        scrolled_window.set_margin_start(INNER_PADDING)
        scrolled_window.set_margin_top(INNER_PADDING)
        scrolled_window.set_margin_bottom(INNER_PADDING)
        scrolled_window.set_margin_end(4)

        # Create the actual content box inside the scrolled window
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_panel.set_spacing(INNER_PADDING // 2)
        left_panel.set_vexpand(True)
        left_panel.set_margin_end(4)

        scrolled_window.set_child(left_panel)

        camera_info_frame = Gtk.Frame(label="Camera Info")
        camera_info_frame.set_margin_bottom(INNER_PADDING)

        self.camera_info_label.set_margin_top(INNER_PADDING)
        self.camera_info_label.set_margin_bottom(INNER_PADDING)
        self.camera_info_label.set_margin_start(INNER_PADDING)
        self.camera_info_label.set_margin_end(INNER_PADDING)
        camera_info_frame.set_child(self.camera_info_label)

        left_panel.append(camera_info_frame)
        left_panel.append(CassetteInfo(self.state))
        left_panel.append(CameraControls(self.state))
        left_panel.append(AutoCapture(self.state))

        return scrolled_window

    def create_right_panel(self):
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_panel.set_hexpand(True)
        right_panel.set_vexpand(True)
        right_panel.set_margin_start(INNER_PADDING // 2)
        right_panel.set_margin_end(INNER_PADDING)
        right_panel.set_margin_top(INNER_PADDING)
        right_panel.set_margin_bottom(INNER_PADDING)
        right_panel.append(LiveView(self.state))
        return right_panel

    def create_status_bar(self):
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_bar.set_margin_top(INNER_PADDING // 2)
        status_bar.set_margin_bottom(INNER_PADDING // 2)
        status_bar.set_margin_start(INNER_PADDING)
        status_bar.set_margin_end(INNER_PADDING)

        status_label = Gtk.Label(label="Ready")
        status_bar.append(status_label)

        return status_bar
