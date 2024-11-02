from dataclasses import dataclass, field
from typing import Tuple, Optional, Set, Dict, Protocol, List
import random
from math_flashcards.utils.constants import DifficultyLevel, GameSettings
from math_flashcards.models.player import OperationStats, Player
from math_flashcards.models.custom_difficulty_analyzer import CustomDifficultyAnalyzer

class NumberGenerator(Protocol):
    """Enhanced protocol for number generation strategies"""

    def generate_numbers(self, config: 'QuestionConfig') -> Tuple[float, float]:
        """Generate a pair of numbers based on configuration"""
        pass

    def adapt_to_performance(self, correct: bool, response_time: float) -> None:
        """Adapt generation strategy based on performance"""
        pass

    def get_fact_family(self, num1: float, num2: float) -> Set[Tuple[float, float]]:
        """Get related facts for the given numbers"""
        pass

@dataclass
class BaseNumberGenerator:
    """Base class with common functionality for number generators"""
    recent_numbers: Set[Tuple[float, float]] = field(default_factory=set)
    max_recent: int = 10
    performance_history: List[Tuple[bool, float]] = field(default_factory=list)
    max_history: int = 20

    def adapt_to_performance(self, correct: bool, response_time: float) -> None:
        """Update performance history and adapt strategy"""
        self.performance_history.append((correct, response_time))
        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)

    def _track_numbers(self, num1: float, num2: float) -> None:
        """Track recently used number pairs"""
        self.recent_numbers.add((num1, num2))
        if len(self.recent_numbers) > self.max_recent:
            self.recent_numbers.pop()

    def _numbers_recently_used(self, num1: float, num2: float) -> bool:
        """Check if numbers were recently used"""
        return (num1, num2) in self.recent_numbers or (num2, num1) in self.recent_numbers

    def _get_recent_performance(self) -> Tuple[float, float]:
        """Calculate recent accuracy and average response time"""
        if not self.performance_history:
            return (1.0, 0.0)

        recent = self.performance_history[-10:]
        accuracy = sum(1 for correct, _ in recent if correct) / len(recent)
        avg_time = sum(time for _, time in recent) / len(recent)
        return (accuracy, avg_time)


@dataclass
class AdditionGenerator(BaseNumberGenerator):
    """Enhanced addition problem generator with pedagogical patterns"""
    doubles_frequency: float = 0.2
    making_ten_frequency: float = 0.2
    near_doubles_frequency: float = 0.2

    def generate_numbers(self, config: 'QuestionConfig') -> Tuple[float, float]:
        """Generate addition problems with educational patterns"""
        min_val, max_val = config.number_range
        accuracy, avg_time = self._get_recent_performance()

        # Adjust frequencies based on performance
        if accuracy < 0.7:
            self.doubles_frequency = 0.3
            self.making_ten_frequency = 0.3
        else:
            self.doubles_frequency = 0.2
            self.making_ten_frequency = 0.2

        for _ in range(10):  # Try 10 times to generate non-repeating numbers
            pattern = random.random()

            if pattern < self.doubles_frequency:
                # Generate doubles (e.g., 4+4, 7+7)
                num = random.randint(min_val, max_val // 2)
                num1 = num2 = num
            elif pattern < self.doubles_frequency + self.making_ten_frequency:
                # Generate problems that make ten
                num1 = random.randint(1, 9)
                num2 = 10 - num1
            elif pattern < self.doubles_frequency + self.making_ten_frequency + self.near_doubles_frequency:
                # Generate near doubles (e.g., 4+5, 7+8)
                base = random.randint(min_val, max_val // 2)
                num1 = base
                num2 = base + random.choice([-1, 1])
            else:
                # Generate regular problems
                if config.allows_negative:
                    num1 = random.randint(-max_val, max_val)
                    num2 = random.randint(-max_val, max_val)
                else:
                    num1 = random.randint(min_val, max_val)
                    num2 = random.randint(min_val, max_val)

            if not self._numbers_recently_used(num1, num2):
                self._track_numbers(num1, num2)
                return (num1, num2)

        # If we couldn't avoid repeats, return last generated pair
        return (num1, num2)

    def get_fact_family(self, num1: float, num2: float) -> Set[Tuple[float, float]]:
        """Get related addition facts"""
        family = {(num1, num2), (num2, num1)}  # Commutative property
        if num1 == num2:  # Doubles
            family.add((num1 - 1, num2 + 1))  # Near doubles
        return family


@dataclass
class SubtractionGenerator(BaseNumberGenerator):
    """Enhanced subtraction problem generator"""
    fact_family_frequency: float = 0.3
    bridging_ten_frequency: float = 0.2

    def generate_numbers(self, config: 'QuestionConfig') -> Tuple[float, float]:
        """Generate subtraction problems with pedagogical patterns"""
        min_val, max_val = config.number_range
        accuracy, avg_time = self._get_recent_performance()

        # Adjust frequencies based on performance
        if accuracy < 0.7:
            self.fact_family_frequency = 0.4
            self.bridging_ten_frequency = 0.3

        for _ in range(10):
            pattern = random.random()

            if pattern < self.fact_family_frequency:
                # Generate from addition fact families
                base = random.randint(min_val, max_val - 5)
                addend = random.randint(1, min(5, max_val - base))
                num1 = base + addend
                num2 = random.choice([base, addend])
            elif pattern < self.fact_family_frequency + self.bridging_ten_frequency:
                # Generate problems that bridge tens (e.g., 32-5)
                # Only use bridging tens strategy if max_val is large enough
                if max_val >= 15:  # Minimum threshold for meaningful bridging
                    base = random.randint(1, max(1, (max_val // 10))) * 10
                    # Ensure num1 doesn't exceed max_val
                    num1 = min(base + random.randint(1, 5), max_val)
                    # Ensure num2 is reasonable and result stays positive
                    num2 = random.randint(2, min(7, num1 - 1))
                else:
                    # Fallback to basic subtraction for small ranges
                    if config.allows_negative:
                        num1 = random.randint(-max_val, max_val)
                        num2 = random.randint(-max_val, max_val)
                    else:
                        num2 = random.randint(min_val, max_val)
                        num1 = random.randint(num2, max_val)  # Ensures positive result
            else:
                if config.allows_negative:
                    num1 = random.randint(-max_val, max_val)
                    num2 = random.randint(-max_val, max_val)
                else:
                    num2 = random.randint(min_val, max_val)
                    num1 = random.randint(num2, max_val)  # Ensures positive result

            if not self._numbers_recently_used(num1, num2):
                self._track_numbers(num1, num2)
                return (num1, num2)

        return (num1, num2)  # Return last generated pair if no unique ones found

    # def generate_numbers(self, config: 'QuestionConfig') -> Tuple[float, float]:
    #     """Generate subtraction problems with pedagogical patterns"""
    #     min_val, max_val = config.number_range
    #     accuracy, avg_time = self._get_recent_performance()
    #
    #     # Adjust frequencies based on performance
    #     if accuracy < 0.7:
    #         self.fact_family_frequency = 0.4
    #         self.bridging_ten_frequency = 0.3
    #
    #     for _ in range(10):
    #         pattern = random.random()
    #
    #         if pattern < self.fact_family_frequency:
    #             # Generate from addition fact families
    #             base = random.randint(min_val, max_val - 5)
    #             addend = random.randint(1, 5)
    #             num1 = base + addend
    #             num2 = random.choice([base, addend])
    #         elif pattern < self.fact_family_frequency + self.bridging_ten_frequency:
    #             # Generate problems that bridge tens (e.g., 32-5)
    #             base = random.randint(1, (max_val // 10)) * 10
    #             num1 = base + random.randint(1, 5)
    #             num2 = random.randint(2, 7)
    #         else:
    #             if config.allows_negative:
    #                 num1 = random.randint(-max_val, max_val)
    #                 num2 = random.randint(-max_val, max_val)
    #             else:
    #                 num2 = random.randint(min_val, max_val)
    #                 num1 = random.randint(num2, max_val)  # Ensures positive result
    #
    #         if not self._numbers_recently_used(num1, num2):
    #             self._track_numbers(num1, num2)
    #             return (num1, num2)
    #
    #     return (num1, num2)

    def get_fact_family(self, num1: float, num2: float) -> Set[Tuple[float, float]]:
        """Get related subtraction facts"""
        result = num1 - num2
        return {
            (num1, num2),
            (num1, result),
            (num2 + result, num2),
            (result + num2, result)
        }


@dataclass
class MultiplicationGenerator(BaseNumberGenerator):
    """Enhanced multiplication problem generator"""
    square_frequency: float = 0.2
    double_halve_frequency: float = 0.2

    def generate_numbers(self, config: 'QuestionConfig') -> Tuple[float, float]:
        """Generate multiplication problems with pedagogical patterns"""
        settings = GameSettings.DIFFICULTY_SETTINGS[config.difficulty]
        max_factor = settings['multiplication_rules']['max_factor']
        max_product = settings['multiplication_rules']['max_product']
        accuracy, avg_time = self._get_recent_performance()

        # Adjust frequencies based on performance
        if accuracy < 0.7:
            self.square_frequency = 0.3
            self.double_halve_frequency = 0.3

        for _ in range(10):
            pattern = random.random()

            if pattern < self.square_frequency:
                # Generate square numbers
                num = random.randint(2, int(max_factor ** 0.5))
                num1 = num2 = num
            elif pattern < self.square_frequency + self.double_halve_frequency:
                # Generate double/half relationships
                base = random.randint(2, max_factor // 2)
                num1 = base * 2
                num2 = base
            else:
                num1 = random.randint(config.number_range[0], max_factor)
                num2 = random.randint(config.number_range[0], max_factor)

            if num1 * num2 <= max_product and not self._numbers_recently_used(num1, num2):
                self._track_numbers(num1, num2)
                return (num1, num2)

        return (num1, num2)

    def get_fact_family(self, num1: float, num2: float) -> Set[Tuple[float, float]]:
        """Get related multiplication facts"""
        family = {(num1, num2), (num2, num1)}  # Commutative property
        if num1 % 2 == 0:  # If even, add double/half relationship
            family.add((num1 // 2, num2 * 2))
        if num2 % 2 == 0:
            family.add((num1 * 2, num2 // 2))
        return family


@dataclass
class DivisionGenerator(BaseNumberGenerator):
    """Enhanced division problem generator"""
    fact_family_frequency: float = 0.3
    decimal_frequency: float = 0.2

    def generate_numbers(self, config: 'QuestionConfig') -> Tuple[float, float]:
        """Generate division problems with support for decimals"""
        settings = GameSettings.DIFFICULTY_SETTINGS[config.difficulty]
        max_divisor = settings['division_rules']['max_divisor']
        max_dividend = settings['division_rules']['max_dividend']
        accuracy, avg_time = self._get_recent_performance()

        # Adjust frequencies based on performance
        if accuracy < 0.7:
            self.fact_family_frequency = 0.4
            if config.requires_decimals:
                self.decimal_frequency = 0.1

        for _ in range(10):
            pattern = random.random()

            if pattern < self.fact_family_frequency:
                # Generate from multiplication fact families
                num2 = random.randint(2, max_divisor)
                quotient = random.randint(1, max_dividend // num2)
                num1 = num2 * quotient
            elif pattern < self.fact_family_frequency + self.decimal_frequency and config.requires_decimals:
                # Generate problems with decimal answers
                num2 = random.randint(2, 10)
                num1 = num2 * random.randint(1, 10) + num2 / 2
            else:
                num2 = max(1, random.randint(1, max_divisor))
                max_possible_quotient = min(
                    max_dividend // num2,
                    settings['division_rules']['max_quotient']
                )
                if max_possible_quotient < 1:
                    num1 = num2  # Fallback to quotient of 1
                else:
                    quotient = random.randint(1, max_possible_quotient)
                    num1 = num2 * quotient

            if not self._numbers_recently_used(num1, num2):
                self._track_numbers(num1, num2)
                return (num1, num2)

        return (num1, num2)

    def get_fact_family(self, num1: float, num2: float) -> Set[Tuple[float, float]]:
        """Get related division facts"""
        quotient = num1 / num2
        return {
            (num1, num2),
            (num1, quotient),
            (num2 * quotient, quotient),
            (num2 * quotient, num2)
        }

@dataclass
class QuestionConfig:
    """Configuration for question generation"""
    number_range: Tuple[int, int]
    operators: list[str]
    max_digits: int
    allows_negative: bool
    requires_decimals: bool
    difficulty: DifficultyLevel
    focus_facts: Set[str] = field(default_factory=set)
    adaptive_timing: bool = False
    
    @classmethod
    def create_custom(cls, operation_stats: Dict[str, OperationStats]) -> 'QuestionConfig':
        """Create an adaptive custom configuration based on detailed player statistics"""
        analyzer = CustomDifficultyAnalyzer()
        config_data = analyzer.analyze_performance(operation_stats)
        
        return cls(
            number_range=config_data['number_range'],
            operators=config_data['operators'],
            max_digits=config_data['max_digits'],
            allows_negative=config_data['allows_negative'],
            requires_decimals=config_data['requires_decimals'],
            difficulty=DifficultyLevel.CUSTOM,
            focus_facts=config_data['focus_facts'],
            adaptive_timing=config_data['adaptive_timing']
        )
    
    def adjust_for_session(self, player: Player, 
                          last_response_time: Optional[float] = None,
                          last_correct: Optional[bool] = None) -> 'QuestionConfig':
        """Create adjusted configuration based on session performance"""
        if self.difficulty != DifficultyLevel.CUSTOM:
            return self
            
        analyzer = CustomDifficultyAnalyzer()
        config_data = analyzer.get_next_question_config(
            player,
            {
                'number_range': self.number_range,
                'operators': self.operators,
                'max_digits': self.max_digits,
                'allows_negative': self.allows_negative,
                'requires_decimals': self.requires_decimals,
                'focus_facts': self.focus_facts,
                'adaptive_timing': self.adaptive_timing
            },
            last_response_time,
            last_correct
        )
        
        return QuestionConfig(
            number_range=config_data['number_range'],
            operators=config_data['operators'],
            max_digits=config_data['max_digits'],
            allows_negative=config_data['allows_negative'],
            requires_decimals=config_data['requires_decimals'],
            difficulty=DifficultyLevel.CUSTOM,
            focus_facts=config_data['focus_facts'],
            adaptive_timing=config_data['adaptive_timing']
        )
    
    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> 'QuestionConfig':
        """Create configuration from difficulty level"""
        settings = GameSettings.DIFFICULTY_SETTINGS[difficulty]
        return cls(
            number_range=settings['number_range'],
            operators=settings['operators'].copy(),
            max_digits=settings['max_digits'],
            allows_negative=settings['allows_negative'],
            requires_decimals=settings['requires_decimals'],
            difficulty=difficulty
        )

@dataclass
class Question:
    """Represents a single math question with generation and validation logic"""
    operator: str
    num1: float
    num2: float
    missing_position: int
    decimal_places: int = 0
    difficulty: DifficultyLevel = field(default=DifficultyLevel.INTRO)
    _last_numbers: Set[float] = field(default_factory=set)
    _generators: Dict[str, NumberGenerator] = field(default_factory=lambda: {
        '+': AdditionGenerator(),
        '-': SubtractionGenerator(),
        '*': MultiplicationGenerator(),
        '/': DivisionGenerator()
    })

    @property
    def answer(self) -> float:
        """Calculate the answer based on operator and numbers"""
        if self.operator == '+':
            return self.num1 + self.num2
        elif self.operator == '-':
            return self.num1 - self.num2
        elif self.operator == '*':
            return self.num1 * self.num2
        else:  # division
            if self.num2 == 0:  # Protect against division by zero
                return float('inf')  # or could raise ValueError if preferred
            return self.num1 / self.num2

    @classmethod
    def generate(cls, config: QuestionConfig, problematic_facts: Optional[Set[str]] = None) -> 'Question':
        """Generate a new question with proper handling of negative numbers"""
        operator = random.choice(config.operators)

        instance = cls._generate_new_question(operator, config)
        instance.difficulty = config.difficulty  # Ensure difficulty is set

        # Special handling for negative numbers in subtraction
        if operator == '-' and config.allows_negative:
            # 25% chance to generate a problem requiring negative answer
            if random.random() < 0.25:
                # Generate numbers that will require a negative answer
                num2 = random.randint(config.number_range[0], config.number_range[1])
                answer = random.randint(-config.number_range[1], -config.number_range[0])
                num1 = answer + num2
                instance.num1, instance.num2 = num1, num2

        return instance

    @classmethod
    def _generate_from_problematic_facts(cls, operator: str, config: QuestionConfig,
                                         problematic_facts: Set[str]) -> 'Question':
        """Generate a question focusing on problematic facts"""
        facts = [f for f in problematic_facts if f.startswith(f"{operator}_")]
        if not facts:
            return cls._generate_new_question(operator, config)

        fact = random.choice(facts)
        try:
            base_str = fact.split(f"{operator}_")[1]
            base_num = int(base_str) if base_str.isdigit() else random.randint(*config.number_range)
        except (IndexError, ValueError):
            return cls._generate_new_question(operator, config)

        instance = cls(operator, 0, 0, random.randint(0, 2),
                       decimal_places=1 if config.requires_decimals else 0)

        generator = instance._generators[operator]

        # Initialize with a default generation
        num1, num2 = generator.generate_numbers(config)

        for _ in range(10):  # Try 10 times to generate non-repeating numbers
            if operator in {'+', '-'}:
                temp_num1, temp_num2 = generator.generate_numbers(config)
                if not instance._numbers_recently_used(temp_num1, temp_num2):
                    num1, num2 = temp_num1, temp_num2
                    break
            else:  # '*' or '/'
                temp_num1 = base_num
                temp_num2 = random.randint(1, min(12, config.number_range[1]))
                if not instance._numbers_recently_used(temp_num1, temp_num2):
                    num1, num2 = temp_num1, temp_num2
                    break

        instance.num1, instance.num2 = num1, num2
        instance._update_last_numbers()
        return instance

    @classmethod
    def _generate_new_question(cls, operator: str, config: QuestionConfig) -> 'Question':
        """Generate a new random question based on configuration"""
        instance = cls(operator, 0, 0, random.randint(0, 2),
                       decimal_places=1 if config.requires_decimals else 0)

        generator = instance._generators[operator]

        # Initialize with a default generation
        num1, num2 = generator.generate_numbers(config)

        for _ in range(10):  # Try 10 times to generate non-repeating numbers
            temp_num1, temp_num2 = generator.generate_numbers(config)
            if not instance._numbers_recently_used(temp_num1, temp_num2):
                num1, num2 = temp_num1, temp_num2
                break

        instance.num1, instance.num2 = num1, num2
        instance._update_last_numbers()
        return instance

    def _numbers_recently_used(self, num1: float, num2: float) -> bool:
        """Check if numbers were recently used"""
        return bool({float(num1), float(num2), float(self.answer)} & self._last_numbers)

    def _update_last_numbers(self) -> None:
        """Update the set of recently used numbers"""
        self._last_numbers = {float(self.num1), float(self.num2), float(self.answer)}

    def format_number(self, num: float) -> str:
        """Format a number according to current decimal places setting"""
        if self.decimal_places > 0:
            return f"{num:.1f}"
        return str(int(num))

    def get_display_numbers(self) -> Tuple[str, ...]:
        """Get the numbers to display, with one missing based on position"""
        nums = [self.format_number(n) for n in (self.num1, self.num2, self.answer)]
        nums[self.missing_position] = ''
        return tuple(nums)

    def get_fact_key(self) -> str:
        """Get the key representing the math fact being tested"""
        base = min(int(self.num1), int(self.num2)) if self.operator in {'*', '/'} else int(self.num1)
        return f"{self.operator}_{base}"

    def check_answer(self, user_input: str) -> bool:
        """Check if the user's answer matches the expected value"""
        try:
            user_num = float(user_input) if self.decimal_places > 0 else int(user_input)
            target = [self.num1, self.num2, self.answer][self.missing_position]

            # For division, maintain special handling
            if self.operator == '/':
                if self.missing_position == 0:  # dividend missing
                    return abs(user_num - (self.num2 * self.answer)) < 0.0001
                elif self.missing_position == 1:  # divisor missing
                    return abs(user_num - (self.num1 / self.answer)) < 0.0001
                else:  # quotient missing
                    return abs(user_num - (self.num1 / self.num2)) < 0.0001

            # For other operators, use appropriate comparison
            if self.decimal_places > 0:
                return abs(user_num - target) < 0.0001
            return user_num == target
        except (ValueError, TypeError, ZeroDivisionError):
            return False

    def validate_input(self, input_str: str, max_digits: int) -> bool:
        """Validate user input against current constraints"""
        # Early return for empty input
        if not input_str:
            return True

        # Special case for standalone minus sign
        if input_str == '-':
            return True  # Always allow typing minus sign initially

        # Determine valid characters
        valid_chars = set('0123456789-')
        if self.decimal_places > 0:
            valid_chars.add('.')

        # Basic character validation
        if not all(c in valid_chars for c in input_str):
            return False

        # Handle decimal validation
        if '.' in input_str:
            if self.decimal_places == 0 or input_str.count('.') > 1:
                return False
            whole, decimal = input_str.replace('-', '').split('.')
            if len(decimal) > self.decimal_places:
                return False
            digit_count = len(whole)
        else:
            digit_count = len(input_str.replace('-', ''))

        # Get the expected value range
        target = [self.num1, self.num2, self.answer][self.missing_position]
        required_digits = len(str(int(abs(target))))

        # Calculate allowed digits based on operator
        max_allowed = {
            '+': len(str(int(abs(self.num1 + self.num2)))),
            '-': len(str(int(abs(self.num1 - self.num2)))),
            '*': len(str(int(abs(self.num1 * self.num2)))),
            '/': max(required_digits, len(str(int(abs(self.num1)))) + 1)
        }[self.operator]

        allowed_digits = max(max_digits, max_allowed)

        # Account for minus sign in length check
        if input_str.startswith('-'):
            allowed_digits += 1

        return digit_count <= allowed_digits

    def with_difficulty(self, difficulty: DifficultyLevel) -> 'Question':
        """Set the difficulty level and return self"""
        self.difficulty = difficulty
        return self