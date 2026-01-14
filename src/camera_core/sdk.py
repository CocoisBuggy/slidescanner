import ctypes
import os

# Define constants before library loading
kEdsPropertyEvent_PropertyChanged = 0x00000101
kEdsCameraCommand_TakePicture = 0x00000000
kEdsObjectEvent_DirItemCreated = 0x00000204

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

try:
    edsdk = ctypes.CDLL(lib_path)
except OSError:
    # Handle case where library is not available (e.g., testing environment)
    edsdk = None

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
EdsObjectEventHandler = ctypes.CFUNCTYPE(
    EdsError, EdsUInt32, EdsBaseRef, ctypes.c_void_p
)
EdsCameraAddedHandler = ctypes.CFUNCTYPE(EdsError, ctypes.c_void_p)

# Function prototypes
if edsdk is not None:
    edsdk.EdsInitializeSDK.restype = EdsError
    edsdk.EdsTerminateSDK.restype = EdsError
    edsdk.EdsTerminateSDK.argtypes = []
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
    edsdk.EdsSendCommand.restype = EdsError
    edsdk.EdsSendCommand.argtypes = [EdsCameraRef, EdsUInt32, EdsInt32]
    edsdk.EdsSetObjectEventHandler.restype = EdsError
    edsdk.EdsSetObjectEventHandler.argtypes = [
        EdsCameraRef,
        EdsUInt32,
        EdsObjectEventHandler,
        ctypes.c_void_p,
    ]

# Property event constants
kEdsPropertyEvent_PropertyChanged = 0x00000101

# Camera commands
kEdsCameraCommand_TakePicture = 0x00000000

# Object events
kEdsObjectEvent_DirItemCreated = 0x00000204

# Global references to avoid GC
_property_handler = None
_object_handler = None
_camera_added_handler = None

# Additional function prototypes
if edsdk is not None:
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
    edsdk.EdsCreateFileStream.restype = EdsError
    edsdk.EdsCreateFileStream.argtypes = [
        ctypes.c_char_p,
        EdsUInt32,
        EdsUInt32,
        ctypes.POINTER(EdsStreamRef),
    ]
    edsdk.EdsDownloadComplete.restype = EdsError
    edsdk.EdsDownloadComplete.argtypes = [EdsBaseRef]
    edsdk.EdsGetEvent.restype = EdsError
    edsdk.EdsGetEvent.argtypes = [EdsCameraRef, ctypes.POINTER(EdsUInt32)]
