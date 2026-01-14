import ctypes
import os
import time
from threading import Event

from .picture import CassetteItem
from .settings import Settings

from .camera_core import (
    EDS_ERR_OK,
    CameraException,
    EdsCameraListRef,
    EdsCameraRef,
    EdsDeviceInfo,
    EdsDirectoryItemInfo,
    EdsEvfImageRef,
    EdsObjectEventHandler,
    EdsPropertyEventHandler,
    EdsPropertyIDEnum,
    EdsStreamRef,
    EdsUInt32,
    EdsUInt64,
    _property_callback,
    edsdk,
    kEdsCameraCommand_PressShutterButton,
    kEdsCameraCommand_ShutterButton_Completely_NonAF,
    kEdsCameraCommand_ShutterButton_OFF,
    kEdsCameraCommand_DoEvfAf,
    kEdsCameraCommand_ShutterButton_Halfway,
    kEdsObjectEvent_All,
    kEdsObjectEvent_DirItemRequestTransfer,
    kEdsPropertyEvent_PropertyChanged,
)
from .camera_core.properties import waiting


def needs_sdk(inner):
    def wrapper(self, *args, **kwargs):
        if not self.initialized.is_set() or not self._edsdk_available():
            raise CameraException("SDK is not initialized")

        return inner(self, *args, **kwargs)

    return wrapper


# Global references for callbacks
_global_camera_manager = None
_global_shared_state = None
_queued_photo_request: CassetteItem | None = None


# Map format to file extension
format_to_extension = {
    0x00000000: ".jpg",  # kEdsImageType_Unknown
    0x00000001: ".jpg",  # kEdsImageType_Jpeg
    0x00000002: ".crw",  # kEdsImageType_CRW
    0x00000004: ".raw",  # kEdsImageType_RAW
    0x00000006: ".cr2",  # kEdsImageType_CR2
    0x00000008: ".heif",  # kEdsImageType_HEIF
    0xB108: ".cr3",  # kEdsObjectFormat_CR3
}


# Object event callback (for image capture events)
def _object_callback(event, object_ref, context):
    global _global_camera_manager, _queued_photo_request
    print(f"Got object event from camera: {event}, {object_ref}")

    if event == kEdsObjectEvent_DirItemRequestTransfer:
        print("Camera requesting image transfer!")

        if _global_camera_manager is not None:
            try:
                # Download the image
                if _queued_photo_request is None:
                    raise Exception("No queued request")

                filename = _global_camera_manager.download_image(
                    object_ref,
                    _queued_photo_request,
                )

                print(f"Successfully downloaded image: {filename}")
            except Exception as e:
                print(f"Failed to download image: {e}")

            _queued_photo_request = None
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

                self.set_property_value(EdsPropertyIDEnum.SaveTo, 2)  # Host = PC only
                print("Set save destination to PC")

                # When saving to Host, set capacity to indicate available space
                from .camera_core.sdk import EdsCapacity

                capacity = EdsCapacity(
                    numberOfFreeClusters=0x7FFFFFFF, bytesPerSector=0x1000, reset=True
                )
                err = edsdk.EdsSetCapacity(self.camera, capacity)
                if err != EDS_ERR_OK:
                    print(f"Failed to set capacity: {err}")
                else:
                    print("Set capacity for host storage")

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
            kEdsObjectEvent_All,
            _object_handler,
            ctypes.c_void_p(0),
        )

        return err == EDS_ERR_OK

    @needs_sdk
    def get_property_value(self, property_id):
        value = EdsUInt32()
        err = edsdk.EdsGetPropertyData(
            self.camera,
            property_id,
            0,
            ctypes.sizeof(EdsUInt32),
            ctypes.byref(value),
        )

        if err == EDS_ERR_OK:
            return value.value

        return None

    @needs_sdk
    def set_property_value(self, property_id: EdsPropertyIDEnum, value):
        waiting[property_id].clear()

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
    def focus(self):
        """Perform auto-focus and wait for focus completion."""

        print("Starting auto-focus...")

        # Clear any previous focus state events
        focus_events = [EdsPropertyIDEnum.FocusInfo, EdsPropertyIDEnum.AfLockState]

        for event in focus_events:
            if event in waiting:
                waiting[event].clear()

        # Send focus command (half-press shutter button to trigger AF)
        err = edsdk.EdsSendCommand(
            self.camera,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_Halfway,
        )

        if err != EDS_ERR_OK:
            # Try alternative EVF AF command if half-press fails
            print("Half-press failed, trying EVF AF command...")
            err = edsdk.EdsSendCommand(
                self.camera,
                kEdsCameraCommand_DoEvfAf,
                1,  # AF ON
            )

            if err != EDS_ERR_OK:
                raise CameraException(f"Failed to start auto-focus: {err}")

        # Wait for focus completion (wait for property changes)
        focus_completed = False
        timeout = 5.0  # 5 second timeout

        for event in focus_events:
            if event in waiting:
                print(f"Waiting for focus event: {event}")
                if waiting[event].wait(timeout):
                    print(f"Focus event received: {event}")
                    focus_completed = True
                    break
                else:
                    print(f"Timeout waiting for focus event: {event}")

        # Release the shutter button
        err = edsdk.EdsSendCommand(
            self.camera,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_OFF,
        )

        if err != EDS_ERR_OK:
            print(f"Warning: Failed to release shutter button: {err}")

        if focus_completed:
            print("Auto-focus completed successfully")
            return True
        else:
            print("Auto-focus may not have completed properly")
            return False

    @needs_sdk
    def take_picture(self, req: CassetteItem):
        """Take a picture using the camera."""
        global _queued_photo_request
        print("Taking picture...")

        if _queued_photo_request is not None:
            raise Exception("We are still waiting for the last photo to resolve")

        _queued_photo_request = req

        # Use PressShutter instead of TakePicture command for better compatibility
        err = edsdk.EdsSendCommand(
            self.camera,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_Completely_NonAF,
        )

        if err != EDS_ERR_OK:
            # Release the shutter button
            edsdk.EdsSendCommand(
                self.camera,
                kEdsCameraCommand_PressShutterButton,
                kEdsCameraCommand_ShutterButton_OFF,
            )
            raise CameraException(err)

        # Release the shutter button
        err = edsdk.EdsSendCommand(
            self.camera,
            kEdsCameraCommand_PressShutterButton,
            kEdsCameraCommand_ShutterButton_OFF,
        )
        if err != EDS_ERR_OK:
            raise CameraException(err)

        print("Picture taken successfully")
        return True

    @needs_sdk
    def download_image(
        self,
        directory_item,
        photo_req: CassetteItem,
        shared_state=None,
    ):
        """Download an image from the camera."""
        settings = Settings()
        print("Downloading image...")

        if photo_req is None:
            raise Exception("No request context")

        # Get directory item information
        dir_item_info = EdsDirectoryItemInfo()
        err = edsdk.EdsGetDirectoryItemInfo(directory_item, ctypes.byref(dir_item_info))
        if err != EDS_ERR_OK:
            raise CameraException(err)

        print(
            f"Downloading file: {dir_item_info.szFileName.decode('utf-8')}, "
            f"size: {dir_item_info.size}, format: {dir_item_info.format}"
        )

        # Get appropriate extension, default to .jpg
        extension = format_to_extension.get(dir_item_info.format, ".jpg")

        print(
            f"Detected format: 0x{dir_item_info.format:08X},"
            f" using extension: {extension}"
        )

        # Create output directory if it doesn't exist
        outdir = os.path.join(settings.photo_location, (photo_req.name or "default"))

        os.makedirs(
            outdir,
            exist_ok=True,
        )

        # Generate filename using cassette name + sequential number
        global _global_shared_state
        if _global_shared_state:
            filename = _global_shared_state.get_next_slide_filename(extension)
        else:
            # Fallback if no state available
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}{extension}"

        filepath = os.path.join(
            outdir,
            filename,
        )

        print(f"Target filepath: {filepath}")
        # Download to memory stream first, then copy to file
        print("Creating memory stream for download...")
        mem_stream = EdsStreamRef()
        err = edsdk.EdsCreateMemoryStream(EdsUInt64(0), ctypes.byref(mem_stream))
        if err != EDS_ERR_OK:
            print(f"Failed to create memory stream: {err}")
            raise CameraException(err)

        try:
            print("Downloading to memory stream...")
            # Download the image to memory
            err = edsdk.EdsDownload(directory_item, dir_item_info.size, mem_stream)
            if err != EDS_ERR_OK:
                print(f"EdsDownload to memory failed: {err}")
                raise CameraException(err)

            print("Download to memory completed, calling EdsDownloadComplete...")
            # Complete the download
            err = edsdk.EdsDownloadComplete(directory_item)
            if err != EDS_ERR_OK:
                print(f"EdsDownloadComplete failed: {err}")
                raise CameraException(err)

            # Get the data from memory stream
            pointer = ctypes.c_void_p()
            length = EdsUInt64()
            edsdk.EdsGetPointer(mem_stream, ctypes.byref(pointer))
            edsdk.EdsGetLength(mem_stream, ctypes.byref(length))

            print(f"Downloaded data size: {length.value} bytes")

            # Extract the data
            data = ctypes.string_at(pointer, length.value)

            # For CR3 files, write first then add metadata using exiftool
            if dir_item_info.format in [0xB108, 0x0000B108]:
                # Write to file first
                print(f"Writing {len(data)} bytes to file: {filepath}")
                with open(filepath, "wb") as f:
                    f.write(data)

                # Add metadata using exiftool after file is written
                print("Adding metadata to image...")
                try:
                    from .exif_utils import add_metadata_to_image

                    add_metadata_to_image(
                        data, photo_req, dir_item_info.format, filepath
                    )
                    print("Metadata added successfully")
                except Exception as e:
                    print(f"Warning: Failed to add metadata: {e}")

                data_with_metadata = data
            else:
                # For other formats, add metadata then write
                print("Adding metadata to image...")
                try:
                    from .exif_utils import add_metadata_to_image

                    data_with_metadata = add_metadata_to_image(
                        data, photo_req, dir_item_info.format, filepath
                    )
                    print("Metadata added successfully")
                except Exception as e:
                    print(f"Warning: Failed to add metadata: {e}")
                    data_with_metadata = data

                # Write to file manually
                print(f"Writing {len(data_with_metadata)} bytes to file: {filepath}")
                with open(filepath, "wb") as f:
                    f.write(data_with_metadata)

            # Check if file was actually written
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"File created: {filepath}, size: {file_size} bytes")
                if file_size == 0:
                    print("WARNING: File is still 0 bytes!")
                else:
                    print(f"SUCCESS: File has {file_size} bytes")
            else:
                print(f"ERROR: File was not created: {filepath}")

            print(f"Image downloaded successfully: {filename}")

            # Notify that picture was taken successfully
            if _global_shared_state:
                _global_shared_state.notify_picture_taken(filename)

            return filename

        finally:
            edsdk.EdsRelease(mem_stream)
