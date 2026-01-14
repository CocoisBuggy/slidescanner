import ctypes
import time
from threading import Event
from .camera_core import (
    EDS_ERR_OK,
    CameraException,
    kEdsPropertyEvent_PropertyChanged,
    kEdsCameraCommand_TakePicture,
    kEdsObjectEvent_DirItemCreated,
    edsdk,
    EdsCameraListRef,
    EdsUInt32,
    EdsUInt64,
    EdsCameraRef,
    EdsDeviceInfo,
    EdsPropertyEventHandler,
    EdsObjectEventHandler,
    EdsEvfImageRef,
    EdsStreamRef,
    EdsPropertyIDEnum,
    _property_callback,
)


def needs_sdk(inner):
    def wrapper(self, *args, **kwargs):
        if not self.initialized.is_set() or not self._edsdk_available():
            raise CameraException("SDK is not initialized")

        return inner(self, *args, **kwargs)

    return wrapper


# Global references for callbacks
_global_camera_manager = None
_global_shared_state = None


# Object event callback (for image capture events)
def _object_callback(event, object_ref, context):
    global _global_camera_manager
    print(f"Got object event from camera: {event}, {object_ref}")

    if event == kEdsObjectEvent_DirItemCreated:
        print("New image created on camera!")

        if _global_camera_manager is not None:
            try:
                # Download the image
                filename = _global_camera_manager.download_image(object_ref)
                print(f"Successfully downloaded image: {filename}")

                # TODO: Add cassette context metadata to the downloaded image

            except Exception as e:
                print(f"Failed to download image: {e}")
        else:
            print("No camera manager available for image download")

    return EDS_ERR_OK


class CameraManager:
    initialized: Event

    def __init__(self):
        self.camera_list = None
        self.camera = None
        self.initialized = Event()

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
        global _global_camera_manager, _global_shared_state
        if not self._edsdk_available():
            return
        if self.camera:
            edsdk.EdsCloseSession(self.camera)
            edsdk.EdsRelease(self.camera)
            self.camera = None
        if self.camera_list:
            edsdk.EdsRelease(self.camera_list)
            self.camera_list = None
        _global_camera_manager = None  # Clear global references
        _global_shared_state = None
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
    def get_device_info(self, camera) -> EdsDeviceInfo | None:
        device_info = EdsDeviceInfo()
        err = edsdk.EdsGetDeviceInfo(camera, ctypes.byref(device_info))

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return device_info

    @needs_sdk
    def open_session(self, camera):
        global _global_camera_manager, _global_shared_state
        err = edsdk.EdsOpenSession(camera)
        if err == EDS_ERR_OK:
            self.camera = camera
            _global_camera_manager = self  # Store global reference

            # Set save destination to PC (value 2 = PC only)
            # This ensures captured images are transferred to the computer
            try:
                from .camera_core import EdsPropertyIDEnum

                self.set_property_value(EdsPropertyIDEnum.SaveTo, 2)
                print("Set save destination to PC")
            except Exception as e:
                print(f"Failed to set save destination: {e}")

            # Set up event handlers
            self.set_property_event_handler()
            self.set_object_event_handler()
            return True

        raise CameraException(err)

    @needs_sdk
    def set_property_event_handler(self):
        global _property_handler
        _property_handler = EdsPropertyEventHandler(_property_callback)

        err = edsdk.EdsSetPropertyEventHandler(
            self.camera,
            kEdsPropertyEvent_PropertyChanged,
            _property_handler,
            ctypes.py_object(self),
        )

        return err == EDS_ERR_OK

    @needs_sdk
    def set_object_event_handler(self):
        """Set up handler for object events (like new images)."""
        global _object_handler
        _object_handler = EdsObjectEventHandler(_object_callback)

        err = edsdk.EdsSetObjectEventHandler(
            self.camera,
            kEdsObjectEvent_DirItemCreated,
            _object_handler,
            ctypes.c_void_p(0),
        )

        return err == EDS_ERR_OK

    @needs_sdk
    def get_property_value(self, property_id):
        value = EdsUInt32()
        err = edsdk.EdsGetPropertyData(
            self.camera, property_id, 0, ctypes.sizeof(EdsUInt32), ctypes.byref(value)
        )
        if err == EDS_ERR_OK:
            return value.value
        return None

    @needs_sdk
    def set_property_value(self, property_id: EdsPropertyIDEnum, value):
        err = edsdk.EdsSetPropertyData(
            self.camera,
            property_id.value,
            0,
            ctypes.sizeof(EdsUInt32),
            ctypes.byref(EdsUInt32(value)),
        )
        if err != EDS_ERR_OK:
            raise CameraException(err)

        return True

    @needs_sdk
    def start_live_view(self):
        # Set output device to PC first
        err = self.set_property_value(EdsPropertyIDEnum.Evf_OutputDevice, 2)
        if err is not True:
            print(f"Failed to set Evf_OutputDevice: {err}")
        time.sleep(0.5)
        # Set mode to on
        err = self.set_property_value(EdsPropertyIDEnum.Evf_Mode, 1)
        if err is not True:
            print(f"Failed to set Evf_Mode: {err}")
        time.sleep(0.5)

    @needs_sdk
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

        err = edsdk.EdsDownloadEvfImage(self.camera, evf_image)
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

    @needs_sdk
    def take_picture(self):
        """Take a picture using the camera."""
        print("Taking picture...")
        err = edsdk.EdsSendCommand(self.camera, kEdsCameraCommand_TakePicture, 0)
        if err != EDS_ERR_OK:
            raise CameraException(err)
        print("Picture taken successfully")
        return True

    @needs_sdk
    def download_image(self, directory_item, shared_state=None):
        """Download an image from the camera."""
        print("Downloading image...")

        # Create file stream for the output
        import os

        # Create output directory if it doesn't exist
        output_dir = "captured_images"
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename using cassette name + sequential number
        global _global_shared_state
        if _global_shared_state:
            filename = _global_shared_state.get_next_slide_filename()
        else:
            # Fallback if no state available
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"

        filepath = f"{output_dir}/{filename}"

        # Create file stream
        stream = EdsStreamRef()
        err = edsdk.EdsCreateFileStream(
            filename.encode("utf-8"),
            1,  # kEdsFileCreateDisposition_CreateAlways
            0,  # kEdsAccess_ReadWrite
            ctypes.byref(stream),
        )
        if err != EDS_ERR_OK:
            raise CameraException(err)

        try:
            # Download the image
            err = edsdk.EdsDownload(directory_item, stream)
            if err != EDS_ERR_OK:
                raise CameraException(err)

            # Complete the download
            err = edsdk.EdsDownloadComplete(directory_item)
            if err != EDS_ERR_OK:
                raise CameraException(err)

            print(f"Image downloaded successfully: {filename}")
            return filename

        finally:
            edsdk.EdsRelease(stream)
