import threading
import time
from gi.repository import GLib, GdkPixbuf, Gtk  # noqa: E402


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

        self.create_header_bar()
        self.create_main_content()

        self.shared_state.connect("camera-name", self.on_camera_name_changed)
        self.on_camera_name_changed(self.shared_state, self.shared_state.camera_name)

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
        self.camera_info_label.set_margin_top(12)
        self.camera_info_label.set_margin_bottom(12)
        self.camera_info_label.set_margin_start(12)
        self.camera_info_label.set_margin_end(12)
        camera_info_frame.set_child(self.camera_info_label)

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
                print(f"Downloaded {len(data)} bytes")
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
                print(f"Updated image {pixbuf.get_width()}x{pixbuf.get_height()}")
            else:
                print("Pixbuf is None")
        except Exception as e:
            print(f"Failed to load image: {e}")
