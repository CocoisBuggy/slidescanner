import ctypes
import datetime
import logging
import os
from threading import Event

from src.exif_utils import add_metadata_to_image
from src.picture import CassetteItem
from src.settings import Settings

log = logging.getLogger(__name__)

from . import (
    EDS_ERR_OK,
    CameraException,
    EdsDirectoryItemInfo,
    edsdk,
    kEdsObjectEvent_DirItemRequestTransfer,
)
from .object_events import EdsObjectEventEnum
from .sdk import EdsBaseRef, EdsStreamRef, EdsUInt64

# Global references for callbacks
queued_photo_request: CassetteItem | None = None
last_downloaded_photo: tuple[CassetteItem, str] | None = None
downloaded_image_available = Event()
format_to_extension = {
    0x00000000: ".jpg",  # kEdsImageType_Unknown
    0x00000001: ".jpg",  # kEdsImageType_Jpeg
    0x00000002: ".crw",  # kEdsImageType_CRW
    0x00000004: ".raw",  # kEdsImageType_RAW
    0x00000006: ".cr2",  # kEdsImageType_CR2
    0x00000008: ".heif",  # kEdsImageType_HEIF
    0xB108: ".cr3",  # kEdsObjectFormat_CR3
}
object_event = {e: Event() for e in EdsObjectEventEnum}


def set_next_photo_request(item: CassetteItem):
    global queued_photo_request

    if queued_photo_request is not None:
        raise Exception(
            "We cannot queue a next photo request while one is already unfulfilled"
        )

    queued_photo_request = item
    downloaded_image_available.clear()


def clear_photo_request():
    global queued_photo_request
    queued_photo_request = None
    downloaded_image_available.set()


def get_current_photo_request() -> CassetteItem | None:
    return queued_photo_request


def download_image(directory_item: EdsBaseRef, photo_req: CassetteItem) -> str | None:
    # First of all, grab the settings so we know where to save files
    settings = Settings()

    log.info("Downloading image...")
    # Get directory item information
    dir_item_info = EdsDirectoryItemInfo()
    err = edsdk.EdsGetDirectoryItemInfo(
        directory_item,
        ctypes.byref(dir_item_info),
    )

    if err != EDS_ERR_OK:
        raise CameraException(err)

    log.info(
        f"Downloading file: {dir_item_info.szFileName.decode('utf-8')}, "
        f"size: {dir_item_info.size}, format: {dir_item_info.format}"
    )

    # Get appropriate extension, default to .jpg
    extension = format_to_extension.get(dir_item_info.format, ".jpg")

    log.info(
        f"Detected format: 0x{dir_item_info.format:08X}, using extension: {extension}"
    )

    # Create output directory if it doesn't exist
    outdir = os.path.join(settings.photo_location, (photo_req.name or "default"))

    os.makedirs(
        outdir,
        exist_ok=True,
    )

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}{extension}"

    filepath = os.path.join(
        outdir,
        filename,
    )

    log.info(f"Target filepath: {filepath}")
    # Download to memory stream first, then copy to file
    log.debug("Creating memory stream for download...")
    mem_stream = EdsStreamRef()
    err = edsdk.EdsCreateMemoryStream(EdsUInt64(0), ctypes.byref(mem_stream))
    if err != EDS_ERR_OK:
        log.error(f"Failed to create memory stream: {err}")
        raise CameraException(err)

    try:
        log.debug("Downloading to memory stream...")
        # Download the image to memory
        err = edsdk.EdsDownload(directory_item, dir_item_info.size, mem_stream)
        if err != EDS_ERR_OK:
            log.error(f"EdsDownload to memory failed: {err}")
            raise CameraException(err)

        log.debug("Download to memory completed, calling EdsDownloadComplete...")
        # Complete the download
        err = edsdk.EdsDownloadComplete(directory_item)
        if err != EDS_ERR_OK:
            log.error(f"EdsDownloadComplete failed: {err}")
            raise CameraException(err)

        # Get the data from memory stream
        pointer = ctypes.c_void_p()
        length = EdsUInt64()
        edsdk.EdsGetPointer(mem_stream, ctypes.byref(pointer))
        edsdk.EdsGetLength(mem_stream, ctypes.byref(length))

        log.debug(f"Downloaded data size: {length.value} bytes")

        # Extract the data
        data = ctypes.string_at(pointer, length.value)

        # For CR3 files, write first then add metadata using exiftool
        if dir_item_info.format in [0xB108, 0x0000B108]:
            # Write to file first
            log.debug(f"Writing {len(data)} bytes to file: {filepath}")
            with open(filepath, "wb") as f:
                f.write(data)

            # Add metadata using exiftool after file is written
            log.debug("Adding metadata to image...")
            try:
                add_metadata_to_image(data, photo_req, dir_item_info.format, filepath)
                log.debug("Metadata added successfully")
            except Exception as e:
                log.warning(f"Failed to add metadata: {e}")

            data_with_metadata = data
        else:
            # For other formats, add metadata then write
            log.debug("Adding metadata to image...")
            try:
                data_with_metadata = add_metadata_to_image(
                    data, photo_req, dir_item_info.format, filepath
                )
                log.info("Metadata added successfully")
            except Exception as e:
                log.warning(f"Failed to add metadata: {e}")
                data_with_metadata = data

            # Write to file manually
            log.debug(f"Writing {len(data_with_metadata)} bytes to file: {filepath}")
            with open(filepath, "wb") as f:
                f.write(data_with_metadata)

        # Check if file was actually written
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            log.info(f"File created: {filepath}, size: {file_size} bytes")
            if file_size == 0:
                log.warning("File is still 0 bytes!")
            else:
                log.info(f"SUCCESS: File has {file_size} bytes")
        else:
            log.error(f"ERROR: File was not created: {filepath}")

        return filename
    finally:
        edsdk.EdsRelease(mem_stream)


# Object event callback (for image capture events)
def _object_callback(event, object_ref, context):
    global queued_photo_request, last_downloaded_photo, object_event
    enum = EdsObjectEventEnum(event)

    log.debug(f"Got object event from camera: {enum} {event}, {object_ref}")
    object_event[enum].set()

    if event == kEdsObjectEvent_DirItemRequestTransfer:
        log.info("Camera requesting image transfer!")

        try:
            # Download the image
            req = get_current_photo_request()
            if req is None:
                raise Exception("No queued request")

            filename = download_image(object_ref, req)
            if not filename:
                raise Exception("Filename was none-ish")

            downloaded_image_available.set()
            last_downloaded_photo = (req, filename)

            log.info(f"Successfully downloaded image: {filename}")
        except Exception as e:
            log.error(f"Failed to download image: {e}")

        clear_photo_request()

    return EDS_ERR_OK
