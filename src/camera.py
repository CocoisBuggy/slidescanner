import ctypes
import time
from threading import Event


from src.common_signal import SignalName
from src.picture import CassetteItem

from .camera_core import (
    EDS_ERR_OK,
    CameraException,
    EdsCameraRef,
    EdsDeviceInfo,
    EdsEvfImageRef,
    EdsPropertyIDEnum,
    EdsStreamRef,
    EdsUInt32,
    EdsUInt64,
    edsdk,
    kEdsCameraCommand_PressShutterButton,
    kEdsCameraCommand_ShutterButton_Completely_NonAF,
    kEdsCameraCommand_ShutterButton_Halfway,
    kEdsCameraCommand_ShutterButton_OFF,
)
from .camera_core.download import set_next_photo_request
from .camera_core.manager import CameraManager
from .camera_core.properties import waiting


class Camera:
    manager: CameraManager
    ref: EdsCameraRef
    connected: Event
    details: EdsDeviceInfo

    def __init__(
        self,
        manager: CameraManager,
        ref: EdsCameraRef,
    ):
        self.manager = manager
        self.ref = ref
        self.connected = Event()
        self.details = self.get_device_info()

    def close(self):
        edsdk.EdsCloseSession(self.ref)
        edsdk.EdsRelease(self.ref)
        self.connected.clear()
        self.manager.signal.emit(SignalName.CameraDisconnected.name)

    def open(self):
        self.manager.initialized.wait()
        self.manager.open_session(self.ref)
        self.connected.set()

    def get_device_info(self) -> EdsDeviceInfo:
        device_info = EdsDeviceInfo()
        err = edsdk.EdsGetDeviceInfo(
            self.ref,
            ctypes.byref(device_info),
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return device_info

    def get_property_value(self, property_id) -> int:
        value = EdsUInt32()
        err = edsdk.EdsGetPropertyData(
            self.ref,
            property_id,
            0,
            ctypes.sizeof(EdsUInt32),
            ctypes.byref(value),
        )

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return value.value

    def set_property_value(self, property_id: EdsPropertyIDEnum, value):
        return self.manager.set_property_value(self.ref, property_id, value)

    def start_live_view(self):
        print("Gotta start live view")
        self.manager.signal.emit(SignalName.LiveViewStarting.name)

        try:
            # Set output device to PC first
            self.set_property_value(EdsPropertyIDEnum.Evf_OutputDevice, 2)
            waiting[EdsPropertyIDEnum.Evf_OutputDevice].wait(1)
            # Set mode to on
            self.set_property_value(EdsPropertyIDEnum.Evf_Mode, 1)
            waiting[EdsPropertyIDEnum.Evf_Mode].wait(1)

        except Exception as e:
            self.manager.signal.emit(SignalName.LiveViewStopped.name)
            raise e

        self.manager.signal.emit(SignalName.LiveViewRunning.name)

    def download_evf_image(self):
        # Create memory stream
        stream = EdsStreamRef()
        err = edsdk.EdsCreateMemoryStream(EdsUInt64(0), ctypes.byref(stream))
        if err != EDS_ERR_OK:
            raise CameraException(err)

        evf_image = EdsEvfImageRef()
        err = edsdk.EdsCreateEvfImageRef(stream, ctypes.byref(evf_image))
        if err != EDS_ERR_OK:
            edsdk.EdsRelease(stream)
            raise CameraException(err)

        err = edsdk.EdsDownloadEvfImage(self.ref, evf_image)
        if err != EDS_ERR_OK:
            edsdk.EdsRelease(evf_image)
            edsdk.EdsRelease(stream)
            raise CameraException(err)

        # Get data
        pointer = ctypes.c_void_p()
        length = EdsUInt64()
        edsdk.EdsGetPointer(stream, ctypes.byref(pointer))
        edsdk.EdsGetLength(stream, ctypes.byref(length))

        data = ctypes.string_at(pointer, length.value)

        edsdk.EdsRelease(evf_image)
        edsdk.EdsRelease(stream)

        return data

    def focus(self):
        """Perform auto-focus using the same approach as the Canon sample code."""

        print("Starting auto-focus...")

        # Use half-press shutter (same as sample code)
        print("Sending half-press shutter command...")
        err = edsdk.EdsSendCommand(
            self.ref,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_Halfway,
        )

        if err != EDS_ERR_OK:
            print(f"Half-press failed: {err}")
            raise CameraException(f"Failed to start auto-focus: {err}")

        print("Half-press command sent successfully")

        # Based on sample code analysis, focus command appears to be synchronous
        # Wait a brief moment for focus to complete, similar to how cameras work
        print("Waiting for focus to complete...")
        time.sleep(0.5)  # Allow time for AF to complete

        # Release the shutter button to end focus operation
        try:
            edsdk.EdsSendCommand(
                self.ref,
                kEdsCameraCommand_PressShutterButton,
                kEdsCameraCommand_ShutterButton_OFF,
            )
            print("Shutter button released")
        except Exception as e:
            print(f"Warning: Failed to release shutter button: {e}")

        print("Auto-focus completed")
        return True

    def take_picture(self, req: CassetteItem):
        """Take a picture using the camera."""
        print("Taking picture...")
        set_next_photo_request(req)

        # Use PressShutter instead of TakePicture command for better compatibility
        err = edsdk.EdsSendCommand(
            self.ref,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_Completely_NonAF,
        )

        if err != EDS_ERR_OK:
            # Release the shutter button
            edsdk.EdsSendCommand(
                self.ref,
                kEdsCameraCommand_PressShutterButton,
                kEdsCameraCommand_ShutterButton_OFF,
            )
            raise CameraException(err)

        # Release the shutter button
        err = edsdk.EdsSendCommand(
            self.ref,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_OFF,
        )
        if err != EDS_ERR_OK:
            raise CameraException(err)

        print("Picture taken successfully")
        return True
