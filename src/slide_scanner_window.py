import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, Gtk

from .header_bar import create_header_bar
from .main_content import MainContent
from .shared_state import SharedState
from .shortcuts import ShortcutsHandler


class SlideScannerWindow(Gtk.ApplicationWindow):
    def __init__(self, shared_state: SharedState, **kwargs):
        super().__init__(**kwargs)

        self.shared_state = shared_state
        self.set_title("Slide Scanner")
        self.set_default_size(800, 600)

        self.live_view_thread = None
        self.live_view_running = False

        # Initialize handlers
        self.shortcuts_handler = ShortcutsHandler(self, shared_state)

        self.set_titlebar(create_header_bar())
        self.set_child(MainContent(shared_state, self.shortcuts_handler))

        # Set up CSS styling for error labels
        self._setup_css()
        # Set up keyboard shortcuts

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
        
        .caption {
            font-size: 0.8em;
            color: #666666;
            font-style: italic;
        }
        """
        css_provider.load_from_data(css_data.encode())

        # Apply the CSS to the default display
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
