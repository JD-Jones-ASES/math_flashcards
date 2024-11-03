from typing import Dict, Optional, Tuple, Any
import pygame
from math_flashcards.utils.constants import Colors, Layout, DifficultyLevel, GameSettings
from math_flashcards.models.player import Player
from math_flashcards.views.login_dialog import LoginDialog
from math_flashcards.views.ui_components import Button, ListItem, StatsPanel
import math
from math_flashcards.utils.version import (
    VERSION, APP_NAME, APP_AUTHOR, APP_COPYRIGHT,
    APP_LICENSE, APP_REPOSITORY
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
        pygame.display.set_caption('Math Flash Cards')

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
            "Submit", Colors.HIGHLIGHT
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
            "Load", Colors.HIGHLIGHT
        )
        
        self.quit_button = Button(
            quit_x, buttons_y,
            self.layout.BUTTON_WIDTH, self.layout.BUTTON_HEIGHT,
            "Quit", Colors.ERROR
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
	    # Calculate position below operations list with spacing
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
	            settings['color']
	        )
	        y += self.layout.BUTTON_HEIGHT + button_spacing
	    
	    # Add Custom mode button at the bottom with some extra spacing
	    buttons[DifficultyLevel.CUSTOM] = Button(
	        self.layout.PADDING,
	        y + button_spacing,
	        button_width,
	        self.layout.BUTTON_HEIGHT,
	        DifficultyLevel.CUSTOM.value,
	        GameSettings.DIFFICULTY_SETTINGS[DifficultyLevel.CUSTOM]['color']
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

            # Update admin message timer if exists
            if self.admin_message and current_time - self.admin_message_timer > 2000:  # 2 seconds
                self.admin_message = None

        # Update game session
        self.game_session.update(current_time)

    def draw(self) -> None:
        """Draw the complete game interface"""
        if not self.game_session:
            return

        self.screen.fill(Colors.WIN_GRAY)
        self._draw_sidebar()
        self._draw_main_content()

        # Draw control buttons
        self._draw_control_button(self.admin_button_rect, 'admin',
                                  self.admin_button_hover,
                                  self.admin_button_pressed)
        self._draw_control_button(self.info_button_rect, 'info',
                                  self.info_button_hover,
                                  self.info_button_pressed)

        # Draw panels
        if self.admin_panel_open:
            self._draw_admin_panel()
        elif self.info_panel_open:
            self._draw_about_panel()

        pygame.display.flip()

    def _draw_sidebar(self) -> None:
	    """Draw the sidebar with controls and stats"""
	    # Draw sidebar background
	    sidebar_rect = pygame.Rect(0, 0, 
	                             self.layout.SIDEBAR_WIDTH, 
	                             self.layout.WINDOW_HEIGHT)
	    pygame.draw.rect(self.screen, Colors.WHITE, sidebar_rect)
	    
	    # Draw header
	    header_rect = pygame.Rect(0, 0, 
	                            self.layout.SIDEBAR_WIDTH, 
	                            self.layout.HEADER_HEIGHT)
	    pygame.draw.rect(self.screen, Colors.HIGHLIGHT, header_rect)
	    header_text = self.fonts['small'].render("Operations", True, Colors.WHITE)
	    self.screen.blit(
	        header_text, 
	        (self.layout.PADDING, 
	         (self.layout.HEADER_HEIGHT - header_text.get_height()) // 2)
	    )
	    
	    # Draw separator line
	    pygame.draw.line(
	        self.screen, Colors.BORDER_GRAY,
	        (self.layout.SIDEBAR_WIDTH - 1, 0),
	        (self.layout.SIDEBAR_WIDTH - 1, self.layout.WINDOW_HEIGHT)
	    )
	    
	    # Draw operation items
	    for item in self.operation_items.values():
	        item.draw(self.screen, self.fonts['small'])  # Using smaller font
	    
	    # Draw difficulty section header
	    operations_height = (self.layout.HEADER_HEIGHT + self.layout.PADDING + 
	                       self.layout.LIST_ITEM_HEIGHT * 4)
	    diff_label_y = operations_height + self.layout.SECTION_SPACING
	    diff_label = self.fonts['small'].render("Difficulty Level", True, Colors.BLACK)
	    self.screen.blit(
	        diff_label,
	        (self.layout.PADDING, diff_label_y)
	    )
	    
	    # Draw difficulty buttons
	    for difficulty, button in self.difficulty_buttons.items():
	        button.selected = (difficulty == self.game_session.state.difficulty)
	        button.disabled = (difficulty == DifficultyLevel.CUSTOM and 
	                         not self.game_session.player.can_use_custom_mode())
	        button.draw(self.screen, self.fonts['small'])
	    
	    # Draw stats panel at the bottom
	    self.stats_panel.draw(self.screen, self.fonts)

    def _draw_main_content(self) -> None:
        """Draw the main game area with the triangle and problem"""
        if not self.game_session.state.current_question:
            return
            
        # Calculate triangle points
        center_x = self.layout.content_center_x
        center_y = self.layout.content_center_y
        half_size = self.layout.TRIANGLE_SIZE // 2
        
        triangle_points = [
            (center_x, center_y + half_size),  # Bottom
            (center_x - half_size, center_y - half_size),  # Top left
            (center_x + half_size, center_y - half_size)   # Top right
        ]
        
        # Draw triangle
        pygame.draw.polygon(self.screen, Colors.HIGHLIGHT, triangle_points, 3)
        
        # Draw operator
        operator = self.game_session.state.current_question.operator
        block_size = 60  # Adjust size as needed
        block_rect = pygame.Rect(
            center_x - block_size // 2,
            center_y - block_size // 2,
            block_size,
            block_size
        )
        self._draw_operator_block(operator, block_rect)
        
        # Draw number boxes
        self._draw_number_boxes(center_x, center_y, half_size)
        
        # Draw submit button
        self.submit_button.draw(self.screen, self.fonts['normal'])
        
        # Draw load and quit buttons
        self.load_button.draw(self.screen, self.fonts['normal'])
        self.quit_button.draw(self.screen, self.fonts['normal'])
        
        # Draw feedback
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
            
        # Draw feedback
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

    def _draw_number_boxes(self, center_x: int, center_y: int, half_size: int) -> None:
        """Draw the number input boxes"""
        box_positions = {
            'left': (center_x - half_size + 40, center_y - half_size + 60),
            'right': (center_x + half_size - 40, center_y - half_size + 60),
            'bottom': (center_x, center_y + half_size - 40)
        }
        
        left, right, bottom = self.game_session.get_display_numbers()
        values = {'left': left, 'right': right, 'bottom': bottom}
        
        for position, center_pos in box_positions.items():
            box_rect = pygame.Rect(
                center_pos[0] - self.layout.INPUT_BOX_WIDTH // 2,
                center_pos[1] - self.layout.INPUT_BOX_HEIGHT // 2,
                self.layout.INPUT_BOX_WIDTH,
                self.layout.INPUT_BOX_HEIGHT
            )
            
            # Draw box background and border
            pygame.draw.rect(self.screen, Colors.WHITE, box_rect)
            pygame.draw.rect(self.screen, Colors.HIGHLIGHT, box_rect, 2)
            
            # Draw text or input
            text = ''
            if (isinstance(values[position], str) and not values[position] and 
                self.game_session.state.current_question.missing_position == 
                list(box_positions.keys()).index(position)):
                text = self.game_session.state.user_input
                if self.game_session.state.cursor_visible:
                    text += '|'
            else:
                text = values[position]
                
            if text:
                text_surface = self.fonts['normal'].render(text, True, Colors.BLACK)
                self.screen.blit(
                    text_surface,
                    text_surface.get_rect(center=box_rect.center)
                )

    def _draw_about_panel(self) -> None:
        """Draw the about/info panel with game information"""
        if not self.game_session:
            return

        # Create semi-transparent overlay
        overlay = pygame.Surface((self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        # Calculate panel dimensions
        panel_width = min(600, self.layout.WINDOW_WIDTH - 100)
        panel_height = min(500, self.layout.WINDOW_HEIGHT - 100)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, Colors.WHITE, panel_rect)
        pygame.draw.rect(self.screen, Colors.BORDER_GRAY, panel_rect, 2)

        # Draw header
        header_height = 40
        header_rect = pygame.Rect(panel_x, panel_y, panel_width, header_height)
        pygame.draw.rect(self.screen, (65, 135, 255), header_rect)  # Match info button color

        header_text = self.fonts['normal'].render("About Math Flash Cards", True, Colors.WHITE)
        self.screen.blit(header_text, (
            panel_x + 15,
            panel_y + (header_height - header_text.get_height()) // 2
        ))

        # Content area
        content_x = panel_x + 20
        content_y = panel_y + header_height + 20
        line_height = 30

        # About content
        about_text = [
            (APP_NAME, Colors.BLACK, 'normal'),
            (f"Version {VERSION}", Colors.TEXT_GRAY, 'small'),
            ("", None, None),  # Spacer
            ("An interactive math practice application featuring:", Colors.BLACK, 'small'),
            ("• Adaptive Learning", Colors.TEXT_GRAY, 'small'),
            ("• Multiple Operation Types", Colors.TEXT_GRAY, 'small'),
            ("• Custom Difficulty Modes", Colors.TEXT_GRAY, 'small'),
            ("• Progress Tracking", Colors.TEXT_GRAY, 'small'),
            ("", None, None),  # Spacer
            (f"Created by {APP_AUTHOR}", Colors.BLACK, 'small'),
            (f"100% Open Source", Colors.INTRO_MODE, 'small'),
            (f"{APP_LICENSE} License", Colors.TEXT_GRAY, 'small'),
            ("", None, None),  # Spacer
            (APP_COPYRIGHT, Colors.TEXT_GRAY, 'small'),
            ("", None, None),  # Spacer
            ("Click anywhere outside this panel to close", Colors.TEXT_GRAY, 'small')
        ]

        # # About content
        # about_text = [
        #     ("Math Flash Cards", Colors.BLACK, 'normal'),
        #     ("Version 0.8.0-beta+1", Colors.TEXT_GRAY, 'small'),
        #     ("", None, None),  # Spacer
        #     ("An interactive math practice application featuring:", Colors.BLACK, 'small'),
        #     ("• Adaptive Learning", Colors.TEXT_GRAY, 'small'),
        #     ("• Multiple Operation Types", Colors.TEXT_GRAY, 'small'),
        #     ("• Custom Difficulty Modes", Colors.TEXT_GRAY, 'small'),
        #     ("• Detailed Analytics", Colors.TEXT_GRAY, 'small'),
        #     ("• Progress Tracking", Colors.TEXT_GRAY, 'small'),
        #     ("", None, None),  # Spacer
        #     ("Created by JD Jones", Colors.BLACK, 'small'),
        #     ("MIT Open Source", Colors.TEXT_GRAY, 'small'),
        #     ("", None, None),  # Spacer
        #     ("Click anywhere outside this panel to close", Colors.TEXT_GRAY, 'small')
        # ]

        for line in about_text:
            if line[1] is None:  # Spacer
                content_y += line_height // 2
                continue

            text_surface = self.fonts[line[2]].render(line[0], True, line[1])
            self.screen.blit(text_surface, (content_x, content_y))
            content_y += line_height

    def _draw_admin_panel(self) -> None:
        """Draw the admin panel with player management"""
        if not self.game_session:
            return

        # Create semi-transparent overlay
        overlay = pygame.Surface((self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        # Calculate panel dimensions
        panel_width = min(600, self.layout.WINDOW_WIDTH - 100)
        panel_height = min(500, self.layout.WINDOW_HEIGHT - 100)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, Colors.WHITE, panel_rect)
        pygame.draw.rect(self.screen, Colors.BORDER_GRAY, panel_rect, 2)

        # Draw header
        header_height = 40
        header_rect = pygame.Rect(panel_x, panel_y, panel_width, header_height)
        pygame.draw.rect(self.screen, Colors.HIGHLIGHT, header_rect)

        header_text = self.fonts['normal'].render("Player Management", True, Colors.WHITE)
        self.screen.blit(header_text, (
            panel_x + 15,
            panel_y + (header_height - header_text.get_height()) // 2
        ))

        # Calculate content area
        content_x = panel_x + 15
        content_y = panel_y + header_height + 10
        content_width = panel_width - 30
        content_height = panel_height - header_height - 20

        # Draw player list
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
        """Draw scrollable player list with delete options"""
        # Get player list from game session's player controller
        player_controller = self.game_session.player_controller
        players = player_controller.load_players()

        # Calculate list metrics
        item_height = 40
        visible_items = height // item_height
        max_scroll = max(0, len(players) - visible_items)

        # Draw visible players
        for i, player in enumerate(players[self.admin_scroll_offset:
        self.admin_scroll_offset + visible_items]):
            item_y = y + (i * item_height)
            item_rect = pygame.Rect(x, item_y, width, item_height)

            # Draw hover highlight
            if self.admin_hover_player == (i + self.admin_scroll_offset):
                pygame.draw.rect(self.screen, Colors.LIGHT_HIGHLIGHT, item_rect)

            # Draw player name
            name_surface = self.fonts['small'].render(player, True, Colors.BLACK)
            self.screen.blit(name_surface, (x + 10, item_y + 10))

            # Draw delete button only for non-protected players
            if player != "Mr. Jones":
                delete_rect = pygame.Rect(
                    x + width - 40,  # Wider clickable area
                    item_y + (item_height - 30) // 2,  # Centered vertically
                    30,  # Wider button
                    30  # Taller button
                )

                # Draw delete button background on hover
                button_hover = (self.admin_hover_player == (i + self.admin_scroll_offset) and
                                delete_rect.collidepoint(pygame.mouse.get_pos()))

                if button_hover:
                    pygame.draw.rect(self.screen, Colors.ERROR, delete_rect, border_radius=15)
                    delete_text = self.fonts['small'].render("×", True, Colors.WHITE)
                else:
                    delete_text = self.fonts['small'].render("×", True, Colors.ERROR)

                # Center the × symbol in the button
                text_rect = delete_text.get_rect(center=delete_rect.center)
                self.screen.blit(delete_text, text_rect)

            # Draw separator line
            if i < len(players) - 1:
                pygame.draw.line(
                    self.screen,
                    Colors.BORDER_GRAY,
                    (x, item_y + item_height),
                    (x + width, item_y + item_height)
                )

        # Draw scroll bar if needed
        if max_scroll > 0:
            scroll_bar_width = 8
            scroll_bar_height = height
            scroll_bar_x = x + width - scroll_bar_width

            # Draw scroll bar background
            pygame.draw.rect(
                self.screen,
                Colors.WIN_GRAY,
                (scroll_bar_x, y, scroll_bar_width, scroll_bar_height)
            )

            # Draw scroll bar handle
            handle_height = max(40, scroll_bar_height * (visible_items / len(players)))
            handle_pos = (self.admin_scroll_offset / max_scroll) * (scroll_bar_height - handle_height)
            pygame.draw.rect(
                self.screen,
                Colors.BORDER_GRAY,
                (scroll_bar_x, y + handle_pos, scroll_bar_width, handle_height)
            )

    def _draw_delete_confirmation(self, x: int, y: int, width: int, height: int) -> None:
        """Draw delete confirmation dialog"""
        # Draw confirmation message
        msg = f"Are you sure you want to delete player '{self.admin_confirm_delete}'?"
        msg_surface = self.fonts['normal'].render(msg, True, Colors.BLACK)
        msg_pos = (
            x + (width - msg_surface.get_width()) // 2,
            y + height // 3
        )
        self.screen.blit(msg_surface, msg_pos)

        # Draw buttons
        button_width = 100
        button_height = 36
        button_y = y + (height * 2 // 3)

        # Cancel button
        cancel_x = x + (width // 2) - button_width - 10
        cancel_rect = pygame.Rect(cancel_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, Colors.BORDER_GRAY, cancel_rect)

        cancel_text = self.fonts['small'].render("Cancel", True, Colors.BLACK)
        self.screen.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

        # Delete button
        delete_x = x + (width // 2) + 10
        delete_rect = pygame.Rect(delete_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, Colors.ERROR, delete_rect)

        delete_text = self.fonts['small'].render("Delete", True, Colors.WHITE)
        self.screen.blit(delete_text, delete_text.get_rect(center=delete_rect.center))

        # Store rects for click handling
        self.admin_confirm_buttons = {
            'cancel': cancel_rect,
            'delete': delete_rect
        }

    def _handle_admin_panel_click(self, pos: Tuple[int, int]) -> bool:
        """Handle clicks in the admin panel"""
        if self.admin_confirm_delete:
            # Handle confirmation dialog buttons
            for action, rect in self.admin_confirm_buttons.items():
                if rect.collidepoint(pos):
                    if action == 'delete':
                        success = self.game_session.player_controller.delete_player(
                            self.admin_confirm_delete
                        )
                        self.admin_message = (
                            f"Player {self.admin_confirm_delete} deleted successfully"
                            if success else
                            f"Error deleting player {self.admin_confirm_delete}"
                        )
                        self.admin_message_timer = pygame.time.get_ticks()
                    self.admin_confirm_delete = None
                    return True
            return True

        # Calculate list area
        panel_width = min(600, self.layout.WINDOW_WIDTH - 100)
        panel_height = min(500, self.layout.WINDOW_HEIGHT - 100)
        panel_x = (self.layout.WINDOW_WIDTH - panel_width) // 2
        panel_y = (self.layout.WINDOW_HEIGHT - panel_height) // 2

        content_x = panel_x + 15
        content_y = panel_y + 50  # After header
        content_width = panel_width - 30
        item_height = 40

        # Check for clicks on delete buttons
        players = self.game_session.player_controller.load_players()
        visible_items = (panel_height - 70) // item_height

        for i, player in enumerate(players[self.admin_scroll_offset:
        self.admin_scroll_offset + visible_items]):
            if player == "Mr. Jones":
                continue

            item_y = content_y + (i * item_height)
            delete_rect = pygame.Rect(
                content_x + content_width - 40,  # Match _draw_player_list
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

        content_x = panel_x + 15
        content_y = panel_y + 50
        content_width = panel_width - 30
        item_height = 40

        # Check if mouse is over any player item
        rect = pygame.Rect(content_x, content_y, content_width, panel_height - 70)
        if rect.collidepoint(pos):
            index = (pos[1] - content_y) // item_height + self.admin_scroll_offset
            self.admin_hover_player = index
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

    def _draw_operator_block(self, operator: str, rect: pygame.Rect) -> None:
        """Draw an operator block with sophisticated visual effects"""
        # Color scheme
        BASE_COLOR = (25, 45, 85)  # Dark navy
        MID_COLOR = (35, 65, 115)  # Mid navy
        TOP_COLOR = (45, 85, 145)  # Light navy
        GLOW_COLOR = (65, 135, 255)  # Electric blue glow
        SYMBOL_COLOR = (240, 240, 255)  # Slightly off-white for better contrast
        EDGE_COLOR = (20, 35, 65)  # Darker navy for edges

        padding = 4  # For inner shadow effect
        radius = 12  # More pronounced rounded corners

        # Draw multi-layered background for depth
        for offset in range(3):
            shadow_rect = rect.inflate(-offset * 2, -offset * 2)
            pygame.draw.rect(self.screen, BASE_COLOR, shadow_rect,
                             border_radius=radius - offset)

        # Main block face with gradient effect
        inner_rect = rect.inflate(-padding * 2, -padding * 2)
        height = inner_rect.height
        for y in range(inner_rect.top, inner_rect.bottom):
            progress = (y - inner_rect.top) / height
            if progress < 0.5:
                # Top half - gradient from TOP_COLOR to MID_COLOR
                factor = progress * 2
                color = tuple(int(TOP_COLOR[i] + (MID_COLOR[i] - TOP_COLOR[i]) * factor)
                              for i in range(3))
            else:
                # Bottom half - gradient from MID_COLOR to BASE_COLOR
                factor = (progress - 0.5) * 2
                color = tuple(int(MID_COLOR[i] + (BASE_COLOR[i] - MID_COLOR[i]) * factor)
                              for i in range(3))

            pygame.draw.line(self.screen, color,
                             (inner_rect.left, y),
                             (inner_rect.right, y))

        # Redraw rounded corners for clean edges
        pygame.draw.rect(self.screen, EDGE_COLOR, inner_rect,
                         border_radius=radius - padding, width=1)

        # Draw glossy highlight
        highlight_rect = inner_rect.copy()
        highlight_rect.height = highlight_rect.height // 2
        highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(highlight_surface, (255, 255, 255, 25),
                         highlight_surface.get_rect(),
                         border_radius=radius - padding)
        self.screen.blit(highlight_surface, highlight_rect)

        # Center point for symbol drawing
        center = rect.center
        size = rect.width // 3
        symbol_thickness = 4

        # Function to draw glowing lines
        def draw_glow_line(start_pos, end_pos, thickness):
            # Outer glow
            for glow in range(3):
                glow_thickness = thickness + (3 - glow) * 2
                glow_alpha = max(0, min(100 - glow * 30, 255))  # Clamp alpha value
                glow_color = (*GLOW_COLOR, glow_alpha)
                glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.line(glow_surface, glow_color,
                                 (start_pos[0] - rect.left, start_pos[1] - rect.top),
                                 (end_pos[0] - rect.left, end_pos[1] - rect.top),
                                 glow_thickness)
                self.screen.blit(glow_surface, rect)

            # Main line
            pygame.draw.line(self.screen, SYMBOL_COLOR, start_pos, end_pos, thickness)

        # Draw operator symbol with glow effect
        if operator == '+':
            # Glowing plus
            draw_glow_line(
                (center[0] - size // 2, center[1]),
                (center[0] + size // 2, center[1]),
                symbol_thickness
            )
            draw_glow_line(
                (center[0], center[1] - size // 2),
                (center[0], center[1] + size // 2),
                symbol_thickness
            )
        elif operator == '-':
            # Glowing minus
            draw_glow_line(
                (center[0] - size // 2, center[1]),
                (center[0] + size // 2, center[1]),
                symbol_thickness
            )
        elif operator == '*':
            # Glowing multiply
            draw_glow_line(
                (center[0] - size // 2, center[1] - size // 2),
                (center[0] + size // 2, center[1] + size // 2),
                symbol_thickness
            )
            draw_glow_line(
                (center[0] - size // 2, center[1] + size // 2),
                (center[0] + size // 2, center[1] - size // 2),
                symbol_thickness
            )
        else:  # Division
            # Glowing divide with spherical dots
            dot_radius = symbol_thickness

            # Function to draw glowing circle
            def draw_glow_circle(pos, radius):
                for glow in range(3):
                    glow_radius = radius + (3 - glow) * 2
                    glow_alpha = max(0, min(100 - glow * 30, 255))  # Clamp alpha value
                    glow_color = (*GLOW_COLOR, glow_alpha)
                    glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, glow_color,
                                       (pos[0] - rect.left, pos[1] - rect.top),
                                       glow_radius)
                    self.screen.blit(glow_surface, rect)
                pygame.draw.circle(self.screen, SYMBOL_COLOR, pos, radius)

            draw_glow_circle((center[0], center[1] - size // 3), dot_radius)
            draw_glow_line(
                (center[0] - size // 2, center[1]),
                (center[0] + size // 2, center[1]),
                symbol_thickness
            )
            draw_glow_circle((center[0], center[1] + size // 3), dot_radius)

        try:
            # Add subtle pulsing animation
            current_time = pygame.time.get_ticks()
            pulse_alpha = int(abs(math.sin(current_time / 1000)) * 30)
            pulse_alpha = max(0, min(pulse_alpha, 255))  # Clamp alpha value
            pulse_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(pulse_surface, (*GLOW_COLOR, pulse_alpha),
                             pulse_surface.get_rect(),
                             border_radius=radius, width=2)
            self.screen.blit(pulse_surface, rect)
        except Exception as e:
            # Fail gracefully if pulse animation encounters any issues
            print(f"Pulse animation skipped: {e}")

    def _draw_control_button(self, rect: pygame.Rect, button_type: str,
                             hover: bool, pressed: bool) -> None:
        """Draw a stylized control button (admin or info)"""
        # Color schemes
        if button_type == 'admin':
            BASE_COLOR = (145, 45, 85)  # Deep rose
            MID_COLOR = (165, 65, 115)  # Mid rose
            TOP_COLOR = (185, 85, 145)  # Light rose
            GLOW_COLOR = (255, 135, 165)  # Pink glow
        else:  # info
            BASE_COLOR = (45, 85, 145)  # Deep teal
            MID_COLOR = (65, 115, 165)  # Mid teal
            TOP_COLOR = (85, 145, 185)  # Light teal
            GLOW_COLOR = (135, 215, 255)  # Cyan glow

        # Adjust colors if pressed
        if pressed:
            BASE_COLOR = tuple(max(0, c - 30) for c in BASE_COLOR)
            MID_COLOR = tuple(max(0, c - 30) for c in MID_COLOR)
            TOP_COLOR = tuple(max(0, c - 30) for c in TOP_COLOR)

        radius = 10  # Rounded corners
        padding = 3  # For inner shadow effect

        # Draw multi-layered background for depth
        for offset in range(3):
            shadow_rect = rect.inflate(-offset * 2, -offset * 2)
            pygame.draw.rect(self.screen, BASE_COLOR, shadow_rect,
                             border_radius=radius - offset)

        # Main button face with gradient effect
        inner_rect = rect.inflate(-padding * 2, -padding * 2)
        height = inner_rect.height

        # Gradient background
        for y in range(inner_rect.top, inner_rect.bottom):
            progress = (y - inner_rect.top) / height
            if progress < 0.5:
                factor = progress * 2
                color = tuple(int(TOP_COLOR[i] + (MID_COLOR[i] - TOP_COLOR[i]) * factor)
                              for i in range(3))
            else:
                factor = (progress - 0.5) * 2
                color = tuple(int(MID_COLOR[i] + (BASE_COLOR[i] - MID_COLOR[i]) * factor)
                              for i in range(3))

            pygame.draw.line(self.screen, color,
                             (inner_rect.left, y),
                             (inner_rect.right, y))

        # Draw icon
        icon_color = (240, 240, 255)  # Slightly off-white
        icon_surface = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
        icon_rect = icon_surface.get_rect()

        if button_type == 'admin':
            # Gear icon
            center = icon_rect.center
            outer_radius = min(icon_rect.width, icon_rect.height) // 3
            inner_radius = outer_radius * 0.7
            teeth = 8

            # Draw gear teeth with glow
            for i in range(teeth):
                angle = i * (360 / teeth)
                rad_angle = math.radians(angle)

                # Outer point
                outer_x = center[0] + outer_radius * math.cos(rad_angle)
                outer_y = center[1] + outer_radius * math.sin(rad_angle)

                # Inner point
                inner_x = center[0] + inner_radius * math.cos(rad_angle)
                inner_y = center[1] + inner_radius * math.sin(rad_angle)

                # Draw glowing tooth
                for glow in range(3):
                    glow_alpha = max(0, min(100 - glow * 30, 255))
                    pygame.draw.line(icon_surface, (*GLOW_COLOR, glow_alpha),
                                     (inner_x, inner_y),
                                     (outer_x, outer_y),
                                     3 - glow)

                pygame.draw.line(icon_surface, icon_color,
                                 (inner_x, inner_y),
                                 (outer_x, outer_y), 2)

            # Draw central circle
            pygame.draw.circle(icon_surface, icon_color, center, inner_radius - 2, 2)

        else:  # info icon
            # Stylized "i" with glow
            center = icon_rect.center
            radius = min(icon_rect.width, icon_rect.height) // 3

            # Draw dot
            for glow in range(3):
                glow_alpha = max(0, min(100 - glow * 30, 255))
                pygame.draw.circle(icon_surface, (*GLOW_COLOR, glow_alpha),
                                   (center[0], center[1] - radius),
                                   4 + glow)
            pygame.draw.circle(icon_surface, icon_color,
                               (center[0], center[1] - radius), 4)

            # Draw stem
            for glow in range(3):
                glow_alpha = max(0, min(100 - glow * 30, 255))
                pygame.draw.line(icon_surface, (*GLOW_COLOR, glow_alpha),
                                 (center[0], center[1] - radius + 8),
                                 (center[0], center[1] + radius),
                                 4 + glow)
            pygame.draw.line(icon_surface, icon_color,
                             (center[0], center[1] - radius + 8),
                             (center[0], center[1] + radius), 4)

        self.screen.blit(icon_surface, inner_rect)

        # Add hover glow
        if hover:
            current_time = pygame.time.get_ticks()
            base_alpha = int(abs(math.sin(current_time / 1000)) * 30)
            hover_alpha = max(0, min(base_alpha + (30 if hover else 0), 255))

            glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*GLOW_COLOR, hover_alpha),
                             glow_surface.get_rect(),
                             border_radius=radius, width=2)
            self.screen.blit(glow_surface, rect)