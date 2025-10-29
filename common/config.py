"""Configuration management for the application."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    
    # Default multiplier for merkantil processor
    DEFAULT_MULTIPLIER: float = 1.27
    
    # Auto updater settings
    GITHUB_OWNER: str = "HeadTDev"
    GITHUB_REPO: str = "dataprocessingtool"
    UPDATE_CHECK_TIMEOUT: int = 30  # Increased from 8 to 30 seconds
    
    # UI settings
    BUTTON_WIDTH: int = 300
    BUTTON_HEIGHT: int = 40
    
    # Fuzzy matching threshold
    FUZZY_MATCH_THRESHOLD: float = 0.80
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @classmethod
    def get_output_dir(cls, module_name: str) -> Path:
        """Get output directory for a specific module."""
        base_dir = Path(__file__).parent.parent / module_name / "output"
        return base_dir
    
    @classmethod
    def get_icon_path(cls, icon_name: str) -> Path:
        """Get path to an icon file."""
        return Path(__file__).parent.parent / icon_name
