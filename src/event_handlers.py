class EventHandlers:
    def __init__(self, window):
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

    def on_cassette_name_changed(self, entry):
        """Handle cassette name entry changes."""
        self.window.shared_state.set_cassette_name(entry.get_text())

    def on_cassette_date_changed(self, entry):
        """Handle cassette date entry changes."""
        self.window.shared_state.set_cassette_date(entry.get_text())

    def on_slide_label_changed(self, entry):
        """Handle slide label entry changes."""
        self.window.shared_state.set_slide_label(entry.get_text())
