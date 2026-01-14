import threading
import time
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import GLib, Gdk, GdkPixbuf, Gtk  # noqa: E402


class SlideScannerWindow(Gtk.ApplicationWindow):
    def __init__(self, shared_state, **kwargs):
        super().__init__(**kwargs)
        self.shared_state = shared_state
        self.set_title("Slide Scanner")
        self.set_default_size(800, 600)

        self.camera_info_label = None
        self.iso_spin = None
        self.shutter_spin = None
        self.live_view_image = None
        self.live_view_thread = None
        self.live_view_running = False

        # Cassette context UI elements
        self.cassette_name_entry = None
        self.cassette_date_entry = None
        self.slide_label_entry = None
        self.quality_label = None

        self.create_header_bar()
        self.create_main_content()

        self.shared_state.connect("camera-name", self.on_camera_name_changed)
        self.on_camera_name_changed(self.shared_state, self.shared_state.camera_name)

        self.shared_state.connect("cassette-context-changed", self.on_cassette_context_changed)
        self.on_cassette_context_changed(self.shared_state)

        # Set up keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for ctrl+key combinations."""
        # Connect key press event
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        # Define shortcut mappings (key -> function)
        self.shortcuts = {
            'c': self.capture_image,      # Ctrl+C
            's': self.open_settings,      # Ctrl+S
            'q': self.quit_application,   # Ctrl+Q
            'n': self.next_cassette,      # Ctrl+N
        }

        # Numpad shortcuts for quality rating (these will be handled separately)
        self.numpad_shortcuts = {
            'KP_1': 1, 'KP_2': 2, 'KP_3': 3, 'KP_4': 4, 'KP_5': 5,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5  # Regular number keys as fallback
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
            self.shared_state.camera_manager.take_picture()
            print(f"Image captured with cassette context:")
            print(f"  Name: {self.shared_state.cassette_name}")
            print(f"  Date: {self.shared_state.cassette_date}")
            print(f"  Slide: {self.shared_state.slide_label}")
            print(f"  Quality: {self.shared_state.quality_rating} stars")

            # TODO: Download the captured image and add metadata
            # TODO: Save image with cassette context in EXIF metadata

        except Exception as e:
            print(f"Failed to capture image: {e}")
            # TODO: Show error dialog to user
        # These should be written to EXIF metadata
        # For now, just print a message

    def open_settings(self):
        """Handle Ctrl+S: Open settings."""
        print("Open settings shortcut triggered")
        # TODO: Implement settings dialog

    def quit_application(self):
        """Handle Ctrl+Q: Quit application."""
        print("Quit application shortcut triggered")
        self.get_application().quit()

    def next_cassette(self):
        """Handle Ctrl+N: Move to next cassette."""
        print("Next cassette shortcut triggered")
        self.shared_state.next_cassette()

    def set_quality_rating(self, rating):
        """Set quality rating (1-5 stars)."""
        print(f"Setting quality rating to {rating} stars")
        self.shared_state.set_quality_rating(rating)

    def show_shortcuts_dialog(self):
        """Display a dialog showing all available keyboard shortcuts."""
        # Dynamically generate shortcuts text from the shortcuts dictionary
        ctrl_shortcut_descriptions = {
            'c': 'Capture Image',
            's': 'Open Settings',
            'q': 'Quit Application',
            'n': 'Next Cassette'
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
        shortcuts_lines.append("• Images saved as: CassetteName_001.jpg, CassetteName_002.jpg, etc.")
        shortcuts_lines.append("• Use cassette name field to set the base filename")

        shortcuts_text = "\n".join(shortcuts_lines)

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Keyboard Shortcuts",
            secondary_text=shortcuts_text
        )
        dialog.connect("response", lambda dialog, response: dialog.destroy())
        dialog.present()

    def create_header_bar(self):
        header_bar = Gtk.HeaderBar()
        self.set_titlebar(header_bar)

        menu_button = Gtk.MenuButton()
        menu_model = self.create_menu_model()
        menu_button.set_menu_model(menu_model)
        header_bar.pack_end(menu_button)

    def create_menu_model(self):
        menu_builder = Gtk.Builder()
        menu_xml = """
        <interface>
            <menu id="app_menu">
                <section>
                    <item>
                        <attribute name="label">Preferences</attribute>
                        <attribute name="action">app.preferences</attribute>
                    </item>
                </section>
                <section>
                    <item>
                        <attribute name="label">About</attribute>
                        <attribute name="action">app.about</attribute>
                    </item>
                    <item>
                        <attribute name="label">Quit</attribute>
                        <attribute name="action">app.quit</attribute>
                    </item>
                </section>
            </menu>
        </interface>
        """

        menu_builder.add_from_string(menu_xml)
        return menu_builder.get_object("app_menu")

    def create_main_content(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(main_box)

        toolbar = self.create_toolbar()
        main_box.append(toolbar)

        content_area = self.create_content_area()
        main_box.append(content_area)

        status_bar = self.create_status_bar()
        main_box.append(status_bar)

    def create_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_spacing(6)

        capture_btn = Gtk.Button(label="Capture")
        toolbar.append(capture_btn)

        settings_btn = Gtk.Button(label="Settings")
        toolbar.append(settings_btn)

        shortcuts_btn = Gtk.Button(label="Shortcuts")
        shortcuts_btn.connect("clicked", lambda btn: self.show_shortcuts_dialog())
        toolbar.append(shortcuts_btn)

        return toolbar

    def create_content_area(self):
        content_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_area.set_hexpand(True)
        content_area.set_vexpand(True)

        left_panel = self.create_left_panel()
        content_area.append(left_panel)

        right_panel = self.create_right_panel()
        content_area.append(right_panel)

        return content_area

    def create_left_panel(self):
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_panel.set_size_request(200, -1)
        left_panel.set_margin_start(12)
        left_panel.set_margin_end(6)
        left_panel.set_margin_top(12)
        left_panel.set_margin_bottom(12)

        camera_info_frame = Gtk.Frame(label="Camera Info")
        camera_info_frame.set_margin_bottom(12)
        left_panel.append(camera_info_frame)

        self.camera_info_label = Gtk.Label(label="No camera connected")
        self.camera_info_label.set_margin_top(12)
        self.camera_info_label.set_margin_bottom(12)
        self.camera_info_label.set_margin_start(12)
        self.camera_info_label.set_margin_end(12)
        camera_info_frame.set_child(self.camera_info_label)

        cassette_frame = Gtk.Frame(label="Cassette Context")
        cassette_frame.set_margin_bottom(12)
        left_panel.append(cassette_frame)

        cassette_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cassette_box.set_margin_top(12)
        cassette_box.set_margin_bottom(12)
        cassette_box.set_margin_start(12)
        cassette_box.set_margin_end(12)
        cassette_frame.set_child(cassette_box)

        # Cassette name
        cassette_name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(cassette_name_box)

        cassette_name_label = Gtk.Label(label="Name:")
        cassette_name_box.append(cassette_name_label)

        self.cassette_name_entry = Gtk.Entry()
        self.cassette_name_entry.set_placeholder_text("e.g., Russia, 1994")
        self.cassette_name_entry.connect("changed", self.on_cassette_name_changed)
        cassette_name_box.append(self.cassette_name_entry)

        # Cassette date
        cassette_date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(cassette_date_box)

        cassette_date_label = Gtk.Label(label="Date:")
        cassette_date_box.append(cassette_date_label)

        self.cassette_date_entry = Gtk.Entry()
        self.cassette_date_entry.set_placeholder_text("Year")
        self.cassette_date_entry.set_max_length(4)
        self.cassette_date_entry.connect("changed", self.on_cassette_date_changed)
        cassette_date_box.append(self.cassette_date_entry)

        # Slide label
        slide_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(slide_label_box)

        slide_label_label = Gtk.Label(label="Slide:")
        slide_label_box.append(slide_label_label)

        self.slide_label_entry = Gtk.Entry()
        self.slide_label_entry.set_placeholder_text("Slide label")
        self.slide_label_entry.connect("changed", self.on_slide_label_changed)
        slide_label_box.append(self.slide_label_entry)

        # Quality rating display
        quality_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(quality_box)

        quality_display_label = Gtk.Label(label="Quality:")
        quality_box.append(quality_display_label)

        self.quality_label = Gtk.Label(label="★★★☆☆")
        quality_box.append(self.quality_label)

        controls_frame = Gtk.Frame(label="Controls")
        left_panel.append(controls_frame)

        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        controls_box.set_margin_top(12)
        controls_box.set_margin_bottom(12)
        controls_box.set_margin_start(12)
        controls_box.set_margin_end(12)
        controls_frame.set_child(controls_box)

        iso_label = Gtk.Label(label="ISO:")
        controls_box.append(iso_label)

        self.iso_spin = Gtk.SpinButton()
        self.iso_spin.set_range(100, 3200)
        self.iso_spin.set_value(400)
        controls_box.append(self.iso_spin)

        shutter_label = Gtk.Label(label="Shutter Speed:")
        controls_box.append(shutter_label)

        self.shutter_spin = Gtk.SpinButton()
        self.shutter_spin.set_range(1, 1000)
        self.shutter_spin.set_value(125)
        controls_box.append(self.shutter_spin)

        return left_panel

    def create_right_panel(self):
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_panel.set_hexpand(True)
        right_panel.set_vexpand(True)
        right_panel.set_margin_start(6)
        right_panel.set_margin_end(12)
        right_panel.set_margin_top(12)
        right_panel.set_margin_bottom(12)

        preview_frame = Gtk.Frame(label="Preview")
        preview_frame.set_hexpand(True)
        right_panel.append(preview_frame)

        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        preview_box.set_margin_top(6)
        preview_box.set_margin_bottom(6)
        preview_box.set_margin_start(6)
        preview_box.set_margin_end(6)
        preview_frame.set_child(preview_box)

        self.live_view_image = Gtk.Picture()
        self.live_view_image.set_vexpand(True)
        self.live_view_image.set_hexpand(True)
        self.live_view_image.set_content_fit(Gtk.ContentFit.COVER)
        preview_box.append(self.live_view_image)

        return right_panel

    def create_status_bar(self):
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_bar.set_margin_top(6)
        status_bar.set_margin_bottom(6)
        status_bar.set_margin_start(12)
        status_bar.set_margin_end(12)

        status_label = Gtk.Label(label="Ready")
        status_bar.append(status_label)

        return status_bar

    def on_camera_name_changed(self, shared_state, camera_name):
        if camera_name:
            self.camera_info_label.set_text(camera_name)
            self.iso_spin.set_sensitive(True)
            self.shutter_spin.set_sensitive(True)
            self.start_live_view()
        else:
            self.camera_info_label.set_text("No camera connected")
            self.iso_spin.set_sensitive(False)
            self.shutter_spin.set_sensitive(False)
            self.stop_live_view()

    def on_cassette_context_changed(self, shared_state):
        """Update UI when cassette context changes."""
        if self.cassette_name_entry:
            self.cassette_name_entry.set_text(self.shared_state.cassette_name)
        if self.cassette_date_entry:
            self.cassette_date_entry.set_text(self.shared_state.cassette_date)
        if self.slide_label_entry:
            self.slide_label_entry.set_text(self.shared_state.slide_label)
        if self.quality_label:
            # Display quality as stars
            stars = "★" * self.shared_state.quality_rating + "☆" * (5 - self.shared_state.quality_rating)
            self.quality_label.set_text(stars)

    def on_cassette_name_changed(self, entry):
        """Handle cassette name entry changes."""
        self.shared_state.set_cassette_name(entry.get_text())

    def on_cassette_date_changed(self, entry):
        """Handle cassette date entry changes."""
        self.shared_state.set_cassette_date(entry.get_text())

    def on_slide_label_changed(self, entry):
        """Handle slide label entry changes."""
        self.shared_state.set_slide_label(entry.get_text())

    def start_live_view(self):
        if self.live_view_thread and self.live_view_thread.is_alive():
            return
        self.live_view_running = True
        self.live_view_thread = threading.Thread(
            target=self.live_view_loop, daemon=True
        )
        self.live_view_thread.start()

    def stop_live_view(self):
        self.live_view_running = False
        if self.live_view_thread:
            self.live_view_thread.join(timeout=1)
            self.live_view_thread = None

    def live_view_loop(self):
        while self.live_view_running and self.shared_state.camera:
            try:
                data = self.shared_state.camera_manager.download_evf_image()
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
                self.live_view_image.set_pixbuf(pixbuf)
            else:
                print("Pixbuf is None")
        except Exception as e:
            print(f"Failed to load image: {e}")
