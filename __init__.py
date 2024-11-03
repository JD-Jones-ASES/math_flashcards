"""
Math Flashcards Game Package
----------------------------
A comprehensive math practice application with analytics and adaptive learning.

License: MIT License
Copyright (c) 2024 JD Jones
"""

from math_flashcards.utils.version import (
    VERSION, APP_NAME, APP_AUTHOR, APP_COPYRIGHT,
    APP_LICENSE, APP_REPOSITORY
)

__version__ = VERSION
__author__ = APP_AUTHOR
__copyright__ = APP_COPYRIGHT
__license__ = APP_LICENSE

# Expose version information at package level
__all__ = ['__version__', '__author__', '__copyright__', '__license__']