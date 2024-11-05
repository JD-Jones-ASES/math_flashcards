from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
import random
from datetime import datetime, timedelta
from math_flashcards.utils.constants import DifficultyLevel, GameSettings
from math_flashcards.models.player import Player, OperationStats


@dataclass
class OperationBoundary:
    """Tracks the difficulty boundaries for an operation"""
    min_number: int = 1
    max_number: int = 10
    comfort_zone: Tuple[int, int] = (1, 10)
    accuracy_threshold: float = 0.8
    speed_threshold: float = 4000  # ms
    recent_trend: float = 0.0
    suggested_step: int = 1

    def adjust_bounds(self, success: bool, response_time: float) -> None:
        """Dynamically adjust boundaries based on performance"""
        if success and response_time < self.speed_threshold:
            self.max_number = min(100, self.max_number + self.suggested_step)
        elif not success and response_time > self.speed_threshold * 1.5:
            self.max_number = max(10, self.max_number - self.suggested_step * 2)

        # Update comfort zone based on recent performance
        self.comfort_zone = (
            max(1, self.max_number - 5),
            self.max_number
        )


@dataclass
class CustomDifficultyAnalyzer:
    """Enhanced analyzer for custom difficulty mode"""
    operation_boundaries: Dict[str, OperationBoundary] = None
    performance_window: int = 7  # Number of recent attempts to analyze
    adaptation_rate: float = 0.4  # How quickly to adjust difficulty

    def __post_init__(self):
        if self.operation_boundaries is None:
            self.operation_boundaries = {
                op: OperationBoundary() for op in ['+', '-', '*', '/']
            }

    def analyze_performance(self, operation_stats: Dict[str, OperationStats]) -> Dict:
        """Analyze performance to find optimal difficulty settings"""
        total_attempts = sum(stats.problems_attempted for stats in operation_stats.values())
        if total_attempts == 0:
            return self._get_default_config()

        # Analyze each operation's boundaries
        viable_operators = []
        max_range = 10
        allows_negative = False
        requires_decimals = False
        focus_facts = set()

        for op, stats in operation_stats.items():
            if stats.problems_attempted == 0:
                continue

            boundary = self.operation_boundaries[op]

            # Calculate recent trend
            recent_trend = self._calculate_recent_trend(stats.recent_response_times)
            boundary.recent_trend = recent_trend

            # Analyze mastery distribution
            mastery_levels = list(stats.fact_mastery.values())
            if mastery_levels:
                avg_mastery = sum(mastery_levels) / len(mastery_levels)

                # Adjust boundaries based on mastery
                if avg_mastery > 0.8:
                    boundary.suggested_step = 2
                elif avg_mastery < 0.4:
                    boundary.suggested_step = 1

            # Determine if operation is viable
            if (stats.accuracy >= 70 and stats.problems_attempted >= 10) or \
                    (stats.last_practiced and
                     datetime.now() - stats.last_practiced < timedelta(days=2)):
                viable_operators.append(op)

                # Update maximum range based on performance
                if stats.accuracy >= 85:
                    max_range = max(max_range, boundary.max_number)

                # Collect struggling facts
                focus_facts.update(
                    f"{op}_{fact}" for fact, mastery in stats.fact_mastery.items()
                    if mastery < GameSettings.ANALYTICS['mastery_threshold']
                )

        # If no viable operators found, use most practiced
        if not viable_operators and operation_stats:
            most_practiced = max(
                operation_stats.items(),
                key=lambda x: x[1].problems_attempted
            )
            viable_operators = [most_practiced[0]]

        # Check readiness for advanced features
        avg_accuracy = sum(
            stats.accuracy for stats in operation_stats.values()
            if stats.problems_attempted > 0
        ) / len([s for s in operation_stats.values() if s.problems_attempted > 0])

        allows_negative = any(
            stats.accuracy >= 75 for stats in operation_stats.values()
            if stats.problems_attempted >= 20
        ) and avg_accuracy >= 80

        requires_decimals = (
                '/' in viable_operators and
                operation_stats['/'].accuracy >= 85 and
                avg_accuracy >= 85
        )

        return {
            'number_range': (1, max_range),
            'operators': viable_operators,
            'max_digits': 2 if avg_accuracy >= 80 else 1,
            'allows_negative': allows_negative,
            'requires_decimals': requires_decimals,
            'focus_facts': focus_facts,
            'adaptive_timing': True
        }

    def get_next_question_config(
            self, player: Player, current_config: Dict,
            last_response_time: Optional[float] = None,
            last_correct: Optional[bool] = None
    ) -> Dict:
        """Dynamically adjust configuration based on recent performance"""
        if not player or not current_config:
            return current_config

        new_config = current_config.copy()

        # Adjust based on immediate performance
        if last_response_time is not None and last_correct is not None:
            # Get active operator boundary
            if player.recent_sessions and player.recent_sessions[-1].operations_used:
                current_op = list(player.recent_sessions[-1].operations_used)[0]
                boundary = self.operation_boundaries[current_op]

                # Update boundary based on performance
                boundary.adjust_bounds(last_correct, last_response_time)

                # Update number range
                new_config['number_range'] = (
                    boundary.comfort_zone[0],
                    boundary.comfort_zone[1]
                )

        # Get recent struggles for focused practice
        recent_struggles = player.get_recent_struggles()
        if recent_struggles:
            new_config['focus_facts'] = recent_struggles

        # Check for fatigue
        if player.recent_sessions:
            current_session = player.recent_sessions[-1]
            if current_session.avg_response_time_ms > 5000:  # Fatigue threshold
                # Temporarily reduce difficulty
                new_config['number_range'] = (
                    new_config['number_range'][0],
                    max(10, new_config['number_range'][1] - 5)
                )

        return new_config

    def _calculate_recent_trend(self, response_times: List[float]) -> float:
        """Calculate trend from recent response times"""
        if len(response_times) < 2:
            return 0.0

        x = list(range(len(response_times)))
        y = response_times

        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)

        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)

        return numerator / denominator if denominator != 0 else 0.0

    def _get_default_config(self) -> Dict:
        """Return default configuration for new players"""
        return {
            'number_range': (1, 10),
            'operators': ['+'],
            'max_digits': 1,
            'allows_negative': False,
            'requires_decimals': False,
            'focus_facts': set(),
            'adaptive_timing': False
        }