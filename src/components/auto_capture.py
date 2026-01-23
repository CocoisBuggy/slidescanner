from gi.repository import GObject, Gtk

from src.graphs import StabilityGraph
from src.shared_state import SharedState
from src.constants import INNER_PADDING


class AutoCapture(Gtk.Frame):
    def __init__(self, state: SharedState):
        super().__init__(label="Auto Capture")  # Auto Capture toggle frame
        self.set_margin_bottom(INNER_PADDING)

        auto_capture_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        auto_capture_box.set_margin_top(INNER_PADDING)
        auto_capture_box.set_margin_bottom(INNER_PADDING)
        auto_capture_box.set_margin_start(INNER_PADDING)
        auto_capture_box.set_margin_end(INNER_PADDING)
        self.set_child(auto_capture_box)

        # Auto Capture switch
        auto_capture_switch_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )
        auto_capture_switch_box.set_margin_top(INNER_PADDING // 2)
        auto_capture_switch_box.set_margin_bottom(INNER_PADDING // 2)
        auto_capture_box.append(auto_capture_switch_box)

        auto_capture_label = Gtk.Label(label="Enable Auto Capture:")
        auto_capture_label.set_halign(Gtk.Align.START)
        auto_capture_label.set_hexpand(True)
        auto_capture_switch_box.append(auto_capture_label)

        self.auto_capture_switch = Gtk.Switch()
        self.auto_capture_switch.set_valign(Gtk.Align.CENTER)
        self.auto_capture_switch.set_active(state.auto_capture_manager.enabled)

        # Bi-directional binding
        state.auto_capture_manager.bind_property(
            "enabled",
            self.auto_capture_switch,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        auto_capture_switch_box.append(self.auto_capture_switch)

        # Auto capture status label
        self.auto_capture_status_label = Gtk.Label(label="")
        self.auto_capture_status_label.set_margin_top(INNER_PADDING // 4)
        self.auto_capture_status_label.set_halign(Gtk.Align.CENTER)
        self.auto_capture_status_label.get_style_context().add_class("caption")
        auto_capture_box.append(self.auto_capture_status_label)

        # Stability graph

        self.stability_graph = StabilityGraph(
            state.auto_capture_manager,
            width=380,
            height=140,
        )

        self.stability_graph.set_margin_top(8)
        self.stability_graph.set_margin_bottom(4)
        auto_capture_box.append(self.stability_graph)
