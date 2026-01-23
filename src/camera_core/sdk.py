import ctypes
import os

# Define constants before library loading
EDS_MAX_NAME = 256
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
EdsChar = ctypes.c_char
EdsPropertyID = EdsUInt32
EdsPropertyEvent = EdsUInt32
EdsDataType = EdsUInt32

# Property events
kEdsPropertyEvent_All = EdsPropertyEvent(0x00000101)
kEdsPropertyEvent_PropertyChanged = EdsPropertyEvent(0x00000101)


# Define EdsDeviceInfo struct
class EdsDeviceInfo(ctypes.Structure):
    _fields_ = [
        ("szPortName", ctypes.c_char * 256),
        ("szDeviceDescription", ctypes.c_char * 256),
        ("deviceSubType", EdsUInt32),
        ("reserved", EdsUInt32),
    ]


# Define EdsRational struct
class EdsRational(ctypes.Structure):
    _fields_ = [
        ("numerator", EdsInt32),
        ("denominator", EdsUInt32),
    ]


# Define EdsPoint struct
class EdsPoint(ctypes.Structure):
    _fields_ = [
        ("x", EdsInt32),
        ("y", EdsInt32),
    ]


# Define EdsRect struct
class EdsRect(ctypes.Structure):
    _fields_ = [
        ("x", EdsInt32),
        ("y", EdsInt32),
        ("width", EdsInt32),
        ("height", EdsInt32),
    ]


# Define EdsCapacity struct
class EdsCapacity(ctypes.Structure):
    _fields_ = [
        ("numberOfFreeClusters", EdsInt32),
        ("bytesPerSector", EdsInt32),
        ("reset", ctypes.c_bool),
    ]


# Define EdsDirectoryItemInfo struct
class EdsDirectoryItemInfo(ctypes.Structure):
    _fields_ = [
        ("size", EdsUInt64),
        ("isFolder", ctypes.c_bool),
        ("groupID", EdsUInt32),
        ("option", EdsUInt32),
        ("szFileName", EdsChar * EDS_MAX_NAME),
        ("format", EdsUInt32),
        ("dateTime", EdsUInt32),
    ]


# Define EdsTime struct
class EdsTime(ctypes.Structure):
    _fields_ = [
        ("year", EdsUInt32),
        ("month", EdsUInt32),
        ("day", EdsUInt32),
        ("hour", EdsUInt32),
        ("minute", EdsUInt32),
        ("second", EdsUInt32),
        ("milliseconds", EdsUInt32),
    ]


# Define EdsFocusInfo struct (simplified, may need expansion)
class EdsFocusInfo(ctypes.Structure):
    _fields_ = [
        ("imageRect", EdsRect),
        ("pointNumber", EdsUInt32),
        # Additional fields would be needed for complete implementation
    ]


# Define EdsPictureStyleDesc struct
class EdsPictureStyleDesc(ctypes.Structure):
    _fields_ = [
        ("contrast", EdsInt32),
        ("sharpness", EdsUInt32),
        ("saturation", EdsInt32),
        ("colorTone", EdsInt32),
        ("filterEffect", EdsUInt32),
        ("toningEffect", EdsUInt32),
        ("sharpFineness", EdsUInt32),
        ("sharpThreshold", EdsUInt32),
    ]


# Callback types
EdsPropertyEventHandler = ctypes.CFUNCTYPE(
    EdsError, EdsPropertyEvent, EdsPropertyID, EdsUInt32, ctypes.c_void_p
)
EdsObjectEventHandler = ctypes.CFUNCTYPE(
    EdsError, EdsUInt32, EdsBaseRef, ctypes.c_void_p
)
EdsStateEventHandler = ctypes.CFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, ctypes.c_void_p)
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
    edsdk.EdsGetPropertySize.restype = EdsError
    edsdk.EdsGetPropertySize.argtypes = [
        EdsBaseRef,
        EdsPropertyID,
        EdsInt32,
        ctypes.POINTER(EdsDataType),
        ctypes.POINTER(EdsUInt32),
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
    edsdk.EdsSetCameraStateEventHandler.restype = EdsError
    edsdk.EdsSetCameraStateEventHandler.argtypes = [
        EdsCameraRef,
        EdsUInt32,
        EdsStateEventHandler,
        ctypes.py_object,
    ]

# Property event constants
kEdsPropertyEvent_PropertyChanged = 0x00000101

# Camera commands
kEdsCameraCommand_TakePicture = 0x00000000
kEdsCameraCommand_PressShutterButton = 0x00000004
kEdsCameraCommand_ShutterButton_Completely_NonAF = 0x00010003
kEdsCameraCommand_ShutterButton_OFF = 0x00000000
kEdsCameraCommand_DoEvfAf = 0x00000102
kEdsCameraCommand_ShutterButton_Halfway = 0x00000001

# Object events
kEdsObjectEvent_All = 0x00000200
kEdsObjectEvent_DirItemCreated = 0x00000204
kEdsObjectEvent_DirItemRequestTransfer = 0x00000208

# State events
kEdsStateEvent_All = 0x00000300
kEdsStateEvent_Shutdown = 0x00000301
kEdsStateEvent_JobStatusChanged = 0x00000302
kEdsStateEvent_WillSoonShutDown = 0x00000303
kEdsStateEvent_ShutDownTimerUpdate = 0x00000304
kEdsStateEvent_CaptureError = 0x00000305
kEdsStateEvent_InternalError = 0x00000306
kEdsStateEvent_AfResult = 0x00000309

# Image types
kEdsImageType_Unknown = 0x00000000
kEdsImageType_Jpeg = 0x00000001
kEdsImageType_CRW = 0x00000002
kEdsImageType_RAW = 0x00000004
kEdsImageType_CR2 = 0x00000006
kEdsImageType_HEIF = 0x00000008

# Object formats
kEdsObjectFormat_CR3 = 0xB108

# Data types
kEdsDataType_Unknown = 0
kEdsDataType_Bool = 1
kEdsDataType_String = 2
kEdsDataType_Int8 = 3
kEdsDataType_UInt8 = 6
kEdsDataType_Int16 = 4
kEdsDataType_UInt16 = 7
kEdsDataType_Int32 = 8
kEdsDataType_UInt32 = 9
kEdsDataType_Int64 = 10
kEdsDataType_UInt64 = 11
kEdsDataType_Float = 12
kEdsDataType_Double = 13
kEdsDataType_ByteBlock = 14
kEdsDataType_Rational = 20
kEdsDataType_Point = 21
kEdsDataType_Rect = 22
kEdsDataType_Time = 23
kEdsDataType_Bool_Array = 30
kEdsDataType_Int8_Array = 31
kEdsDataType_Int16_Array = 32
kEdsDataType_Int32_Array = 33
kEdsDataType_UInt8_Array = 34
kEdsDataType_UInt16_Array = 35
kEdsDataType_UInt32_Array = 36
kEdsDataType_Rational_Array = 37
kEdsDataType_FocusInfo = 101
kEdsDataType_PictureStyleDesc = 102

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
    edsdk.EdsDownload.argtypes = [EdsDirectoryItemRef, EdsUInt64, EdsStreamRef]
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
    edsdk.EdsSetCapacity.restype = EdsError
    edsdk.EdsSetCapacity.argtypes = [EdsCameraRef, EdsCapacity]
    edsdk.EdsGetDirectoryItemInfo.restype = EdsError
    edsdk.EdsGetDirectoryItemInfo.argtypes = [
        EdsDirectoryItemRef,
        ctypes.POINTER(EdsDirectoryItemInfo),
    ]
    edsdk.EdsCopyData.restype = EdsError
    edsdk.EdsCopyData.argtypes = [EdsStreamRef, EdsUInt64, EdsStreamRef]
    edsdk.EdsGetEvent.restype = EdsError
    edsdk.EdsGetEvent.argtypes = [EdsCameraRef, ctypes.POINTER(EdsUInt32)]
