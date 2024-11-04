import pygame
from typing import Optional, List, Dict, Tuple
from math_flashcards.utils.constants import Colors, Layout, GameSettings
from math_flashcards.views.ui_components import Button, ScrollableList


class PlayerInput:
    """Input field for player name with validation"""

    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.text = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.active = True
        self.max_length = 20
        self.error_message = ""
        self.error_timer = 0

        # Create validation rules
        self.invalid_chars = set('<>:"/\\|?*')

    def handle_input(self, event: pygame.event.Event) -> None:
        """Handle keyboard input"""
        if not self.active:
            return

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            self.error_message = ""
        elif event.key == pygame.K_RETURN:
            pass  # Handled by dialog
        elif event.unicode:
            # Validate input
            if event.unicode in self.invalid_chars:
                self.error_message = "Invalid character"
                self.error_timer = pygame.time.get_ticks()
                return

            if len(self.text) < self.max_length:
                self.text += event.unicode
                self.error_message = ""

    def update(self, current_time: int) -> None:
        """Update animation states"""
        # Update cursor blink
        if current_time - self.cursor_timer > GameSettings.ANIMATION['cursor_blink_time']:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time

        # Clear error message after delay
        if (self.error_message and
                current_time - self.error_timer > GameSettings.ANIMATION['feedback_duration']):
            self.error_message = ""

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the input field with modern styling"""
        # Draw input box with shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(surface, Colors.NAVY_DARKEST, shadow_rect, border_radius=10)

        # Draw main box
        pygame.draw.rect(surface, Colors.WHITE, self.rect, border_radius=10)

        # Draw glossy highlight on top half
        highlight_rect = self.rect.copy()
        highlight_rect.height = self.rect.height // 2
        highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(highlight_surface, (255, 255, 255, 25),
                         highlight_surface.get_rect(), border_radius=10)
        surface.blit(highlight_surface, highlight_rect)

        # Draw border with glow effect if active
        border_color = Colors.HIGHLIGHT if self.active else Colors.BORDER_GRAY
        if self.active:
            # Draw outer glow
            for offset in range(3):
                glow_rect = self.rect.inflate(offset * 2, offset * 2)
                pygame.draw.rect(surface, (*Colors.NAVY_LIGHTEST, 30),
                                 glow_rect, border_radius=10, width=1)

        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=10)

        # Draw text
        display_text = self.text
        if self.active and self.cursor_visible:
            display_text += "|"

        if display_text:
            # Add subtle text shadow
            shadow_surface = font.render(display_text, True, (0, 0, 0, 128))
            shadow_rect = shadow_surface.get_rect(center=self.rect.center)
            shadow_rect.y += 1
            surface.blit(shadow_surface, shadow_rect)

            # Draw main text
            text_surface = font.render(display_text, True, Colors.NAVY_PRIMARY)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)

        # Draw error message if any
        if self.error_message:
            error_surface = font.render(self.error_message, True, Colors.ERROR)
            error_pos = (self.rect.centerx, self.rect.bottom + 20)
            surface.blit(error_surface, error_surface.get_rect(center=error_pos))

class LoginDialog:
    """Dialog for player selection and creation"""
    def __init__(self, screen: pygame.Surface, layout: Layout):
        """Initialize the login dialog"""
        self.screen = screen
        if layout is None:
            layout = Layout()
        self.layout = layout
        
        # Store background
        self.background = screen.copy()
        self.stored_background = False
        
        # Calculate dialog dimensions - now with fixed height
        self.dialog_width = min(500, self.layout.WINDOW_WIDTH - 40)  # Add margin
        self.dialog_height = min(600, self.layout.WINDOW_HEIGHT - 40)  # Add margin
        self.dialog_x = (layout.WINDOW_WIDTH - self.dialog_width) // 2
        self.dialog_y = (layout.WINDOW_HEIGHT - self.dialog_height) // 2
        
        # Create dialog rect
        self.dialog_rect = pygame.Rect(
            self.dialog_x, self.dialog_y,
            self.dialog_width, self.dialog_height
        )
        
        # Fixed heights for components
        self.title_height = 40
        self.input_section_height = 120  # Space for label, input, and create button
        self.list_section_label_height = 30
        
        # Calculate available height for player list
        self.available_list_height = (
            self.dialog_height - 
            self.title_height - 
            self.input_section_height - 
            self.list_section_label_height - 
            40  # Additional padding
        )
        
        # Create input field
        input_width = min(300, self.dialog_width - 40)
        input_height = self.layout.DIALOG_INPUT_HEIGHT
        input_x = self.dialog_x + (self.dialog_width - input_width) // 2
        input_y = self.dialog_y + self.title_height + 30
        self.name_input = PlayerInput(pygame.Rect(
            input_x, input_y, input_width, input_height
        ))
        
        # Create buttons
        button_width = input_width
        button_height = self.layout.DIALOG_BUTTON_HEIGHT
        self.new_player_button = Button(
            input_x,
            input_y + input_height + 10,
            button_width,
            button_height,
            "Create New Player"
        )
        
        # Create player list with calculated height
        list_width = input_width
        visible_items = max(3, self.available_list_height // self.layout.DIALOG_LIST_ITEM_HEIGHT)
        list_y = (self.dialog_y + self.title_height + 
                 self.input_section_height + self.list_section_label_height)
        
        self.player_list = ScrollableList(
            pygame.Rect(input_x, list_y, list_width, self.available_list_height),
            [],  # Will be populated later
            self.layout.DIALOG_LIST_ITEM_HEIGHT,
            visible_items
        )
        
        # Initialize fonts
        self.fonts = {
            size: pygame.font.Font(None, GameSettings.FONT_SIZES[size])
            for size in GameSettings.FONT_SIZES
        }

    def set_player_list(self, players: List[str]) -> None:
        """Update the list of available players"""
        self.player_list.items = sorted(players)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events and return selected player name when ready"""
        if event.type == pygame.KEYDOWN:
            self.name_input.handle_input(event)
            if event.key == pygame.K_RETURN and self.name_input.text.strip():
                return self._validate_new_player(self.name_input.text.strip())
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle mouse wheel scrolling
            if event.button in (4, 5):  # 4 is scroll up, 5 is scroll down
                self.player_list.handle_scroll(1 if event.button == 5 else -1)
                return None
                
            # Handle new player button
            if (self.new_player_button.handle_click(event.pos) and 
                self.name_input.text.strip()):
                return self._validate_new_player(self.name_input.text.strip())
                
            # Handle player list selection
            selected = self.player_list.handle_click(event.pos)
            if selected:
                return selected
                
        return None

    def _validate_new_player(self, name: str) -> Optional[str]:
        """Validate new player name"""
        if name in self.player_list.items:
            self.name_input.error_message = "Name already exists"
            self.name_input.error_timer = pygame.time.get_ticks()
            return None
            
        if len(name) < 2:
            self.name_input.error_message = "Name too short"
            self.name_input.error_timer = pygame.time.get_ticks()
            return None
            
        return name

    def update(self, current_time: int) -> None:
        """Update animation states"""
        self.name_input.update(current_time)
        
        # Update hover states
        mouse_pos = pygame.mouse.get_pos()
        self.new_player_button.update_hover(mouse_pos)
        self.player_list.update_hover(mouse_pos)

    def draw(self) -> None:
        """Draw the login dialog with enhanced styling"""
        # Store or restore background
        if not self.stored_background:
            self.background = self.screen.copy()
            self.stored_background = True
        else:
            self.screen.blit(self.background, (0, 0))

        # Draw dark overlay with blur effect
        overlay = pygame.Surface((self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        # Draw dialog box with shadow
        shadow_offset = 4
        shadow_rect = self.dialog_rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(self.screen, Colors.NAVY_DARKEST, shadow_rect, border_radius=12)

        # Main panel with subtle gradient
        dialog_surface = pygame.Surface((self.dialog_rect.width, self.dialog_rect.height), pygame.SRCALPHA)
        for y in range(self.dialog_rect.height):
            progress = y / self.dialog_rect.height
            color = self._lerp_color(
                (250, 252, 255, 255),  # Very light blue-white at top
                (240, 245, 255, 255),  # Slightly more blue at bottom
                progress
            )
            pygame.draw.line(dialog_surface, color, (0, y), (self.dialog_rect.width, y))

        self.screen.blit(dialog_surface, self.dialog_rect)
        pygame.draw.rect(self.screen, Colors.BORDER_GRAY, self.dialog_rect, 2, border_radius=12)

        # Draw title with gradient header
        header_height = 50
        header_rect = pygame.Rect(
            self.dialog_rect.x,
            self.dialog_rect.y,
            self.dialog_rect.width,
            header_height
        )
        header_surface = pygame.Surface((header_rect.width, header_height), pygame.SRCALPHA)

        for y in range(header_height):
            progress = y / header_height
            color = self._lerp_color(Colors.NAVY_PRIMARY, Colors.NAVY_LIGHT, progress)
            pygame.draw.line(header_surface, color, (0, y), (header_rect.width, y))

        self.screen.blit(header_surface, header_rect)

        # Draw title text with glow
        title = "Welcome to Math Flash Cards!"
        title_text = self.fonts['normal'].render(title, True, Colors.WHITE)
        title_rect = title_text.get_rect(
            centerx=self.dialog_rect.centerx,
            centery=header_rect.centery
        )

        # Add glow effect
        glow_surface = pygame.Surface((title_text.get_width() + 4, title_text.get_height() + 4), pygame.SRCALPHA)
        glow_text = self.fonts['normal'].render(title, True, (*Colors.NAVY_LIGHTEST, 128))
        glow_rect = glow_text.get_rect(center=(glow_surface.get_width() // 2, glow_surface.get_height() // 2))
        glow_surface.blit(glow_text, glow_rect)
        self.screen.blit(glow_surface, title_rect)
        self.screen.blit(title_text, title_rect)

        # Draw input field with enhanced styling
        self.name_input.draw(self.screen, self.fonts['normal'])

        # Draw create button (already styled nicely)
        self.new_player_button.draw(self.screen, self.fonts['normal'])

        # Draw player list section with enhanced styling
        returning_text = self.fonts['small'].render(
            "Player List:", True, Colors.NAVY_PRIMARY
        )
        returning_rect = returning_text.get_rect(
            centerx=self.dialog_rect.centerx,
            bottom=self.player_list.rect.top - 10
        )
        self.screen.blit(returning_text, returning_rect)

        # Draw enhanced player list
        self.player_list.draw(self.screen, self.fonts['normal'])

        # Update display
        pygame.display.flip()

    def _lerp_color(self, color1: tuple, color2: tuple, progress: float) -> tuple:
        """Linearly interpolate between two colors"""
        return tuple(
            int(c1 + (c2 - c1) * progress)
            for c1, c2 in zip(color1, color2)
        )

