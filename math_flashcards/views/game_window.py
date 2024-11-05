from typing import Dict, Optional, Tuple, Any
import pygame
import random
import math
from datetime import datetime
from math_flashcards.utils.constants import Colors, Layout, DifficultyLevel, GameSettings
from math_flashcards.models.player import Player
from math_flashcards.views.login_dialog import LoginDialog
from math_flashcards.views.ui_components import Button, ListItem, StatsPanel
from math_flashcards.utils.version import (
    VERSION, APP_NAME, APP_AUTHOR, APP_COPYRIGHT,
    APP_LICENSE, APP_REPOSITORY, VERSION
)

class GameWindow:
    """Main game window handling all display elements"""
    def __init__(self, width: int, height: int):
        """Initialize the game window"""
        pygame.init()
        self.layout = Layout()
        self.layout.WINDOW_WIDTH = width
        self.layout.WINDOW_HEIGHT = height

        self.screen = pygame.display.set_mode(
            (self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT),
            pygame.RESIZABLE
        )
        pygame.display.set_caption('Math Flashcards')

        # Initialize fonts
        self.fonts = {
            size: pygame.font.Font(None, GameSettings.FONT_SIZES[size])
            for size in GameSettings.FONT_SIZES
        }

        # Control button dimensions and state
        self.control_button_size = 40
        self.control_button_padding = 12

        # Admin button in top right
        self.admin_button_rect = pygame.Rect(
            self.layout.WINDOW_WIDTH - self.control_button_size - self.control_button_padding,
            self.control_button_padding,
            self.control_button_size,
            self.control_button_size
        )

        # Info button to its left
        self.info_button_rect = pygame.Rect(
            self.layout.WINDOW_WIDTH - (self.control_button_size * 2) - (self.control_button_padding * 2),
            self.control_button_padding,
            self.control_button_size,
            self.control_button_size
        )

        # Initialize panel states
        self.admin_panel_open = False
        self.info_panel_open = False

        # Initialize button states
        self.admin_button_hover = False
        self.info_button_hover = False
        self.admin_button_pressed = False
        self.info_button_pressed = False

        # Initialize admin panel specific states
        self.admin_confirm_delete = None
        self.admin_message = None
        self.admin_message_timer = 0
        self.admin_scroll_offset = 0
        self.admin_hover_player = None
        self.admin_confirm_buttons = {}

        # Game session will be set after player selection
        self.game_session: Optional[Any] = None

        # Initialize UI components
        self._init_ui_components()

    def _init_ui_components(self) -> None:
        """Initialize all UI components"""
        # Sidebar operation buttons
        self.operation_items = self._create_operation_items()
        
        # Difficulty buttons
        self.difficulty_buttons = self._create_difficulty_buttons()

        # Submit button
        button_x = self.layout.content_center_x - self.layout.BUTTON_WIDTH // 2
        button_y = (self.layout.content_center_y +
                    self.layout.TRIANGLE_SIZE // 2 + 40)
        self.submit_button = Button(
            button_x, button_y,
            self.layout.BUTTON_WIDTH, self.layout.BUTTON_HEIGHT,
            "Submit",
            color=Colors.NAVY_PRIMARY,  # Use the navy theme
            text_color=Colors.WHITE,
            border_radius=25  # More rounded corners
        )

        # Add Load and Quit buttons
        buttons_y = button_y + self.layout.BUTTON_HEIGHT + 10
        button_spacing = 20
        total_width = (self.layout.BUTTON_WIDTH * 2) + button_spacing
        load_x = self.layout.content_center_x - (total_width // 2)
        quit_x = load_x + self.layout.BUTTON_WIDTH + button_spacing

        self.load_button = Button(
            load_x, buttons_y,
            self.layout.BUTTON_WIDTH, self.layout.BUTTON_HEIGHT,
            "Load",
            color=Colors.NAVY_LIGHT,  # Lighter navy for secondary action
            text_color=Colors.WHITE,
            border_radius=25
        )

        self.quit_button = Button(
            quit_x, buttons_y,
            self.layout.BUTTON_WIDTH, self.layout.BUTTON_HEIGHT,
            "Quit",
            color=Colors.ERROR,  # Keep the error color for quit
            text_color=Colors.WHITE,
            border_radius=25
        )
        
        # Stats panel
        self.stats_panel = StatsPanel(self.layout)

    def _create_operation_items(self) -> Dict[str, ListItem]:
	    """Create operation selection items"""
	    items = {}
	    start_y = self.layout.HEADER_HEIGHT + self.layout.PADDING
	    operations = [
	        ('+ Addition', '+'),
	        ('− Subtraction', '-'),
	        ('× Multiplication', '*'),
	        ('÷ Division', '/')
	    ]
	    
	    for i, (display_name, op_symbol) in enumerate(operations):
	        y_pos = start_y + self.layout.LIST_ITEM_HEIGHT * i
	        items[op_symbol] = ListItem(
	            display_name, y_pos, self.layout,
	            checked=(op_symbol == '+')
	        )
	        
	    return items

    def _create_difficulty_buttons(self) -> Dict[DifficultyLevel, Button]:
        """Create difficulty selection buttons"""
        buttons = {}
        operations_height = (self.layout.HEADER_HEIGHT + self.layout.PADDING +
                             self.layout.LIST_ITEM_HEIGHT * 4)
        start_y = operations_height + self.layout.SECTION_SPACING

        # Add "Difficulty" label
        diff_label_height = 20

        # Create single column of smaller buttons
        button_width = self.layout.SIDEBAR_WIDTH - (self.layout.PADDING * 2)
        button_spacing = 4

        difficulties = [d for d in DifficultyLevel if d != DifficultyLevel.CUSTOM]
        y = start_y + diff_label_height + self.layout.PADDING

        for difficulty in difficulties:
            settings = GameSettings.DIFFICULTY_SETTINGS[difficulty]
            buttons[difficulty] = Button(
                self.layout.PADDING,
                y,
                button_width,
                self.layout.BUTTON_HEIGHT,
                difficulty.value,
                settings['color'],
                settings['text_color']
            )
            y += self.layout.BUTTON_HEIGHT + button_spacing

        # Add Custom mode button at the bottom with some extra spacing
        settings = GameSettings.DIFFICULTY_SETTINGS[DifficultyLevel.CUSTOM]
        buttons[DifficultyLevel.CUSTOM] = Button(
            self.layout.PADDING,
            y + button_spacing,
            button_width,
            self.layout.BUTTON_HEIGHT,
            DifficultyLevel.CUSTOM.value,
            settings['color'],
            settings['text_color']
        )

        return buttons

    def set_game_session(self, session: Any) -> None:
        """Set the active game session"""
        self.game_session = session
        self.stats_panel.set_game_session(session)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle all game events"""
        if not self.game_session:
            return False

        if event.type == pygame.VIDEORESIZE:
            self._handle_resize(event.w, event.h)
            return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Add this block for admin panel scroll handling
            if self.admin_panel_open and event.button in (4, 5):  # 4 is scroll up, 5 is scroll down
                self._handle_admin_panel_scroll(1 if event.button == 5 else -1)
                return True
            return self._handle_mouse_click(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            # Handle button release states
            self.submit_button.handle_release()
            self.load_button.handle_release()
            self.quit_button.handle_release()
            for button in self.difficulty_buttons.values():
                button.handle_release()
            return True

        elif event.type == pygame.KEYDOWN:
            return self.game_session.handle_input(event)

        return False

    def _handle_resize(self, width: int, height: int) -> None:
        """Handle window resize event"""
        self.layout.WINDOW_WIDTH = width
        self.layout.WINDOW_HEIGHT = height
        self.screen = pygame.display.set_mode(
            (self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT),
            pygame.RESIZABLE
        )
        self._init_ui_components()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle all game events"""
        if not self.game_session:
            return False

        if event.type == pygame.VIDEORESIZE:
            self._handle_resize(event.w, event.h)
            return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Add this block for admin panel scroll handling
            if self.admin_panel_open and event.button in (4, 5):  # 4 is scroll up, 5 is scroll down
                self._handle_admin_panel_scroll(1 if event.button == 5 else -1)
                return True
            return self._handle_mouse_click(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            # Handle button release states
            self.submit_button.handle_release()
            self.load_button.handle_release()
            self.quit_button.handle_release()
            for button in self.difficulty_buttons.values():
                button.handle_release()
            return True

        elif event.type == pygame.KEYDOWN:
            return self.game_session.handle_input(event)

        return False

    def _handle_mouse_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click events"""
        # Admin button check
        if self.admin_button_rect.collidepoint(pos):
            self.admin_button_pressed = True
            self.admin_panel_open = not self.admin_panel_open
            self.info_panel_open = False  # Close info panel if open
            return True

        # Info button check
        if self.info_button_rect.collidepoint(pos):
            self.info_button_pressed = True
            self.info_panel_open = not self.info_panel_open
            self.admin_panel_open = False  # Close admin panel if open
            return True

        # If info panel is open, check for outside clicks to close it
        if self.info_panel_open:
            panel_rect = pygame.Rect(
                self.layout.WINDOW_WIDTH // 4,
                self.layout.WINDOW_HEIGHT // 4,
                self.layout.WINDOW_WIDTH // 2,
                self.layout.WINDOW_HEIGHT // 2
            )
            if not panel_rect.collidepoint(pos):
                self.info_panel_open = False
                return True
            return True

        # If admin panel is open, handle its clicks first
        if self.admin_panel_open:
            if self._handle_admin_panel_click(pos):
                return True

            # Check if click is outside panel to close it
            panel_rect = pygame.Rect(
                self.layout.WINDOW_WIDTH // 4,
                self.layout.WINDOW_HEIGHT // 4,
                self.layout.WINDOW_WIDTH // 2,
                self.layout.WINDOW_HEIGHT // 2
            )
            if not panel_rect.collidepoint(pos):
                self.admin_panel_open = False
                return True

        # Handle operation selection
        total_checked = sum(1 for item in self.operation_items.values() if item.checked)
        for op_symbol, item in self.operation_items.items():
            if item.handle_click(pos, total_checked):
                self.game_session.update_operators(op_symbol, item.checked)
                return True

        # Handle difficulty selection
        for difficulty, button in self.difficulty_buttons.items():
            if button.handle_click(pos):
                self.game_session.update_difficulty(difficulty)
                return True

        # Handle submit button
        if self.submit_button.handle_click(pos):
            self.game_session.check_answer()
            return True

        # Handle load button
        if self.load_button.handle_click(pos):
            pygame.event.post(pygame.event.Event(
                pygame.USEREVENT,
                {'action': 'load'}
            ))
            return True

        # Handle quit button
        if self.quit_button.handle_click(pos):
            pygame.event.post(pygame.event.Event(
                pygame.USEREVENT,
                {'action': 'quit'}
            ))
            return True

        return False

    def update(self, current_time: int) -> None:
        """Update all game elements"""
        if not self.game_session:
            return

        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        self.admin_button_hover = self.admin_button_rect.collidepoint(mouse_pos)
        self.info_button_hover = self.info_button_rect.collidepoint(mouse_pos)

        # Reset pressed states if mouse button is up
        if not pygame.mouse.get_pressed()[0]:  # Left mouse button
            self.admin_button_pressed = False
            self.info_button_pressed = False

        # Update operation item hover states
        for item in self.operation_items.values():
            item.update_hover(mouse_pos)

        # Update difficulty button hover states
        for button in self.difficulty_buttons.values():
            button.update_hover(mouse_pos)

        # Update main game button hover states
        self.submit_button.update_hover(mouse_pos)
        self.load_button.update_hover(mouse_pos)
        self.quit_button.update_hover(mouse_pos)

        # Update admin panel hover states if open
        if self.admin_panel_open:
            self._handle_admin_panel_hover(mouse_pos)

            # Update confirmation button states if they exist
            if hasattr(self, 'confirm_cancel_button') and hasattr(self, 'confirm_delete_button'):
                self.confirm_cancel_button.update_hover(mouse_pos)
                self.confirm_delete_button.update_hover(mouse_pos)

            # Update admin message timer if exists
            if self.admin_message and current_time - self.admin_message_timer > 2000:  # 2 seconds
                self.admin_message = None

        # Update game session
        self.game_session.update(current_time)

    def _draw_sidebar(self) -> None:
        """Draw the sidebar with enhanced styling"""
        # Create sidebar surface with translucent navy overlay
        sidebar_rect = pygame.Rect(
            0, 0,
            self.layout.SIDEBAR_WIDTH,
            self.layout.WINDOW_HEIGHT
        )

        # Draw sidebar background with subtle gradient
        sidebar_surface = pygame.Surface((sidebar_rect.width, sidebar_rect.height), pygame.SRCALPHA)
        for y in range(sidebar_rect.height):
            progress = y / sidebar_rect.height
            color = self._lerp_color(
                (245, 250, 255, 250),  # Almost white at top
                (235, 245, 255, 250),  # Slightly blue-tinted white at bottom
                progress
            )
            pygame.draw.line(sidebar_surface, color,
                             (0, y), (sidebar_rect.width, y))

        # Add subtle edge lighting
        edge_width = 3
        for i in range(edge_width):
            alpha = 100 - (i * 30)
            pygame.draw.line(
                sidebar_surface,
                (255, 255, 255, alpha),
                (sidebar_rect.width - i, 0),
                (sidebar_rect.width - i, sidebar_rect.height)
            )

        self.screen.blit(sidebar_surface, sidebar_rect)

        # Rest of sidebar drawing code remains the same...

    def _lerp_color(self, color1: tuple, color2: tuple, progress: float) -> tuple:
        """Linearly interpolate between two colors"""
        return tuple(
            int(c1 + (c2 - c1) * progress)
            for c1, c2 in zip(color1, color2)
        )

    # Update draw() method to use new background
    def draw(self) -> None:
        """Draw the complete game interface"""
        if not self.game_session:
            return

        # Draw layered background first
        self._draw_background()

        # Draw main sections
        self._draw_sidebar()
        self._draw_main_content()

        # Draw control buttons
        self._draw_control_button(self.admin_button_rect, 'admin',
                                  self.admin_button_hover,
                                  self.admin_button_pressed)
        self._draw_control_button(self.info_button_rect, 'info',
                                  self.info_button_hover,
                                  self.info_button_pressed)

        # Draw panels if open
        if self.admin_panel_open:
            self._draw_admin_panel()
        elif self.info_panel_open:
            self._draw_about_panel()

        pygame.display.flip()

    def _draw_sidebar(self) -> None:
        """Draw the sidebar with enhanced styling"""
        # ... [previous sidebar background code remains the same] ...

        # Draw difficulty section header
        operations_height = (self.layout.HEADER_HEIGHT + self.layout.PADDING +
                             self.layout.LIST_ITEM_HEIGHT * 4)
        diff_label_y = operations_height + self.layout.SECTION_SPACING
        diff_label = self.fonts['small'].render("Difficulty Level", True, Colors.BLACK)
        self.screen.blit(diff_label, (self.layout.PADDING, diff_label_y))

        # Difficulty buttons
        for difficulty, button in self.difficulty_buttons.items():
            # Set button state but preserve the original color
            button.selected = (difficulty == self.game_session.state.difficulty)
            button.disabled = (difficulty == DifficultyLevel.CUSTOM and
                               not self.game_session.player.can_use_custom_mode())
            button.draw(self.screen, self.fonts['small'])

        # Operation items
        for item in self.operation_items.values():
            item.draw(self.screen, self.fonts['small'])

        # Stats panel at the bottom
        self.stats_panel.draw(self.screen, self.fonts)

    def _draw_main_content(self) -> None:
        """Draw the main content area with animated background symbols"""
        if not self.game_session.state.current_question:
            return

        # Initialize animation state if needed
        if not hasattr(self, '_animation_state'):
            self._animation_state = {
                'symbols': self._generate_new_symbols(),
                'previous_symbols': None,
                'transition_start': pygame.time.get_ticks(),
                'is_transitioning': False
            }

        # Get animation settings
        settings = GameSettings.ANIMATION
        current_time = pygame.time.get_ticks()
        content_width = self.layout.WINDOW_WIDTH - self.layout.SIDEBAR_WIDTH
        content_height = self.layout.WINDOW_HEIGHT

        # Check if it's time for new symbols
        if (not self._animation_state['is_transitioning'] and
                current_time - self._animation_state['transition_start'] > settings['background_symbol_speed']):
            self._animation_state['previous_symbols'] = self._animation_state['symbols']
            self._animation_state['symbols'] = self._generate_new_symbols()
            self._animation_state['is_transitioning'] = True
            self._animation_state['transition_start'] = current_time

        # Create pattern surface
        pattern_surface = pygame.Surface((content_width, content_height), pygame.SRCALPHA)

        # Calculate fade progress if transitioning
        if self._animation_state['is_transitioning']:
            progress = min(1.0, (current_time - self._animation_state['transition_start']) /
                           float(settings['background_fade_time']))

            # Draw previous symbols fading out
            if self._animation_state['previous_symbols']:
                self._draw_symbol_set(pattern_surface,
                                      self._animation_state['previous_symbols'],
                                      int(255 * (1.0 - progress)))

            # Draw new symbols fading in
            self._draw_symbol_set(pattern_surface,
                                  self._animation_state['symbols'],
                                  int(255 * progress))

            if progress >= 1.0:
                self._animation_state['is_transitioning'] = False
                self._animation_state['previous_symbols'] = None
        else:
            # Draw current symbols at full opacity
            self._draw_symbol_set(pattern_surface,
                                  self._animation_state['symbols'],
                                  255)

        # Draw pattern onto main screen
        self.screen.blit(pattern_surface, (self.layout.SIDEBAR_WIDTH, 0))

        # Draw math problem
        self._draw_math_problem()

    def _draw_number_boxes(self, center_x: int, center_y: int, half_size: int) -> None:
        """Draw enhanced number input boxes with modern styling and visual effects"""
        if not self.game_session:
            return

        # Enhanced triangle styling
        triangle_points = [
            (center_x, center_y + half_size),  # Bottom
            (center_x - half_size, center_y - half_size),  # Top left
            (center_x + half_size, center_y - half_size)  # Top right
        ]

        # Draw glowing triangle outline
        glow_color = (*Colors.NAVY_LIGHTEST, 30)  # Light blue with alpha
        # Multiple passes for glow effect
        for offset in range(3):
            expanded_points = [
                (x + (5 - offset) * math.cos(angle), y + (5 - offset) * math.sin(angle))
                for (x, y), angle in zip(triangle_points,
                                         [math.pi / 2, -5 * math.pi / 6, -math.pi / 6])  # Angles for each point
            ]
            pygame.draw.polygon(self.screen, glow_color, expanded_points, 3)

        # Main triangle outline with gradient effect
        pygame.draw.polygon(self.screen, Colors.NAVY_PRIMARY, triangle_points, 2)

        # Calculate box positions with slight adjustments for better visual balance
        box_positions = {
            'left': (center_x - half_size + 40, center_y - half_size + 60),
            'right': (center_x + half_size - 40, center_y - half_size + 60),
            'bottom': (center_x, center_y + half_size - 40)
        }

        # Get number values
        left, right, bottom = self.game_session.get_display_numbers()
        values = {'left': left, 'right': right, 'bottom': bottom}

        # Draw boxes with enhanced styling
        for position, center_pos in box_positions.items():
            # Create box rectangle
            box_rect = pygame.Rect(
                center_pos[0] - self.layout.INPUT_BOX_WIDTH // 2,
                center_pos[1] - self.layout.INPUT_BOX_HEIGHT // 2,
                self.layout.INPUT_BOX_WIDTH,
                self.layout.INPUT_BOX_HEIGHT
            )

            # Draw box shadow
            shadow_offset = 2
            shadow_rect = box_rect.copy()
            shadow_rect.y += shadow_offset
            pygame.draw.rect(self.screen, Colors.NAVY_DARKEST, shadow_rect,
                             border_radius=10)

            # Draw main box background
            pygame.draw.rect(self.screen, Colors.WHITE, box_rect, border_radius=10)

            # Draw glossy highlight on top half
            highlight_rect = box_rect.copy()
            highlight_rect.height = box_rect.height // 2
            highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(highlight_surface, (255, 255, 255, 25),
                             highlight_surface.get_rect(), border_radius=10)
            self.screen.blit(highlight_surface, highlight_rect)

            # Determine if this is the active input box
            is_active = (self.game_session.state.current_question.missing_position ==
                         list(box_positions.keys()).index(position))

            # Draw border with glow effect for active box
            border_color = Colors.HIGHLIGHT if is_active else Colors.NAVY_PRIMARY
            if is_active:
                # Draw outer glow
                glow_alpha = abs(math.sin(pygame.time.get_ticks() / 500)) * 50 + 20
                glow_color = (*Colors.NAVY_LIGHTEST, int(glow_alpha))
                for offset in range(3):
                    glow_rect = box_rect.inflate(offset * 2, offset * 2)
                    pygame.draw.rect(self.screen, glow_color, glow_rect,
                                     border_radius=10, width=1)

            # Draw main border
            pygame.draw.rect(self.screen, border_color, box_rect,
                             border_radius=10, width=2)

            # Draw text or input
            text = ''
            if (isinstance(values[position], str) and not values[position] and is_active):
                # Show user input with cursor
                text = self.game_session.state.user_input
                if self.game_session.state.cursor_visible:
                    text += '|'
            else:
                text = values[position]

            if text:
                # Add subtle text shadow for depth
                shadow_color = (0, 0, 0, 128)
                text_shadow = self.fonts['normal'].render(text, True, shadow_color)
                shadow_rect = text_shadow.get_rect(center=box_rect.center)
                shadow_rect.y += 1
                self.screen.blit(text_shadow, shadow_rect)

                # Draw main text
                text_color = Colors.NAVY_PRIMARY if is_active else Colors.BLACK
                text_surface = self.fonts['normal'].render(text, True, text_color)
                self.screen.blit(text_surface,
                                 text_surface.get_rect(center=box_rect.center))

    def _draw_about_panel(self) -> None:
        """Draw the about/info panel with game information"""
        if not self.game_session:
            return

        # Create semi-transparent overlay with blur effect
        overlay = pygame.Surface((self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        # Calculate panel dimensions with golden ratio
        panel_width = min(680, self.layout.WINDOW_WIDTH - 50)
        panel_height = max(int(panel_width / 1.618), self.layout.WINDOW_HEIGHT - 50)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        # Draw panel background with enhanced styling
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # Draw shadow
        shadow_offset = 4
        shadow_rect = panel_rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(self.screen, Colors.NAVY_DARKEST, shadow_rect, border_radius=12)

        # Main panel
        pygame.draw.rect(self.screen, Colors.WHITE, panel_rect, border_radius=12)

        # Gradient header
        header_height = 50
        header_rect = pygame.Rect(panel_x, panel_y, panel_width, header_height)
        header_surface = pygame.Surface((panel_width, header_height), pygame.SRCALPHA)

        for y in range(header_height):
            progress = y / header_height
            color = self._lerp_color(Colors.NAVY_PRIMARY, Colors.NAVY_LIGHT, progress)
            pygame.draw.line(header_surface, color, (0, y), (panel_width, y))

        self.screen.blit(header_surface, header_rect)

        # Header text with glow effect
        header_text = self.fonts['normal'].render(APP_NAME, True, Colors.WHITE)
        text_rect = header_text.get_rect(
            centerx=header_rect.centerx,
            centery=header_rect.centery
        )

        # Draw text glow
        glow_surface = pygame.Surface((header_text.get_width() + 4, header_text.get_height() + 4), pygame.SRCALPHA)
        glow_text = self.fonts['normal'].render(APP_NAME, True, (*Colors.NAVY_LIGHTEST, 128))
        glow_rect = glow_text.get_rect(center=(glow_surface.get_width() // 2, glow_surface.get_height() // 2))
        glow_surface.blit(glow_text, glow_rect)
        self.screen.blit(glow_surface, text_rect)
        self.screen.blit(header_text, text_rect)

        # Content area with sections
        content_x = panel_x + 30
        content_y = panel_y + header_height + 25
        line_height = 28
        section_spacing = 20

        # Define sections
        sections = [
            {
                'title': 'Version Information',
                'content': [
                    (f"Version {VERSION}", Colors.NAVY_PRIMARY)
                ]
            },
            {
                'title': 'Features',
                'content': [
                    ("• Adaptive Learning System", Colors.TEXT_GRAY),
                    ("• Multiple Operation Types", Colors.TEXT_GRAY),
                    ("• Custom Difficulty Modes", Colors.TEXT_GRAY),
                    ("• Detailed Progress Tracking", Colors.TEXT_GRAY),
                    ("• Multi-User Support", Colors.TEXT_GRAY)
                ]
            },
            {
                'title': 'Credits',
                'content': [
                    (f"Created by {APP_AUTHOR}", Colors.BLACK),
                    (f"{APP_LICENSE} License", Colors.HIGHLIGHT),
                    (APP_COPYRIGHT, Colors.TEXT_GRAY),
                    (f"Repository: {APP_REPOSITORY}", Colors.TEXT_GRAY)
                ]
            }
        ]

        # Draw sections
        for section in sections:
            # Section title with underline
            title_surface = self.fonts['normal'].render(section['title'], True, Colors.NAVY_PRIMARY)
            self.screen.blit(title_surface, (content_x, content_y))

            # Animated underline
            line_progress = (math.sin(pygame.time.get_ticks() / 1000) + 1) / 2
            line_width = int(title_surface.get_width() * line_progress)
            line_y = content_y + title_surface.get_height() + 2
            pygame.draw.line(self.screen, Colors.HIGHLIGHT,
                             (content_x, line_y),
                             (content_x + line_width, line_y), 2)

            content_y += title_surface.get_height() + 10

            # Section content
            for item in section['content']:
                if item:  # Skip None entries
                    text, color = item
                    text_surface = self.fonts['small'].render(text, True, color)
                    self.screen.blit(text_surface, (content_x + 10, content_y))
                    content_y += line_height

            content_y += section_spacing

        # Draw footer
        footer_text = "Click anywhere outside this panel to close"
        footer_surface = self.fonts['small'].render(footer_text, True, Colors.TEXT_GRAY)
        footer_rect = footer_surface.get_rect(
            centerx=panel_rect.centerx,
            bottom=panel_rect.bottom - 15
        )
        self.screen.blit(footer_surface, footer_rect)

    def _draw_admin_panel(self) -> None:
        """Draw the admin panel with enhanced styling to match about panel"""
        if not self.game_session:
            return

        # Create semi-transparent overlay with blur effect
        overlay = pygame.Surface((self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        # Calculate panel dimensions with golden ratio
        panel_width = min(600, self.layout.WINDOW_WIDTH - 100)
        panel_height = min(500, self.layout.WINDOW_HEIGHT - 100)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        # Draw panel background with enhanced styling
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # Draw shadow
        shadow_offset = 4
        shadow_rect = panel_rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(self.screen, Colors.NAVY_DARKEST, shadow_rect, border_radius=12)

        # Main panel
        pygame.draw.rect(self.screen, Colors.WHITE, panel_rect, border_radius=12)

        # Gradient header
        header_height = 50
        header_rect = pygame.Rect(panel_x, panel_y, panel_width, header_height)
        header_surface = pygame.Surface((panel_width, header_height), pygame.SRCALPHA)

        for y in range(header_height):
            progress = y / header_height
            color = self._lerp_color(Colors.NAVY_PRIMARY, Colors.NAVY_LIGHT, progress)
            pygame.draw.line(header_surface, color, (0, y), (panel_width, y))

        self.screen.blit(header_surface, header_rect)

        # Header text with glow effect
        header_text = self.fonts['normal'].render("Player Management", True, Colors.WHITE)
        text_rect = header_text.get_rect(
            centerx=header_rect.centerx,
            centery=header_rect.centery
        )

        # Draw text glow
        glow_surface = pygame.Surface((header_text.get_width() + 4, header_text.get_height() + 4), pygame.SRCALPHA)
        glow_text = self.fonts['normal'].render("Player Management", True, (*Colors.NAVY_LIGHTEST, 128))
        glow_rect = glow_text.get_rect(center=(glow_surface.get_width() // 2, glow_surface.get_height() // 2))
        glow_surface.blit(glow_text, glow_rect)
        self.screen.blit(glow_surface, text_rect)
        self.screen.blit(header_text, text_rect)

        # Calculate content area
        content_x = panel_x + 20
        content_y = panel_y + header_height + 10
        content_width = panel_width - 40
        content_height = panel_height - header_height - 20

        # Draw player list or confirmation dialog
        if self.admin_confirm_delete:
            self._draw_delete_confirmation(
                content_x, content_y, content_width, content_height
            )
        else:
            self._draw_player_list(
                content_x, content_y, content_width, content_height
            )

        # Draw feedback message if exists
        if self.admin_message:
            current_time = pygame.time.get_ticks()
            if current_time - self.admin_message_timer < 2000:  # 2 second display
                msg_color = Colors.SUCCESS if "successfully" in self.admin_message else Colors.ERROR
                msg_surface = self.fonts['small'].render(self.admin_message, True, msg_color)
                msg_pos = (
                    panel_x + (panel_width - msg_surface.get_width()) // 2,
                    panel_y + panel_height - 30
                )
                self.screen.blit(msg_surface, msg_pos)
            else:
                self.admin_message = None

    def _draw_player_list(self, x: int, y: int, width: int, height: int) -> None:
        """Draw scrollable player list with modern, clean styling"""
        # Get player list from game session's player controller
        player_controller = self.game_session.player_controller
        players = player_controller.load_players()

        # Background styling
        background_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, Colors.WHITE, background_rect)

        # Calculate list metrics
        item_height = 56  # Increased height for more spacious feel
        visible_items = height // item_height
        max_scroll = max(0, len(players) - visible_items)

        # Draw visible players
        for i, player in enumerate(players[self.admin_scroll_offset:
        self.admin_scroll_offset + visible_items]):
            item_y = y + (i * item_height)

            # Full-width row for hover effect
            row_rect = pygame.Rect(x, item_y, width, item_height)

            # Hover effect
            is_hovered = self.admin_hover_player == (i + self.admin_scroll_offset)
            if is_hovered:
                # Draw a light blue background for the entire row
                hover_color = (240, 247, 255)  # Light blue
                pygame.draw.rect(self.screen, hover_color, row_rect)

                # Add subtle left border accent when hovered
                accent_rect = pygame.Rect(x, item_y, 3, item_height)
                pygame.draw.rect(self.screen, Colors.HIGHLIGHT, accent_rect)

            # Draw player name
            name_surface = self.fonts['normal'].render(player, True, Colors.NAVY_PRIMARY)
            name_pos = (x + 24, item_y + (item_height - name_surface.get_height()) // 2)
            self.screen.blit(name_surface, name_pos)

            # Draw delete button for non-protected players
            if player != "Mr. Jones":
                # Delete button dimensions and position
                button_width = 80
                button_height = 32
                button_x = x + width - button_width - 16
                button_y = item_y + (item_height - button_height) // 2

                button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

                # Check if mouse is over delete button
                delete_hovered = (is_hovered and button_rect.collidepoint(pygame.mouse.get_pos()))

                if delete_hovered:
                    # Danger state
                    bg_color = Colors.ERROR
                    text_color = Colors.WHITE
                    border_color = Colors.ERROR
                else:
                    # Normal state - subtle design
                    bg_color = Colors.WHITE
                    text_color = Colors.ERROR
                    border_color = (255, 200, 200)  # Light red border

                # Draw button background
                pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=16)
                if not delete_hovered:
                    # Only draw border in normal state
                    pygame.draw.rect(self.screen, border_color, button_rect, 1, border_radius=16)

                # Draw button text
                delete_text = self.fonts['small'].render("Delete", True, text_color)
                text_rect = delete_text.get_rect(center=button_rect.center)
                self.screen.blit(delete_text, text_rect)

            # Draw separator line
            line_y = item_y + item_height - 1
            pygame.draw.line(
                self.screen,
                (240, 240, 240),  # Very light gray
                (x + 16, line_y),
                (x + width - 16, line_y)
            )

        # Add final separator line at the bottom of the list
        final_line_y = y + (min(len(players), visible_items) * item_height) - 1
        pygame.draw.line(
            self.screen,
            (240, 240, 240),
            (x + 16, final_line_y),
            (x + width - 16, final_line_y)
        )

        # Draw scroll bar if needed
        if max_scroll > 0:
            bar_width = 4
            bar_right_margin = 4
            scroll_track_rect = pygame.Rect(
                x + width - bar_width - bar_right_margin,
                y,
                bar_width,
                height
            )

            # Draw scroll track
            pygame.draw.rect(self.screen, (245, 245, 245), scroll_track_rect)

            # Calculate and draw scroll thumb
            visible_ratio = visible_items / len(players)
            thumb_height = max(30, int(height * visible_ratio))
            thumb_pos = y + (self.admin_scroll_offset / max_scroll) * (height - thumb_height)
            thumb_rect = pygame.Rect(
                x + width - bar_width - bar_right_margin,
                thumb_pos,
                bar_width,
                thumb_height
            )

            # Draw rounded scroll thumb
            pygame.draw.rect(self.screen, Colors.NAVY_LIGHT, thumb_rect, border_radius=2)

    def _draw_delete_confirmation(self, x: int, y: int, width: int, height: int) -> None:
        """Draw delete confirmation dialog with styled buttons"""
        # Draw confirmation message
        msg = f"Are you sure you want to delete player '{self.admin_confirm_delete}'?"
        msg_surface = self.fonts['normal'].render(msg, True, Colors.BLACK)
        msg_pos = (
            x + (width - msg_surface.get_width()) // 2,
            y + height // 3
        )
        self.screen.blit(msg_surface, msg_pos)

        # Button dimensions matching our other buttons
        button_width = 120
        button_height = 36
        button_y = y + (height * 2 // 3)
        spacing = 20

        # Calculate positions to center the buttons
        total_width = (button_width * 2) + spacing
        cancel_x = x + (width - total_width) // 2
        delete_x = cancel_x + button_width + spacing

        # Create buttons if they don't exist
        if not hasattr(self, 'confirm_cancel_button'):
            self.confirm_cancel_button = Button(
                cancel_x, button_y,
                button_width, button_height,
                "Cancel",
                color=Colors.NAVY_LIGHT,  # Light navy for secondary action
                text_color=Colors.WHITE,
                border_radius=25
            )

        if not hasattr(self, 'confirm_delete_button'):
            self.confirm_delete_button = Button(
                delete_x, button_y,
                button_width, button_height,
                "Delete",
                color=Colors.ERROR,
                text_color=Colors.WHITE,
                border_radius=25
            )

        # Draw buttons
        self.confirm_cancel_button.draw(self.screen, self.fonts['normal'])
        self.confirm_delete_button.draw(self.screen, self.fonts['normal'])

        # Store rects for click handling
        self.admin_confirm_buttons = {
            'cancel': self.confirm_cancel_button.rect,
            'delete': self.confirm_delete_button.rect
        }

    def _handle_admin_panel_click(self, pos: Tuple[int, int]) -> bool:
        """Handle clicks in the admin panel"""
        if self.admin_confirm_delete:
            # Handle confirmation dialog buttons
            if hasattr(self, 'confirm_cancel_button'):
                if self.confirm_cancel_button.handle_click(pos):
                    self.admin_confirm_delete = None
                    return True

            if hasattr(self, 'confirm_delete_button'):
                if self.confirm_delete_button.handle_click(pos):
                    success = self.game_session.player_controller.delete_player(
                        self.admin_confirm_delete
                    )
                    self.admin_message = (
                        f"Player {self.admin_confirm_delete} deleted successfully"
                        if success else
                        f"Error deleting player {self.admin_confirm_delete}"
                    )
                    self.admin_message_timer = pygame.time.get_ticks()

                    # If the deleted player was the current player, return to login
                    if success and self.game_session.player.name == self.admin_confirm_delete:
                        pygame.event.post(pygame.event.Event(
                            pygame.USEREVENT,
                            {'action': 'load'}
                        ))
                        self.admin_panel_open = False

                    self.admin_confirm_delete = None
                    return True

            return True

        # Handle clicks on delete buttons
        panel_width = min(600, self.layout.WINDOW_WIDTH - 100)
        panel_height = min(500, self.layout.WINDOW_HEIGHT - 100)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        content_x = panel_x + 20
        content_y = panel_y + 50  # After header
        content_width = panel_width - 40
        item_height = 50  # Match the drawing height

        # Check for clicks on delete buttons
        players = self.game_session.player_controller.load_players()
        visible_items = (panel_height - 70) // item_height

        for i, player in enumerate(players[self.admin_scroll_offset:
        self.admin_scroll_offset + visible_items]):
            if player == "Mr. Jones":
                continue

            item_y = content_y + (i * item_height)
            # CRITICAL: Use same delete_rect dimensions as in _draw_player_list
            delete_rect = pygame.Rect(
                content_x + content_width - 40,
                item_y + (item_height - 30) // 2,
                30,
                30
            )

            if delete_rect.collidepoint(pos):
                self.admin_confirm_delete = player
                return True

        return False

    def _handle_admin_panel_hover(self, pos: Tuple[int, int]) -> None:
        """Update hover states in admin panel"""
        if self.admin_confirm_delete:
            return

        # Calculate list area
        panel_width = min(600, self.layout.WINDOW_WIDTH - 100)
        panel_height = min(500, self.layout.WINDOW_HEIGHT - 100)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        content_x = panel_x + 20
        content_y = panel_y + 50  # After header
        content_width = panel_width - 40
        item_height = 56  # Match the height used in _draw_player_list

        # Check if mouse is within the list area
        list_rect = pygame.Rect(content_x, content_y, content_width, panel_height - 70)

        if list_rect.collidepoint(pos):
            # Calculate which item is being hovered
            relative_y = pos[1] - content_y
            hovered_index = (relative_y // item_height) + self.admin_scroll_offset

            # Verify the index is valid
            players = self.game_session.player_controller.load_players()
            if 0 <= hovered_index < len(players):
                self.admin_hover_player = hovered_index
            else:
                self.admin_hover_player = None
        else:
            self.admin_hover_player = None

    def _handle_admin_panel_scroll(self, y: int) -> None:
        """Handle mouse wheel scrolling in admin panel"""
        players = self.game_session.player_controller.load_players()
        visible_items = (min(500, self.layout.WINDOW_HEIGHT - 100) - 70) // 40
        max_scroll = max(0, len(players) - visible_items)

        # Scroll up if y is positive, down if negative
        if y > 0:
            self.admin_scroll_offset = min(max_scroll, self.admin_scroll_offset + 1)
        elif y < 0:
            self.admin_scroll_offset = max(0, self.admin_scroll_offset - 1)

    # Replace the _draw_operator_block method in game_window.py

    def _draw_operator_block(self, operator: str, rect: pygame.Rect) -> None:
        """Draw a clean, simple operator block with clear symbols"""
        # Base colors
        BLOCK_COLOR = Colors.NAVY_PRIMARY  # (35, 65, 115)
        SYMBOL_COLOR = Colors.WHITE  # Pure white for contrast
        EDGE_COLOR = Colors.NAVY_DARKEST  # Dark edge for depth

        # Draw block background with subtle edge
        pygame.draw.rect(self.screen, EDGE_COLOR, rect, border_radius=10)
        inner_rect = rect.inflate(-2, -2)
        pygame.draw.rect(self.screen, BLOCK_COLOR, inner_rect, border_radius=9)

        # Calculate dimensions
        center = rect.center
        symbol_size = min(rect.width, rect.height) // 2
        line_width = max(3, symbol_size // 8)  # Scale line width with size

        # Draw operator symbols
        if operator == '+':
            # Horizontal line
            pygame.draw.line(self.screen, SYMBOL_COLOR,
                             (center[0] - symbol_size // 2, center[1]),
                             (center[0] + symbol_size // 2, center[1]),
                             line_width)
            # Vertical line
            pygame.draw.line(self.screen, SYMBOL_COLOR,
                             (center[0], center[1] - symbol_size // 2),
                             (center[0], center[1] + symbol_size // 2),
                             line_width)

        elif operator == '-':
            # Single horizontal line
            pygame.draw.line(self.screen, SYMBOL_COLOR,
                             (center[0] - symbol_size // 2, center[1]),
                             (center[0] + symbol_size // 2, center[1]),
                             line_width)

        elif operator == '*':
            # Draw × symbol
            offset = symbol_size // 2
            # Diagonal line from top-left to bottom-right
            pygame.draw.line(self.screen, SYMBOL_COLOR,
                             (center[0] - offset, center[1] - offset),
                             (center[0] + offset, center[1] + offset),
                             line_width)
            # Diagonal line from top-right to bottom-left
            pygame.draw.line(self.screen, SYMBOL_COLOR,
                             (center[0] + offset, center[1] - offset),
                             (center[0] - offset, center[1] + offset),
                             line_width)

        else:  # Division
            dot_radius = line_width + 1
            # Draw dots
            pygame.draw.circle(self.screen, SYMBOL_COLOR,
                               (center[0], center[1] - symbol_size // 3), dot_radius)
            pygame.draw.circle(self.screen, SYMBOL_COLOR,
                               (center[0], center[1] + symbol_size // 3), dot_radius)
            # Draw line
            pygame.draw.line(self.screen, SYMBOL_COLOR,
                             (center[0] - symbol_size // 2, center[1]),
                             (center[0] + symbol_size // 2, center[1]),
                             line_width)

    def _draw_control_button(self, rect: pygame.Rect, button_type: str,
                             hover: bool, pressed: bool) -> None:
        """Draw a modern control button (admin or info)"""
        # Base colors
        if button_type == 'admin':
            base_color = (120, 55, 155)  # Deep purple
            glow_color = (180, 55, 155, 30)  # Magenta glow
        else:  # info
            base_color = (35, 65, 115)  # Navy blue
            glow_color = (65, 135, 255, 30)  # Light blue glow

        # Adjust colors when pressed
        if pressed:
            base_color = tuple(max(0, c - 20) for c in base_color)

        # Draw button background
        if hover or pressed:
            # Draw glow effect
            glow_rect = rect.inflate(4, 4)
            current_time = pygame.time.get_ticks()
            glow_alpha = int(abs(math.sin(current_time / 500)) * 30) + 10
            glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*glow_color[:3], glow_alpha),
                             glow_surface.get_rect(), border_radius=12)
            self.screen.blit(glow_surface, glow_rect)

        # Main button background
        pygame.draw.rect(self.screen, base_color, rect, border_radius=10)

        # Calculate icon dimensions
        icon_padding = rect.width // 5
        icon_rect = rect.inflate(-icon_padding * 2, -icon_padding * 2)

        if button_type == 'info':
            # Draw modern "i" icon
            color = (240, 240, 255)  # Bright white

            # Draw dot
            dot_y = icon_rect.top + icon_rect.height // 4
            dot_radius = max(2, icon_rect.width // 8)
            pygame.draw.circle(self.screen, color,
                               (icon_rect.centerx, dot_y), dot_radius)

            # Draw stem with rounded bottom
            stem_width = max(2, icon_rect.width // 6)
            stem_top = dot_y + dot_radius + 2
            stem_bottom = icon_rect.bottom - dot_radius

            # Main stem
            pygame.draw.line(self.screen, color,
                             (icon_rect.centerx, stem_top),
                             (icon_rect.centerx, stem_bottom),
                             stem_width)

            # Rounded bottom
            pygame.draw.circle(self.screen, color,
                               (icon_rect.centerx, stem_bottom - stem_width // 2),
                               stem_width // 2)

        else:  # admin button
            # Draw three horizontal bars of different lengths
            color = (240, 240, 255)  # Bright white
            bar_height = max(2, icon_rect.height // 8)
            bar_spacing = icon_rect.height // 3

            # Calculate base positions
            left_margin = icon_rect.left
            offset = 0 if pressed else (math.sin(pygame.time.get_ticks() / 500) * 2 if hover else 0)

            # Draw three bars with different lengths and positions
            bar_lengths = [0.9, 0.7, 0.8]  # Relative lengths

            for i, length in enumerate(bar_lengths):
                bar_y = icon_rect.top + (i * bar_spacing) + (icon_rect.height - bar_spacing * 2) // 2
                bar_width = int(icon_rect.width * length)

                # Add slight offset when hovering
                x_offset = offset * (-1 if i % 2 == 0 else 1) if hover else 0

                pygame.draw.rect(self.screen, color,
                                 (left_margin + x_offset, bar_y, bar_width, bar_height),
                                 border_radius=bar_height // 2)

    def _draw_background(self) -> None:
        """Draw the main application background with enhanced visual elements"""
        # Create base gradient
        gradient_surface = pygame.Surface(
            (self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT),
            pygame.SRCALPHA
        )

        # Enhanced gradient colors
        top_color = (240, 245, 255)  # Light blue-white
        bottom_color = (225, 235, 250)  # Slightly deeper blue-white

        for y in range(self.layout.WINDOW_HEIGHT):
            progress = y / self.layout.WINDOW_HEIGHT
            color = self._lerp_color(top_color, bottom_color, progress)
            pygame.draw.line(gradient_surface, (*color, 255),
                             (0, y), (self.layout.WINDOW_WIDTH, y))

        self.screen.blit(gradient_surface, (0, 0))

        # Create pattern surface with proper alpha
        pattern_surface = pygame.Surface(
            (self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT),
            pygame.SRCALPHA
        )

        # Draw dot grid pattern
        dot_spacing = 20
        dot_radius = 1
        dot_color = (200, 210, 240, 15)  # Increased alpha for better visibility

        for x in range(0, self.layout.WINDOW_WIDTH, dot_spacing):
            for y in range(0, self.layout.WINDOW_HEIGHT, dot_spacing):
                offset = 5 * math.sin(y * 0.05)  # Create wave effect
                pygame.draw.circle(
                    pattern_surface,
                    dot_color,
                    (int(x + offset), y),
                    dot_radius
                )

        # Apply pattern with proper blending
        self.screen.blit(pattern_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    def set_background_animation(self, **kwargs) -> None:
        """Update background animation settings

        Valid kwargs:
        - speed: Time between updates (ms)
        - count: Number of symbols
        - fade_time: Transition fade time (ms)
        - min_alpha: Minimum symbol transparency
        - max_alpha: Maximum symbol transparency
        """
        if not hasattr(self, '_animation_settings'):
            return

        valid_keys = {'speed', 'count', 'fade_time', 'min_alpha', 'max_alpha'}
        for key, value in kwargs.items():
            if key in valid_keys and value > 0:
                self._animation_settings[key] = value

    def set_animation_settings(self, **settings) -> None:
        """Update animation settings

        Valid settings:
        - symbol_speed: Time between updates (ms)
        - fade_time: Transition fade time (ms)
        - symbol_count: Number of background symbols
        - min_alpha: Minimum symbol transparency
        - max_alpha: Maximum symbol transparency
        """
        valid_settings = {
            'symbol_speed', 'fade_time', 'symbol_count',
            'min_alpha', 'max_alpha'
        }

        if not hasattr(self, '_animation_state'):
            return

        for key, value in settings.items():
            if key in valid_settings and value > 0:
                GameSettings.ANIMATION[f'background_{key}'] = value

    def _generate_new_symbols(self) -> list:
        """Generate a new set of background symbols"""
        settings = GameSettings.ANIMATION
        content_width = self.layout.WINDOW_WIDTH - self.layout.SIDEBAR_WIDTH
        content_height = self.layout.WINDOW_HEIGHT

        # Use fixed alpha values for testing
        base_colors = [
            (180, 190, 220),  # Light navy blue
            (160, 180, 230),  # Lighter blue
            (140, 160, 210)  # Slightly darker blue
        ]

        symbols = []
        for _ in range(settings['background_symbol_count']):
            color = random.choice(base_colors)
            symbols.append({
                'symbol': random.choice(settings['background_symbols']),
                'pos': (
                    random.randint(0, content_width),
                    random.randint(0, content_height)
                ),
                'size': random.randint(
                    settings['background_symbol_size_min'],
                    settings['background_symbol_size_max']
                ),
                'color': color,
                'angle': random.randint(-30, 30)
            })
        return symbols

    def _draw_symbol_set(self, surface: pygame.Surface, symbols: list, alpha: int) -> None:
        """Draw a set of symbols with given alpha value"""
        for symbol in symbols:
            # Create text surface
            font = pygame.font.Font(None, symbol['size'])
            text_surface = font.render(symbol['symbol'], True, symbol['color'])

            # Rotate if needed
            if symbol['angle']:
                text_surface = pygame.transform.rotate(text_surface, symbol['angle'])

            # Set transparency
            text_surface.set_alpha(alpha)

            # Draw to pattern surface
            rect = text_surface.get_rect(center=symbol['pos'])
            surface.blit(text_surface, rect)

    def _draw_symbol_set(self, surface: pygame.Surface, symbols: list, alpha: int) -> None:
        """Draw a set of symbols with given alpha value"""
        for symbol in symbols:
            # Create text surface
            font = pygame.font.Font(None, symbol['size'])
            text_surface = font.render(symbol['symbol'], True, symbol['color'])

            # Rotate if needed
            if symbol['angle']:
                text_surface = pygame.transform.rotate(text_surface, symbol['angle'])

            # Set transparency
            text_surface.set_alpha(alpha)

            # Draw to pattern surface
            rect = text_surface.get_rect(center=symbol['pos'])
            surface.blit(text_surface, rect)

    def _draw_math_problem(self) -> None:
        """Draw the math problem components"""
        if not self.game_session.state.current_question:
            return

        center_x = self.layout.content_center_x
        center_y = self.layout.content_center_y
        half_size = self.layout.TRIANGLE_SIZE // 2

        # Draw triangle points with enhanced styling
        triangle_points = [
            (center_x, center_y + half_size),  # Bottom
            (center_x - half_size, center_y - half_size),  # Top left
            (center_x + half_size, center_y - half_size)  # Top right
        ]

        # Draw triangle glow effect
        glow_colors = [
            (65, 135, 255, 10),  # Outer glow
            (65, 135, 255, 20),  # Middle glow
            (65, 135, 255, 30)  # Inner glow
        ]

        for color in glow_colors:
            glow_surface = pygame.Surface(
                (self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT),
                pygame.SRCALPHA
            )
            pygame.draw.polygon(glow_surface, color, triangle_points)
            self.screen.blit(glow_surface, (0, 0))

        # Draw main triangle
        pygame.draw.polygon(self.screen, Colors.HIGHLIGHT, triangle_points, 3)

        # Draw operator block
        block_size = 60
        block_rect = pygame.Rect(
            center_x - block_size // 2,
            center_y - block_size // 2,
            block_size,
            block_size
        )
        self._draw_operator_block(
            self.game_session.state.current_question.operator,
            block_rect
        )

        # Draw number boxes
        self._draw_number_boxes(center_x, center_y, half_size)

        # Draw buttons
        self.submit_button.draw(self.screen, self.fonts['normal'])
        self.load_button.draw(self.screen, self.fonts['normal'])
        self.quit_button.draw(self.screen, self.fonts['normal'])

        # Draw feedback message if any
        if self.game_session.state.feedback:
            color = (Colors.SUCCESS if self.game_session.state.feedback == 'Correct!'
                     else Colors.ERROR)
            feedback_surface = self.fonts['normal'].render(
                self.game_session.state.feedback, True, color
            )
            feedback_pos = (center_x, center_y + half_size + 80)
            self.screen.blit(
                feedback_surface,
                feedback_surface.get_rect(center=feedback_pos)
            )