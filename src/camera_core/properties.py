import ctypes
from enum import Enum
from threading import Event
from typing import Any, Callable

from .err import EDS_ERR_OK, CameraException
from .prop_values import AvEnum, EdsBatteryLevel2, ISOEnum, TvEnum
from .sdk import (
    EdsFocusInfo,
    EdsInt32,
    EdsPictureStyleDesc,
    EdsPoint,
    EdsRational,
    EdsRect,
    EdsTime,
    EdsUInt32,
    edsdk,
    kEdsDataType_FocusInfo,
    kEdsDataType_Int32,
    kEdsDataType_PictureStyleDesc,
    kEdsDataType_Point,
    kEdsDataType_Rational,
    kEdsDataType_Rect,
    kEdsDataType_String,
    kEdsDataType_Time,
    kEdsDataType_UInt32,
)


def battery_level_to_percentage(level: int) -> int | None:
    """Convert EDSDK battery level to percentage."""
    if level == EdsBatteryLevel2.AC.value:
        return 100  # AC power, treat as full
    elif level == EdsBatteryLevel2.Unknown.value:
        return None  # Unknown
    elif level == EdsBatteryLevel2.Error.value:
        return None  # Error
    elif level == EdsBatteryLevel2.Empty.value:
        return 0
    elif level == EdsBatteryLevel2.Low.value:
        return 10
    elif level == EdsBatteryLevel2.Quarter.value:
        return 25
    elif level == EdsBatteryLevel2.Half.value:
        return 50
    elif level == EdsBatteryLevel2.Hi.value:
        return 70
    elif level == EdsBatteryLevel2.Normal.value:
        return 100
    else:
        # Fallback for unknown values
        return None


def iso_to_human_readable(value: int) -> str:
    """Convert raw ISO value to human readable string."""
    try:
        iso = ISOEnum(value)
        if iso == ISOEnum.Auto:
            return "Auto"
        else:
            # Extract the ISO number from the enum name
            name = iso.name.replace("ISO_", "")
            if name.isdigit():
                return f"ISO {name}"
            return name
    except ValueError:
        return f"Unknown (0x{value:X})"


def tv_to_human_readable(value: int) -> str:
    """Convert raw shutter speed value to human readable string."""
    try:
        tv = TvEnum(value)
        if tv == TvEnum.Auto:
            return "Auto"
        elif tv == TvEnum.Bulb:
            return "Bulb"
        elif tv.name.startswith("SEC_"):
            # Extract seconds value
            sec = tv.name.replace("SEC_", "").replace("_", ".")
            return f'{sec}"'
        elif tv.name.startswith("SPEED_"):
            # Extract speed value (fraction of second)
            speed = tv.name.replace("SPEED_", "")
            return f'1/{speed}"'
        else:
            return tv.name
    except ValueError:
        return f"Unknown (0x{value:X})"


def av_to_human_readable(value: int) -> str:
    """Convert raw aperture value to human readable string."""
    try:
        av = AvEnum(value)
        if av == AvEnum.AUTO:
            return "Auto"
        elif av.name.startswith("F"):
            # Extract f-number (handle both F1_0 and F1.0 formats)
            f_num = av.name[1:]  # Remove 'F' prefix
            f_num = f_num.replace("_", ".")  # Replace underscores with dots
            return f"f/{f_num}"
        else:
            return av.name
    except ValueError:
        return f"Unknown (0x{value:X})"


class EdsPropertyEventKind(Enum):
    All = 0x100
    PropertyChanged = 0x101
    PropertyDescChanged = 0x102
    PropertyDescExChanged = 0x110


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
    PropertyChanged = 0x101


results: dict[EdsPropertyIDEnum, Any] = {}
waiting: dict[EdsPropertyIDEnum, Event] = {p: Event() for p in EdsPropertyIDEnum}
listeners: dict[EdsPropertyIDEnum, list[Callable]] = {p: [] for p in EdsPropertyIDEnum}


def _property_callback(event, property_id: int, param, context):
    """
    We ideally want a robust method by which we can notify our application
    when the camera actually CHANGES one of its attributes
    """
    global waiting, results
    try:
        property = EdsPropertyIDEnum(property_id)
        print(
            f"Got property change: {property} (event: {EdsPropertyEventKind(event)}, param: {param})"
        )
    except ValueError:
        print(
            f"Got property event change on prop_id: {property_id} (event: {EdsPropertyEventKind(event)}, param: {param}) "
            " but we do not have a corresponding understanding of this code in our enum"
        )
        return EDS_ERR_OK

    waiting[property].set()
    for listener in listeners[property]:
        listener(results.get(property))

    return EDS_ERR_OK


def _allocate_buffers(size, data_type):
    if data_type.value == kEdsDataType_UInt32:
        buffer = EdsUInt32()
        buffer_size = ctypes.sizeof(EdsUInt32)
    elif data_type.value == kEdsDataType_Int32:
        buffer = EdsInt32()
        buffer_size = ctypes.sizeof(EdsInt32)
    elif data_type.value == kEdsDataType_String:
        # For strings, use a reasonable buffer size
        buffer = ctypes.create_string_buffer(256)
        buffer_size = 256
    elif data_type.value == kEdsDataType_Rational:
        buffer = EdsRational()
        buffer_size = ctypes.sizeof(EdsRational)
    elif data_type.value == kEdsDataType_Point:
        buffer = EdsPoint()
        buffer_size = ctypes.sizeof(EdsPoint)
    elif data_type.value == kEdsDataType_Rect:
        buffer = EdsRect()
        buffer_size = ctypes.sizeof(EdsRect)
    elif data_type.value == kEdsDataType_Time:
        buffer = EdsTime()
        buffer_size = ctypes.sizeof(EdsTime)
    elif data_type.value == kEdsDataType_FocusInfo:
        buffer = EdsFocusInfo()
        buffer_size = ctypes.sizeof(EdsFocusInfo)
    elif data_type.value == kEdsDataType_PictureStyleDesc:
        buffer = EdsPictureStyleDesc()
        buffer_size = ctypes.sizeof(EdsPictureStyleDesc)
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
    if data_type.value == kEdsDataType_UInt32:
        raw_value = buffer.value
        # Special handling for properties that need conversion
        if property_id == EdsPropertyIDEnum.BatteryLevel.value:
            return battery_level_to_percentage(raw_value)
        elif property_id == EdsPropertyIDEnum.ISOSpeed.value:
            return iso_to_human_readable(raw_value)
        elif property_id == EdsPropertyIDEnum.Tv.value:
            return tv_to_human_readable(raw_value)
        elif property_id == EdsPropertyIDEnum.Av.value:
            return av_to_human_readable(raw_value)
        return raw_value
    elif data_type.value == kEdsDataType_Int32:
        return buffer.value
    elif data_type.value == kEdsDataType_String:
        return buffer.value.decode("utf-8").rstrip("\x00")  # type: ignore
    elif data_type.value == kEdsDataType_Rational:
        if hasattr(buffer, "numerator"):
            return {"numerator": buffer.numerator, "denominator": buffer.denominator}
        else:
            return buffer.value
    elif data_type.value == kEdsDataType_Point:
        if hasattr(buffer, "x"):
            return {"x": buffer.x, "y": buffer.y}
        else:
            return buffer.value
    elif data_type.value == kEdsDataType_Rect:
        if hasattr(buffer, "x"):
            return {
                "x": buffer.x,
                "y": buffer.y,
                "width": buffer.width,
                "height": buffer.height,
            }
        else:
            return buffer.value
    elif data_type.value == kEdsDataType_Time:
        if hasattr(buffer, "year"):
            return {
                "year": buffer.year,
                "month": buffer.month,
                "day": buffer.day,
                "hour": buffer.hour,
                "minute": buffer.minute,
                "second": buffer.second,
                "milliseconds": buffer.milliseconds,
            }
        else:
            return buffer.value
    elif data_type.value == kEdsDataType_FocusInfo:
        # Simplified - only returning basic info
        if hasattr(buffer, "imageRect"):
            return {"imageRect": buffer.imageRect, "pointNumber": buffer.pointNumber}
        else:
            return buffer.value
    elif data_type.value == kEdsDataType_PictureStyleDesc:
        if hasattr(buffer, "contrast"):
            return {
                "contrast": buffer.contrast,
                "sharpness": buffer.sharpness,
                "saturation": buffer.saturation,
                "colorTone": buffer.colorTone,
                "filterEffect": buffer.filterEffect,
                "toningEffect": buffer.toningEffect,
                "sharpFineness": buffer.sharpFineness,
                "sharpThreshold": buffer.sharpThreshold,
            }
        else:
            return buffer.value
    else:
        return buffer.value
