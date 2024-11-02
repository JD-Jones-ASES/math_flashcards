from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from math_flashcards.utils.constants import DifficultyLevel, GameSettings
# from math_flashcards.models.player import Player

@dataclass
class PerformanceMetrics:
    """Enhanced tracking of detailed performance metrics for analysis"""
    total_attempts: int = 0
    correct_attempts: int = 0
    total_time_ms: float = 0.0
    fastest_time_ms: Optional[float] = None
    slowest_time_ms: Optional[float] = None
    streak: int = 0
    best_streak: int = 0
    last_attempt_timestamp: Optional[datetime] = None
    
    # New fields for enhanced analytics
    response_times: List[float] = field(default_factory=list)
    correct_history: List[bool] = field(default_factory=list)
    time_between_attempts: List[float] = field(default_factory=list)
    window_size: int = 20  # For moving averages
    difficulty_levels: Dict[str, List[float]] = field(default_factory=dict)  # Track performance by difficulty
    confidence_scores: List[float] = field(default_factory=list)  # Track confidence in mastery

    def update(self, correct: bool, response_time_ms: float, difficulty: Optional[str] = None) -> None:
        """Update metrics with new attempt including enhanced analytics"""
        current_time = datetime.now()
        
        # Update basic metrics
        self.total_attempts += 1
        self.total_time_ms += response_time_ms
        self.last_attempt_timestamp = current_time
        
        # Update time records
        if self.fastest_time_ms is None or response_time_ms < self.fastest_time_ms:
            self.fastest_time_ms = response_time_ms
        if self.slowest_time_ms is None or response_time_ms > self.slowest_time_ms:
            self.slowest_time_ms = response_time_ms
            
        # Update streak information
        if correct:
            self.correct_attempts += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.streak = 0
            
        # Update enhanced analytics
        self.response_times.append(response_time_ms)
        self.correct_history.append(correct)
        
        # Calculate time between attempts
        if self.last_attempt_timestamp and len(self.time_between_attempts) > 0:
            time_diff = (current_time - self.last_attempt_timestamp).total_seconds()
            self.time_between_attempts.append(time_diff)
            
        # Track performance by difficulty level
        if difficulty:
            if difficulty not in self.difficulty_levels:
                self.difficulty_levels[difficulty] = []
            self.difficulty_levels[difficulty].append(response_time_ms)
            
        # Calculate and update confidence score
        confidence = self._calculate_confidence_score(correct, response_time_ms)
        self.confidence_scores.append(confidence)
        
        # Maintain window size for all lists
        self._trim_history()

    def _calculate_confidence_score(self, correct: bool, response_time_ms: float) -> float:
        """Calculate confidence score based on correctness and response time"""
        base_score = 1.0 if correct else 0.0
        
        # Adjust based on response time
        if self.fastest_time_ms and self.slowest_time_ms:
            time_range = self.slowest_time_ms - self.fastest_time_ms
            if time_range > 0:
                time_factor = (self.slowest_time_ms - response_time_ms) / time_range
                return base_score * (0.5 + 0.5 * time_factor)
        
        return base_score

    def _trim_history(self) -> None:
        """Maintain window size for historical data"""
        if len(self.response_times) > self.window_size:
            self.response_times = self.response_times[-self.window_size:]
        if len(self.correct_history) > self.window_size:
            self.correct_history = self.correct_history[-self.window_size:]
        if len(self.time_between_attempts) > self.window_size:
            self.time_between_attempts = self.time_between_attempts[-self.window_size:]
        if len(self.confidence_scores) > self.window_size:
            self.confidence_scores = self.confidence_scores[-self.window_size:]
        
        # Trim difficulty level histories
        for difficulty in self.difficulty_levels:
            if len(self.difficulty_levels[difficulty]) > self.window_size:
                self.difficulty_levels[difficulty] = \
                    self.difficulty_levels[difficulty][-self.window_size:]

    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_attempts / self.total_attempts) * 100

    @property
    def average_time_ms(self) -> float:
        """Calculate average response time"""
        if self.total_attempts == 0:
            return 0.0
        return self.total_time_ms / self.total_attempts

    @property
    def recent_accuracy(self) -> float:
        """Calculate accuracy over recent attempts"""
        if not self.correct_history:
            return 0.0
        recent = self.correct_history[-self.window_size:]
        return (sum(1 for x in recent if x) / len(recent)) * 100

    @property
    def recent_average_time(self) -> float:
        """Calculate average time over recent attempts"""
        if not self.response_times:
            return 0.0
        recent = self.response_times[-self.window_size:]
        return sum(recent) / len(recent)

    def get_trend(self) -> Dict[str, float]:
        """Calculate performance trends"""
        if len(self.response_times) < 2:
            return {
                'time_trend': 0.0,
                'accuracy_trend': 0.0,
                'confidence_trend': 0.0
            }
            
        time_trend = self._calculate_trend(self.response_times)
        accuracy_trend = self._calculate_trend([float(x) for x in self.correct_history])
        confidence_trend = self._calculate_trend(self.confidence_scores)
        
        return {
            'time_trend': -time_trend,  # Negative because decreasing time is good
            'accuracy_trend': accuracy_trend,
            'confidence_trend': confidence_trend
        }

    def get_difficulty_analysis(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance across difficulty levels"""
        analysis = {}
        for difficulty, times in self.difficulty_levels.items():
            if times:
                analysis[difficulty] = {
                    'average_time': sum(times) / len(times),
                    'best_time': min(times),
                    'trend': self._calculate_trend(times)
                }
        return analysis

    def get_mastery_score(self) -> float:
        """Calculate overall mastery score without numpy dependency"""
        if not self.confidence_scores:
            return 0.0

        recent_confidence = self.confidence_scores[-self.window_size:]
        base_mastery = sum(recent_confidence) / len(recent_confidence)

        # Calculate variance manually if we have enough data
        if len(recent_confidence) >= 3:
            mean = base_mastery
            variance = sum((x - mean) ** 2 for x in recent_confidence) / len(recent_confidence)
            consistency_factor = max(0, 1 - variance)
            return base_mastery * (0.7 + 0.3 * consistency_factor)

        return base_mastery

    # def get_mastery_score(self) -> float:
    #     """Calculate overall mastery score"""
    #     if not self.confidence_scores:
    #         return 0.0
    #
    #     recent_confidence = self.confidence_scores[-self.window_size:]
    #     base_mastery = sum(recent_confidence) / len(recent_confidence)
    #
    #     # Adjust for consistency
    #     if len(recent_confidence) >= 3:
    #         variance = np.var(recent_confidence) if len(recent_confidence) > 1 else 0
    #         consistency_factor = max(0, 1 - variance)
    #         return base_mastery * (0.7 + 0.3 * consistency_factor)
    #
    #     return base_mastery

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend line slope"""
        if len(values) < 2:
            return 0.0
            
        x = list(range(len(values)))
        x_mean = sum(x) / len(x)
        y_mean = sum(values) / len(values)
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        return numerator / denominator if denominator != 0 else 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'basic_stats': {
                'total_attempts': self.total_attempts,
                'accuracy': self.accuracy,
                'average_time': self.average_time_ms,
                'best_streak': self.best_streak
            },
            'recent_performance': {
                'accuracy': self.recent_accuracy,
                'average_time': self.recent_average_time,
                'trends': self.get_trend()
            },
            'mastery': {
                'overall_score': self.get_mastery_score(),
                'confidence_level': statistics.mean(self.confidence_scores) 
                    if self.confidence_scores else 0.0,
                'difficulty_analysis': self.get_difficulty_analysis()
            }
        }

@dataclass
class LearningCurve:
    """Tracks learning progress over time"""
    time_blocks: List[PerformanceMetrics] = field(default_factory=list)
    block_size_minutes: int = 15
    current_block: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    block_start_time: datetime = field(default_factory=datetime.now)

    def update(self, correct: bool, response_time_ms: float) -> None:
        """Update learning curve with new attempt"""
        current_time = datetime.now()
        
        # Check if we need to start a new time block
        if (current_time - self.block_start_time).total_seconds() / 60 >= self.block_size_minutes:
            self.time_blocks.append(self.current_block)
            self.current_block = PerformanceMetrics()
            self.block_start_time = current_time
            
        self.current_block.update(correct, response_time_ms)

    def get_trend(self) -> Dict[str, float]:
        """Calculate learning trends"""
        if not self.time_blocks:
            return {
                'accuracy_trend': 0.0,
                'speed_trend': 0.0,
                'overall_improvement': 0.0
            }
            
        # Calculate trends
        accuracy_trend = self._calculate_trend([block.accuracy for block in self.time_blocks])
        speed_trend = self._calculate_trend([block.average_time_ms for block in self.time_blocks])
        
        # Weight the trends for overall improvement
        return {
            'accuracy_trend': accuracy_trend,
            'speed_trend': -speed_trend,  # Negative because lower times are better
            'overall_improvement': (accuracy_trend * 0.6 - speed_trend * 0.4)
        }

    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """Calculate the trend line slope for a series of values"""
        if len(values) < 2:
            return 0.0
            
        x = list(range(len(values)))
        x_mean = sum(x) / len(x)
        y_mean = sum(values) / len(values)
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        return numerator / denominator if denominator != 0 else 0.0

@dataclass
class FactAnalytics:
    """Detailed analytics for individual math facts"""
    total_attempts: int = 0
    correct_attempts: int = 0
    total_time_ms: float = 0.0
    last_attempt: Optional[datetime] = None
    mastery_level: float = 0.0
    due_for_review: Optional[datetime] = None

    def update(self, correct: bool, response_time_ms: float) -> None:
        """Update fact analytics with new attempt"""
        self.total_attempts += 1
        self.total_time_ms += response_time_ms
        
        if correct:
            self.correct_attempts += 1
            
        # Update mastery level
        accuracy = self.correct_attempts / self.total_attempts
        speed_factor = max(0, 1 - (self.average_time_ms / 5000))  # 5000ms as baseline
        
        # Weight factors
        accuracy_weight = 0.6
        speed_weight = 0.4
        
        # Calculate new mastery level
        self.mastery_level = (accuracy * accuracy_weight + speed_factor * speed_weight)
        
        # Update review schedule
        self.last_attempt = datetime.now()
        self.due_for_review = self._calculate_next_review()

    @property
    def average_time_ms(self) -> float:
        """Calculate average response time"""
        if self.total_attempts == 0:
            return 0.0
        return self.total_time_ms / self.total_attempts

    def _calculate_next_review(self) -> datetime:
        """Calculate next review time using spaced repetition"""
        base_interval = timedelta(hours=24)
        
        if self.mastery_level < 0.3:
            interval = base_interval
        elif self.mastery_level < 0.5:
            interval = base_interval * 2
        elif self.mastery_level < 0.7:
            interval = base_interval * 4
        elif self.mastery_level < 0.9:
            interval = base_interval * 7
        else:
            interval = base_interval * 14
            
        return datetime.now() + interval

class Analytics:
    """Main analytics system for tracking and analyzing player performance"""
    def __init__(self):
        # Initialize tracking structures
        self.fact_analytics: Dict[str, FactAnalytics] = {}
        self.difficulty_metrics: Dict[DifficultyLevel, PerformanceMetrics] = {
            level: PerformanceMetrics() for level in DifficultyLevel
        }
        self.operator_metrics: Dict[str, PerformanceMetrics] = {
            op: PerformanceMetrics() for op in ['+', '-', '*', '/']
        }
        self.learning_curve = LearningCurve()
        
        # Track recent performance for adaptive difficulty
        self.recent_performance: List[Tuple[bool, float]] = []
        self.MAX_RECENT_ATTEMPTS = 20

    def record_attempt(self, question: Question, response_time_ms: float, 
                      correct: bool, difficulty: DifficultyLevel) -> Dict:
        """Record and analyze a question attempt"""
        # Get fact key
        fact_key = question.get_fact_key()
        
        # Update fact analytics
        if fact_key not in self.fact_analytics:
            self.fact_analytics[fact_key] = FactAnalytics()
        self.fact_analytics[fact_key].update(correct, response_time_ms)
        
        # Update metrics
        self.difficulty_metrics[difficulty].update(correct, response_time_ms)
        self.operator_metrics[question.operator].update(correct, response_time_ms)
        self.learning_curve.update(correct, response_time_ms)
        
        # Update recent performance
        self.recent_performance.append((correct, response_time_ms))
        if len(self.recent_performance) > self.MAX_RECENT_ATTEMPTS:
            self.recent_performance.pop(0)
        
        # Generate analytics summary
        return self.generate_summary()

    def get_problematic_facts(self) -> List[str]:
        """Get list of facts needing practice"""
        return [
            fact for fact, analytics in self.fact_analytics.items()
            if analytics.mastery_level < GameSettings.ANALYTICS['mastery_threshold']
        ]

    def get_facts_due_review(self) -> List[str]:
        """Get list of facts due for review"""
        current_time = datetime.now()
        return [
            fact for fact, analytics in self.fact_analytics.items()
            if (analytics.due_for_review and 
                analytics.due_for_review <= current_time)
        ]

    def get_recommended_difficulty(self) -> Dict:
        """Generate difficulty recommendations"""
        if not self.recent_performance:
            return {
                'recommended_level': DifficultyLevel.INTRO,
                'should_include_negatives': False,
                'should_include_decimals': False
            }
            
        # Calculate recent performance metrics
        recent_accuracy = sum(1 for correct, _ in self.recent_performance if correct) / len(self.recent_performance)
        recent_avg_time = sum(time for _, time in self.recent_performance) / len(self.recent_performance)
        
        # Get learning trends
        trends = self.learning_curve.get_trend()
        
        # Make recommendations
        if recent_accuracy < 0.6 or recent_avg_time > 5000:
            recommended = DifficultyLevel.INTRO
        elif recent_accuracy < 0.75 or recent_avg_time > 3000:
            recommended = DifficultyLevel.BASIC
        elif recent_accuracy < 0.85 or recent_avg_time > 2000:
            recommended = DifficultyLevel.MEDIUM
        else:
            recommended = DifficultyLevel.HARD
            
        return {
            'recommended_level': recommended,
            'should_include_negatives': recent_accuracy > 0.8,
            'should_include_decimals': recent_accuracy > 0.85 and recent_avg_time < 3000,
            'learning_trends': trends
        }

    def generate_summary(self) -> Dict:
        """Generate comprehensive analytics summary"""
        return {
            'recent_performance': {
                'accuracy': (sum(1 for correct, _ in self.recent_performance if correct) / 
                           max(1, len(self.recent_performance)) * 100),
                'avg_response_time': (sum(time for _, time in self.recent_performance) / 
                                    max(1, len(self.recent_performance)))
            },
            'learning_trends': self.learning_curve.get_trend(),
            'mastery_levels': {
                fact: analytics.mastery_level
                for fact, analytics in self.fact_analytics.items()
            },
            'problematic_facts': self.get_problematic_facts(),
            'facts_due_review': self.get_facts_due_review(),
            'recommendations': self.get_recommended_difficulty(),
            'operator_stats': {
                op: {
                    'accuracy': metrics.accuracy,
                    'avg_time': metrics.average_time_ms,
                    'streak': metrics.streak,
                    'best_streak': metrics.best_streak
                }
                for op, metrics in self.operator_metrics.items()
            },
            'difficulty_stats': {
                diff.value: {
                    'accuracy': metrics.accuracy,
                    'avg_time': metrics.average_time_ms,
                    'total_attempts': metrics.total_attempts
                }
                for diff, metrics in self.difficulty_metrics.items()
            }
        }
