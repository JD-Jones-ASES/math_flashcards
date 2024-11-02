from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
import random
from datetime import datetime, timedelta
from math_flashcards.utils.constants import DifficultyLevel, GameSettings
from math_flashcards.models.player import Player, OperationStats

@dataclass
class CustomDifficultyAnalyzer:
    """Analyzes player performance to customize difficulty settings"""
    
    @staticmethod
    def analyze_performance(operation_stats: Dict[str, OperationStats]) -> Dict[str, any]:
        """Analyze performance across all operations to determine optimal settings"""
        # Calculate overall performance metrics
        total_attempts = sum(stats.problems_attempted for stats in operation_stats.values())
        if total_attempts == 0:
            return CustomDifficultyAnalyzer._get_default_config()
            
        # Analyze each operation
        operation_metrics = {}
        for op, stats in operation_stats.items():
            if stats.problems_attempted > 0:
                # Calculate recent trend
                recent_trend = CustomDifficultyAnalyzer._calculate_recent_trend(
                    stats.recent_response_times
                )
                
                # Calculate fact mastery distribution
                fact_mastery = stats.fact_mastery
                weak_facts = [
                    fact for fact, mastery in fact_mastery.items()
                    if mastery < GameSettings.ANALYTICS['mastery_threshold']
                ]
                
                operation_metrics[op] = {
                    'accuracy': stats.accuracy,
                    'avg_time': stats.avg_response_time_ms,
                    'weak_facts': weak_facts,
                    'recent_trend': recent_trend,
                    'last_practiced': stats.last_practiced,
                    'total_attempts': stats.problems_attempted
                }
        
        return CustomDifficultyAnalyzer._generate_adaptive_config(operation_metrics)

    @staticmethod
    def _calculate_recent_trend(response_times: List[float]) -> float:
        """Calculate trend from recent response times"""
        if len(response_times) < 2:
            return 0.0
            
        # Calculate slope of response times
        x = list(range(len(response_times)))
        y = response_times
        
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        return numerator / denominator if denominator != 0 else 0.0

    @staticmethod
    def _get_default_config() -> Dict:
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

    @staticmethod
    def _generate_adaptive_config(metrics: Dict[str, Dict]) -> Dict:
        """Generate adaptive configuration based on performance metrics"""
        if not metrics:
            return CustomDifficultyAnalyzer._get_default_config()
            
        # Determine viable operators based on performance
        viable_ops = []
        focus_facts = set()
        max_range = 10
        allows_negative = False
        requires_decimals = False
        
        for op, data in metrics.items():
            # Include operator if either:
            # 1. Good accuracy (>70%) with sufficient attempts (>20)
            # 2. Recent practice with improving trend
            if ((data['accuracy'] >= 70 and data['total_attempts'] >= 20) or
                (data['last_practiced'] and 
                 datetime.now() - data['last_practiced'] < timedelta(days=2) and
                 data['recent_trend'] < 0)):  # Negative trend means improving times
                viable_ops.append(op)
                
                # Collect weak facts for focused practice
                focus_facts.update(f"{op}_{fact}" for fact in data['weak_facts'])
                
                # Adjust number range based on performance
                if data['accuracy'] >= 85:
                    max_range = max(max_range, 50)
                elif data['accuracy'] >= 75:
                    max_range = max(max_range, 25)
                    
        # If no viable operators found, use most practiced one
        if not viable_ops:
            most_practiced = max(metrics.items(), 
                               key=lambda x: x[1]['total_attempts'])
            viable_ops = [most_practiced[0]]
            
        # Determine if ready for negative numbers
        sub_metrics = metrics.get('-', {'accuracy': 0})
        avg_accuracy = sum(m['accuracy'] for m in metrics.values()) / len(metrics)
        if sub_metrics['accuracy'] >= 75 and avg_accuracy >= 80:
            allows_negative = True
            
        # Determine if ready for decimals
        div_metrics = metrics.get('/', {'accuracy': 0})
        if div_metrics['accuracy'] >= 85 and avg_accuracy >= 85:
            requires_decimals = True
            
        return {
            'number_range': (1, max_range),
            'operators': viable_ops,
            'max_digits': 2 if avg_accuracy >= 80 else 1,
            'allows_negative': allows_negative,
            'requires_decimals': requires_decimals,
            'focus_facts': focus_facts,
            'adaptive_timing': True
        }

    @staticmethod
    def get_next_question_config(player: Player, 
                               current_config: Dict,
                               last_response_time: Optional[float] = None,
                               last_correct: Optional[bool] = None) -> Dict:
        """Dynamically adjust question configuration based on recent performance"""
        if not player or not current_config:
            return current_config
            
        # Start with current config
        new_config = current_config.copy()
        
        # Adjust based on very recent performance
        if last_response_time and last_correct is not None:
            if last_correct and last_response_time < 3000:
                # If fast and correct, gradually increase difficulty
                new_config['number_range'] = (
                    new_config['number_range'][0],
                    min(100, new_config['number_range'][1] + 2)
                )
            elif not last_correct and last_response_time > 8000:
                # If slow and incorrect, temporarily decrease difficulty
                new_config['number_range'] = (
                    new_config['number_range'][0],
                    max(10, new_config['number_range'][1] - 5)
                )
                
        # Get problematic facts
        recent_struggles = player.get_recent_struggles()
        if recent_struggles:
            new_config['focus_facts'].update(recent_struggles)
            
        return new_config

    @staticmethod
    def analyze_session_performance(session_data: Dict) -> Dict[str, any]:
        """Analyze current session performance for adaptive difficulty"""
        if not session_data:
            return {}
            
        accuracy = (session_data['correct'] / 
                   max(1, session_data['problems_attempted']) * 100)
        avg_time = session_data['avg_response_time']
        
        return {
            'increase_difficulty': accuracy >= 85 and avg_time < 3000,
            'decrease_difficulty': accuracy <= 60 or avg_time > 8000,
            'suggest_new_operation': accuracy >= 80,
            'performance_level': (
                'excellent' if accuracy >= 90 and avg_time < 2500
                else 'good' if accuracy >= 75 and avg_time < 5000
                else 'struggling'
            )
        }
