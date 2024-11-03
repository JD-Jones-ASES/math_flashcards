import pygame
from typing import Dict, Optional, Tuple, Any
from math_flashcards.utils.constants import Colors, Layout, GameSettings
from math_flashcards.models.game_session import GameSession
import math

import pygame
from typing import Dict, Optional, Tuple, Any
from math_flashcards.utils.constants import Colors, Layout, GameSettings
import math

import pygame
from typing import Dict, Optional, Tuple, Any
from math_flashcards.utils.constants import Colors, Layout, GameSettings
import math


class Button:
    """Interactive button with clean, modern style"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, color: Optional[Tuple[int, int, int]] = None,
                 style: str = 'default',
                 border_radius: int = 20):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = color or Colors.HIGHLIGHT
        self.style = style
        self.hover = False
        self.disabled = False
        self.selected = False
        self.border_radius = border_radius
        self._pressed = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button with a clean, modern style"""
        # Calculate colors
        if self.disabled:
            fill_color = (245, 245, 245)
            border_color = Colors.BORDER_GRAY
        else:
            # Create a very light tint of the base color
            # Mix more white but keep some of the original color
            fill_color = tuple(int((c * 0.15) + (255 * 0.85)) for c in self.base_color)

            if self.selected:
                # Selected state: slightly stronger fill color
                fill_color = tuple(int((c * 0.25) + (255 * 0.75)) for c in self.base_color)
                border_color = self.base_color
            elif self.hover:
                # Hover: slightly stronger than normal
                fill_color = tuple(int((c * 0.2) + (255 * 0.8)) for c in self.base_color)
                border_color = self.base_color
            else:
                border_color = self.base_color

        # Pressed effect
        if self._pressed and not self.disabled:
            self.rect.y += 1
            # Slightly stronger color when pressed
            fill_color = tuple(int((c * 0.3) + (255 * 0.7)) for c in self.base_color)

        # Draw filled background
        pygame.draw.rect(surface, fill_color, self.rect,
                         border_radius=self.border_radius)

        # Draw border - thicker for selected state
        border_width = 2 if self.selected else 1
        pygame.draw.rect(surface, border_color, self.rect,
                         border_radius=self.border_radius, width=border_width)

        # Draw text
        text_color = Colors.TEXT_GRAY if self.disabled else Colors.BLACK
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

        # Reset pressed offset
        if self._pressed and not self.disabled:
            self.rect.y -= 1

    def update_hover(self, pos: Tuple[int, int]) -> None:
        """Update hover state"""
        self.hover = self.rect.collidepoint(pos) and not self.disabled

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click"""
        if self.rect.collidepoint(pos) and not self.disabled:
            self._pressed = True
            return True
        return False

    def handle_release(self) -> None:
        """Handle mouse release"""
        self._pressed = False


class ListItem:
    """Clickable list item with checkbox"""

    def __init__(self, text: str, y_pos: int, layout: Layout, checked: bool = False):
        self.text = text
        self.checked = checked
        self.layout = layout
        self.rect = pygame.Rect(0, y_pos, layout.SIDEBAR_WIDTH, layout.LIST_ITEM_HEIGHT)
        self.checkbox_rect = pygame.Rect(
            layout.PADDING,
            y_pos + (layout.LIST_ITEM_HEIGHT - 16) // 2,
            16, 16
        )
        self.hover = False
        self._pressed = False
        self.disabled = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the list item with checkbox"""
        # Draw hover effect
        if self.hover and not self.disabled:
            pygame.draw.rect(surface, Colors.LIGHT_HIGHLIGHT, self.rect)

        # Draw checkbox
        # Draw checkbox background
        pygame.draw.rect(surface, Colors.WHITE, self.checkbox_rect)
        checkbox_color = Colors.BORDER_GRAY if self.disabled else Colors.HIGHLIGHT
        pygame.draw.rect(surface, checkbox_color, self.checkbox_rect, 1)

        if self.checked:
            # Draw checkmark
            check_color = Colors.TEXT_GRAY if self.disabled else Colors.HIGHLIGHT
            margin = 3
            # Draw checkmark as a small filled square for cleaner look
            inner_rect = pygame.Rect(
                self.checkbox_rect.x + margin,
                self.checkbox_rect.y + margin,
                self.checkbox_rect.width - (margin * 2),
                self.checkbox_rect.height - (margin * 2)
            )
            pygame.draw.rect(surface, check_color, inner_rect)

        # Draw text
        text_color = Colors.TEXT_GRAY if self.disabled else Colors.BLACK
        text_surface = font.render(self.text, True, text_color)
        text_pos = (self.checkbox_rect.right + self.layout.PADDING,
                    self.rect.centery - text_surface.get_height() // 2)
        surface.blit(text_surface, text_pos)

    def update_hover(self, pos: Tuple[int, int]) -> None:
        """Update hover state"""
        self.hover = self.rect.collidepoint(pos) and not self.disabled

    def handle_click(self, pos: Tuple[int, int], total_checked: int) -> bool:
        """Handle mouse click with selection constraints"""
        if self.rect.collidepoint(pos):
            if self.checked and total_checked <= 1:
                self.disabled = True
                return False
            if not self.checked or total_checked > 1:
                self.disabled = False
                self.checked = not self.checked
                return True
        return False

    def handle_release(self) -> None:
        """Handle mouse release"""
        self._pressed = False


class StatsPanel:
    """Panel displaying player statistics"""

    def __init__(self, layout: Layout):
        self.layout = layout
        self.game_session: Optional[Any] = None
        self.panel_height = 200
        self.rect = pygame.Rect(
            layout.PADDING,
            layout.WINDOW_HEIGHT - self.panel_height - layout.PADDING,
            layout.SIDEBAR_WIDTH - layout.PADDING * 2,
            self.panel_height
        )

    def set_game_session(self, session: Any) -> None:
        """Set the game session to display stats for"""
        self.game_session = session

    def draw(self, surface: pygame.Surface, fonts: Dict[str, pygame.font.Font]) -> None:
        """Draw the stats panel"""
        if not self.game_session:
            return

        # Update rect position
        self.rect.bottom = self.layout.WINDOW_HEIGHT - self.layout.PADDING

        # Draw panel background with light fill and border
        pygame.draw.rect(surface, Colors.WHITE, self.rect, border_radius=4)
        pygame.draw.rect(surface, Colors.BORDER_GRAY, self.rect, 1, border_radius=4)

        # Draw player name
        name_surface = fonts['normal'].render(
            self.game_session.player.name, True, Colors.BLACK)
        name_rect = name_surface.get_rect(
            left=self.rect.left + self.layout.PADDING,
            top=self.rect.top + self.layout.PADDING
        )
        surface.blit(name_surface, name_rect)

        # Draw separator
        separator_y = name_rect.bottom + self.layout.PADDING
        pygame.draw.line(
            surface, Colors.BORDER_GRAY,
            (self.rect.left + self.layout.PADDING, separator_y),
            (self.rect.right - self.layout.PADDING, separator_y)
        )

        # Get and display stats
        stats = self.game_session.get_stats()
        y = separator_y + self.layout.PADDING
        padding = 5

        # Format and draw statistics
        stats_display = [
            (f"Score: {stats['correct']}/{stats['problems_attempted']}", Colors.BLACK),
            (f"Accuracy: {stats['accuracy']:.1f}%",
             Colors.SUCCESS if stats['accuracy'] >= 80 else Colors.TEXT_GRAY),
            (f"Current Streak: {stats['current_streak']}", Colors.BLACK),
            (f"Best Streak: {stats['best_streak']}", Colors.BLACK)
        ]

        for text, color in stats_display:
            text_surface = fonts['small'].render(text, True, color)
            surface.blit(text_surface, (
                self.rect.left + self.layout.PADDING,
                y
            ))
            y += text_surface.get_height() + padding

        # Draw another separator
        separator_y = y + padding
        pygame.draw.line(
            surface, Colors.BORDER_GRAY,
            (self.rect.left + self.layout.PADDING, separator_y),
            (self.rect.right - self.layout.PADDING, separator_y)
        )

        # Draw mode info
        y = separator_y + padding * 2
        mode_info = [
            f"Mode: {stats['difficulty']}",
            f"Operations: {', '.join(GameSettings.OPERATION_SYMBOLS[op] for op in stats['operators'])}"
        ]

        for text in mode_info:
            text_surface = fonts['small'].render(text, True, Colors.TEXT_GRAY)
            surface.blit(text_surface, (
                self.rect.left + self.layout.PADDING,
                y
            ))
            y += text_surface.get_height() + padding


class ScrollableList:
    """Scrollable list with optional search"""

    def __init__(self, rect: pygame.Rect, items: list[str],
                 item_height: int, max_visible: int):
        self.rect = rect
        self.items = items
        self.item_height = item_height
        self.max_visible = max_visible
        self.scroll_offset = 0
        self.selected_index = -1
        self.hover_index = -1

        # Create scroll buttons
        button_width = 25
        button_height = 20
        self.scroll_up = Button(
            rect.right - button_width - 5,
            rect.top - button_height - 5,
            button_width, button_height,
            "↑"
        )
        self.scroll_down = Button(
            rect.right - button_width - 5,
            rect.bottom + 5,
            button_width, button_height,
            "↓"
        )

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the scrollable list"""
        # Draw list background
        pygame.draw.rect(surface, Colors.WHITE, self.rect)
        pygame.draw.rect(surface, Colors.BORDER_GRAY, self.rect, 1)

        # Draw visible items
        visible_items = self.items[self.scroll_offset:
                                   self.scroll_offset + self.max_visible]
        for i, item in enumerate(visible_items):
            item_rect = pygame.Rect(
                self.rect.left,
                self.rect.top + i * self.item_height,
                self.rect.width,
                self.item_height
            )

            # Draw selection/hover highlight
            real_index = i + self.scroll_offset
            if real_index == self.selected_index:
                pygame.draw.rect(surface, Colors.HIGHLIGHT, item_rect)
                text_color = Colors.WHITE
            elif real_index == self.hover_index:
                pygame.draw.rect(surface, Colors.LIGHT_HIGHLIGHT, item_rect)
                text_color = Colors.BLACK
            else:
                text_color = Colors.BLACK

            # Draw item text
            text_surface = font.render(item, True, text_color)
            text_rect = text_surface.get_rect(
                left=item_rect.left + 10,
                centery=item_rect.centery
            )
            surface.blit(text_surface, text_rect)

            # Draw separator line
            if i < len(visible_items) - 1:
                pygame.draw.line(
                    surface, Colors.BORDER_GRAY,
                    (item_rect.left, item_rect.bottom),
                    (item_rect.right, item_rect.bottom)
                )

        # Draw scroll buttons if needed
        if len(self.items) > self.max_visible:
            self.scroll_up.disabled = self.scroll_offset == 0
            self.scroll_down.disabled = (self.scroll_offset >=
                                         len(self.items) - self.max_visible)
            self.scroll_up.draw(surface, font)
            self.scroll_down.draw(surface, font)

    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click and return selected item if any"""
        # Check scroll buttons
        if self.scroll_up.handle_click(pos):
            self.scroll(-1)
            return None

        if self.scroll_down.handle_click(pos):
            self.scroll(1)
            return None

        # Only handle selection on left click
        if pygame.mouse.get_pressed()[0]:  # Left click
            # Check item clicks
            if self.rect.collidepoint(pos):
                y_offset = pos[1] - self.rect.top
                clicked_index = self.scroll_offset + y_offset // self.item_height

                if 0 <= clicked_index < len(self.items):
                    self.selected_index = clicked_index
                    return self.items[clicked_index]

        return None

    def handle_scroll(self, y: int) -> None:
        """Handle mouse wheel scrolling"""
        # Scroll up if y is positive, down if negative
        if y > 0:
            self.scroll(1)
        elif y < 0:
            self.scroll(-1)

    def scroll(self, direction: int) -> None:
        """Scroll the list up or down"""
        if len(self.items) <= self.max_visible:
            return

        new_offset = self.scroll_offset + direction

        # Clamp the scroll offset
        max_offset = len(self.items) - self.max_visible
        new_offset = max(0, min(new_offset, max_offset))

        self.scroll_offset = new_offset

    def update_hover(self, pos: Tuple[int, int]) -> None:
        """Update hover states"""
        self.scroll_up.update_hover(pos)
        self.scroll_down.update_hover(pos)

        if self.rect.collidepoint(pos):
            y_offset = pos[1] - self.rect.top
            hover_index = self.scroll_offset + y_offset // self.item_height
            if 0 <= hover_index < len(self.items):
                self.hover_index = hover_index
        else:
            self.hover_index = -1