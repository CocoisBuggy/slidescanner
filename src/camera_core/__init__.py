import ctypes
import os

from .err import EDS_ERR_OK, ERROR_CODE_NAMES
from .properties import EdsPropertyIDEnum


__all__ = ["EdsPropertyIDEnum", "EDS_ERR_OK", "ERROR_CODE_NAMES"]

# Load EDSDK library
lib_path = os.path.join(
    os.path.dirname(__file__),
    "..",
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
EdsStreamRef = EdsBaseRef
EdsImageRef = EdsStreamRef
EdsEvfImageRef = EdsBaseRef
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


# Callback types
EdsPropertyEventHandler = ctypes.CFUNCTYPE(
    EdsError, EdsPropertyEvent, EdsPropertyID, EdsUInt32, ctypes.c_void_p
)
EdsCameraAddedHandler = ctypes.CFUNCTYPE(EdsError, ctypes.c_void_p)

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
    ctypes.py_object,
]
edsdk.EdsGetPropertyData.restype = EdsError
edsdk.EdsGetPropertyData.argtypes = [
    EdsCameraRef,
    EdsPropertyID,
    EdsUInt32,
    EdsUInt32,
    ctypes.c_void_p,
]
edsdk.EdsSetCameraAddedHandler.restype = EdsError
edsdk.EdsSetCameraAddedHandler.argtypes = [EdsCameraAddedHandler, ctypes.c_void_p]

# Property event constants
kEdsPropertyEvent_PropertyChanged = 0x00000101

# Global references to avoid GC
_property_handler = None
_camera_added_handler = None


class CameraException(Exception):
    def __init__(self, msg: int | str):
        if isinstance(msg, str):
            super().__init__(msg)
        else:
            name = ERROR_CODE_NAMES.get(msg, f"Unknown error code {msg}")
            super().__init__(f"EDSDK Error code {msg} - {name}")
