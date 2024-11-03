import os
import sys
import pathlib
import pygame
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from math_flashcards.utils.constants import DifficultyLevel, GameSettings, Layout, Colors
from math_flashcards.models.player import Player
from math_flashcards.models.game_session import GameSession
from math_flashcards.views.game_window import GameWindow
from math_flashcards.views.login_dialog import LoginDialog
from math_flashcards.controllers.analytics_controller import AnalyticsController
from math_flashcards.controllers.player_controller import PlayerController

class GameState(Enum):
    """Game states for flow control"""
    LOGIN = "login"
    PLAYING = "playing"
    PAUSED = "paused"
    STATS = "stats"
    EXIT = "exit"

class GameController:
    """Main game controller coordinating all components"""
    def __init__(self, width: int = 800, height: int = 600):
        """Initialize the game controller"""
        self.width = width
        self.height = height

        if getattr(sys, 'frozen', False):
            base_dir = pathlib.Path(sys._MEIPASS)
        else:
            base_dir = pathlib.Path(__file__).parent.parent

        # Initialize pygame first
        pygame.init()
        
        # Initialize layout before creating windows
        self.layout = Layout()
        self.layout.WINDOW_WIDTH = width
        self.layout.WINDOW_HEIGHT = height

        # Load Icon
        icon_path = base_dir / "data" / "icon.jpg"
        icon = pygame.image.load(str(icon_path))
        pygame.display.set_icon(icon)

        # # Load Icon
        # icon = pygame.image.load('data/icon.jpg')
        # pygame.display.set_icon(icon)

        # Set up initial window
        pygame.display.set_caption('Math Flash Cards @ All Saints')
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE
        )
        
        # Initialize controllers
        self.player_controller = PlayerController()
        self.analytics_controller = AnalyticsController()
        
        # Initialize game state
        self.state = GameState.LOGIN
        self.game_window = None
        self.login_dialog = None
        self.game_session = None
        self.current_player = None
        
        # Initialize achievement tracking
        self.pending_achievements: list[Dict[str, Any]] = []
        
        # Initialize auto-save timer
        self.last_save_time = pygame.time.get_ticks()
        
        # Initialize fonts
        self.fonts = {
            size: pygame.font.Font(None, GameSettings.FONT_SIZES[size])
            for size in GameSettings.FONT_SIZES
        }

    def run(self) -> None:
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running and self.state != GameState.EXIT:
            current_time = pygame.time.get_ticks()
            
            # Handle different game states
            if self.state == GameState.LOGIN:
                running = self._handle_login(current_time)
            elif self.state == GameState.PLAYING:
                running = self._handle_playing(current_time)
            elif self.state == GameState.PAUSED:
                running = self._handle_paused(current_time)
            elif self.state == GameState.STATS:
                running = self._handle_stats(current_time)
            
            # Auto-save if needed
            self._check_auto_save(current_time)
            
            # Process achievement notifications
            self._process_achievements()
            
            clock.tick(60)
        
        self._cleanup()
        pygame.quit()

    def _handle_login(self, current_time: int) -> bool:
        """Handle login state events"""
        if not self.login_dialog:
            self.login_dialog = LoginDialog(self.screen, self.layout)
            self.login_dialog.set_player_list(self.player_controller.load_players())
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
                
            selected_name = self.login_dialog.handle_event(event)
            if selected_name:
                success = self._handle_player_selection(selected_name)
                if success:
                    self.state = GameState.PLAYING
        
        self.login_dialog.update(current_time)
        self.login_dialog.draw()
        return True

    def _handle_playing(self, current_time: int) -> bool:
        """Handle playing state events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                    continue
                    
            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
                
            if event.type == pygame.USEREVENT:
                if event.dict.get('action') == 'load':
                    # Save current player's progress
                    if self.current_player:
                        self.player_controller.save_progress(force=True)
                    # Reset to login state
                    self.state = GameState.LOGIN
                    self.login_dialog = None
                    continue
                elif event.dict.get('action') == 'quit':
                    # Save progress before quitting
                    if self.current_player:
                        self.player_controller.save_progress(force=True)
                    self.state = GameState.EXIT
                    return False
                
            self.game_window.handle_event(event)
        
        self.game_window.update(current_time)
        self.game_window.draw()
        return True

    def _handle_paused(self, current_time: int) -> bool:
        """Handle paused state events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_TAB:
                    self.state = GameState.STATS
                    
            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
        
        self._draw_pause_screen()
        return True

    def _handle_stats(self, current_time: int) -> bool:
        """Handle stats state events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PLAYING
                    
            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
        
        self._draw_stats_screen()
        return True

    def _handle_player_selection(self, name: str) -> bool:
        """Handle player selection or creation"""
        # Try to select existing player
        player = self.player_controller.select_player(name)
        if not player:
            # Create new player if doesn't exist
            player = self.player_controller.create_player(name)
            if not player:
                return False

        self.current_player = player

        # Initialize game components
        self.game_session = GameSession(player, self.player_controller)
        self.game_window = GameWindow(self.width, self.height)
        self.game_window.set_game_session(self.game_session)

        # Initialize analytics
        self.analytics_controller.set_player(player)

        return True

    def _handle_resize(self, width: int, height: int) -> None:
        """Handle window resize event"""
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE
        )
        
        # Update layout dimensions
        self.layout.WINDOW_WIDTH = width
        self.layout.WINDOW_HEIGHT = height
        
        if self.game_window:
            self.game_window = GameWindow(self.width, self.height)
            self.game_window.set_game_session(self.game_session)
        
        if self.login_dialog:
            self.login_dialog = LoginDialog(self.screen, self.layout)
            self.login_dialog.set_player_list(self.player_controller.load_players())

    def _check_auto_save(self, current_time: int) -> None:
        """Check and perform auto-save if needed"""
        if (current_time - self.last_save_time > 
            GameSettings.ANALYTICS['save_interval'] * 1000):
            if self.current_player:
                self.player_controller.save_progress()
            self.last_save_time = current_time

    def _process_achievements(self) -> None:
        """Process and display pending achievements"""
        if not self.pending_achievements:
            return
            
        # Process one achievement at a time
        achievement = self.pending_achievements[0]
        if self._display_achievement(achievement):
            self.pending_achievements.pop(0)

    def _display_achievement(self, achievement: Dict[str, Any]) -> bool:
        """Display achievement notification - returns True when complete"""
        # For now, just return True to clear it
        # In a full implementation, this would handle the animation
        return True

    def _draw_pause_screen(self) -> None:
        """Draw the pause screen overlay"""
        # Store current screen
        screen_copy = self.screen.copy()
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause menu
        font = self.fonts['large']
        text = font.render("PAUSED", True, Colors.WHITE)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)
        
        # Draw instructions
        font = self.fonts['small']
        instructions = [
            "Press ESC to resume",
            "Press TAB for statistics",
            "Press Q to quit"
        ]
        
        y = text_rect.bottom + 20
        for instruction in instructions:
            text = font.render(instruction, True, Colors.WHITE)
            text_rect = text.get_rect(center=(self.width // 2, y))
            self.screen.blit(text, text_rect)
            y += 30
        
        pygame.display.flip()

    def _draw_stats_screen(self) -> None:
        """Draw the statistics screen"""
        if not self.current_player:
            return
            
        # Get stats data
        stats = self.player_controller.get_player_stats()
        
        # Create stats screen
        screen_copy = self.screen.copy()
        self.screen.fill(Colors.WHITE)
        
        # Draw header
        font = self.fonts['large']
        header = font.render(f"Statistics for {self.current_player.name}", 
                           True, Colors.BLACK)
        header_rect = header.get_rect(
            centerx=self.width // 2,
            top=20
        )
        self.screen.blit(header, header_rect)
        
        # Draw stats sections
        self._draw_stats_section("Overall Performance", stats["overall"], 
                               (20, header_rect.bottom + 20))
        self._draw_stats_section("Operation Mastery", stats["operations"],
                               (20, header_rect.bottom + 200))
        self._draw_stats_section("Achievements", stats["achievements"],
                               (self.width // 2 + 20, header_rect.bottom + 20))
        self._draw_recent_sessions(stats["recent_sessions"],
                                 (self.width // 2 + 20, header_rect.bottom + 200))
        
        pygame.display.flip()

    def _draw_stats_section(self, title: str, data: Dict[str, Any], 
                          pos: Tuple[int, int]) -> None:
        """Draw a section of statistics"""
        font = self.fonts['normal']
        small_font = self.fonts['small']
        
        # Draw section title
        title_surface = font.render(title, True, Colors.BLACK)
        self.screen.blit(title_surface, pos)
        
        # Draw stats
        y = pos[1] + title_surface.get_height() + 10
        for key, value in data.items():
            if isinstance(value, (int, float)):
                text = f"{key.replace('_', ' ').title()}: {value:.1f}" \
                       if isinstance(value, float) else \
                       f"{key.replace('_', ' ').title()}: {value}"
                text_surface = small_font.render(text, True, Colors.TEXT_GRAY)
                self.screen.blit(text_surface, (pos[0] + 10, y))
                y += text_surface.get_height() + 5

    def _draw_recent_sessions(self, sessions: list[Dict[str, Any]], 
                            pos: Tuple[int, int]) -> None:
        """Draw recent sessions chart"""
        font = self.fonts['normal']
        small_font = self.fonts['small']
        
        # Draw section title
        title_surface = font.render("Recent Sessions", True, Colors.BLACK)
        self.screen.blit(title_surface, pos)
        
        # Draw sessions as mini bar chart
        chart_width = 300
        bar_height = 20
        bar_spacing = 5
        max_accuracy = 100
        
        y = pos[1] + title_surface.get_height() + 10
        for session in reversed(sessions[-10:]):  # Show last 10 sessions
            # Draw date
            date_text = small_font.render(session["date"], True, Colors.TEXT_GRAY)
            self.screen.blit(date_text, (pos[0], y))
            
            # Draw accuracy bar
            bar_width = int((session["accuracy"] / max_accuracy) * chart_width)
            bar_rect = pygame.Rect(
                pos[0] + 100,
                y,
                bar_width,
                bar_height
            )
            pygame.draw.rect(self.screen, Colors.HIGHLIGHT, bar_rect)
            
            # Draw accuracy value
            accuracy_text = small_font.render(
                f"{session['accuracy']:.1f}%", True, Colors.BLACK
            )
            self.screen.blit(accuracy_text, 
                           (bar_rect.right + 5, y + 2))
            
            y += bar_height + bar_spacing

    def _cleanup(self) -> None:
        """Clean up before exiting"""
        if self.current_player:
            self.player_controller.save_progress(force=True)
            self.player_controller.cleanup_old_sessions()
