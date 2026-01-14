import io
import os
import subprocess
import tempfile
from typing import Optional
from .picture import CassetteItem

from PIL import Image
from PIL.ExifTags import TAGS

import piexif


def add_metadata_to_image(
    image_data: bytes,
    cassette_item: CassetteItem,
    image_format: int | None = None,
    filepath: str | None = None,
) -> bytes:
    """
    Add metadata (date, comment, rating) to image data based on format.

    Supports JPEG, HEIF (limited metadata), and writes XMP sidecars for RAW formats.

    Args:
        image_data: Raw image data as bytes
        cassette_item: CassetteItem containing metadata to add
        image_format: Image format code from camera SDK (see format_to_extension in camera.py)
        filepath: Full path to where the image will be saved (needed for XMP sidecar creation)

    Returns:
        Image data with metadata added, or original data if metadata writing fails
    """
    print("METADATA TO ADD TO IMAGE:")
    print(f"  Date: {cassette_item.date}")
    print(f"  Label: {cassette_item.label}")
    print(f"  Stars: {cassette_item.stars}")
    print(f"  Cassette: {cassette_item.name}")
    print(f"  Format: 0x{image_format:08X}" if image_format else "  Format: Unknown")

    # Validate image data before processing
    if not image_data or len(image_data) < 100:
        print("Invalid image data: too small or empty")
        return image_data

    # Format-specific handling
    if image_format is None:
        # Try auto-detection for backward compatibility
        if image_data.startswith(b"\xff\xd8\xff"):
            image_format = 0x00000001  # JPEG
        elif image_data.startswith(b"\x00\x00\x00\x18ftyp"):
            image_format = 0x00000008  # HEIF
        else:
            print("Unknown image format, returning original data")
            return image_data

    # Handle RAW formats based on their EXIF support
    if image_format in [0x00000006]:  # CR2 - can be handled by PIL
        return _add_embedded_metadata(image_data, cassette_item, image_format)
    elif image_format in [0xB108, 0x0000B108]:  # CR3 - use exiftool
        _update_cr3_metadata(image_data, cassette_item, filepath)
        return image_data
    elif image_format in [0x00000002, 0x00000004]:  # CRW, older RAW - use XMP sidecar
        _create_xmp_sidecar(image_data, cassette_item, filepath)
        return image_data

    # Handle JPEG and HEIF with embedded metadata
    if image_format in [0x00000001, 0x00000008]:  # JPEG or HEIF
        return _add_embedded_metadata(image_data, cassette_item, image_format)

    # Unknown format, return original
    print(f"Unsupported format 0x{image_format:08X}, returning original data")
    return image_data


def _update_cr3_metadata(
    image_data: bytes, cassette_item: CassetteItem, filepath: str | None = None
) -> None:
    """Update CR3 metadata using exiftool subprocess."""
    print(f"Updating CR3 metadata using exiftool")

    if not filepath:
        print("No filepath provided for CR3 metadata update")
        return

    try:
        # Check if exiftool is available
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("exiftool not available, creating XMP sidecar instead")
        _create_xmp_sidecar(image_data, cassette_item, filepath)
        return

    # Prepare metadata for exiftool
    date_str = (
        cassette_item.date.strftime("%Y:%m:%d %H:%M:%S") if cassette_item.date else ""
    )
    description = cassette_item.label or ""
    rating = cassette_item.stars or 0
    copyright = f"Cassette: {cassette_item.name}" if cassette_item.name else ""

    # Build exiftool command
    cmd = [
        "exiftool",
        "-overwrite_original",
        f"-DateTimeOriginal={date_str}",
        f"-CreateDate={date_str}",
        f"-ModifyDate={date_str}",
        f"-Description={description}",
        f"-ImageDescription={description}",
        f"-Rating={rating}",
        f"-Copyright={copyright}",
        "-XPSubject=Slide Scanner",
        filepath,
    ]

    print(f"Running exiftool command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"exiftool return code: {result.returncode}")
        print(f"exiftool stdout: {result.stdout}")
        if result.stderr:
            print(f"exiftool stderr: {result.stderr}")

        if result.returncode == 0:
            print(f"CR3 metadata updated successfully: {filepath}")
        else:
            print(f"exiftool failed: {result.stderr}")
            # Fallback to XMP sidecar
            _create_xmp_sidecar(image_data, cassette_item, filepath)
    except Exception as e:
        print(f"Failed to update CR3 metadata: {e}")
        # Fallback to XMP sidecar
        _create_xmp_sidecar(image_data, cassette_item, filepath)


def _create_xmp_sidecar(
    image_data: bytes, cassette_item: CassetteItem, filepath: str | None = None
) -> None:
    """Create XMP sidecar file for RAW files that don't support embedded EXIF (CRW, older RAW)."""
    print(f"Creating XMP sidecar metadata for RAW file without embedded EXIF support")

    if not filepath:
        print("No filepath provided for XMP sidecar creation")
        return

    # Create XMP file path
    xmp_filepath = filepath.rsplit(".", 1)[0] + ".xmp"

    # Create proper XMP XML structure
    date_str = cassette_item.date.strftime("%Y-%m-%d") if cassette_item.date else ""
    time_str = cassette_item.date.strftime("%H:%M:%S") if cassette_item.date else ""
    datetime_str = f"{date_str}T{time_str}" if date_str and time_str else date_str

    xmp_content = f"""<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about=""
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:xmp="http://ns.adobe.com/xap/1.0/"
            xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/">
            <dc:title>
                <rdf:Alt>
                    <rdf:li xml:lang="x-default">{cassette_item.label or ''}</rdf:li>
                </rdf:Alt>
            </dc:title>
            <dc:description>
                <rdf:Alt>
                    <rdf:li xml:lang="x-default">Cassette: {cassette_item.name or ''}</rdf:li>
                </rdf:Alt>
            </dc:description>
            <dc:date>
                <rdf:Seq>
                    <rdf:li>{datetime_str}</rdf:li>
                </rdf:Seq>
            </dc:date>
            <xmp:Rating>{cassette_item.stars or 0}</xmp:Rating>
            <photoshop:Category>Slide Scanner</photoshop:Category>
            <photoshop:Credit>{cassette_item.name or ''}</photoshop:Credit>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

    try:
        # Write XMP file
        with open(xmp_filepath, "w", encoding="utf-8") as f:
            f.write(xmp_content)
        print(f"XMP sidecar created: {xmp_filepath}")
    except Exception as e:
        print(f"Failed to create XMP sidecar: {e}")


def _add_embedded_metadata(
    image_data: bytes, cassette_item: CassetteItem, image_format: int
) -> bytes:
    """Add metadata to JPEG/HEIF/CR2/CR3 files using PIL/Pillow and piexif."""
    try:
        # Try to use PIL/Pillow if available in the environment
        try:
            # Load the image with better error handling
            try:
                image = Image.open(io.BytesIO(image_data))
                # For JPEG/HEIF, verify the format
                if image_format in [0x00000001, 0x00000008]:
                    image.verify()
                    # Need to reopen after verify
                    image = Image.open(io.BytesIO(image_data))
            except Exception as img_error:
                print(f"Cannot identify image file: {img_error}")
                return image_data

            # Get existing EXIF data
            exif_dict = image.getexif() if hasattr(image, "getexif") else {}

            # Add/modify EXIF tags
            if cassette_item.date:
                date_str = cassette_item.date.strftime("%Y:%m:%d %H:%M:%S")

                # Find DateTime tag (306)
                for tag_id, tag_name in TAGS.items():
                    if tag_name == "DateTime":
                        exif_dict[tag_id] = date_str
                        break

            # Add ImageDescription
            if cassette_item.label:
                for tag_id, tag_name in TAGS.items():
                    if tag_name == "ImageDescription":
                        exif_dict[tag_id] = cassette_item.label
                        break

            # Add Copyright with cassette name
            if cassette_item.name:
                for tag_id, tag_name in TAGS.items():
                    if tag_name == "Copyright":
                        exif_dict[tag_id] = f"Cassette: {cassette_item.name}"
                        break

            # Try to save with EXIF data
            if hasattr(exif_dict, "tobytes"):
                output_buffer = io.BytesIO()
                image.save(
                    output_buffer, format="JPEG", exif=exif_dict.tobytes(), quality=95
                )
                print("EXIF metadata added successfully using Pillow")
                return output_buffer.getvalue()
            elif hasattr(exif_dict, "save"):
                # For newer Pillow versions
                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", exif=exif_dict, quality=95)
                print("EXIF metadata added successfully using Pillow")
                return output_buffer.getvalue()

        except ImportError:
            print("PIL/Pillow not available, skipping EXIF writing")

        # Try using piexif if available
        try:
            # Load existing EXIF if available
            try:
                exif_dict = piexif.load(image_data)
            except:
                exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "thumbnail": None}

            # Add metadata
            if cassette_item.date:
                date_str = cassette_item.date.strftime("%Y:%m:%d %H:%M:%S")
                if hasattr(piexif.ExifIFD, "DateTimeOriginal"):
                    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_str
                if hasattr(piexif.ImageIFD, "DateTime"):
                    exif_dict["0th"][piexif.ImageIFD.DateTime] = date_str

            if cassette_item.label:
                if hasattr(piexif.ImageIFD, "ImageDescription"):
                    exif_dict["0th"][
                        piexif.ImageIFD.ImageDescription
                    ] = cassette_item.label

            if cassette_item.name:
                if hasattr(piexif.ImageIFD, "Copyright"):
                    exif_dict["0th"][
                        piexif.ImageIFD.Copyright
                    ] = f"Cassette: {cassette_item.name}"

            if cassette_item.stars and 1 <= cassette_item.stars <= 5:
                if hasattr(piexif.ExifIFD, "Rating"):
                    exif_dict["Exif"][piexif.ExifIFD.Rating] = cassette_item.stars

            # Convert and save
            exif_bytes = piexif.dump(exif_dict)
            image = Image.open(io.BytesIO(image_data))
            output_buffer = io.BytesIO()
            image.save(output_buffer, format="JPEG", exif=exif_bytes, quality=95)
            print("EXIF metadata added successfully using piexif")
            return output_buffer.getvalue()

        except ImportError:
            print("piexif not available, skipping EXIF writing")

    except Exception as e:
        print(f"Warning: Failed to add metadata to image: {e}")

    # Return original image data if EXIF writing fails or libraries not available
    print("Returning original image data without EXIF modifications")
    return image_data


def get_star_rating_from_exif(image_data: bytes) -> Optional[int]:
    """
    Extract star rating from image EXIF data.

    Args:
        image_data: JPEG image data as bytes

    Returns:
        Star rating (1-5) or None if not found
    """
    try:
        # Try using Pillow first
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            image = Image.open(io.BytesIO(image_data))
            if hasattr(image, "getexif"):
                exif_dict = image.getexif()

                # Try to find Rating tag
                for tag_id, tag_name in TAGS.items():
                    if tag_name == "Rating":
                        if tag_id in exif_dict:
                            rating = exif_dict[tag_id]
                            return rating if 1 <= rating <= 5 else None
        except ImportError:
            pass

        # Try using piexif
        try:
            import piexif

            exif_dict = piexif.load(image_data)

            if hasattr(
                piexif.ExifIFD, "Rating"
            ) and piexif.ExifIFD.Rating in exif_dict.get("Exif", {}):
                rating = exif_dict["Exif"][piexif.ExifIFD.Rating]
                return rating if 1 <= rating <= 5 else None

        except ImportError:
            pass

        return None

    except Exception:
        return None
