# AI Assisted Productivity in Education

This package was written by Anthropic's Claude Sonnet 3.5 with human guidance. With few exceptions, all 
files, including this one, for the most part, were written by Claude. This should be considered a proof 
of concept, showing that teachers can make on-demand, targeted, AI-assisted resources for their schools. I 
have attempted to follow reasonable licensing and versioning conventions, opting for complete open source.
Please pardon lapses in proper practice. Claude did the best he could.

## Math Flash Cards

An interactive math practice application featuring adaptive learning, detailed analytics, and personalized difficulty progression.

## Features

- **Adaptive Learning**: Automatically adjusts difficulty based on student performance
- **Multiple Operation Types**: Practice addition, subtraction, multiplication, and division
- **Customizable Difficulty Levels**: 
  - Intro: Basic single-digit operations
  - Basic: Standard multiplication table range
  - Medium: Extended range with negative numbers
  - Hard: Advanced operations with larger numbers
  - Custom: AI-driven personalized difficulty settings
- **Detailed Analytics**: 
  - Track progress across operations
  - Monitor mastery of specific math facts
  - View learning curves and performance trends
  - Session-based statistics and achievements
- **Multi-User Support**: 
  - Individual player profiles
  - Progress tracking per user
  - Automatic data backup
- **User Interface**:
  - Clear, intuitive design
  - Real-time feedback
  - Visual progress indicators
  - Stats panel showing current performance

## Installation

### Requirements
- Python 3.8 or higher
- pygame >= 2.0.0

### Basic Installation
```bash
# Clone the repository
git clone [repository-url]
cd math-flash-cards

# Install dependencies
pip install -e .
```

### Development Installation
```bash
# Install with development dependencies
pip install -e .[build]
```

## Usage

### Running the Application
```bash
python -m math_flashcards.main
```

### Basic Controls
- **Mouse/Keyboard**: Enter answers and navigate menus
- **ESC**: Pause game
- **TAB**: View detailed statistics
- **Enter/Return**: Submit answer

## Project Structure

```
math_flashcards/
├── controllers/       # Game logic and control flow
├── models/           # Data structures and business logic
├── utils/            # Helper functions and constants
└── views/            # UI components and rendering
```

### Key Components

- **Game Controller**: Manages game flow and user interaction
- **Analytics Controller**: Tracks and analyzes player performance
- **Player Controller**: Handles user data and persistence
- **Custom Difficulty Analyzer**: Adapts game difficulty to player skill

## Features in Detail

### Difficulty Levels

1. **Intro Mode**
   - Number range: 1-7
   - Operations: Addition only
   - Focus on building confidence

2. **Basic Mode**
   - Number range: 1-12
   - Operations: Addition and subtraction
   - Standard multiplication table range

3. **Medium Mode**
   - Number range: 1-20
   - Operations: Addition, subtraction, multiplication
   - Introduction to negative numbers

4. **Hard Mode**
   - Number range: 1-50
   - All operations including division
   - Advanced number manipulation

5. **Custom Mode**
   - Adaptive number range
   - AI-selected operations based on performance
   - Personalized fact selection

### Analytics & Progress Tracking

- Detailed performance metrics per operation
- Learning curve analysis
- Mastery tracking for individual math facts
- Achievement system
- Session-based statistics
- Long-term progress monitoring

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with pygame
- Created with assistance from Anthropic's Claude AI
- Designed for educational use

## Version

Current Version: 0.8.0-beta+1

---

## For Developers

### Building from Source

```bash
# Install development dependencies
pip install -e .[build]

# Build executable (Windows)
pyinstaller math_flashcards.spec
```

### Data Storage

- Player data is stored in JSON format
- Automatic backups are maintained
- Data validation ensures integrity

### Architecture

The application follows a Model-View-Controller (MVC) pattern:
- Models handle data structures and business logic
- Views manage UI rendering and user input
- Controllers coordinate game flow and state management

### Key Classes

- `GameController`: Main game loop and state management
- `AnalyticsController`: Performance tracking and analysis
- `PlayerController`: User data management
- `QuestionGenerator`: Adaptive problem generation
- `CustomDifficultyAnalyzer`: Difficulty adjustment system

## Support

For issues, please use the GitHub issue tracker.