import time
from enum import Enum
from threading import Lock
from typing import Optional
import numpy as np
import cv2


class AutoCaptureState(Enum):
    """States for the auto-capture state machine."""

    WAITING_FOR_NEW_IMAGE = "waiting_for_new_image"
    MONITORING_STABILITY = "monitoring_stability"
    STABLE = "stable"
    CAPTURING = "capturing"


class AutoCaptureManager:
    """Manages auto-capture functionality with image stability detection."""

    def __init__(
        self,
        window,
        stability_threshold: float = 0.98,
        stability_duration: float = 0.2,
    ):
        """
        Initialize auto-capture manager.

        Args:
            window: The main window instance
            stability_threshold: Correlation threshold (0-1) for considering images stable
            stability_duration: Duration in seconds that image must remain stable
        """
        self.window = window
        self.stability_threshold = stability_threshold
        self.stability_duration = stability_duration

        # State management
        self.state = AutoCaptureState.WAITING_FOR_NEW_IMAGE
        self.state_lock = Lock()

        # Image tracking
        self.last_image_data: Optional[bytes] = None
        self.current_image_data: Optional[bytes] = None
        self.stable_start_time: Optional[float] = None

        # Statistics
        self.total_frames_processed = 0
        self.captures_taken = 0

    def process_frame(self, frame_data: bytes) -> bool:
        """
        Process a new live view frame for auto-capture.

        Args:
            frame_data: Raw image data from live view

        Returns:
            True if a capture should be triggered, False otherwise
        """
        with self.state_lock:
            self.total_frames_processed += 1

            # Check if this is a new image (different from last stable image)
            is_new_image = self._is_new_image(frame_data)

            should_capture = False

            if self.state == AutoCaptureState.WAITING_FOR_NEW_IMAGE:
                if is_new_image:
                    # New image detected, start monitoring stability
                    self.current_image_data = frame_data
                    self.stable_start_time = time.time()
                    self.state = AutoCaptureState.MONITORING_STABILITY
                    print("Auto-capture: New image detected, monitoring stability...")

            elif self.state == AutoCaptureState.MONITORING_STABILITY:
                if self._is_image_stable(frame_data):
                    # Image is still stable
                    stability_time = (
                        time.time() - self.stable_start_time
                        if self.stable_start_time
                        else 0.0
                    )
                    if stability_time >= self.stability_duration:
                        # Image has been stable long enough
                        self.state = AutoCaptureState.STABLE
                        should_capture = True
                        print(
                            f"Auto-capture: Image stable for {stability_time:.2f}s, triggering capture..."
                        )
                else:
                    # Image changed, reset to waiting state
                    self.current_image_data = frame_data
                    self.stable_start_time = time.time()
                    print("Auto-capture: Image changed, resetting stability timer...")

            elif self.state == AutoCaptureState.STABLE:
                if self._is_image_stable(frame_data):
                    # Still stable, but we already captured, wait for new image
                    pass  # Do nothing, continue in stable state
                else:
                    # New image appeared, reset to waiting
                    self.current_image_data = frame_data
                    self.stable_start_time = time.time()
                    self.state = AutoCaptureState.MONITORING_STABILITY
                    print("Auto-capture: New image appeared, monitoring stability...")

            elif self.state == AutoCaptureState.CAPTURING:
                # After capture, reset to waiting for new image
                self.last_image_data = frame_data
                self.current_image_data = None
                self.stable_start_time = None
                self.state = AutoCaptureState.WAITING_FOR_NEW_IMAGE
                print("Auto-capture: Capture complete, waiting for new image...")

            return should_capture

    def reset(self):
        """Reset the auto-capture state machine."""
        with self.state_lock:
            self.state = AutoCaptureState.WAITING_FOR_NEW_IMAGE
            self.last_image_data = None
            self.current_image_data = None
            self.stable_start_time = None
            print("Auto-capture: State machine reset")

    def on_capture_completed(self):
        """Called when a capture has been completed."""
        with self.state_lock:
            self.captures_taken += 1
            self.state = AutoCaptureState.CAPTURING

    def _calculate_frame_similarity(
        self, frame_data1: bytes, frame_data2: bytes
    ) -> float:
        """
        Calculate similarity between two frames using correlation.

        Args:
            frame_data1: First frame data
            frame_data2: Second frame data

        Returns:
            Correlation coefficient (0-1), higher means more similar
        """
        img1 = self._frame_data_to_array(frame_data1)
        img2 = self._frame_data_to_array(frame_data2)

        if img1.size == 0 or img2.size == 0:
            return 0.0

        # Apply Hanning window to reduce edge importance
        hanning_window = np.hanning(img1.shape[0])[:, np.newaxis] * np.hanning(img1.shape[1])[np.newaxis, :]
        img1_windowed = img1 * hanning_window
        img2_windowed = img2 * hanning_window

        # Use normalized cross-correlation for similarity
        correlation = np.corrcoef(img1_windowed.flatten(), img2_windowed.flatten())[0, 1]

        # Handle NaN case when images are constant
        if np.isnan(correlation):
            correlation = 1.0 if np.array_equal(img1, img2) else 0.0

        return max(0.0, correlation)  # Ensure non-negative

    def _frame_data_to_array(self, frame_data: bytes) -> np.ndarray:
        """Convert frame data to numpy array for correlation analysis."""
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if frame is None:
            return np.array([])
        return cv2.resize(frame, (64, 64))  # Resize for faster processing

    def _is_new_image(self, frame_data: bytes) -> bool:
        """Check if the current image is different from the last stable image using correlation."""
        if self.last_image_data is None:
            return True
        similarity = self._calculate_frame_similarity(frame_data, self.last_image_data)
        return similarity < self.stability_threshold

    def _is_image_stable(self, frame_data: bytes) -> bool:
        """Check if the current image is stable using correlation with the monitoring image."""
        if self.current_image_data is None:
            return False
        similarity = self._calculate_frame_similarity(
            frame_data, self.current_image_data
        )
        return similarity >= self.stability_threshold

    def get_status_text(self) -> str:
        """Get current status text for debugging/UI feedback."""
        with self.state_lock:
            status_parts = [
                f"State: {self.state.value}",
                f"Frames: {self.total_frames_processed}",
                f"Captures: {self.captures_taken}",
            ]

            if (
                self.state == AutoCaptureState.MONITORING_STABILITY
                and self.stable_start_time
            ):
                stability_time = time.time() - self.stable_start_time
                status_parts.append(f"Stability: {stability_time:.2f}s")

            return " | ".join(status_parts)
