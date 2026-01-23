import ctypes
from threading import Event
from typing import Any, Callable, Protocol

from gi.repository import GObject

from src.picture import CassetteItem
from src.common_signal import SignalName

from . import (
    EDS_ERR_OK,
    CameraException,
    EdsCameraListRef,
    EdsCameraRef,
    EdsObjectEventHandler,
    EdsPropertyEventHandler,
    EdsPropertyIDEnum,
    EdsStateEventHandler,
    EdsUInt32,
    _property_callback,
    _state_callback,
    edsdk,
    kEdsObjectEvent_All,
    kEdsPropertyEvent_PropertyChanged,
    kEdsStateEvent_All,
)
from .download import _object_callback, object_event
from .object_events import EdsObjectEventEnum
from .properties import waiting
from .sdk import EdsCapacity


def needs_sdk(inner):
    def wrapper(self, *args, **kwargs):
        if not self.initialized.is_set() or not self._edsdk_available():
            raise CameraException("SDK is not initialized")

        return inner(self, *args, **kwargs)

    return wrapper


class SignalWithCassette(Protocol):
    cassette: CassetteItem

    def emit(self, signal_name: str | GObject.Signal, *args: Any) -> Any: ...

    def connect(
        self, detailed_signal: str | GObject.Signal, handler: Callable
    ) -> Any: ...


class CameraManager:
    initialized: Event
    opening: Event
    camera_list: EdsCameraListRef | None
    signal: SignalWithCassette

    def __init__(self, signal: SignalWithCassette):
        self.camera_list = None
        self.initialized = Event()
        self.opening = Event()
        self.signal = signal

    def _edsdk_available(self):
        return edsdk is not None

    def initialize(self):
        if not self._edsdk_available():
            return False

        err = edsdk.EdsInitializeSDK()
        if err == EDS_ERR_OK:
            self.initialized.set()

            return True
        return False

    def terminate(self):
        if not self._edsdk_available():
            return

        if self.camera_list:
            edsdk.EdsRelease(self.camera_list)
            self.camera_list = None

        if self.initialized:
            edsdk.EdsTerminateSDK()
            self.initialized.clear()

    @needs_sdk
    def get_camera_list(self):
        camera_list = EdsCameraListRef()
        err = edsdk.EdsGetCameraList(ctypes.byref(camera_list))

        if err != EDS_ERR_OK:
            raise CameraException(err)

        self.camera_list = camera_list

        return True

    @needs_sdk
    def get_camera_count(self):
        if self.camera_list is None:
            if not self.get_camera_list():
                raise CameraException("Camera list uninitialized")

        count = EdsUInt32()
        err = edsdk.EdsGetChildCount(self.camera_list, ctypes.byref(count))

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return count.value

    @needs_sdk
    def get_camera(self, index=0):
        camera_ref = EdsCameraRef()
        err = edsdk.EdsGetChildAtIndex(
            self.camera_list, index, ctypes.byref(camera_ref)
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return camera_ref

    @needs_sdk
    def set_property_value(
        self, camera: EdsCameraRef, property_id: EdsPropertyIDEnum, value
    ):
        waiting[property_id].clear()

        err = edsdk.EdsSetPropertyData(
            camera,
            property_id.value,
            0,
            ctypes.sizeof(EdsUInt32),
            ctypes.byref(EdsUInt32(value)),
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

    @needs_sdk
    def open_session(self, camera: EdsCameraRef):
        print("We are going to open a session to the camera")

        self.set_property_event_handler(camera)
        self.set_object_event_handler(camera)
        self.set_state_event_handler(camera)

        print("All events are set up for handle")

        self.signal.emit(SignalName.CameraConnecting.name)
        err = edsdk.EdsOpenSession(camera)

        if err == EDS_ERR_OK:
            # Set save destination to PC (value 2 = PC only)
            # This ensures captured images are transferred to the computer
            try:
                self.set_property_value(camera, EdsPropertyIDEnum.SaveTo, 2)
                print("Set save destination to PC")

                # When saving to Host, set capacity to indicate available space
                capacity = EdsCapacity(
                    numberOfFreeClusters=0x7FFFFFFF,
                    bytesPerSector=0x1000,
                    reset=True,
                )

                object_event[EdsObjectEventEnum.VolumeInfoChanged].clear()
                err = edsdk.EdsSetCapacity(camera, capacity)
                if err != EDS_ERR_OK:
                    raise CameraException(err)
                object_event[EdsObjectEventEnum.VolumeInfoChanged].wait(5)
                self.signal.emit(SignalName.CameraConnected.name)

            except Exception as e:
                print(f"Failed to set save destination: {e}")

            return True

        raise CameraException(err)

    @needs_sdk
    def set_property_event_handler(self, camera: EdsCameraRef):
        global _property_handler
        _property_handler = EdsPropertyEventHandler(_property_callback)

        err = edsdk.EdsSetPropertyEventHandler(
            camera,
            kEdsPropertyEvent_PropertyChanged,
            _property_handler,
            ctypes.py_object(self),
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

    @needs_sdk
    def set_object_event_handler(self, camera: EdsCameraRef):
        """Set up handler for object events (like new images)."""
        global _object_handler
        _object_handler = EdsObjectEventHandler(_object_callback)

        err = edsdk.EdsSetObjectEventHandler(
            camera,
            kEdsObjectEvent_All,
            _object_handler,
            ctypes.c_void_p(0),
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

    @needs_sdk
    def set_state_event_handler(self, camera: EdsCameraRef):
        """Set up handler for state events (like AF results)."""
        global _state_handler
        _state_handler = EdsStateEventHandler(_state_callback)

        err = edsdk.EdsSetCameraStateEventHandler(
            camera,
            kEdsStateEvent_All,
            _state_handler,
            ctypes.c_void_p(0),
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return err == EDS_ERR_OK
