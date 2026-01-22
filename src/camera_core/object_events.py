from enum import Enum


class EdsObjectEventEnum(Enum):
    """Object events for camera file system operations."""

    # All events (wildcard)
    All = 0x00000200

    # Volume (storage device) events
    VolumeInfoChanged = 0x00000201  # Volume information changed
    VolumeUpdateItems = 0x00000202  # Volume items updated
    VolumeAdded = 0x0000020C  # New volume added
    VolumeRemoved = 0x0000020D  # Volume removed

    # Folder events
    FolderUpdateItems = 0x00000203  # Folder contents updated

    # Directory item (file) events
    DirItemCreated = 0x00000204  # New file created
    DirItemRemoved = 0x00000205  # File deleted
    DirItemInfoChanged = 0x00000206  # File metadata changed
    DirItemContentChanged = 0x00000207  # File content changed

    # Transfer events
    DirItemRequestTransfer = 0x00000208  # File ready for download
    DirItemRequestTransferDT = 0x00000209  # Direct transfer requested
    DirItemCancelTransferDT = 0x0000020A  # Direct transfer cancelled


# Object event descriptions for debugging and UI
OBJECT_EVENT_DESCRIPTIONS = {
    EdsObjectEventEnum.All: "All object events",
    EdsObjectEventEnum.VolumeInfoChanged: "Volume information changed",
    EdsObjectEventEnum.VolumeUpdateItems: "Volume items updated",
    EdsObjectEventEnum.VolumeAdded: "Volume added",
    EdsObjectEventEnum.VolumeRemoved: "Volume removed",
    EdsObjectEventEnum.FolderUpdateItems: "Folder contents updated",
    EdsObjectEventEnum.DirItemCreated: "File created",
    EdsObjectEventEnum.DirItemRemoved: "File deleted",
    EdsObjectEventEnum.DirItemInfoChanged: "File metadata changed",
    EdsObjectEventEnum.DirItemContentChanged: "File content changed",
    EdsObjectEventEnum.DirItemRequestTransfer: "File ready for transfer",
    EdsObjectEventEnum.DirItemRequestTransferDT: "Direct transfer requested",
    EdsObjectEventEnum.DirItemCancelTransferDT: "Direct transfer cancelled",
}


def get_object_event_description(event: EdsObjectEventEnum) -> str:
    """Get human-readable description for an object event."""
    return OBJECT_EVENT_DESCRIPTIONS.get(event, f"Unknown event: {event}")


def is_transfer_event(event: EdsObjectEventEnum) -> bool:
    """Check if an event is related to file transfer operations."""
    return event in [
        EdsObjectEventEnum.DirItemRequestTransfer,
        EdsObjectEventEnum.DirItemRequestTransferDT,
        EdsObjectEventEnum.DirItemCancelTransferDT,
    ]


def is_volume_event(event: EdsObjectEventEnum) -> bool:
    """Check if an event is related to volume/storage operations."""
    return event in [
        EdsObjectEventEnum.VolumeInfoChanged,
        EdsObjectEventEnum.VolumeUpdateItems,
        EdsObjectEventEnum.VolumeAdded,
        EdsObjectEventEnum.VolumeRemoved,
    ]


def is_file_event(event: EdsObjectEventEnum) -> bool:
    """Check if an event is related to file operations."""
    return event in [
        EdsObjectEventEnum.DirItemCreated,
        EdsObjectEventEnum.DirItemRemoved,
        EdsObjectEventEnum.DirItemInfoChanged,
        EdsObjectEventEnum.DirItemContentChanged,
    ]


# Commonly used event combinations
TRANSFER_EVENTS = [
    EdsObjectEventEnum.DirItemRequestTransfer,
    EdsObjectEventEnum.DirItemRequestTransferDT,
]

STORAGE_EVENTS = [
    EdsObjectEventEnum.VolumeInfoChanged,
    EdsObjectEventEnum.VolumeUpdateItems,
    EdsObjectEventEnum.VolumeAdded,
    EdsObjectEventEnum.VolumeRemoved,
    EdsObjectEventEnum.FolderUpdateItems,
]

FILE_SYSTEM_EVENTS = [
    EdsObjectEventEnum.DirItemCreated,
    EdsObjectEventEnum.DirItemRemoved,
    EdsObjectEventEnum.DirItemInfoChanged,
    EdsObjectEventEnum.DirItemContentChanged,
    EdsObjectEventEnum.FolderUpdateItems,
]
