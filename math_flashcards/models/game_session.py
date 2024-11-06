from dataclasses import dataclass, field
from typing import Set, Optional, Dict, List, Any
from datetime import datetime
import time
import pygame
from math_flashcards.utils.constants import DifficultyLevel, GameSettings
from math_flashcards.models.player import Player
from math_flashcards.models.question import Question, QuestionConfig

@dataclass
class GameState:
    """Current game state information"""
    difficulty: DifficultyLevel = DifficultyLevel.INTRO
    selected_operators: Set[str] = field(default_factory=lambda: {'+',})
    current_question: Optional[Any] = None  # Change from Question to Any
    user_input: str = ''
    feedback: str = ''
    feedback_timer: int = 0
    cursor_visible: bool = True
    cursor_timer: int = 0
    session_start_time: float = field(default_factory=time.time)
    question_start_time: float = field(default_factory=time.time)

class GameSession:
    """Manages the active game session"""
    def __init__(self, player: Player, player_controller: Any):  # Change PlayerController to Any
        self.player = player
        self.player_controller = player_controller
        self.state = GameState()
        self.player.start_new_session()
        self.generate_new_question()

    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle keyboard input for the current question"""
        if not self.state.current_question:
            return False

        config = QuestionConfig.from_difficulty(self.state.difficulty)

        # Handle both regular Enter and numpad Enter
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.state.user_input:
            self.check_answer()
            return True

        elif event.key == pygame.K_BACKSPACE:
            self.state.user_input = self.state.user_input[:-1]
            return True

        elif event.unicode.isprintable():
            # Allow minus sign only at start of input
            if (event.unicode == '-' and not self.state.user_input and
                    self.state.current_question.validate_input('-', config.max_digits)):
                self.state.user_input = '-'
                return True

            # For all other input, validate against current constraints
            if self.state.current_question.validate_input(
                    self.state.user_input + event.unicode,
                    config.max_digits
            ):
                self.state.user_input += event.unicode
                return True

        return False

    def check_answer(self) -> bool:
        """Check the current answer and update statistics"""
        if not self.state.current_question:
            return False
            
        # Calculate response time
        response_time_ms = (time.time() - self.state.question_start_time) * 1000
        
        # Check answer
        correct = self.state.current_question.check_answer(self.state.user_input)
        
        # Get fact key for tracking
        fact_key = self.state.current_question.get_fact_key()
        
        # Update player statistics
        self.player.record_attempt(
            operation=self.state.current_question.operator,
            difficulty=self.state.difficulty,
            fact=fact_key,
            correct=correct,
            response_time_ms=response_time_ms
        )
        
        # Update session data
        current_session = self.player.recent_sessions[-1]
        current_session.problems_attempted += 1
        if correct:
            current_session.correct += 1
        current_session.operations_used.add(self.state.current_question.operator)
        current_session.difficulty_levels.add(self.state.difficulty.value)
        
        # Calculate running average response time
        current_session.avg_response_time_ms = (
            (current_session.avg_response_time_ms * (current_session.problems_attempted - 1) 
             + response_time_ms) / current_session.problems_attempted
        )
        
        # Update duration
        current_session.duration_mins = (time.time() - self.state.session_start_time) / 60
        
        # Set feedback
        if correct:
            self.state.feedback = 'Correct!'
            self.state.feedback_timer = pygame.time.get_ticks()
            self.generate_new_question()
        else:
            self.state.feedback = 'incorrect'  # Changed from 'Try Again!' to use as a state identifier
            self.state.feedback_timer = pygame.time.get_ticks()
            self.state.user_input = ''
            
        return correct

    def generate_new_question(self) -> None:
	    """Generate a new question based on current settings"""
	    if not self.state.selected_operators:
	        self.state.selected_operators = {'+'}
	        
	    # Get configuration based on difficulty
	    if self.state.difficulty == DifficultyLevel.CUSTOM:
	        # Pass full operation stats for custom configuration
	        config = QuestionConfig.create_custom(self.player.operation_stats)
	    else:
	        config = QuestionConfig.from_difficulty(self.state.difficulty)
	    
	    # IMPORTANT: Override the operators in the config with only the selected operators
	    config.operators = list(self.state.selected_operators)
	    
	    # Get problematic facts if appropriate
	    problematic_facts = None
	    if self.state.difficulty in {DifficultyLevel.CUSTOM, DifficultyLevel.MEDIUM}:
	        problematic_facts = {
	            f"{op}_{fact}" 
	            for op in self.state.selected_operators  # Only use selected operators
	            for fact, mastery in self.player.operation_stats[op].fact_mastery.items()
	            if mastery < GameSettings.ANALYTICS['mastery_threshold']
	        }
	        
	    # Generate new question
	    self.state.current_question = Question.generate(config, problematic_facts)
	    self.state.user_input = ''
	    self.state.feedback = ''
	    self.state.question_start_time = time.time()

    def update_operators(self, operator: str, active: bool) -> None:
	    """Update the set of active operators"""
	    # If trying to deactivate an operator
	    if not active:
	        # Only allow deactivation if more than one operator is currently selected
	        if len(self.state.selected_operators) > 1:
	            self.state.selected_operators.discard(operator)
	    else:
	        # Always allow adding new operators
	        self.state.selected_operators.add(operator)

    def update_difficulty(self, new_difficulty: DifficultyLevel) -> bool:
        """Update difficulty level if requirements are met"""
        if new_difficulty == DifficultyLevel.CUSTOM:
            if not self.player.can_use_custom_mode():
                self.state.feedback = 'Complete more problems to unlock Custom mode!'
                self.state.feedback_timer = pygame.time.get_ticks()
                return False
                
        self.state.difficulty = new_difficulty
        return True

    def update(self, current_time: int) -> None:
        """Update animation states"""
        # Update cursor blink
        if current_time - self.state.cursor_timer > GameSettings.ANIMATION['cursor_blink_time']:
            self.state.cursor_visible = not self.state.cursor_visible
            self.state.cursor_timer = current_time
            
        # Clear feedback if timer expired
        if (self.state.feedback and 
            current_time - self.state.feedback_timer > GameSettings.ANIMATION['feedback_duration']):
            self.state.feedback = ''

    def get_stats(self) -> Dict:
        """Get current session statistics"""
        return {
            'problems_attempted': self.player.recent_sessions[-1].problems_attempted,
            'correct': self.player.recent_sessions[-1].correct,
            'current_streak': self.player.current_streak,
            'best_streak': self.player.best_streak,
            'accuracy': (
                self.player.recent_sessions[-1].correct / 
                max(1, self.player.recent_sessions[-1].problems_attempted) * 100
            ),
            'avg_response_time': self.player.recent_sessions[-1].avg_response_time_ms,
            'difficulty': self.state.difficulty.value,
            'operators': list(self.state.selected_operators)
        }

    def get_display_numbers(self) -> tuple[str, str, str]:
        """Get the numbers to display in the UI"""
        if not self.state.current_question:
            return ('', '', '')
        return self.state.current_question.get_display_numbers()

    def get_recommended_settings(self) -> Dict:
        """Get recommended settings based on player performance"""
        return {
            'difficulty': self.player.get_recommended_difficulty(),
            'operators': [
                op for op in ['+', '-', '*', '/']
                if self.player.get_mastery_level(op) > 0.4
            ],
            'problematic_facts': [
                f"{op}_{fact}"
                for op in self.state.selected_operators
                for fact, mastery in self.player.operation_stats[op].fact_mastery.items()
                if mastery < GameSettings.ANALYTICS['mastery_threshold']
            ]
        }

    def save_session(self) -> None:
        """Save the current session data"""
        # Update final session duration
        current_session = self.player.recent_sessions[-1]
        current_session.duration_mins = (time.time() - self.state.session_start_time) / 60
