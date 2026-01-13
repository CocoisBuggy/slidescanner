import ctypes
import os

from .err import EDS_ERR_OK, ERROR_CODE_NAMES
from .properties import EdsPropertyIDEnum


__all__ = [
    "EdsPropertyIDEnum", "EDS_ERR_OK", "ERROR_CODE_NAMES",
    "EdsError", "EdsBaseRef", "EdsCameraListRef", "EdsCameraRef",
    "EdsEvfImageRef", "EdsStreamRef", "EdsDirectoryItemRef",
    "EdsInt32", "EdsUInt32", "EdsInt64", "EdsUInt64",
    "EdsPropertyID", "EdsPropertyEvent", "kEdsPropertyEvent_PropertyChanged",
    "EdsDeviceInfo", "EdsPropertyEventHandler", "EdsCameraAddedHandler",
    "edsdk", "CameraException"
]

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
EdsEvfImageRef = EdsBaseRef
EdsStreamRef = EdsBaseRef
EdsDirectoryItemRef = EdsBaseRef
EdsInt32 = ctypes.c_int32
EdsUInt32 = ctypes.c_uint32
EdsInt64 = ctypes.c_int64
EdsUInt64 = ctypes.c_uint64
EdsPropertyID = EdsUInt32
EdsPropertyEvent = EdsUInt32

# Property events
kEdsPropertyEvent_PropertyChanged = EdsPropertyEvent(0x00000101)


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
edsdk.EdsSetPropertyData.restype = EdsError
edsdk.EdsSetPropertyData.argtypes = [
    EdsCameraRef,
    EdsPropertyID,
    EdsInt32,
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

# Additional function prototypes
edsdk.EdsCreateEvfImageRef.restype = EdsError
edsdk.EdsCreateEvfImageRef.argtypes = [EdsStreamRef, ctypes.POINTER(EdsEvfImageRef)]
edsdk.EdsDownloadEvfImage.restype = EdsError
edsdk.EdsDownloadEvfImage.argtypes = [EdsCameraRef, EdsEvfImageRef]
edsdk.EdsCreateMemoryStream.restype = EdsError
edsdk.EdsCreateMemoryStream.argtypes = [EdsUInt64, ctypes.POINTER(EdsStreamRef)]
edsdk.EdsDownload.restype = EdsError
edsdk.EdsDownload.argtypes = [EdsBaseRef, EdsUInt64, EdsStreamRef]
edsdk.EdsGetPointer.restype = EdsError
edsdk.EdsGetPointer.argtypes = [EdsStreamRef, ctypes.POINTER(ctypes.c_void_p)]
edsdk.EdsGetLength.restype = EdsError
edsdk.EdsGetLength.argtypes = [EdsStreamRef, ctypes.POINTER(EdsUInt64)]


class CameraException(Exception):
    def __init__(self, msg: int | str):
        if isinstance(msg, str):
            super().__init__(msg)
        else:
            name = ERROR_CODE_NAMES.get(msg, f"Unknown error code {msg}")
            super().__init__(f"EDSDK Error code {msg} - {name}")
