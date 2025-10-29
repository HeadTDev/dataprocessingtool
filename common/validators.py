"""File validation utilities."""

import os
from pathlib import Path
from typing import List, Optional
import pandas as pd


class FileValidator:
    """Validates file existence and structure."""
    
    @staticmethod
    def validate_exists(path: Path) -> None:
        """
        Validate that a file exists.
        
        Args:
            path: Path to validate
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
    
    @staticmethod
    def validate_excel(path: Path, required_columns: Optional[List[str]] = None) -> None:
        """
        Validate an Excel file and optionally check for required columns.
        
        Args:
            path: Path to the Excel file
            required_columns: List of column names that must be present
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If required columns are missing
        """
        FileValidator.validate_exists(path)
        
        if required_columns:
            try:
                df = pd.read_excel(path, nrows=0)  # Read only headers
                missing = set(required_columns) - set(df.columns)
                if missing:
                    raise ValueError(
                        f"Excel file missing required columns: {missing}. "
                        f"Found columns: {list(df.columns)}"
                    )
            except Exception as e:
                if isinstance(e, ValueError) and "missing required columns" in str(e):
                    raise
                raise ValueError(f"Failed to read Excel file: {e}")
    
    @staticmethod
    def validate_pdf(path: Path) -> None:
        """
        Validate a PDF file.
        
        Args:
            path: Path to the PDF file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        FileValidator.validate_exists(path)
        if not str(path).lower().endswith('.pdf'):
            raise ValueError(f"File is not a PDF: {path}")
    
    @staticmethod
    def validate_directory(path: Path, create_if_missing: bool = False) -> None:
        """
        Validate that a directory exists.
        
        Args:
            path: Path to validate
            create_if_missing: If True, create the directory if it doesn't exist
            
        Raises:
            FileNotFoundError: If the directory doesn't exist and create_if_missing is False
        """
        if not path.exists():
            if create_if_missing:
                path.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"Directory not found: {path}")
        elif not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
