from datetime import datetime
from typing import Literal

from gi.repository import GObject, Gtk

from src.constants import INNER_PADDING
from src.date_utils import format_datetime_friendly
from src.picture import CassetteItem
from src.shared_state import SharedState


class DateWithStatus(Gtk.Box):
    def __init__(
        self,
        cassette: CassetteItem,
        field: Literal["date", "slide_date"] = "date",
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=INNER_PADDING // 3,
        )

        self.cassette = cassette
        self.field = field

        cassette_date_label = Gtk.Label(
            label=" ".join([x.capitalize() for x in field.split("_")])
        )
        cassette_date_label.set_halign(Gtk.Align.START)
        self.append(cassette_date_label)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("e.g., 2023, Dec 2023, 25/12/2023")

        cassette.bind_property(
            field + "_backing",
            self.entry,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        # Date status label (for error messages or friendly datetime display)
        self.status_label = Gtk.Label(label="")
        self.status_label.set_margin_top(4)
        self.status_label.set_halign(Gtk.Align.END)

        self.append(self.entry)
        self.append(self.status_label)
        self.cassette.connect("notify::slide-date-backing", self.on_date_change)
        self.cassette.connect("notify::date-backing", self.on_date_change)

    def on_date_change(self, intsance, param):
        date: datetime | None = getattr(self.cassette, self.field)
        err: str = getattr(self.cassette, "_" + self.field + "_err")

        if self.field == "date":
            self.set_sensitive(self.cassette.slide_date_backing == "")

        if err:
            self.status_label.set_label(err)
            self.status_label.add_css_class("error")
            self.entry.add_css_class("error")
        else:
            self.status_label.set_label(
                format_datetime_friendly(date) if date is not None else ""
            )
            self.status_label.remove_css_class("error")
            self.entry.remove_css_class("error")


class CassetteInfo(Gtk.Frame):
    def __init__(self, state: SharedState):
        super().__init__(label="Cassette Context")
        self.state = state
        self.set_margin_bottom(INNER_PADDING)

        cassette_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cassette_box.set_margin_top(INNER_PADDING)
        cassette_box.set_margin_bottom(INNER_PADDING)
        cassette_box.set_margin_start(INNER_PADDING)
        cassette_box.set_margin_end(INNER_PADDING)
        self.set_child(cassette_box)

        # Cassette name
        cassette_name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cassette_box.append(cassette_name_box)

        cassette_name_label = Gtk.Label(label="Name:")
        cassette_name_label.set_halign(Gtk.Align.START)
        cassette_name_box.append(cassette_name_label)

        cassette_name_entry = Gtk.Entry()
        cassette_name_entry.set_placeholder_text("e.g., Russia, 1994")
        cassette_name_box.append(cassette_name_entry)

        cassette_box.append(DateWithStatus(state.cassette))
        cassette_box.append(DateWithStatus(state.cassette, "slide_date"))

        # Slide label
        slide_label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cassette_box.append(slide_label_box)

        slide_label = Gtk.Label(label="Slide:")
        slide_label.set_halign(Gtk.Align.START)
        slide_label_box.append(slide_label)

        slide_label_entry = Gtk.Entry()
        slide_label_entry.set_placeholder_text("Slide label")
        slide_label_box.append(slide_label_entry)
        state.cassette.bind_property(
            "label",
            slide_label_entry,
            "text",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
