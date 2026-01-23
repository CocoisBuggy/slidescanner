import logging
from enum import Enum
from threading import Event

from .err import EDS_ERR_OK

log = logging.getLogger(__name__)


class StateEvent(Enum):
    All = 0x00000300
    Shutdown = 0x00000301
    JobStatusChanged = 0x00000302
    WillSoonShutDown = 0x00000303
    ShutDownTimerUpdate = 0x00000304
    CaptureError = 0x00000305
    InternalError = 0x00000306
    AfResult = 0x00000309
    PowerZoomInfoChanged = 0x311
    PropertyChanged = 0x101


state: dict[StateEvent, Event] = {evt: Event() for evt in StateEvent}


def _state_callback(event, param, context):
    """Handle state events (like AF results)."""
    global state
    log.debug(f"Got state event: {StateEvent(event)} - {hex(event)} (param: {param})")

    if event in state:
        state[event].set()

    return EDS_ERR_OK
