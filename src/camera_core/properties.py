from enum import Enum

import ctypes
from threading import Event
from typing import Any, Callable
from .err import EDS_ERR_OK, CameraException
from .sdk import (
    edsdk,
    EdsUInt32,
    EdsInt32,
)


# Property IDs
class EdsPropertyIDEnum(Enum):
    Unknown = 0x0000FFFF
    ProductName = 0x00000002
    OwnerName = 0x00000004
    MakerName = 0x00000005
    DateTime = 0x00000006
    FirmwareVersion = 0x00000007
    BatteryLevel = 0x00000008
    SaveTo = 0x0000000B
    CurrentStorage = 0x0000000C
    CurrentFolder = 0x0000000D
    BatteryQuality = 0x00000010
    BodyIDEx = 0x00000015
    HDDirectoryStructure = 0x00000020
    ImageQuality = 0x00000100
    Orientation = 0x00000102
    ICCProfile = 0x00000103
    FocusInfo = 0x00000104
    WhiteBalance = 0x00000106
    ColorTemperature = 0x00000107
    WhiteBalanceShift = 0x00000108
    ColorSpace = 0x0000010D
    PictureStyle = 0x00000114
    PictureStyleDesc = 0x00000115
    PictureStyleCaption = 0x00000200
    GPSVersionID = 0x00000800
    GPSLatitudeRef = 0x00000801
    GPSLatitude = 0x00000802
    GPSLongitudeRef = 0x00000803
    GPSLongitude = 0x00000804
    GPSAltitudeRef = 0x00000805
    GPSAltitude = 0x00000806
    GPSTimeStamp = 0x00000807
    GPSSatellites = 0x00000808
    GPSStatus = 0x00000809
    GPSMapDatum = 0x00000812
    GPSDateStamp = 0x0000081D
    AEMode = 0x00000400
    DriveMode = 0x00000401
    ISOSpeed = 0x00000402
    MeteringMode = 0x00000403
    AFMode = 0x00000404
    Av = 0x00000405
    Tv = 0x00000406
    ExposureCompensation = 0x00000407
    FocalLength = 0x00000409
    AvailableShots = 0x0000040A
    Bracket = 0x0000040B
    WhiteBalanceBracket = 0x0000040C
    LensName = 0x0000040D
    AEBracket = 0x0000040E
    FEBracket = 0x0000040F
    ISOBracket = 0x00000410
    NoiseReduction = 0x00000411
    FlashOn = 0x00000412
    RedEye = 0x00000413
    FlashMode = 0x00000414
    LensStatus = 0x00000416
    Artist = 0x00000418
    Copyright = 0x00000419
    AEModeSelect = 0x00000436
    PowerZoom_Speed = 0x00000444
    ColorFilter = 0x0000047F
    DigitalZoomSetting = 0x00000477
    AfLockState = 0x00000480
    BrightnessSetting = 0x00000483
    IBIS_HighResoShot = 0x000004E0
    StillFileNameSetting = 0x000004E1
    StillFileNameUserSet1 = 0x000004E2
    StillFileNameUserSet2 = 0x000004E3
    StillFolderName = 0x000004E4
    MovieFileNameIndex = 0x000004E5
    MovieFileNameReelNo = 0x000004E6
    MovieFileNameClipNo = 0x000004E7
    MovieFileNameUserDef = 0x000004E8
    Evf_OutputDevice = 0x00000500
    Evf_Mode = 0x00000501
    Evf_WhiteBalance = 0x00000502
    Evf_ColorTemperature = 0x00000503
    Evf_DepthOfFieldPreview = 0x00000504
    Evf_Zoom = 0x00000507
    Evf_ZoomPosition = 0x00000508
    Evf_Histogram = 0x0000050A
    Evf_ImagePosition = 0x0000050B
    Evf_HistogramStatus = 0x0000050C
    Evf_AFMode = 0x0000050E
    Record = 0x00000510
    Evf_HistogramY = 0x00000515
    Evf_HistogramR = 0x00000516
    Evf_HistogramG = 0x00000517
    Evf_HistogramB = 0x00000518
    Evf_CoordinateSystem = 0x00000540
    Evf_ZoomRect = 0x00000541
    Evf_ImageClipRect = 0x00000545
    Evf_PowerZoom_CurPosition = 0x00000550
    Evf_PowerZoom_MaxPosition = 0x00000551
    Evf_PowerZoom_MinPosition = 0x00000552
    UTCTime = 0x01000016
    TimeZone = 0x01000017
    SummerTimeSetting = 0x01000018
    ManualWhiteBalanceData = 0x01000204
    TempStatus = 0x01000415
    MirrorLockUpState = 0x01000421
    FixedMovie = 0x01000422
    MovieParam = 0x01000423
    Aspect = 0x01000431
    ContinuousAfMode = 0x01000433
    MirrorUpSetting = 0x01000438
    MovieServoAf = 0x0100043E
    AutoPowerOffSetting = 0x0100045E
    AFEyeDetect = 0x01000455
    FocusShiftSetting = 0x01000457
    MovieHFRSetting = 0x0100045D
    AFTrackingObject = 0x01000468
    RegisterFocusEdge = 0x0100046C
    DriveFocusToEdge = 0x0100046D
    FocusPosition = 0x0100046E
    StillMovieDivideSetting = 0x01000470
    CardExtension = 0x01000471
    MovieCardExtension = 0x01000472
    StillCurrentMedia = 0x01000473
    MovieCurrentMedia = 0x01000474
    ApertureLockSetting = 0x01000476
    LensIsSetting = 0x010004C0
    ScreenDimmerTime = 0x010004C1
    ScreenOffTime = 0x010004C2
    ViewfinderOffTime = 0x010004C3
    Evf_ClickWBCoeffs = 0x01000506
    EVF_RollingPitching = 0x01000544
    Evf_VisibleRect = 0x01000546
    MovieRecVolume_IntMic = 0x01000489
    MovieRecVolume_ExtMic = 0x0100048A
    MovieRecVolume_Acc = 0x0100048B
    MovieParamEx = 0x011004C6
    SlowFastMode = 0x010004C7
    Flash_Firing = 0x0000200D
    Flash_Target = 0x0000201E
    DC_Zoom = 0x00000600
    DC_Strobe = 0x00000601
    LensBarrelStatus = 0x00000605


results: dict[EdsPropertyIDEnum, Any] = {}
waiting: dict[EdsPropertyIDEnum, Event] = {p: Event() for p in EdsPropertyIDEnum}
listeners: dict[EdsPropertyIDEnum, list[Callable]] = {p: [] for p in EdsPropertyIDEnum}


def _property_callback(event, property_id: int, param, context):
    """Extract property data from camera when properties change."""
    global waiting, results
    property = EdsPropertyIDEnum(property_id)
    print(f"Got property change: {property} (event: {event}, param: {param})")

    # Extract the camera manager from context
    if context:
        try:
            manager = ctypes.cast(context, ctypes.py_object).value
            if hasattr(manager, "camera") and manager.camera:
                # Get the actual property data
                try:
                    data = _extract_property_data(manager.camera, property_id)
                    results[property] = data
                    print(f"  Extracted data: {data}")
                except Exception as e:
                    print(f"  Failed to extract property data: {e}")
        except Exception as e:
            print(f"  Failed to extract manager from context: {e}")

    if property in waiting:
        waiting[property].set()

        for listener in listeners[property]:
            listener(results.get(property))

    return EDS_ERR_OK


def _allocate_buffers(size, data_type):
    if data_type.value == 3:  # kEdsDataType_UInt32
        buffer = EdsUInt32()
        buffer_size = ctypes.sizeof(EdsUInt32)
    elif data_type.value == 2:  # kEdsDataType_Int32
        buffer = EdsInt32()
        buffer_size = ctypes.sizeof(EdsInt32)
    elif data_type.value == 6:  # kEdsDataType_String
        # For strings, use a reasonable buffer size
        buffer = ctypes.create_string_buffer(256)
        buffer_size = 256
    else:
        # Default to UInt32 for unknown types
        buffer = EdsUInt32()
        buffer_size = ctypes.sizeof(EdsUInt32)

    return buffer, buffer_size


def _extract_property_data(camera, property_id):
    """Extract property data from camera for the given property ID."""
    # First get the property size and data type
    size = EdsUInt32()
    data_type = EdsUInt32()
    err = edsdk.EdsGetPropertySize(
        camera, property_id, 0, ctypes.byref(size), ctypes.byref(data_type)
    )
    if err != EDS_ERR_OK:
        raise CameraException(f"Failed to get property size: {err}")

    # Allocate buffer based on data type and size
    buffer, buffer_size = _allocate_buffers(size, data_type)

    # Get the actual property data
    err = edsdk.EdsGetPropertyData(
        camera,
        property_id,
        0,
        buffer_size,
        ctypes.byref(buffer),
    )

    if err != EDS_ERR_OK:
        raise CameraException(f"Failed to get property data: {err}")

    # Extract the value based on data type
    if data_type.value == 3:  # UInt32
        return buffer.value
    elif data_type.value == 2:  # Int32
        return buffer.value
    elif data_type.value == 6:  # String
        return buffer.value.decode("utf-8").rstrip("\x00")  # type: ignore
    else:
        return buffer.value
