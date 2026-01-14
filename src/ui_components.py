import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk

from .camera_controls import CameraControls


class UIComponents:
    def __init__(self, window):
        self.window = window
        self.camera_controls = CameraControls(window)

    def create_header_bar(self):
        header_bar = Gtk.HeaderBar()
        self.window.set_titlebar(header_bar)

        menu_button = Gtk.MenuButton()
        menu_model = self.create_menu_model()
        menu_button.set_menu_model(menu_model)
        header_bar.pack_end(menu_button)

        return header_bar

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
        self.window.set_child(main_box)

        toolbar = self.create_toolbar()
        main_box.append(toolbar)

        content_area = self.create_content_area()
        main_box.append(content_area)

        status_bar = self.create_status_bar()
        main_box.append(status_bar)

        return main_box

    def create_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_spacing(6)

        capture_btn = Gtk.Button(label="Capture")
        capture_btn.connect("clicked", self.on_capture_clicked)
        toolbar.append(capture_btn)

        settings_btn = Gtk.Button(label="Settings")
        settings_btn.connect("clicked", lambda btn: self.window.shortcuts_handler.open_settings())
        toolbar.append(settings_btn)

        shortcuts_btn = Gtk.Button(label="Shortcuts")
        shortcuts_btn.connect(
            "clicked", lambda btn: self.window.shortcuts_handler.show_shortcuts_dialog()
        )
        toolbar.append(shortcuts_btn)

        return toolbar

    def on_capture_clicked(self, button):
        """Handle capture button click."""
        self.window.shortcuts_handler.capture_image()

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

        self.window.camera_info_label = Gtk.Label(label="No camera connected")
        self.window.camera_info_label.set_margin_top(12)
        self.window.camera_info_label.set_margin_bottom(12)
        self.window.camera_info_label.set_margin_start(12)
        self.window.camera_info_label.set_margin_end(12)
        camera_info_frame.set_child(self.window.camera_info_label)

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

        self.window.cassette_name_entry = Gtk.Entry()
        self.window.cassette_name_entry.set_placeholder_text("e.g., Russia, 1994")
        self.window.cassette_name_entry.connect(
            "changed", self.window.event_handlers.on_cassette_name_changed
        )
        cassette_name_box.append(self.window.cassette_name_entry)

        # Cassette date
        cassette_date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(cassette_date_box)

        cassette_date_label = Gtk.Label(label="Date:")
        cassette_date_box.append(cassette_date_label)

        self.window.cassette_date_entry = Gtk.Entry()
        self.window.cassette_date_entry.set_placeholder_text("Year")
        self.window.cassette_date_entry.set_max_length(4)
        self.window.cassette_date_entry.connect(
            "changed", self.window.event_handlers.on_cassette_date_changed
        )
        cassette_date_box.append(self.window.cassette_date_entry)

        # Slide label
        slide_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(slide_label_box)

        slide_label_label = Gtk.Label(label="Slide:")
        slide_label_box.append(slide_label_label)

        self.window.slide_label_entry = Gtk.Entry()
        self.window.slide_label_entry.set_placeholder_text("Slide label")
        self.window.slide_label_entry.connect(
            "changed", self.window.event_handlers.on_slide_label_changed
        )
        slide_label_box.append(self.window.slide_label_entry)

        # Quality rating display
        quality_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cassette_box.append(quality_box)

        quality_display_label = Gtk.Label(label="Quality:")
        quality_box.append(quality_display_label)

        self.window.quality_label = Gtk.Label(label="★★★☆☆")
        quality_box.append(self.window.quality_label)

        controls_frame = self.camera_controls.create_controls_box()
        left_panel.append(controls_frame)

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

        self.window.live_view_image = Gtk.Picture()
        self.window.live_view_image.set_vexpand(True)
        self.window.live_view_image.set_hexpand(True)
        self.window.live_view_image.set_content_fit(Gtk.ContentFit.COVER)
        preview_box.append(self.window.live_view_image)

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
