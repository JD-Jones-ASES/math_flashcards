"""
Version and build information for Math Flashcards
------------------------------------------------
This module provides centralized version information and metadata
for both development and executable builds.

License: MIT License

Copyright (c) 2024 JD Jones

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

import sys
import platform
from datetime import datetime
from typing import Dict, Any

# Version information
VERSION_MAJOR = 0
VERSION_MINOR = 8
VERSION_PATCH = 5
VERSION_TAG = "Beta"  # Can be alpha, beta, rc1, etc., or empty string for release
BUILD_NUMBER = "1"  # Incremented with each build

# Generate version string
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
if VERSION_TAG:
    VERSION = f"{VERSION}-{VERSION_TAG}"
if BUILD_NUMBER:
    VERSION = f"{VERSION}+{BUILD_NUMBER}"

# Application metadata
APP_NAME = "Math Flashcards"
APP_AUTHOR = "JD Jones"
APP_ID = "org.mathflashcards.app"  # Unique application identifier
APP_LICENSE = "MIT"
APP_REPOSITORY = "https://github.com/JD-Jones-ASES/math_flashcards.git"
APP_COPYRIGHT = f"Copyright © {datetime.now().year} {APP_AUTHOR}"

THIRD_PARTY_TEXT = """This project uses open-source components:
- Pygame (LGPL v2.1)
- PyInstaller (GPL with linking exception) 
- Setuptools (MIT)
See README.md for full attribution and license details."""

def get_build_info() -> Dict[str, Any]:
    """Get comprehensive build information"""
    return {
        "version": VERSION,
        "build_number": BUILD_NUMBER,
        "build_date": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "machine": platform.machine(),
        "license": APP_LICENSE,
        "repository": APP_REPOSITORY
    }

def is_frozen() -> bool:
    """Check if running as a frozen executable"""
    return getattr(sys, 'frozen', False)

def get_application_path() -> str:
    """Get the application base path, handling both frozen and development cases"""
    if is_frozen():
        return sys._MEIPASS  # type: ignore  # pylint: disable=protected-access
    return sys.path[0]

# Optional: Include digital signature information
SIGNATURE_INFO = {
    "signed": False,
    "signer": None,
    "timestamp": None,
    "certificate_info": None
}

# Windows-specific metadata (for executable builds)
WINDOWS_METADATA = {
    "CompanyName": "JD Jones",
    "FileDescription": "Open Source Interactive Math Practice Application",
    "FileVersion": VERSION,
    "InternalName": "mathflashcards",
    "LegalCopyright": APP_COPYRIGHT,
    "OriginalFilename": "MathFlashcards.exe",
    "ProductName": APP_NAME,
    "ProductVersion": VERSION
}