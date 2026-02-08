from pathlib import Path
from typing import Optional


def validate_file_path(file_path: str) -> Path:
    """
    Validate that a file path exists and is a file.

    Args:
        file_path: Path to validate

    Returns:
        Path object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is not a file
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return path


def validate_directory(dir_path: str) -> Path:
    """
    Validate that a directory path exists and is a directory.

    Args:
        dir_path: Path to validate

    Returns:
        Path object

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If path is not a directory
    """
    path = Path(dir_path)

    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")

    return path
