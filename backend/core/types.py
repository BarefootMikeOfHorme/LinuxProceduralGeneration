"""
VaultMind Forge - Type System
Defines data types for type-safe node connections
"""

from enum import Enum
from typing import Set, Dict


class DataType(Enum):
    """Data types that can flow through node connections"""

    # Primitive types
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"

    # Media types
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MESH = "mesh"

    # AI/ML types
    MASK = "mask"
    LATENT = "latent"
    MODEL = "model"
    EMBEDDING = "embedding"

    # Structured types
    DICT = "dict"
    LIST = "list"

    # Special types
    ANY = "any"
    SEED = "seed"
    FILE_PATH = "file_path"

    def __str__(self):
        return self.value


# Type compatibility matrix
# Key: source type, Value: set of compatible target types
COMPATIBLE_TYPES: Dict[DataType, Set[DataType]] = {
    DataType.TEXT: {DataType.TEXT, DataType.ANY},
    DataType.NUMBER: {DataType.NUMBER, DataType.SEED, DataType.ANY},
    DataType.BOOLEAN: {DataType.BOOLEAN, DataType.ANY},

    DataType.IMAGE: {DataType.IMAGE, DataType.ANY},
    DataType.VIDEO: {DataType.VIDEO, DataType.ANY},
    DataType.AUDIO: {DataType.AUDIO, DataType.ANY},
    DataType.MESH: {DataType.MESH, DataType.ANY},

    # Mask can connect to image (grayscale image)
    DataType.MASK: {DataType.MASK, DataType.IMAGE, DataType.ANY},
    DataType.LATENT: {DataType.LATENT, DataType.ANY},
    DataType.MODEL: {DataType.MODEL, DataType.ANY},
    DataType.EMBEDDING: {DataType.EMBEDDING, DataType.ANY},

    DataType.DICT: {DataType.DICT, DataType.ANY},
    DataType.LIST: {DataType.LIST, DataType.ANY},

    DataType.SEED: {DataType.SEED, DataType.NUMBER, DataType.ANY},
    DataType.FILE_PATH: {DataType.FILE_PATH, DataType.TEXT, DataType.ANY},

    # ANY accepts everything
    DataType.ANY: set(DataType),
}


def can_connect(source_type: DataType, target_type: DataType) -> bool:
    """
    Check if a source output can connect to a target input.

    Args:
        source_type: Type of the source output
        target_type: Type of the target input

    Returns:
        True if connection is valid, False otherwise

    Examples:
        >>> can_connect(DataType.TEXT, DataType.TEXT)
        True
        >>> can_connect(DataType.IMAGE, DataType.TEXT)
        False
        >>> can_connect(DataType.IMAGE, DataType.ANY)
        True
        >>> can_connect(DataType.MASK, DataType.IMAGE)
        True
    """
    # Target accepts ANY - always compatible
    if target_type == DataType.ANY:
        return True

    # Check compatibility matrix
    compatible = COMPATIBLE_TYPES.get(source_type, set())
    return target_type in compatible


def get_type_color(data_type: DataType) -> str:
    """
    Get color hex code for visual representation of data type.
    Used in frontend for connection handles.

    Args:
        data_type: The data type

    Returns:
        Hex color string (e.g., "#55FF55")
    """
    colors = {
        DataType.TEXT: "#55FF55",       # Green
        DataType.NUMBER: "#5555FF",     # Blue
        DataType.BOOLEAN: "#FF55FF",    # Magenta

        DataType.IMAGE: "#FF5555",      # Red
        DataType.VIDEO: "#FF8855",      # Orange
        DataType.AUDIO: "#55FFFF",      # Cyan
        DataType.MESH: "#FFFF55",       # Yellow

        DataType.MASK: "#AAAAAA",       # Gray
        DataType.LATENT: "#AA55FF",     # Purple
        DataType.MODEL: "#FF55AA",      # Pink
        DataType.EMBEDDING: "#55AAFF",  # Light Blue

        DataType.DICT: "#AAFF55",       # Lime
        DataType.LIST: "#55FFAA",       # Mint

        DataType.ANY: "#FFFFFF",        # White
        DataType.SEED: "#FFAA55",       # Amber
        DataType.FILE_PATH: "#55AAAA",  # Teal
    }
    return colors.get(data_type, "#888888")


if __name__ == "__main__":
    # Quick tests
    print("Type Compatibility Tests:")
    print(f"TEXT → TEXT: {can_connect(DataType.TEXT, DataType.TEXT)}")
    print(f"IMAGE → TEXT: {can_connect(DataType.IMAGE, DataType.TEXT)}")
    print(f"IMAGE → ANY: {can_connect(DataType.IMAGE, DataType.ANY)}")
    print(f"MASK → IMAGE: {can_connect(DataType.MASK, DataType.IMAGE)}")
    print(f"NUMBER → SEED: {can_connect(DataType.NUMBER, DataType.SEED)}")
