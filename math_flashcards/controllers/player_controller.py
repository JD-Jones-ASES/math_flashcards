import json
import os
import sys
import shutil
import pathlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from math_flashcards.models.player import Player
from math_flashcards.utils.constants import GameSettings

class PlayerController:
    """Controls player data management and persistence with improved validation and backup"""
    def __init__(self, backup_dir: str = "backups"):
        # Get the application base directory
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            base_dir = pathlib.Path(sys._MEIPASS)
        else:
            # If running from source
            base_dir = pathlib.Path(__file__).parent.parent

        # Set up all paths first
        self.data_dir = base_dir / "data"
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        # Keep all data files together
        self.backup_dir = self.data_dir / backup_dir
        self.data_file = self.data_dir.absolute() / "players.json"
        self.log_file = self.data_dir.absolute() / "player_controller.log"

        # Initialize directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Now set up logging based on execution context
        if getattr(sys, 'frozen', False):
            # Use simpler logging for frozen executable
            logging.basicConfig(
                filename=str(self.log_file),  # Convert Path to string
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger('PlayerController')
        else:
            # Use rotating file handler for development
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=1024 * 1024,  # 1MB max file size
                backupCount=2
            )
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            logger = logging.getLogger('PlayerController')
            logger.setLevel(logging.INFO)
            logger.handlers = []
            logger.addHandler(handler)
            logger.propagate = False
            self.logger = logger

        # Initialize remaining attributes
        self.current_player: Optional[Player] = None
        self.auto_save_interval = GameSettings.ANALYTICS['save_interval']
        self.last_save_time = datetime.now()

        # Initialize data file if it doesn't exist
        if not self.data_file.exists():
            self._create_default_data()

    def _validate_player_data(self, data: Dict) -> bool:
        """Validate player data structure and content"""
        try:
            # Check required top-level fields
            required_fields = ["version", "last_updated", "players"]
            if not all(field in data for field in required_fields):
                self.logger.error("Missing required fields in player data")
                return False
                
            # Validate version
            if data["version"] != "1.0":
                self.logger.error(f"Unsupported data version: {data['version']}")
                return False
                
            # Validate last_updated timestamp
            try:
                datetime.fromisoformat(data["last_updated"])
            except ValueError:
                self.logger.error("Invalid last_updated timestamp")
                return False
                
            # Validate each player's data
            for player in data["players"]:
                if not self._validate_single_player(player):
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False

    def _validate_single_player(self, player: Dict) -> bool:
        """Validate individual player data"""
        required_fields = [
            "name", "creation_date", "total_problems_attempted",
            "total_correct", "operation_stats", "difficulty_stats"
        ]
        
        try:
            # Check required fields
            if not all(field in player for field in required_fields):
                self.logger.error(f"Missing required fields for player {player.get('name', 'UNKNOWN')}")
                return False
                
            # Validate numeric fields are non-negative
            numeric_fields = ["total_problems_attempted", "total_correct", 
                            "current_streak", "best_streak"]
            for field in numeric_fields:
                if field in player and (not isinstance(player[field], (int, float)) or 
                                      player[field] < 0):
                    self.logger.error(f"Invalid {field} value for player {player['name']}")
                    return False
                    
            # Validate statistics consistency
            if player["total_problems_attempted"] < player["total_correct"]:
                self.logger.error(f"Inconsistent attempt/correct counts for player {player['name']}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Player validation error: {str(e)}")
            return False

    def _create_backup(self) -> bool:
        """Create a backup of the current player data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"players_backup_{timestamp}.json"

            # Create backup
            shutil.copy2(self.data_file, backup_file)

            # Cleanup old backups
            self._cleanup_old_backups()

            self.logger.info(f"Backup created: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return False

    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the 10 most recent"""
        try:
            backups = sorted([
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.startswith("players_backup_")
            ])
            
            # Remove excess backups
            while len(backups) > 10:
                os.remove(backups.pop(0))
                
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")

    def load_players(self) -> List[str]:
        """Load and return list of player names with validation"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            if not self._validate_player_data(data):
                # Try to restore from latest backup
                backup_file = self._find_latest_backup()
                if backup_file:
                    self.logger.warning("Attempting to restore from backup")
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                    if not self._validate_player_data(data):
                        raise ValueError("Backup data also invalid")
                else:
                    self.logger.warning("No valid backup found. Creating new default data.")
                    self._create_default_data()
                    with open(self.data_file, 'r') as f:
                        data = json.load(f)

            return [player["name"] for player in data["players"]]

        except Exception as e:
            self.logger.error(f"Error loading players: {str(e)}")
            self._create_default_data()
            return ["Mr. Jones"]

    def _find_latest_backup(self) -> Optional[pathlib.Path]:
        """Find the most recent backup file"""
        try:
            backups = sorted(
                [f for f in self.backup_dir.glob("players_backup_*.json")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            return backups[0] if backups else None
        except Exception:
            return None

    def save_progress(self, force: bool = False) -> bool:
        """Save current player's progress with validation and backup"""
        if not self.current_player:
            return False
            
        # Check if auto-save interval has elapsed
        current_time = datetime.now()
        if not force and (current_time - self.last_save_time).total_seconds() < self.auto_save_interval:
            return False
            
        try:
            # Read current data
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Create backup before modifying
            self._create_backup()
            
            # Update player data
            updated = False
            for i, player in enumerate(data["players"]):
                if player["name"] == self.current_player.name:
                    new_player_data = self.current_player.to_dict()
                    if self._validate_single_player(new_player_data):
                        data["players"][i] = new_player_data
                        updated = True
                        break
            
            if not updated:
                self.logger.error(f"Player {self.current_player.name} not found in data file")
                return False
                
            data["last_updated"] = current_time.isoformat()
            
            # Validate complete data before saving
            if not self._validate_player_data(data):
                self.logger.error("Data validation failed before save")
                return False
                
            # Save updated data
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.last_save_time = current_time
            self.logger.info(f"Progress saved for player {self.current_player.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving progress: {str(e)}")
            return False

    def _create_default_data(self) -> None:
        """Create default player data file"""
        try:
            # Ensure data directory exists and is writable
            os.makedirs(self.data_dir, exist_ok=True)

            # Create default data
            default_data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "players": [
                {
                    "name": "Mr. Jones",
                    "creation_date": datetime.now().isoformat(),
                    "last_active": None,
                    "total_problems_attempted": 0,
                    "total_correct": 0,
                    "current_streak": 0,
                    "best_streak": 0,
                    "time_spent_mins": 0.0,
                    "operation_stats": {
                        op: {
                            "problems_attempted": 0,
                            "correct": 0,
                            "avg_response_time_ms": 0.0,
                            "accuracy": 0.0,
                            "fact_mastery": {},
                            "last_practiced": None
                        }
                        for op in ['+', '-', '*', '/']
                    },
                    "difficulty_stats": {
                        diff: {
                            "problems_attempted": 0,
                            "correct": 0,
                            "avg_response_time_ms": 0.0,
                            "accuracy": 0.0,
                            "last_played": None
                        }
                        for diff in ["Intro", "Basic", "Medium", "Hard", "Custom"]
                    },
                    "achievement_stats": {
                        "perfect_sessions": 0,
                        "problems_solved_under_3s": 0,
                        "longest_streak": 0,
                        "total_practice_days": 0,
                        "consecutive_days_streak": 0,
                        "last_practice_date": None
                    },
                    "recent_sessions": []
                }
            ]
        }
            with open(self.data_file, 'w') as f:
                json.dump(default_data, f, indent=2)
                # self.logger.info("Created default player data file")
            os.chmod(self.data_file, 0o644)
        except Exception as e:
            self.logger.error(f"Error creating default data: {str(e)}")

    def create_player(self, name: str) -> Optional[Player]:
        """Create a new player"""
        if self._player_exists(name):
            return None
            
        try:
            # Create new player
            new_player = Player(name)
            
            # Load existing data
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Add new player
            data["players"].append(new_player.to_dict())
            data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.current_player = new_player
            return new_player
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error creating player: {e}")
            return None

    def _player_exists(self, name: str) -> bool:
        """Check if player name exists with improved validation"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            if not self._validate_player_data(data):
                self.logger.error("Invalid data structure detected during player existence check")
                return False

            return any(p["name"] == name for p in data["players"])

        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error checking player existence: {str(e)}")
            return False

    def _update_last_active(self) -> None:
        """Update last active timestamp for current player"""
        if not self.current_player:
            return
            
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            # Update player data
            for player in data["players"]:
                if player["name"] == self.current_player.name:
                    player["last_active"] = datetime.now().isoformat()
                    break
                    
            data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error updating last active: {e}")

    def get_leaderboard_data(self) -> List[Dict[str, Any]]:
        """Get leaderboard data for all players"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            leaderboard = []
            for player_data in data["players"]:
                leaderboard.append({
                    "name": player_data["name"],
                    "total_solved": player_data["total_correct"],
                    "accuracy": (player_data["total_correct"] / 
                               max(1, player_data["total_problems_attempted"]) * 100),
                    "best_streak": player_data["best_streak"],
                    "practice_days": player_data["achievement_stats"]["total_practice_days"]
                })
                
            # Sort by total solved (could add other sorting options)
            return sorted(leaderboard, key=lambda x: x["total_solved"], reverse=True)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error getting leaderboard: {e}")
            return []

    def cleanup_old_sessions(self, days: int = 30) -> None:
        """Clean up old session data beyond specified days"""
        if not self.current_player:
            return
            
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent sessions
        self.current_player.recent_sessions = [
            session for session in self.current_player.recent_sessions
            if datetime.strptime(session.date, "%Y-%m-%d").date() > cutoff_date.date()
        ]
        
        # Save changes
        self.save_progress(force=True)

    def get_player_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for current player"""
        if not self.current_player:
            return {}
            
        return {
            "overall": {
                "total_problems": self.current_player.total_problems_attempted,
                "correct": self.current_player.total_correct,
                "accuracy": (self.current_player.total_correct / 
                           max(1, self.current_player.total_problems_attempted) * 100),
                "time_spent": self.current_player.time_spent_mins,
                "best_streak": self.current_player.best_streak
            },
            "operations": {
                op: {
                    "mastery": self.current_player.get_mastery_level(op),
                    "accuracy": stats.accuracy,
                    "avg_time": stats.avg_response_time_ms,
                    "total_attempts": stats.problems_attempted
                }
                for op, stats in self.current_player.operation_stats.items()
            },
            "achievements": self.current_player.achievement_stats,
            "recent_sessions": [
                {
                    "date": session.date,
                    "problems": session.problems_attempted,
                    "correct": session.correct,
                    "accuracy": (session.correct / max(1, session.problems_attempted) * 100),
                    "avg_time": session.avg_response_time_ms
                }
                for session in self.current_player.recent_sessions[-10:]  # Last 10 sessions
            ]
        }

    def delete_player(self, name: str) -> bool:
        """Delete a player from the system with improved validation and cleanup"""
        # Protect the default player
        if name == "Mr. Jones":
            self.logger.warning(f"Attempted to delete protected default player {name}")
            return False

        try:
            # Validate player exists before attempting deletion
            if not self._player_exists(name):
                self.logger.warning(f"Attempted to delete non-existent player {name}")
                return False

            with open(self.data_file, 'r') as f:
                data = json.load(f)

            # Verify data structure before modification
            if not self._validate_player_data(data):
                self.logger.error("Invalid data structure detected before deletion")
                return False

            # Create backup before modification
            if not self._create_backup():
                self.logger.error("Failed to create backup before player deletion")
                return False

            # Store initial player count
            initial_count = len(data["players"])

            # Remove player
            data["players"] = [p for p in data["players"] if p["name"] != name]

            # Verify one player was removed
            if len(data["players"]) != initial_count - 1:
                self.logger.error(
                    f"Unexpected player count after deletion: expected {initial_count - 1}, got {len(data['players'])}")
                return False

            # Update timestamp
            data["last_updated"] = datetime.now().isoformat()

            # Validate modified data
            if not self._validate_player_data(data):
                self.logger.error("Invalid data structure detected after deletion")
                return False

            # Save updated data
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)

            # Clear current player if deleted
            if self.current_player and self.current_player.name == name:
                self.current_player = None
                self.logger.info(f"Cleared current player after deletion of {name}")

            # Remove any backup files specific to this player
            try:
                backup_pattern = f"*{name}*.json"
                for backup_file in self.backup_dir.glob(backup_pattern):
                    backup_file.unlink()
            except Exception as e:
                self.logger.warning(f"Error cleaning up backup files for {name}: {str(e)}")

            self.logger.info(f"Successfully deleted player {name}")
            return True

        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error during player deletion: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during player deletion: {str(e)}")
            return False

    def select_player(self, name: str) -> Optional[Player]:
        """Load and select a player by name with validation"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            if not self._validate_player_data(data):
                self.logger.error("Data validation failed during player selection")
                return None

            for player_data in data["players"]:
                if player_data["name"] == name:
                    try:
                        # Initialize empty fact mastery if needed
                        for op_stats in player_data["operation_stats"].values():
                            if not op_stats["fact_mastery"]:
                                op_stats["fact_mastery"] = {}

                        self.current_player = Player.from_dict(player_data)
                        self._update_last_active()
                        self.logger.info(f"Player {name} selected successfully")
                        return self.current_player
                    except Exception as e:
                        self.logger.error(f"Error creating player object: {str(e)}")
                        return None

            self.logger.warning(f"Player {name} not found")
            return None

        except Exception as e:
            self.logger.error(f"Error selecting player: {str(e)}")
            return None
            
    def _update_last_active(self) -> None:
        """Update last active timestamp for current player"""
        if not self.current_player:
            return
            
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            # Update player data
            updated = False
            for player in data["players"]:
                if player["name"] == self.current_player.name:
                    player["last_active"] = datetime.now().isoformat()
                    updated = True
                    break
                    
            if not updated:
                self.logger.warning(f"Player {self.current_player.name} not found during last_active update")
                return
                    
            data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Last active timestamp updated for {self.current_player.name}")
                
        except Exception as e:
            self.logger.error(f"Error updating last active: {str(e)}")
