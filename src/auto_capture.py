import contextlib
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

    stability_threshold: float
    stability_duration: int
    prior_frames: list = []
    state: AutoCaptureState
    total_frames_processed = 0
    stability_history = []
    last_captured_image: bytes | None = None
    last_capture_time: float = 0
    stability_duration: int = 12

    def __init__(
        self,
        window,
        stability_threshold: float = 0.95,
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

    @contextlib.contextmanager
    def frame_context(self, frame_data: bytes):
        yield  # Do something with the frame

        # Capture the frame stuff
        self.prior_frames.append(frame_data)
        self.total_frames_processed += 1

        if len(self.prior_frames) > self.stability_duration:
            self.prior_frames.pop(0)

    def process_frame(self, frame_data: bytes) -> bool:
        """
        Process a new live view frame for auto-capture.

        Args:
            frame_data: Raw image data from live view

        Returns:
            True if a capture should be triggered, False otherwise
        """

        with self.frame_context(frame_data):
            if not self._is_image_stable(frame_data):
                # The image is not stable
                return False

            if (
                self.last_captured_image is not None
                and self._calculate_frame_similarity(
                    frame_data, self.last_captured_image
                )
                >= self.stability_threshold
            ):
                # The image is stable but we have a stable capture of it in any event
                return False

            if len(self.prior_frames) < self.stability_duration:
                return False

            # The image is both sufficiently dissimilar to the last capture, and we also
            # are presently stable
            return True

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
        hanning_window = (
            np.hanning(img1.shape[0])[:, np.newaxis]
            * np.hanning(img1.shape[1])[np.newaxis, :]
        )
        img1_windowed = img1 * hanning_window
        img2_windowed = img2 * hanning_window

        # Use normalized cross-correlation for similarity
        correlation = np.corrcoef(img1_windowed.flatten(), img2_windowed.flatten())[
            0, 1
        ]

        # Handle NaN case when images are constant
        if np.isnan(correlation):
            correlation = 1.0 if np.array_equal(img1, img2) else 0.0

        similarity = max(0.0, correlation)  # Ensure non-negative

        # Store stability for graph (keep only recent history)
        self.stability_history.append(similarity)
        if len(self.stability_history) > 100:
            self.stability_history.pop(0)

        return similarity

    def _frame_data_to_array(self, frame_data: bytes) -> np.ndarray:
        """Convert frame data to numpy array for correlation analysis."""
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if frame is None:
            return np.array([])
        return cv2.resize(frame, (64, 64))  # Resize for faster processing

    def _is_image_stable(self, frame_data: bytes) -> bool:
        """Check if the current image is stable using correlation with the monitoring image."""
        if not self.prior_frames:
            return False

        previous_similarities = [
            self._calculate_frame_similarity(frame_data, prior)
            for prior in self.prior_frames
        ]

        similarity = np.average(previous_similarities)
        self.stability_history = (
            list(
                [
                    0
                    for _ in range(
                        int(self.stability_duration) - len(previous_similarities)
                    )
                ]
            )
            + previous_similarities
        )

        return bool(similarity >= self.stability_threshold)
