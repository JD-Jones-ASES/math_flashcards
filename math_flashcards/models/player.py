from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from math_flashcards.utils.constants import DifficultyLevel, GameSettings

@dataclass
class OperationStats:
    """Statistics for a specific operation"""
    problems_attempted: int = 0
    correct: int = 0
    avg_response_time_ms: float = 0.0
    accuracy: float = 0.0
    fact_mastery: Dict[str, float] = field(default_factory=dict)  # Empty dict, no default values
    last_practiced: Optional[datetime] = None
    recent_response_times: List[float] = field(default_factory=list)
    mastery_decay_rate: float = 0.05  # 5% decay per day without practice

    def update_with_attempt(self, correct: bool, response_time_ms: float, fact: str):
        """Update stats with a new attempt using improved mastery tracking"""
        self.problems_attempted += 1
        if correct:
            self.correct += 1
        
        # Update running average response time
        self.avg_response_time_ms = (
            (self.avg_response_time_ms * (self.problems_attempted - 1) + response_time_ms)
            / self.problems_attempted
        )
        
        # Update accuracy
        self.accuracy = (self.correct / self.problems_attempted) * 100
        
        # Track recent response times for trend analysis
        self.recent_response_times.append(response_time_ms)
        if len(self.recent_response_times) > 20:  # Keep last 20 attempts
            self.recent_response_times.pop(0)
        
        # Apply mastery decay since last practice
        if self.last_practiced:
            days_since_practice = (datetime.now() - self.last_practiced).days
            decay = self.mastery_decay_rate * days_since_practice
            self.fact_mastery = {
                k: max(0.0, v - decay)
                for k, v in self.fact_mastery.items()
            }
        
        # Create fact key in format "operator_number" (e.g. "+_3")
        fact_key = f"{fact}"  # fact already includes the operator prefix
        
        # Update fact mastery with weighted factors
        current_mastery = self.fact_mastery.get(fact_key, 0.0)
        accuracy_weight = 0.6
        speed_weight = 0.4
        
        # Calculate speed factor (normalized to 0-1 range)
        speed_factor = max(0, 1 - (response_time_ms / 5000))  # 5000ms as baseline
        
        # Calculate mastery change
        if correct:
            mastery_change = (accuracy_weight + speed_factor * speed_weight) * 0.1
        else:
            mastery_change = -0.15  # Larger penalty for incorrect answers
        
        # Update mastery with limits
        self.fact_mastery[fact_key] = max(0.0, min(1.0, current_mastery + mastery_change))
        
        self.last_practiced = datetime.now()

    def get_fact_mastery(self, fact: str) -> float:
        """Get mastery level for a specific fact"""
        return self.fact_mastery.get(fact, 0.0)

    def cleanup_unused_facts(self) -> None:
        """Remove facts with 0.0 mastery to keep the data clean"""
        self.fact_mastery = {
            k: v for k, v in self.fact_mastery.items()
            if v > 0.0
        }
        
@dataclass
class DifficultyStats:
    """Statistics for a specific difficulty level"""
    problems_attempted: int = 0
    correct: int = 0
    avg_response_time_ms: float = 0.0
    accuracy: float = 0.0
    last_played: Optional[datetime] = None

    def update_with_attempt(self, correct: bool, response_time_ms: float):
        """Update stats with a new attempt"""
        self.problems_attempted += 1
        if correct:
            self.correct += 1
            
        self.avg_response_time_ms = (
            (self.avg_response_time_ms * (self.problems_attempted - 1) + response_time_ms)
            / self.problems_attempted
        )
        
        self.accuracy = (self.correct / self.problems_attempted) * 100
        self.last_played = datetime.now()

@dataclass
class SessionData:
    """Data for a single practice session"""
    date: str
    duration_mins: float
    problems_attempted: int
    correct: int
    operations_used: Set[str]
    difficulty_levels: Set[str]
    avg_response_time_ms: float

@dataclass
class AchievementStats:
    """Track player achievements"""
    perfect_sessions: int = 0
    problems_solved_under_3s: int = 0
    longest_streak: int = 0
    total_practice_days: int = 0
    consecutive_days_streak: int = 0
    last_practice_date: Optional[date] = None

    def update_day_streak(self, current_date: date) -> None:
        """Update practice day streaks"""
        if not self.last_practice_date:
            self.consecutive_days_streak = 1
        else:
            days_diff = (current_date - self.last_practice_date).days
            if days_diff == 1:
                self.consecutive_days_streak += 1
            elif days_diff > 1:
                self.consecutive_days_streak = 1
                
        self.total_practice_days += 1
        self.last_practice_date = current_date

@dataclass
class Player:
    """Main player class containing all player-related data"""
    name: str
    creation_date: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    total_problems_attempted: int = 0
    total_correct: int = 0
    current_streak: int = 0
    best_streak: int = 0
    time_spent_mins: float = 0.0
    
    # Statistics tracking
    operation_stats: Dict[str, OperationStats] = field(
        default_factory=lambda: {
            op: OperationStats() for op in ['+', '-', '*', '/']
        }
    )
    
    difficulty_stats: Dict[DifficultyLevel, DifficultyStats] = field(
        default_factory=lambda: {
            level: DifficultyStats() for level in DifficultyLevel
        }
    )
    
    recent_sessions: List[SessionData] = field(default_factory=list)
    achievement_stats: AchievementStats = field(default_factory=AchievementStats)
    
    def record_attempt(self, operation: str, difficulty: DifficultyLevel, 
                  fact: str, correct: bool, response_time_ms: float) -> None:
	    """Record a single problem attempt"""
	    self.total_problems_attempted += 1
	    if correct:
	        self.total_correct += 1
	        self.current_streak += 1
	        self.best_streak = max(self.best_streak, self.current_streak)
	    else:
	        self.current_streak = 0
	        
	    # Update time spent (convert ms to minutes)
	    self.time_spent_mins += response_time_ms / (1000 * 60)
	        
	    # Update operation stats with improved mastery tracking
	    op_stats = self.operation_stats[operation]
	    op_stats.update_with_attempt(correct, response_time_ms, fact)
	    
	    # Update difficulty stats
	    diff_stats = self.difficulty_stats[difficulty]
	    diff_stats.update_with_attempt(correct, response_time_ms)
	    
	    # Update achievement stats with more detailed tracking
	    self._update_achievements(correct, response_time_ms)
	    
	    # Update last active time
	    self.last_active = datetime.now()
    
    def _update_achievements(self, correct: bool, response_time_ms: float) -> None:
	    """Update achievement statistics with more comprehensive tracking"""
	    today = date.today()
	    
	    # Update speed achievements
	    if response_time_ms < GameSettings.ANALYTICS['response_time_threshold']:
	        self.achievement_stats.problems_solved_under_3s += 1
	    
	    # Update practice day tracking
	    if (not self.achievement_stats.last_practice_date or 
	        self.achievement_stats.last_practice_date != today):
	        self.achievement_stats.total_practice_days += 1
	        
	        # Update consecutive days streak
	        if (self.achievement_stats.last_practice_date and 
	            (today - self.achievement_stats.last_practice_date).days == 1):
	            self.achievement_stats.consecutive_days_streak += 1
	        else:
	            self.achievement_stats.consecutive_days_streak = 1
	            
	        self.achievement_stats.last_practice_date = today
	    
	    # Update perfect session tracking
	    current_session = self.recent_sessions[-1]
	    if (current_session.problems_attempted >= 10 and 
	        current_session.correct == current_session.problems_attempted):
	        self.achievement_stats.perfect_sessions += 1
	    
	    # Update longest streak
	    if self.current_streak > self.achievement_stats.longest_streak:
	        self.achievement_stats.longest_streak = self.current_streak
        
    def start_new_session(self) -> None:
        """Initialize a new practice session"""
        self.current_session = SessionData(
            date=datetime.now().strftime("%Y-%m-%d"),
            duration_mins=0.0,
            problems_attempted=0,
            correct=0,
            operations_used=set(),
            difficulty_levels=set(),
            avg_response_time_ms=0.0
        )
        self.recent_sessions.append(self.current_session)
        
        # Limit stored sessions to most recent 50
        if len(self.recent_sessions) > 50:
            self.recent_sessions = self.recent_sessions[-50:]

    def get_mastery_level(self, operation: str) -> float:
        """Calculate overall mastery level for an operation"""
        op_stats = self.operation_stats[operation]
        if op_stats.problems_attempted == 0:
            return 0.0
            
        # Weight factors for mastery calculation
        accuracy_weight = 0.6
        speed_weight = 0.2
        fact_weight = 0.2
        
        # Calculate components
        accuracy_factor = op_stats.accuracy / 100
        speed_factor = max(0, 1 - (op_stats.avg_response_time_ms / 5000))
        fact_mastery = sum(op_stats.fact_mastery.values()) / len(op_stats.fact_mastery)
        
        return (accuracy_factor * accuracy_weight + 
                speed_factor * speed_weight + 
                fact_mastery * fact_weight)

    def can_use_custom_mode(self) -> bool:
        """Check if player has met requirements for custom mode"""
        return (self.total_problems_attempted >= 
                GameSettings.ANALYTICS['min_problems_for_custom'])

    def get_recommended_difficulty(self) -> DifficultyLevel:
        """Calculate recommended difficulty level based on performance"""
        if self.total_problems_attempted < 10:
            return DifficultyLevel.INTRO
            
        # Calculate average accuracy across all difficulties
        total_accuracy = sum(
            stats.accuracy for stats in self.difficulty_stats.values()
            if stats.problems_attempted > 0
        ) / sum(
            1 for stats in self.difficulty_stats.values()
            if stats.problems_attempted > 0
        )
        
        # Recommend based on accuracy
        if total_accuracy < 60:
            return DifficultyLevel.INTRO
        elif total_accuracy < 75:
            return DifficultyLevel.BASIC
        elif total_accuracy < 85:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.HARD

    def to_dict(self) -> Dict:
        """Convert player data to dictionary for storage"""
        return {
            "name": self.name,
            "creation_date": self.creation_date.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "total_problems_attempted": self.total_problems_attempted,
            "total_correct": self.total_correct,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "time_spent_mins": self.time_spent_mins,
            "operation_stats": {
                op: {
                    "problems_attempted": stats.problems_attempted,
                    "correct": stats.correct,
                    "avg_response_time_ms": stats.avg_response_time_ms,
                    "accuracy": stats.accuracy,
                    "fact_mastery": stats.fact_mastery,
                    "last_practiced": stats.last_practiced.isoformat() 
                        if stats.last_practiced else None
                }
                for op, stats in self.operation_stats.items()
            },
            "difficulty_stats": {
                diff.value: {
                    "problems_attempted": stats.problems_attempted,
                    "correct": stats.correct,
                    "avg_response_time_ms": stats.avg_response_time_ms,
                    "accuracy": stats.accuracy,
                    "last_played": stats.last_played.isoformat() 
                        if stats.last_played else None
                }
                for diff, stats in self.difficulty_stats.items()
            },
            "achievement_stats": {
                "perfect_sessions": self.achievement_stats.perfect_sessions,
                "problems_solved_under_3s": self.achievement_stats.problems_solved_under_3s,
                "longest_streak": self.achievement_stats.longest_streak,
                "total_practice_days": self.achievement_stats.total_practice_days,
                "consecutive_days_streak": self.achievement_stats.consecutive_days_streak,
                "last_practice_date": self.achievement_stats.last_practice_date.isoformat()
                    if self.achievement_stats.last_practice_date else None
            },
            "recent_sessions": [
                {
                    "date": session.date,
                    "duration_mins": session.duration_mins,
                    "problems_attempted": session.problems_attempted,
                    "correct": session.correct,
                    "operations_used": list(session.operations_used),
                    "difficulty_levels": list(session.difficulty_levels),
                    "avg_response_time_ms": session.avg_response_time_ms
                }
                for session in self.recent_sessions
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Player':
        """Create a Player instance from dictionary data"""
        player = cls(name=data["name"])
        
        # Load basic stats
        player.creation_date = datetime.fromisoformat(data["creation_date"])
        player.last_active = (datetime.fromisoformat(data["last_active"]) 
                            if data["last_active"] else None)
        player.total_problems_attempted = data["total_problems_attempted"]
        player.total_correct = data["total_correct"]
        player.current_streak = data["current_streak"]
        player.best_streak = data["best_streak"]
        player.time_spent_mins = data["time_spent_mins"]
        
        # Load operation stats
        for op, stats in data["operation_stats"].items():
            op_stats = player.operation_stats[op]
            op_stats.problems_attempted = stats["problems_attempted"]
            op_stats.correct = stats["correct"]
            op_stats.avg_response_time_ms = stats["avg_response_time_ms"]
            op_stats.accuracy = stats["accuracy"]
            op_stats.fact_mastery = stats["fact_mastery"]
            op_stats.last_practiced = (datetime.fromisoformat(stats["last_practiced"])
                                     if stats["last_practiced"] else None)
        
        # Load difficulty stats
        for diff_name, stats in data["difficulty_stats"].items():
            diff_level = DifficultyLevel(diff_name)
            diff_stats = player.difficulty_stats[diff_level]
            diff_stats.problems_attempted = stats["problems_attempted"]
            diff_stats.correct = stats["correct"]
            diff_stats.avg_response_time_ms = stats["avg_response_time_ms"]
            diff_stats.accuracy = stats["accuracy"]
            diff_stats.last_played = (datetime.fromisoformat(stats["last_played"])
                                    if stats["last_played"] else None)
        
        # Load achievement stats
        ach_stats = data["achievement_stats"]
        player.achievement_stats = AchievementStats(
            perfect_sessions=ach_stats["perfect_sessions"],
            problems_solved_under_3s=ach_stats["problems_solved_under_3s"],
            longest_streak=ach_stats["longest_streak"],
            total_practice_days=ach_stats["total_practice_days"],
            consecutive_days_streak=ach_stats["consecutive_days_streak"],
            last_practice_date=(date.fromisoformat(ach_stats["last_practice_date"])
                              if ach_stats["last_practice_date"] else None)
        )
        
        # Load recent sessions
        player.recent_sessions = [
            SessionData(
                date=session["date"],
                duration_mins=session["duration_mins"],
                problems_attempted=session["problems_attempted"],
                correct=session["correct"],
                operations_used=set(session["operations_used"]),
                difficulty_levels=set(session["difficulty_levels"]),
                avg_response_time_ms=session["avg_response_time_ms"]
            )
            for session in data["recent_sessions"]
        ]
        
        return player
        
    def get_recent_struggles(self) -> Set[str]:
	    """Get set of facts that player has recently struggled with"""
	    struggles = set()
	    
	    # Look at recent sessions (last 3)
	    recent_attempts = []
	    for session in self.recent_sessions[-3:]:
	        for op in session.operations_used:
	            stats = self.operation_stats[op]
	            
	            # Find facts with low mastery
	            weak_facts = {
	                f"{op}_{fact}"
	                for fact, mastery in stats.fact_mastery.items()
	                if mastery < GameSettings.ANALYTICS['mastery_threshold']
	            }
	            
	            # Prioritize recently practiced facts
	            if stats.last_practiced:
	                days_since = (datetime.now() - stats.last_practiced).days
	                if days_since <= 2:  # Focus on very recent struggles
	                    struggles.update(weak_facts)
	                elif days_since <= 7:  # Include week-old struggles with lower priority
	                    struggles.update(list(weak_facts)[:3])  # Limit older struggles
	    
	    return struggles
	
