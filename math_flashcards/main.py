"""
Main entry point for the Math Flashcards application.
"""
import os
import sys

def main():
    """Initialize and run the game"""
    # Add the project root to sys.path if needed
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from math_flashcards.controllers.game_controller import GameController
    game = GameController()
    game.run()

if __name__ == "__main__":
    main()