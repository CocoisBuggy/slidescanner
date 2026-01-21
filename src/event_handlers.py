from .application_abstract import SlideWindowAbstract
from .auto_capture import AutoCaptureManager


class EventHandlers:
    def __init__(self, window: SlideWindowAbstract):
        self.window = window

    def on_camera_name_changed(self, shared_state, camera_name):
        if camera_name:
            self.window.camera_info_label.set_text(camera_name)
            self.window.live_view.start_live_view()
        else:
            self.window.camera_info_label.set_text("No camera connected")
            self.window.live_view.stop_live_view()

    def on_cassette_context_changed(self, shared_state):
        """Update UI when cassette context changes."""
        if self.window.cassette_name_entry:
            # Only update if the text is different to avoid recursion
            current_text = self.window.cassette_name_entry.get_text()
            if current_text != self.window.shared_state.cassette_name:
                self.window.cassette_name_entry.set_text(
                    self.window.shared_state.cassette_name
                )
        if self.window.cassette_date_entry:
            # Only update if the text is different to avoid recursion
            current_text = self.window.cassette_date_entry.get_text()
            if current_text != self.window.shared_state.cassette_date:
                self.window.cassette_date_entry.set_text(
                    self.window.shared_state.cassette_date
                )
                # Also update the status label when date changes programmatically
                self._update_date_status_label(self.window.shared_state.cassette_date)
        if self.window.slide_label_entry:
            # Only update if the text is different to avoid recursion
            current_text = self.window.slide_label_entry.get_text()
            if current_text != self.window.shared_state.slide_label:
                self.window.slide_label_entry.set_text(
                    self.window.shared_state.slide_label
                )

        if self.window.quality_label:
            # Display quality as stars
            stars = "★" * self.window.shared_state.quality_rating + "☆" * (
                5 - self.window.shared_state.quality_rating
            )
            self.window.quality_label.set_text(stars)

    def _update_date_status_label(self, date_text):
        """Update the date status label based on the current date text."""
        from .date_utils import parse_fuzzy_date, format_datetime_friendly

        parsed_date, error_message = parse_fuzzy_date(date_text)

        if parsed_date:
            # Success - show friendly datetime
            friendly_text = format_datetime_friendly(parsed_date)
            self.window.cassette_date_status_label.set_text(friendly_text)
            self.window.cassette_date_status_label.get_style_context().remove_class(
                "error-label"
            )
        elif error_message:
            # Error - show error message in red
            self.window.cassette_date_status_label.set_text(error_message)
            self.window.cassette_date_status_label.get_style_context().add_class(
                "error-label"
            )
        else:
            # Empty input - clear status
            self.window.cassette_date_status_label.set_text("")
            self.window.cassette_date_status_label.get_style_context().remove_class(
                "error-label"
            )

    def on_cassette_name_changed(self, entry):
        """Handle cassette name entry changes."""
        self.window.shared_state.set_cassette_name(entry.get_text())

    def on_cassette_date_changed(self, entry):
        """Handle cassette date entry changes with fuzzy parsing."""
        date_text = entry.get_text()

        # Try to parse the fuzzy date
        from .date_utils import parse_fuzzy_date, format_datetime_friendly

        parsed_date, error_message = parse_fuzzy_date(date_text)

        if parsed_date:
            # Success - show friendly datetime
            friendly_text = format_datetime_friendly(parsed_date)
            self.window.cassette_date_status_label.set_text(friendly_text)
            self.window.cassette_date_status_label.get_style_context().remove_class(
                "error-label"
            )
            # Store the original text, not the parsed version
            self.window.shared_state.set_cassette_date(date_text)
        elif error_message:
            # Error - show error message in red
            self.window.cassette_date_status_label.set_text(error_message)
            self.window.cassette_date_status_label.get_style_context().add_class(
                "error-label"
            )
            # Still store the text so user can continue editing
            self.window.shared_state.set_cassette_date(date_text)
        else:
            # Empty input - clear status
            self.window.cassette_date_status_label.set_text("")
            self.window.cassette_date_status_label.get_style_context().remove_class(
                "error-label"
            )
            self.window.shared_state.set_cassette_date(date_text)

        # Update visual override indication
        self._update_date_override_visuals()

    def on_slide_date_changed(self, entry):
        """Handle slide date entry changes with fuzzy parsing."""
        date_text = entry.get_text()

        # Try to parse the fuzzy date
        from .date_utils import parse_fuzzy_date, format_datetime_friendly

        parsed_date, error_message = parse_fuzzy_date(date_text)

        if parsed_date:
            # Success - show friendly datetime
            friendly_text = format_datetime_friendly(parsed_date)
            self.window.slide_date_status_label.set_text(friendly_text)
            self.window.slide_date_status_label.get_style_context().remove_class(
                "error-label"
            )
            # Store the original text, not the parsed version
            self.window.shared_state.set_slide_date(date_text)
        elif error_message:
            # Error - show error message in red
            self.window.slide_date_status_label.set_text(error_message)
            self.window.slide_date_status_label.get_style_context().add_class(
                "error-label"
            )
            # Still store the text so user can continue editing
            self.window.shared_state.set_slide_date(date_text)
        else:
            # Empty input - clear status
            self.window.slide_date_status_label.set_text("")
            self.window.slide_date_status_label.get_style_context().remove_class(
                "error-label"
            )
            self.window.shared_state.set_slide_date(date_text)

        # Update visual override indication
        self._update_date_override_visuals()

    def on_slide_label_changed(self, entry):
        """Handle slide label entry changes."""
        self.window.shared_state.set_slide_label(entry.get_text())

    def on_auto_capture_toggled(self, switch, param_spec):
        """Handle auto capture toggle changes."""
        enabled = switch.get_active()
        self.window.shared_state.set_auto_capture(enabled)

    def on_auto_capture_changed(self, shared_state, enabled):
        """Handle auto capture state changes from shared state."""
        # Update UI to reflect state (in case it's changed programmatically)
        if hasattr(self.window, "auto_capture_switch"):
            current_state = self.window.auto_capture_switch.get_active()
            if current_state != enabled:
                self.window.auto_capture_switch.set_active(enabled)

        # Notify live view system of state change
        if enabled:
            self.window.live_view.auto_capture_manager = AutoCaptureManager(self.window)
            self._update_auto_capture_status("Waiting for image...")
        else:
            self.window.live_view.auto_capture_manager = None
            self._update_auto_capture_status("")

        print(
            f"Auto capture {'enabled' if enabled else 'disabled'} {self.window.live_view.auto_capture_manager}"
        )

    def _update_date_override_visuals(self):
        """Update visual indication when slide date overrides cassette date."""
        slide_date_text = self.window.slide_date_entry.get_text().strip()

        if slide_date_text:
            # Slide date is present, gray out cassette date components
            self.window.cassette_date_label.get_style_context().add_class("dimmed")
            self.window.cassette_date_entry.get_style_context().add_class("dimmed")
            self.window.cassette_date_entry.set_sensitive(False)

            # Update cassette date status to show it's overridden
            cassette_date_text = self.window.cassette_date_entry.get_text().strip()
            if cassette_date_text:
                self.window.cassette_date_status_label.set_text(
                    "(overridden by slide date)"
                )
                self.window.cassette_date_status_label.get_style_context().add_class(
                    "dimmed"
                )
        else:
            # No slide date, restore cassette date components
            self.window.cassette_date_label.get_style_context().remove_class("dimmed")
            self.window.cassette_date_entry.get_style_context().remove_class("dimmed")
            self.window.cassette_date_entry.set_sensitive(True)

            # Remove override message if present
            current_status = self.window.cassette_date_status_label.get_text()
            if current_status == "(overridden by slide date)":
                self.window.cassette_date_status_label.set_text("")
                self.window.cassette_date_status_label.get_style_context().remove_class(
                    "dimmed"
                )

    def _update_auto_capture_status(self, status_text: str):
        """Update the auto capture status label."""
        if hasattr(self.window, "auto_capture_status_label"):
            self.window.auto_capture_status_label.set_text(status_text)

    def update_auto_capture_status_from_manager(self):
        """Update status from auto capture manager (call this periodically)."""
        if self.window.shared_state.auto_capture and hasattr(
            self.window, "auto_capture_status_label"
        ):
            status = self.window.live_view.auto_capture_manager.get_status_text()
            self._update_auto_capture_status(status)

    def on_picture_taken(self, shared_state, filename):
        """Handle picture taken event - clear slide date field."""
        print(f"Picture taken: {filename} - clearing slide date field")

        # Clear the slide date field
        self.window.slide_date_entry.set_text("")
        self.window.slide_date_status_label.set_text("")

        # Update shared state
        shared_state.set_slide_date("")

        # Update visual override indication
        self._update_date_override_visuals()
