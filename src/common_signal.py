from enum import Enum, auto


class SignalName(Enum):
    CameraDisconnected = auto()
    CameraConnected = auto()
    CameraConnecting = auto()

    LiveViewStopped = auto()
    LiveViewStarting = auto()
    LiveViewRunning = auto()
    LiveViewStopping = auto()
