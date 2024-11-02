from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from math_flashcards.utils.constants import DifficultyLevel, GameSettings
from math_flashcards.models.player import Player
from math_flashcards.models.question import Question

@dataclass
class LearningProgress:
    """Tracks learning progress metrics"""
    accuracy_trend: float = 0.0
    speed_trend: float = 0.0
    mastery_trend: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    data_points: List[Tuple[datetime, float, float, float]] = field(default_factory=list)
    window_size: int = 20  # Number of attempts to analyze

    def update(self, accuracy: float, response_time: float, mastery: float) -> None:
        """Update progress trends"""
        current_time = datetime.now()
        self.data_points.append((current_time, accuracy, response_time, mastery))
        
        # Keep only recent data points
        if len(self.data_points) > self.window_size:
            self.data_points.pop(0)
            
        # Calculate trends if enough data
        if len(self.data_points) >= 3:
            self.accuracy_trend = self._calculate_trend([p[1] for p in self.data_points])
            self.speed_trend = -self._calculate_trend([p[2] for p in self.data_points])  # Negative because lower is better
            self.mastery_trend = self._calculate_trend([p[3] for p in self.data_points])
            
        self.last_update = current_time

    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """Calculate trend line slope"""
        n = len(values)
        if n < 2:
            return 0.0
            
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        return numerator / denominator if denominator != 0 else 0.0

@dataclass
class OperationAnalytics:
    """Analytics for specific operations"""
    total_attempts: int = 0
    correct_attempts: int = 0
    total_time_ms: float = 0.0
    fastest_time_ms: Optional[float] = None
    slowest_time_ms: Optional[float] = None
    fact_attempts: Dict[str, int] = field(default_factory=dict)
    fact_correct: Dict[str, int] = field(default_factory=dict)
    fact_times: Dict[str, List[float]] = field(default_factory=dict)
    learning_progress: LearningProgress = field(default_factory=LearningProgress)

    def update(self, fact: str, correct: bool, response_time_ms: float) -> None:
        """Update operation analytics"""
        self.total_attempts += 1
        if correct:
            self.correct_attempts += 1
            
        self.total_time_ms += response_time_ms
        
        # Update time records
        if self.fastest_time_ms is None or response_time_ms < self.fastest_time_ms:
            self.fastest_time_ms = response_time_ms
        if self.slowest_time_ms is None or response_time_ms > self.slowest_time_ms:
            self.slowest_time_ms = response_time_ms
            
        # Update fact statistics
        self.fact_attempts[fact] = self.fact_attempts.get(fact, 0) + 1
        if correct:
            self.fact_correct[fact] = self.fact_correct.get(fact, 0) + 1
            
        if fact not in self.fact_times:
            self.fact_times[fact] = []
        self.fact_times[fact].append(response_time_ms)
        
        # Update learning progress
        self.learning_progress.update(
            self.accuracy,
            self.average_response_time,
            self.get_fact_mastery(fact)
        )

    @property
    def accuracy(self) -> float:
        """Calculate overall accuracy"""
        return (self.correct_attempts / max(1, self.total_attempts)) * 100

    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        return self.total_time_ms / max(1, self.total_attempts)

    def get_fact_mastery(self, fact: str) -> float:
        """Calculate mastery level for specific fact"""
        attempts = self.fact_attempts.get(fact, 0)
        if attempts == 0:
            return 0.0
            
        correct = self.fact_correct.get(fact, 0)
        times = self.fact_times.get(fact, [])
        
        accuracy = correct / attempts
        avg_time = sum(times) / len(times)
        speed_factor = max(0, 1 - (avg_time / 5000))  # 5000ms baseline
        
        return (accuracy * 0.6 + speed_factor * 0.4)

class AnalyticsController:
    """Controls analytics processing and reporting"""
    def __init__(self):
        self.player: Optional[Player] = None
        self.operation_analytics: Dict[str, OperationAnalytics] = {
            op: OperationAnalytics() for op in ['+', '-', '*', '/']
        }
        self.difficulty_progress: Dict[DifficultyLevel, LearningProgress] = {
            level: LearningProgress() for level in DifficultyLevel
        }
        self.session_start = datetime.now()
        self.last_attempt: Optional[datetime] = None
        self.streak_start: Optional[datetime] = None

    def set_player(self, player: Player) -> None:
        """Set current player and initialize analytics"""
        self.player = player
        self.session_start = datetime.now()

    def record_attempt(self, question: Question, response_time_ms: float,
                      correct: bool, difficulty: DifficultyLevel) -> Dict:
        """Record and analyze an attempt"""
        if not self.player:
            return {}
            
        current_time = datetime.now()
        fact = question.get_fact_key()
        
        # Update operation analytics
        self.operation_analytics[question.operator].update(
            fact, correct, response_time_ms
        )
        
        # Update difficulty progress
        self.difficulty_progress[difficulty].update(
            correct * 100,  # Convert to percentage
            response_time_ms,
            self.operation_analytics[question.operator].get_fact_mastery(fact)
        )
        
        # Update streak timing
        if correct:
            if not self.streak_start:
                self.streak_start = current_time
        else:
            self.streak_start = None
            
        self.last_attempt = current_time
        
        # Generate analytics summary
        return self.generate_summary()

    def get_problematic_facts(self) -> Set[str]:
        """Get set of facts needing practice"""
        problematic = set()
        threshold = GameSettings.ANALYTICS['mastery_threshold']
        
        for op, analytics in self.operation_analytics.items():
            for fact in analytics.fact_attempts.keys():
                if analytics.get_fact_mastery(fact) < threshold:
                    problematic.add(f"{op}_{fact}")
                    
        return problematic

    def get_operation_recommendations(self) -> Dict[str, bool]:
        """Get recommendations for operation practice"""
        recommendations = {}
        for op, analytics in self.operation_analytics.items():
            # Recommend based on accuracy and trend
            needs_practice = (
                analytics.accuracy < 80 or
                analytics.learning_progress.accuracy_trend <= 0 or
                analytics.average_response_time > 3000
            )
            recommendations[op] = needs_practice
            
        return recommendations

    def get_recommended_difficulty(self) -> DifficultyLevel:
        """Get recommended difficulty level"""
        if not self.last_attempt:
            return DifficultyLevel.INTRO
            
        # Get current difficulty stats
        current_diff = self.player.get_recommended_difficulty()
        progress = self.difficulty_progress[current_diff]
        
        # Check if ready for next level
        if (progress.accuracy_trend > 0 and
            progress.speed_trend > 0 and
            progress.mastery_trend > 0):
            # Move up one level if not at max
            levels = list(DifficultyLevel)
            current_index = levels.index(current_diff)
            if current_index < len(levels) - 2:  # -2 to exclude CUSTOM
                return levels[current_index + 1]
                
        # Check if need to move down
        elif (progress.accuracy_trend < -0.1 or
              progress.speed_trend < -0.1):
            # Move down one level if not at min
            levels = list(DifficultyLevel)
            current_index = levels.index(current_diff)
            if current_index > 0:
                return levels[current_index - 1]
                
        return current_diff

    def generate_summary(self) -> Dict:
        """Generate comprehensive analytics summary"""
        return {
            'session_stats': {
                'duration_mins': (datetime.now() - self.session_start).total_seconds() / 60,
                'attempts_per_min': self._calculate_attempts_per_minute(),
                'current_streak_mins': self._calculate_streak_duration()
            },
            'operation_stats': {
                op: {
                    'accuracy': analytics.accuracy,
                    'avg_time': analytics.average_response_time,
                    'learning_progress': {
                        'accuracy_trend': analytics.learning_progress.accuracy_trend,
                        'speed_trend': analytics.learning_progress.speed_trend,
                        'mastery_trend': analytics.learning_progress.mastery_trend
                    },
                    'problematic_facts': [
                        fact for fact in analytics.fact_attempts.keys()
                        if analytics.get_fact_mastery(fact) < 
                        GameSettings.ANALYTICS['mastery_threshold']
                    ]
                }
                for op, analytics in self.operation_analytics.items()
            },
            'difficulty_progress': {
                diff.value: {
                    'accuracy_trend': progress.accuracy_trend,
                    'speed_trend': progress.speed_trend,
                    'mastery_trend': progress.mastery_trend
                }
                for diff, progress in self.difficulty_progress.items()
            },
            'recommendations': {
                'difficulty': self.get_recommended_difficulty(),
                'operations': self.get_operation_recommendations(),
                'problematic_facts': self.get_problematic_facts()
            }
        }

    def _calculate_attempts_per_minute(self) -> float:
        """Calculate attempts per minute for current session"""
        if not self.last_attempt:
            return 0.0
            
        session_mins = (datetime.now() - self.session_start).total_seconds() / 60
        total_attempts = sum(analytics.total_attempts 
                           for analytics in self.operation_analytics.values())
        
        return total_attempts / max(1, session_mins)

    def _calculate_streak_duration(self) -> float:
        """Calculate current streak duration in minutes"""
        if not self.streak_start:
            return 0.0
            
        return (datetime.now() - self.streak_start).total_seconds() / 60

    def get_session_achievements(self) -> List[Dict]:
        """Get list of achievements earned this session"""
        achievements = []
        
        # Check speed achievement
        for op, analytics in self.operation_analytics.items():
            if (analytics.total_attempts >= 10 and 
                analytics.average_response_time < 2000):
                achievements.append({
                    'type': 'speed',
                    'name': 'Speed Demon',
                    'description': f'Average time under 2 seconds for {op}!'
                })
        
        # Check accuracy achievement
        for op, analytics in self.operation_analytics.items():
            if (analytics.total_attempts >= 10 and 
                analytics.accuracy >= 95):
                achievements.append({
                    'type': 'accuracy',
                    'name': 'Precision Master',
                    'description': f'95% accuracy with {op}!'
                })
        
        # Check mastery achievements
        for op, analytics in self.operation_analytics.items():
            mastered_facts = sum(1 for fact in analytics.fact_attempts.keys()
                               if analytics.get_fact_mastery(fact) >= 0.9)
            if mastered_facts >= 10:
                achievements.append({
                    'type': 'mastery',
                    'name': 'Fact Master',
                    'description': f'Mastered 10 facts with {op}!'
                })
        
        return achievements

    def clean_old_data(self, days: int = 30) -> None:
        """Clean up old analytics data"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for analytics in self.operation_analytics.values():
            analytics.data_points = [
                point for point in analytics.data_points
                if point[0] > cutoff
            ]
            
        for progress in self.difficulty_progress.values():
            progress.data_points = [
                point for point in progress.data_points
                if point[0] > cutoff
            ]
