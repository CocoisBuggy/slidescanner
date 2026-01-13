import ctypes
import os

# Load EDSDK library
lib_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "EDSDK",
    "Library",
    "docs",
    "Linux",
    "EDSDK",
    "Library",
    "x86_64",
    "libEDSDK.so",
)
edsdk = ctypes.CDLL(lib_path)

# Define types
EdsError = ctypes.c_uint32
EdsBaseRef = ctypes.c_void_p
EdsCameraListRef = EdsBaseRef
EdsCameraRef = EdsBaseRef
EdsUInt32 = ctypes.c_uint32
EdsPropertyID = EdsUInt32
EdsPropertyEvent = EdsUInt32


# Define EdsDeviceInfo struct
class EdsDeviceInfo(ctypes.Structure):
    _fields_ = [
        ("szPortName", ctypes.c_char * 256),
        ("szDeviceDescription", ctypes.c_char * 256),
        ("deviceSubType", EdsUInt32),
        ("reserved", EdsUInt32),
    ]


# Callback type
EdsPropertyEventHandler = ctypes.CFUNCTYPE(
    EdsError, EdsPropertyEvent, EdsPropertyID, EdsUInt32, ctypes.c_void_p
)

# Function prototypes
edsdk.EdsInitializeSDK.restype = EdsError
edsdk.EdsTerminateSDK.restype = EdsError
edsdk.EdsGetCameraList.restype = EdsError
edsdk.EdsGetCameraList.argtypes = [ctypes.POINTER(EdsCameraListRef)]
edsdk.EdsGetChildCount.restype = EdsError
edsdk.EdsGetChildCount.argtypes = [EdsBaseRef, ctypes.POINTER(EdsUInt32)]
edsdk.EdsGetChildAtIndex.restype = EdsError
edsdk.EdsGetChildAtIndex.argtypes = [
    EdsBaseRef,
    EdsUInt32,
    ctypes.POINTER(EdsCameraRef),
]
edsdk.EdsGetDeviceInfo.restype = EdsError
edsdk.EdsGetDeviceInfo.argtypes = [EdsCameraRef, ctypes.POINTER(EdsDeviceInfo)]
edsdk.EdsOpenSession.restype = EdsError
edsdk.EdsOpenSession.argtypes = [EdsCameraRef]
edsdk.EdsCloseSession.restype = EdsError
edsdk.EdsCloseSession.argtypes = [EdsCameraRef]
edsdk.EdsRelease.restype = EdsError
edsdk.EdsRelease.argtypes = [EdsBaseRef]
edsdk.EdsSetPropertyEventHandler.restype = EdsError
edsdk.EdsSetPropertyEventHandler.argtypes = [
    EdsCameraRef,
    EdsPropertyEvent,
    EdsPropertyEventHandler,
    ctypes.c_void_p,
]
edsdk.EdsGetPropertyData.restype = EdsError
edsdk.EdsGetPropertyData.argtypes = [
    EdsCameraRef,
    EdsPropertyID,
    EdsUInt32,
    EdsUInt32,
    ctypes.c_void_p,
]

# Error codes
EDS_ERR_OK = 0x00000000

# Property event constants
kEdsPropertyEvent_PropertyChanged = 0x00000101

# Property IDs
kEdsPropID_ISOSpeed = 0x00000402
kEdsPropID_Av = 0x00000405
kEdsPropID_Tv = 0x00000406


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
    def __init__(self):
        self.camera_list = None
        self.camera = None
        self.initialized = False

    def _edsdk_available(self):
        return edsdk is not None

    def initialize(self):
        if not self._edsdk_available():
            return False
        err = edsdk.EdsInitializeSDK()
        if err == EDS_ERR_OK:
            self.initialized = True
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
            self.initialized = False

    def get_camera_list(self):
        if not self.initialized or not self._edsdk_available():
            return False
        camera_list = EdsCameraListRef()
        err = edsdk.EdsGetCameraList(ctypes.byref(camera_list))
        if err != EDS_ERR_OK:
            return False
        self.camera_list = camera_list
        return True

    def get_camera_count(self):
        if not self.camera_list or not self._edsdk_available():
            return 0
        count = EdsUInt32()
        err = edsdk.EdsGetChildCount(self.camera_list, ctypes.byref(count))
        if err != EDS_ERR_OK:
            return 0
        return count.value

    def get_camera(self, index=0):
        if not self.camera_list or not self._edsdk_available():
            return None
        camera = EdsCameraRef()
        err = edsdk.EdsGetChildAtIndex(self.camera_list, index, ctypes.byref(camera))
        if err != EDS_ERR_OK:
            return None
        return camera

    def get_device_info(self, camera):
        if not self._edsdk_available():
            return None
        device_info = EdsDeviceInfo()
        err = edsdk.EdsGetDeviceInfo(camera, ctypes.byref(device_info))
        if err != EDS_ERR_OK:
            return None
        return device_info.szDeviceDescription.decode("utf-8")

    def open_session(self, camera):
        if not self._edsdk_available():
            return False
        err = edsdk.EdsOpenSession(camera)
        if err == EDS_ERR_OK:
            self.camera = camera
            return True
        return False

    def set_property_event_handler(self):
        if not self.camera or not self._edsdk_available():
            return False
        global _property_handler
        _property_handler = EdsPropertyEventHandler(_property_callback)
        err = edsdk.EdsSetPropertyEventHandler(
            self.camera,
            kEdsPropertyEvent_PropertyChanged,
            _property_handler,
            ctypes.py_object(self),
        )
        return err == EDS_ERR_OK

    def get_property_value(self, property_id):
        if not self.camera or not self._edsdk_available():
            return None
        value = EdsUInt32()
        err = edsdk.EdsGetPropertyData(
            self.camera, property_id, 0, ctypes.sizeof(EdsUInt32), ctypes.byref(value)
        )
        if err == EDS_ERR_OK:
            return value.value
        return None

    def connect_first_camera(self):
        if not self.get_camera_list():
            return False, "Failed to get camera list"

        count = self.get_camera_count()
        if count == 0:
            return False, "No cameras found"

        camera = self.get_camera(0)
        if not camera:
            return False, "Failed to get camera"

        name = self.get_device_info(camera)
        if not name:
            return False, "Failed to get device info"

        if not self.open_session(camera):
            return False, "Failed to open session"

        if not self.set_property_event_handler():
            return False, "Failed to set property event handler"

        return True, name
