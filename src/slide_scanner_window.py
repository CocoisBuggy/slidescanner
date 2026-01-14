import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Gdk  # noqa: E402

from .shortcuts import ShortcutsHandler
from .ui_components import UIComponents
from .event_handlers import EventHandlers
from .live_view import LiveView


class SlideScannerWindow(Gtk.ApplicationWindow):
    def __init__(self, shared_state, **kwargs):
        super().__init__(**kwargs)
        self.shared_state = shared_state
        self.set_title("Slide Scanner")
        self.set_default_size(800, 600)

        self.live_view_thread = None
        self.live_view_running = False

        # Initialize handlers
        self.shortcuts_handler = ShortcutsHandler(self)
        self.ui = UIComponents(self)
        self.event_handlers = EventHandlers(self)
        self.live_view = LiveView(self)

        # Create UI
        self.ui.create_header_bar()
        self.ui.create_main_content()

        # Connect signals
        self.shared_state.connect(
            "camera-name", self.event_handlers.on_camera_name_changed
        )
        self.event_handlers.on_camera_name_changed(
            self.shared_state, self.shared_state.camera_name
        )

        self.shared_state.connect("battery-level-changed", self.ui.update_battery_level)

        self.shared_state.connect(
            "cassette-context-changed", self.event_handlers.on_cassette_context_changed
        )
        self.event_handlers.on_cassette_context_changed(self.shared_state)

        self.shared_state.connect("picture-taken", self.event_handlers.on_picture_taken)

        # Set up CSS styling for error labels
        self._setup_css()

        # Set up keyboard shortcuts
        self.shortcuts_handler.setup_shortcuts()

    def _setup_css(self):
        """Set up CSS styling for the application."""
        css_provider = Gtk.CssProvider()
        css_data = """
        .error-label {
            color: #e01b24;
            font-size: 0.85em;
        }
        
        .dimmed {
            opacity: 0.5;
            color: #888888;
        }
        """
        css_provider.load_from_data(css_data.encode())

        # Apply the CSS to the default display
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
