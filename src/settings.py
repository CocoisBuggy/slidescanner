import json
from pathlib import Path

from gi.repository import Gtk, GLib, Pango


class Settings:
    def __init__(self):
        self.cache_dir = Path.home() / ".cache" / "slidescanner"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.cache_dir / "config.json"
        self.photo_location = str(Path.home() / "Pictures")
        self.load()

    def load(self):
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self.photo_location = data.get("photo_location", self.photo_location)

    def save(self):
        data = {"photo_location": self.photo_location}
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=4)


class SettingsDialog(Gtk.Window):
    def __init__(self, parent, shared_state):
        super().__init__(title="Settings", transient_for=parent, modal=True)
        self.set_default_size(500, 300)
        self.shared_state = shared_state
        self.settings = Settings()

        # Apply current settings
        self.shared_state.photo_location = self.settings.photo_location

        # Build UI
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_margin_top(30)
        main_box.set_margin_bottom(30)
        main_box.set_margin_start(30)
        main_box.set_margin_end(30)
        main_box.set_spacing(30)

        # Photo location
        loc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        loc_box.set_hexpand(True)
        loc_label = Gtk.Label(label="Photo Location")
        loc_label.set_xalign(0.5)
        loc_box.append(loc_label)

        current_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        self.loc_label = Gtk.Label(label=self.settings.photo_location)
        self.loc_label.set_ellipsize(Pango.EllipsizeMode.START)
        self.loc_label.set_hexpand(True)
        self.loc_label.set_xalign(0.5)
        current_box.append(self.loc_label)

        choose_btn = Gtk.Button(label="Choose...")
        choose_btn.connect("clicked", self.on_choose_folder)
        current_box.append(choose_btn)

        loc_box.append(current_box)
        main_box.append(loc_box)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        button_box.set_hexpand(True)
        button_box.set_margin_top(20)
        save_btn = Gtk.Button(label="Save")
        save_btn.connect("clicked", self.on_save)
        button_box.append(save_btn)
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", self.on_cancel)
        button_box.append(cancel_btn)
        main_box.append(button_box)

        self.set_child(main_box)

        self.file_dialog = Gtk.FileDialog()

    def on_choose_folder(self, button):
        self.file_dialog.select_folder(
            parent=self, cancellable=None, callback=self.on_folder_selected
        )

    def on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self.settings.photo_location = path
                self.loc_label.set_text(path)
        except GLib.Error:
            pass

    def on_save(self, btn):
        self.shared_state.photo_location = self.settings.photo_location
        self.settings.save()
        self.close()

    def on_cancel(self, btn):
        self.close()
