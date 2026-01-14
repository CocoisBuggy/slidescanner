import gi

from .picture import CassetteItem

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk


class ShortcutsHandler:
    def __init__(self, window):
        self.window = window

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for ctrl+key combinations."""
        # Connect key press event
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.window.add_controller(key_controller)

        # Define shortcut mappings (key -> function)
        self.shortcuts = {
            "space": self.capture_image,  # Ctrl+Space
            "s": self.open_settings,  # Ctrl+S
            "q": self.quit_application,  # Ctrl+Q
            "n": self.next_cassette,  # Ctrl+N
        }

        # Numpad shortcuts for quality rating (these will be handled separately)
        self.numpad_shortcuts = {
            "KP_1": 1,
            "KP_2": 2,
            "KP_3": 3,
            "KP_4": 4,
            "KP_5": 5,
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,  # Regular number keys as fallback
        }

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events for shortcuts."""
        # Check if Ctrl is pressed
        if state & Gdk.ModifierType.CONTROL_MASK:
            # Convert keyval to key name
            key_name = Gdk.keyval_name(keyval).lower()
            if key_name in self.shortcuts:
                self.shortcuts[key_name]()
                return True  # Event handled
        else:
            # Check for numpad shortcuts (no modifier required)
            key_name = Gdk.keyval_name(keyval)
            if key_name in self.numpad_shortcuts:
                rating = self.numpad_shortcuts[key_name]
                self.set_quality_rating(rating)
                return True  # Event handled
        return False  # Event not handled

    def capture_image(self):
        """Handle Ctrl+C: Capture image."""
        print("Capture image shortcut triggered")

        # Take the picture
        try:
            from datetime import datetime

            # Parse cassette_date string to datetime, or use None if empty
            cassette_date = None
            if self.window.shared_state.cassette_date.strip():
                try:
                    cassette_date = datetime.strptime(
                        self.window.shared_state.cassette_date.strip(), "%Y"
                    )
                except ValueError:
                    # If parsing fails, try more formats or use None
                    cassette_date = None

            self.window.shared_state.camera_manager.take_picture(
                CassetteItem(
                    name=self.window.shared_state.cassette_name,
                    label=self.window.shared_state.slide_label,
                    stars=self.window.shared_state.quality_rating,
                    date=cassette_date,
                )
            )

        except Exception as e:
            print(f"Failed to capture image: {e}")
            # TODO: Show error dialog to user

    def open_settings(self):
        """Handle Ctrl+S: Open settings."""
        from src.settings import SettingsDialog

        dialog = SettingsDialog(self.window, self.window.shared_state)
        dialog.present()

    def quit_application(self):
        """Handle Ctrl+Q: Quit application."""
        print("Quit application shortcut triggered")
        self.window.get_application().quit()

    def next_cassette(self):
        """Handle Ctrl+N: Move to next cassette."""
        print("Next cassette shortcut triggered")
        self.window.shared_state.next_cassette()

    def set_quality_rating(self, rating):
        """Set quality rating (1-5 stars)."""
        print(f"Setting quality rating to {rating} stars")
        self.window.shared_state.set_quality_rating(rating)

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
