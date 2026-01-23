import gi

from src.constants import INNER_PADDING

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from src.shared_state import SharedState
from src.shortcuts import ShortcutsHandler


def create_toolbar(state: SharedState, shortcuts_handler: ShortcutsHandler):
    toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    toolbar.set_margin_start(INNER_PADDING)
    toolbar.set_margin_end(INNER_PADDING)
    toolbar.set_margin_top(INNER_PADDING // 2)
    toolbar.set_margin_bottom(INNER_PADDING // 2)
    toolbar.set_spacing(INNER_PADDING // 2)

    capture_btn = Gtk.Button(label="Capture")
    capture_btn.connect("clicked", shortcuts_handler.capture_image)

    toolbar.append(capture_btn)

    settings_btn = Gtk.Button(label="Settings")
    settings_btn.connect("clicked", lambda btn: shortcuts_handler.open_settings())
    toolbar.append(settings_btn)

    shortcuts_btn = Gtk.Button(label="Shortcuts")
    shortcuts_btn.connect(
        "clicked", lambda btn: shortcuts_handler.show_shortcuts_dialog()
    )

    toolbar.append(shortcuts_btn)

    # Spacer to push battery label to the far right
    spacer = Gtk.Box()
    spacer.set_hexpand(True)
    toolbar.append(spacer)

    # Battery label on the far right
    battery_label = Gtk.Label(label="Battery: --%")
    toolbar.append(battery_label)
    state.connect(
        "notify::battery_level",
        lambda obj, pspec: battery_label.set_text(f"Battery: {obj.battery_level}%"),
    )

    return toolbar
