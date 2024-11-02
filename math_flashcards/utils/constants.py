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
    """Color scheme for the application"""
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WIN_GRAY: Tuple[int, int, int] = (240, 240, 240)
    HIGHLIGHT: Tuple[int, int, int] = (51, 153, 255)
    LIGHT_HIGHLIGHT: Tuple[int, int, int] = (229, 241, 251)
    TEXT_GRAY: Tuple[int, int, int] = (96, 96, 96)
    BORDER_GRAY: Tuple[int, int, int] = (204, 204, 204)
    SUCCESS: Tuple[int, int, int] = (40, 167, 69)
    ERROR: Tuple[int, int, int] = (220, 53, 69)
    
    # Difficulty level colors
    INTRO_MODE: Tuple[int, int, int] = (70, 80, 181)    # Light green
    BASIC_MODE: Tuple[int, int, int] = (92, 184, 92)      # Standard green
    MEDIUM_MODE: Tuple[int, int, int] = (240, 173, 78)    # Warning yellow
    HARD_MODE: Tuple[int, int, int] = (217, 83, 79)       # Danger red
    CUSTOM_MODE: Tuple[int, int, int] = (138, 43, 226)    # Purple

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
        
        # Player list dialog dimensions
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
        """Calculate triangle size based on window dimensions"""
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
    
    # Difficulty configurations
    DIFFICULTY_SETTINGS = {
        DifficultyLevel.INTRO: {
            'number_range': (1, 7),  # Focus on smaller numbers for beginners
            'operators': ['+'],  # Start with just addition
            'max_digits': 2,
            'allows_negative': False,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 49,  # 7 x 7
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
            'number_range': (1, 12),  # Standard multiplication table range
            'operators': ['+', '-'],  # Add subtraction
            'max_digits': 2,
            'allows_negative': False,
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 144,  # 12 x 12
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
            'number_range': (1, 20),  # Extended range
            'operators': ['+', '-', '*'],  # Add multiplication
            'max_digits': 2,
            'allows_negative': True,  # Allow negatives but only in subtraction results
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 400,  # 20 x 20
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
            'number_range': (1, 50),  # Challenging range
            'operators': ['+', '-', '*', '/'],  # All operations
            'max_digits': 2,
            'allows_negative': True,  # Allow negatives in addition/subtraction
            'requires_decimals': False,
            'division_rules': {
                'max_dividend': 2500,  # 50 x 50
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
            'number_range': (1, 20),  # Default values, will be updated based on analytics
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
        'mastery_threshold': 0.8,       # Threshold for considering a fact mastered
        'response_time_threshold': 3000, # Time threshold for fast responses (ms)
        'save_interval': 20,            # Interval for auto-saving progress (seconds)
        'streak_milestone': 10          # Milestone for achievement tracking
    }
    
    # Animation timings
    ANIMATION = {
        'cursor_blink_time': 530,       # Cursor blink interval (ms)
        'feedback_duration': 1000,      # Duration to show correct/incorrect feedback (ms)
        'transition_time': 300          # Time for UI transitions (ms)
    }
