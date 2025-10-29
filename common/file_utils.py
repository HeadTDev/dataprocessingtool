"""File utility functions."""

import os
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def ensure_output_dir(base_path: Path, subdir: str = "output") -> Path:
    """
    Ensure output directory exists.
    
    Args:
        base_path: Base path (typically module directory)
        subdir: Subdirectory name (default: "output")
        
    Returns:
        Path to the output directory
    """
    output_dir = base_path / subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def safe_remove_dir(directory: Path, ignore_errors: bool = True) -> bool:
    """
    Safely remove a directory and its contents.
    
    Args:
        directory: Directory to remove
        ignore_errors: If True, log errors instead of raising them
        
    Returns:
        True if successfully removed, False otherwise
    """
    if not directory.exists():
        return True
    
    if not directory.is_dir():
        logger.warning(f"Path is not a directory: {directory}")
        return False
    
    try:
        shutil.rmtree(directory)
        logger.info(f"Removed directory: {directory}")
        return True
    except Exception as e:
        if ignore_errors:
            logger.error(f"Failed to remove directory {directory}: {e}")
            return False
        else:
            raise


def safe_remove_file(file_path: Path, ignore_errors: bool = True) -> bool:
    """
    Safely remove a file.
    
    Args:
        file_path: File to remove
        ignore_errors: If True, log errors instead of raising them
        
    Returns:
        True if successfully removed, False otherwise
    """
    if not file_path.exists():
        return True
    
    try:
        os.remove(file_path)
        logger.info(f"Removed file: {file_path}")
        return True
    except Exception as e:
        if ignore_errors:
            logger.error(f"Failed to remove file {file_path}: {e}")
            return False
        else:
            raise
