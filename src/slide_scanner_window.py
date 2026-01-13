from gi.repository import Gtk  # noqa: E402


class SlideScannerWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Slide Scanner")
        self.set_default_size(800, 600)

        self.camera_info_label = None

        self.create_header_bar()
        self.create_main_content()

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
        self.camera_info_label.set_margin_top(6)
        self.camera_info_label.set_margin_bottom(6)
        self.camera_info_label.set_margin_start(6)
        self.camera_info_label.set_margin_end(6)
        camera_info_frame.set_child(self.camera_info_label)

        controls_frame = Gtk.Frame(label="Controls")
        left_panel.append(controls_frame)

        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        controls_box.set_margin_top(6)
        controls_box.set_margin_bottom(6)
        controls_box.set_margin_start(6)
        controls_box.set_margin_end(6)
        controls_frame.set_child(controls_box)

        iso_label = Gtk.Label(label="ISO:")
        controls_box.append(iso_label)

        iso_spin = Gtk.SpinButton()
        iso_spin.set_range(100, 3200)
        iso_spin.set_value(400)
        controls_box.append(iso_spin)

        shutter_label = Gtk.Label(label="Shutter Speed:")
        controls_box.append(shutter_label)

        shutter_spin = Gtk.SpinButton()
        shutter_spin.set_range(1, 1000)
        shutter_spin.set_value(125)
        controls_box.append(shutter_spin)

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

        preview_label = Gtk.Label(label="Camera preview will appear here")
        preview_label.set_vexpand(True)
        preview_label.set_valign(Gtk.Align.CENTER)
        preview_box.append(preview_label)

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
