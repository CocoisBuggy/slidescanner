import ctypes
from threading import Event
from .camera_core import (
    EDS_ERR_OK,
    CameraException,
    kEdsPropertyEvent_PropertyChanged,
    kEdsPropID_ISOSpeed,
    kEdsPropID_Av,
    kEdsPropID_Tv,
    edsdk,
    EdsCameraListRef,
    EdsUInt32,
    EdsCameraRef,
    EdsDeviceInfo,
    EdsPropertyEventHandler,
)


def needs_sdk(inner):
    def wrapper(self, *args, **kwargs):
        if not self.initialized.is_set() or not self._edsdk_available():
            raise CameraException("SDK is not initialized")

        return inner(self, *args, **kwargs)

    return wrapper


# Property change callback
def _property_callback(event, property_id, param, context):
    manager = ctypes.cast(context, ctypes.py_object).value
    if event == kEdsPropertyEvent_PropertyChanged:
        if property_id == kEdsPropID_ISOSpeed:
            iso_value = manager.get_property_value(property_id)
            print(f"ISO changed to: {iso_value}")
        elif property_id == kEdsPropID_Av:
            av_value = manager.get_property_value(property_id)
            print(f"Aperture changed to: {av_value}")
        elif property_id == kEdsPropID_Tv:
            tv_value = manager.get_property_value(property_id)
            print(f"Shutter speed changed to: {tv_value}")
        else:
            print(f"Property {property_id} changed")
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
        if not self._edsdk_available():
            return
        if self.camera:
            edsdk.EdsCloseSession(self.camera)
            edsdk.EdsRelease(self.camera)
            self.camera = None
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
    def get_device_info(self, camera) -> EdsDeviceInfo | None:
        device_info = EdsDeviceInfo()
        err = edsdk.EdsGetDeviceInfo(camera, ctypes.byref(device_info))

        if err != EDS_ERR_OK:
            raise CameraException(err)

        return device_info

    @needs_sdk
    def open_session(self, camera):
        err = edsdk.EdsOpenSession(camera)
        if err == EDS_ERR_OK:
            self.camera = camera
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
    def get_property_value(self, property_id):
        value = EdsUInt32()
        err = edsdk.EdsGetPropertyData(
            self.camera, property_id, 0, ctypes.sizeof(EdsUInt32), ctypes.byref(value)
        )
        if err == EDS_ERR_OK:
            return value.value
        return None
