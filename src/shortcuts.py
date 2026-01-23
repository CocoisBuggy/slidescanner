import gi
import logging


gi.require_version("Gtk", "4.0")

from threading import Thread

log = logging.getLogger(__name__)

from gi.repository import Gdk, Gtk

from .picture import CassetteItem
from .shared_state import SharedState
from .common_signal import SignalName


class ShortcutsHandler:
    def __init__(self, window: Gtk.ApplicationWindow, state: SharedState):
        self.state = state
        self.window = window

        self.key_controller = Gtk.EventControllerKey()
        window.add_controller(self.key_controller)
        # Connect key press event
        self.key_controller.connect("key-pressed", self.on_key_pressed)
        self.shortcuts = {
            "space": self.capture_image,  # Ctrl+Space
            "s": self.open_settings,  # Ctrl+S
            "q": self.quit_application,  # Ctrl+Q
            "n": self.next_cassette,  # Ctrl+N
        }

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events for shortcuts."""
        # Check if Ctrl is pressed
        if state & Gdk.ModifierType.CONTROL_MASK:
            # Convert keyval to key name
            key_name = (Gdk.keyval_name(keyval) or "").lower()
            if key_name in self.shortcuts:
                self.shortcuts[key_name]()
                return True  # Event handled
        return False  # Event not handled

    def capture_image(self):
        log.debug("Capture image shortcut triggered")
        self.state.emit(SignalName.TakePicture.name)

    def open_settings(self):
        """Handle Ctrl+S: Open settings."""
        from src.settings import SettingsDialog

        dialog = SettingsDialog(self.window, self.window.shared_state)
        dialog.present()

    def quit_application(self):
        """Handle Ctrl+Q: Quit application."""
        log.debug("Quit application shortcut triggered")
        self.window.get_application().quit()

    def next_cassette(self):
        """Handle Ctrl+N: Move to next cassette."""
        log.debug("Next cassette shortcut triggered")
        self.state.next_cassette()

    def show_shortcuts_dialog(self):
        """Display a dialog showing all available keyboard shortcuts."""
        # Dynamically generate shortcuts text from the shortcuts dictionary
        ctrl_shortcut_descriptions = {
            "space": "Capture Image",
            "s": "Open Settings",
            "q": "Quit Application",
            "n": "Next Cassette",
        }

        shortcuts_lines = ["Available Keyboard Shortcuts:"]
        shortcuts_lines.append("")
        shortcuts_lines.append("Ctrl+Key shortcuts:")
        for key, description in ctrl_shortcut_descriptions.items():
            shortcuts_lines.append(f"• Ctrl+{key.upper()}: {description}")

        shortcuts_lines.append("")
        shortcuts_lines.append("Quality Rating (numpad or number keys):")
        shortcuts_lines.append("• 1-5: Set quality rating (1-5 stars)")
        shortcuts_lines.append("")
        shortcuts_lines.append("File Naming:")
        shortcuts_lines.append(
            "• Images saved as: CassetteName_001.jpg, CassetteName_002.jpg, etc."
        )
        shortcuts_lines.append("• Use cassette name field to set the base filename")

        shortcuts_text = "\n".join(shortcuts_lines)

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Keyboard Shortcuts",
            secondary_text=shortcuts_text,
        )
        dialog.connect("response", lambda dialog, response: dialog.destroy())
        dialog.present()
