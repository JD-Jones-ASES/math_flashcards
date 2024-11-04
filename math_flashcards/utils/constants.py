from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict

# Window Constants
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600


class DifficultyLevel(Enum):
    """Difficulty levels for the game"""
    INTRO = "Intro"
    BASIC = "Basic"
    MEDIUM = "Medium"
    HARD = "Hard"
    CUSTOM = "Custom"


@dataclass
class Colors:
    """Color scheme for the application with navy blue theme"""
    # Base colors
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    BLACK: Tuple[int, int, int] = (0, 0, 0)

    # Primary navy colors
    NAVY_DARKEST: Tuple[int, int, int] = (16, 24, 48)  # Very dark navy
    NAVY_DARK: Tuple[int, int, int] = (25, 45, 85)  # Dark navy
    NAVY_PRIMARY: Tuple[int, int, int] = (35, 65, 115)  # Primary navy
    NAVY_LIGHT: Tuple[int, int, int] = (45, 85, 145)  # Light navy
    NAVY_LIGHTEST: Tuple[int, int, int] = (65, 135, 255)  # Very light navy/blue

    # UI Elements
    WIN_GRAY: Tuple[int, int, int] = (245, 248, 250)  # Slight blue tint
    HIGHLIGHT: Tuple[int, int, int] = (65, 135, 255)  # Electric blue
    LIGHT_HIGHLIGHT: Tuple[int, int, int] = (229, 241, 251)
    TEXT_GRAY: Tuple[int, int, int] = (96, 116, 136)  # Bluish gray
    BORDER_GRAY: Tuple[int, int, int] = (204, 214, 224)  # Bluish border

    # Status colors
    SUCCESS: Tuple[int, int, int] = (40, 167, 145)  # Teal-leaning green
    ERROR: Tuple[int, int, int] = (220, 53, 89)  # Warm red

    # Difficulty level colors
    INTRO_MODE: Tuple[int, int, int] = (65, 135, 255)  # Light navy
    BASIC_MODE: Tuple[int, int, int] = (40, 167, 145)  # Teal
    MEDIUM_MODE: Tuple[int, int, int] = (120, 145, 255)  # Periwinkle
    HARD_MODE: Tuple[int, int, int] = (180, 55, 155)  # Royal purple
    CUSTOM_MODE: Tuple[int, int, int] = (255, 145, 95)  # Coral orange


@dataclass
class Layout:
    """Layout configuration with dynamic sizing"""

    def __init__(self):
        # Initialize with default values
        self._window_width = MIN_WINDOW_WIDTH
        self._window_height = MIN_WINDOW_HEIGHT

        # Sidebar dimensions
        self.SIDEBAR_WIDTH = 220
        self.HEADER_HEIGHT = 28
        self.PADDING = 6
        self.BUTTON_HEIGHT = 32
        self.LIST_ITEM_HEIGHT = 32

        # Spacing between sections
        self.SECTION_SPACING = 12

        # Stats panel dimensions
        self.STATS_PANEL_HEIGHT = 180

        # Dialog dimensions
        self.DIALOG_WIDTH = 500
        self.DIALOG_HEIGHT = 600
        self.DIALOG_INPUT_HEIGHT = 40
        self.DIALOG_BUTTON_HEIGHT = 40
        self.DIALOG_LIST_ITEM_HEIGHT = 45
        self.DIALOG_MAX_VISIBLE_PLAYERS = 10

        # Game elements
        self.TRIANGLE_SIZE = self._calculate_triangle_size()
        self.INPUT_BOX_WIDTH = 100
        self.INPUT_BOX_HEIGHT = 40
        self.BUTTON_WIDTH = 120

    def _calculate_triangle_size(self) -> int:
        return min(320, (self._window_width - self.SIDEBAR_WIDTH) // 2)

    @property
    def WINDOW_WIDTH(self) -> int:
        return max(self._window_width, MIN_WINDOW_WIDTH)

    @WINDOW_WIDTH.setter
    def WINDOW_WIDTH(self, value: int):
        self._window_width = max(value, MIN_WINDOW_WIDTH)
        self.TRIANGLE_SIZE = self._calculate_triangle_size()

    @property
    def WINDOW_HEIGHT(self) -> int:
        return max(self._window_height, MIN_WINDOW_HEIGHT)

    @WINDOW_HEIGHT.setter
    def WINDOW_HEIGHT(self, value: int):
        self._window_height = max(value, MIN_WINDOW_HEIGHT)

    @property
    def content_width(self) -> int:
        return self.WINDOW_WIDTH - self.SIDEBAR_WIDTH

    @property
    def content_center_x(self) -> int:
        return self.SIDEBAR_WIDTH + (self.content_width // 2)

    @property
    def content_center_y(self) -> int:
        return self.WINDOW_HEIGHT // 2


class GameSettings:
    """Game configuration settings"""
    # Font sizes
    FONT_SIZES = {
        'small': 24,
        'normal': 32,
        'large': 48
    }

    # Operation symbols for display
    OPERATION_SYMBOLS = {
        '+': '+',
        '-': '−',  # Using minus sign instead of hyphen
        '*': '×',
        '/': '÷'
    }

    # Animation timings and settings
    ANIMATION = {
        # UI Animation timings
        'cursor_blink_time': 400,
        'feedback_duration': 1500,
        'transition_time': 300,

        # Background Symbol Animation Settings
        'background_symbol_speed': 5000,  # Time between updates (ms)
        'background_fade_time': 3000,  # Longer fade time for testing
        'background_symbol_count': 3,  # More symbols for visibility
        'background_symbol_size_min': 36,  # Larger minimum size
        'background_symbol_size_max': 72,  # Larger maximum size
        'background_animations_enabled': True,

        # Available Symbols (limited set for testing)
        'background_symbols': [
            '+', '-', '×', '÷', '=',  # Basic operations only for now
        ],

        # Symbol Colors (temporarily removed alpha component)
        'background_symbol_colors': [
            (180, 190, 220),  # Light navy blue
            (160, 180, 230),  # Lighter blue
            (140, 160, 210)  # Slightly darker blue
        ]
    }

    # Difficulty configurations
    DIFFICULTY_SETTINGS = {
        DifficultyLevel.INTRO: {
            'number_range': (1, 7),
            'operators': ['+'],
            'max_digits': 2,
            'allows_negative': False,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 49,
                'max_divisor': 7,
                'max_quotient': 7
            },
            'multiplication_rules': {
                'max_factor': 7,
                'max_product': 49
            },
            'color': Colors.INTRO_MODE
        },
        DifficultyLevel.BASIC: {
            'number_range': (1, 12),
            'operators': ['+', '-'],
            'max_digits': 2,
            'allows_negative': False,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 144,
                'max_divisor': 12,
                'max_quotient': 12
            },
            'multiplication_rules': {
                'max_factor': 12,
                'max_product': 144
            },
            'color': Colors.BASIC_MODE
        },
        DifficultyLevel.MEDIUM: {
            'number_range': (1, 20),
            'operators': ['+', '-', '*'],
            'max_digits': 2,
            'allows_negative': True,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 400,
                'max_divisor': 20,
                'max_quotient': 20
            },
            'multiplication_rules': {
                'max_factor': 20,
                'max_product': 400
            },
            'color': Colors.MEDIUM_MODE
        },
        DifficultyLevel.HARD: {
            'number_range': (1, 50),
            'operators': ['+', '-', '*', '/'],
            'max_digits': 2,
            'allows_negative': True,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 2500,
                'max_divisor': 50,
                'max_quotient': 50
            },
            'multiplication_rules': {
                'max_factor': 50,
                'max_product': 2500
            },
            'color': Colors.HARD_MODE
        },
        DifficultyLevel.CUSTOM: {
            'number_range': (1, 20),
            'operators': ['+'],
            'max_digits': 2,
            'allows_negative': False,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 400,
                'max_divisor': 20,
                'max_quotient': 20
            },
            'multiplication_rules': {
                'max_factor': 20,
                'max_product': 400
            },
            'color': Colors.CUSTOM_MODE
        }
    }

    # Analytics settings
    ANALYTICS = {
        'min_problems_for_custom': 20,  # Minimum problems needed to unlock custom mode
        'mastery_threshold': 0.8,  # Threshold for considering a fact mastered
        'response_time_threshold': 3000,  # Time threshold for fast responses (ms)
        'save_interval': 20,  # Interval for auto-saving progress (seconds)
        'streak_milestone': 10  # Milestone for achievement tracking
    }