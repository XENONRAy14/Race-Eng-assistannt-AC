"""
Setup Repository - SQLite database for storing setups and profiles.
Handles persistence of setups, driver profiles, and feedback.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from models.setup import Setup
from models.driver_profile import DriverProfile
from ai.feedback_engine import FeedbackEntry


class SetupRepository:
    """
    SQLite repository for storing application data.
    Manages setups, driver profiles, and feedback entries.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize repository.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Driver profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                stability_rotation REAL DEFAULT 50.0,
                grip_slide REAL DEFAULT 30.0,
                safety_aggression REAL DEFAULT 40.0,
                drift_grip REAL DEFAULT 70.0,
                comfort_performance REAL DEFAULT 50.0,
                preferred_behavior TEXT DEFAULT 'balanced',
                experience_level TEXT DEFAULT 'intermediate',
                created_at TEXT,
                last_used TEXT,
                is_active INTEGER DEFAULT 0
            )
        """)
        
        # Setups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS setups (
                setup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                car_id TEXT NOT NULL,
                track_id TEXT NOT NULL,
                behavior TEXT,
                sections_json TEXT,
                created_at TEXT,
                notes TEXT,
                ai_score REAL DEFAULT 0.0,
                ai_confidence REAL DEFAULT 0.0,
                profile_id INTEGER,
                file_path TEXT,
                FOREIGN KEY (profile_id) REFERENCES driver_profiles(profile_id)
            )
        """)
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                setup_id INTEGER,
                profile_id INTEGER,
                feedback_type TEXT DEFAULT 'rating',
                rating INTEGER DEFAULT 3,
                issues_json TEXT,
                comments TEXT,
                behavior TEXT,
                created_at TEXT,
                FOREIGN KEY (setup_id) REFERENCES setups(setup_id),
                FOREIGN KEY (profile_id) REFERENCES driver_profiles(profile_id)
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        conn.commit()
        
        # Create default profile if none exists
        cursor.execute("SELECT COUNT(*) FROM driver_profiles")
        if cursor.fetchone()[0] == 0:
            self._create_default_profile(cursor)
            conn.commit()
    
    def _create_default_profile(self, cursor: sqlite3.Cursor) -> None:
        """Create a default driver profile."""
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO driver_profiles 
            (name, stability_rotation, grip_slide, safety_aggression, 
             drift_grip, comfort_performance, preferred_behavior, 
             experience_level, created_at, last_used, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Default Driver",
            50.0, 30.0, 40.0, 70.0, 50.0,
            "balanced", "intermediate",
            now, now, 1
        ))
    
    # ═══════════════════════════════════════════════════════════════
    # DRIVER PROFILE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def save_profile(self, profile: DriverProfile) -> int:
        """
        Save a driver profile.
        Returns the profile ID.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if profile.profile_id:
            # Update existing
            cursor.execute("""
                UPDATE driver_profiles SET
                    name = ?,
                    stability_rotation = ?,
                    grip_slide = ?,
                    safety_aggression = ?,
                    drift_grip = ?,
                    comfort_performance = ?,
                    preferred_behavior = ?,
                    experience_level = ?,
                    last_used = ?
                WHERE profile_id = ?
            """, (
                profile.name,
                profile.stability_rotation,
                profile.grip_slide,
                profile.safety_aggression,
                profile.drift_grip,
                profile.comfort_performance,
                profile.preferred_behavior,
                profile.experience_level,
                now,
                profile.profile_id
            ))
            profile_id = profile.profile_id
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO driver_profiles 
                (name, stability_rotation, grip_slide, safety_aggression,
                 drift_grip, comfort_performance, preferred_behavior,
                 experience_level, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.name,
                profile.stability_rotation,
                profile.grip_slide,
                profile.safety_aggression,
                profile.drift_grip,
                profile.comfort_performance,
                profile.preferred_behavior,
                profile.experience_level,
                now, now
            ))
            profile_id = cursor.lastrowid
        
        conn.commit()
        return profile_id
    
    def get_profile(self, profile_id: int) -> Optional[DriverProfile]:
        """Get a driver profile by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM driver_profiles WHERE profile_id = ?",
            (profile_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_profile(row)
    
    def get_active_profile(self) -> Optional[DriverProfile]:
        """Get the currently active driver profile."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM driver_profiles WHERE is_active = 1 LIMIT 1"
        )
        row = cursor.fetchone()
        
        if not row:
            # Return first profile if no active
            cursor.execute("SELECT * FROM driver_profiles LIMIT 1")
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_profile(row)
    
    def set_active_profile(self, profile_id: int) -> None:
        """Set a profile as the active profile."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Deactivate all
        cursor.execute("UPDATE driver_profiles SET is_active = 0")
        
        # Activate selected
        cursor.execute(
            "UPDATE driver_profiles SET is_active = 1 WHERE profile_id = ?",
            (profile_id,)
        )
        
        conn.commit()
    
    def get_all_profiles(self) -> list[DriverProfile]:
        """Get all driver profiles."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM driver_profiles ORDER BY last_used DESC")
        rows = cursor.fetchall()
        
        return [self._row_to_profile(row) for row in rows]
    
    def delete_profile(self, profile_id: int) -> bool:
        """Delete a driver profile."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM driver_profiles WHERE profile_id = ?",
            (profile_id,)
        )
        conn.commit()
        
        return cursor.rowcount > 0
    
    def _row_to_profile(self, row: sqlite3.Row) -> DriverProfile:
        """Convert a database row to a DriverProfile."""
        return DriverProfile(
            profile_id=row["profile_id"],
            name=row["name"],
            stability_rotation=row["stability_rotation"],
            grip_slide=row["grip_slide"],
            safety_aggression=row["safety_aggression"],
            drift_grip=row["drift_grip"],
            comfort_performance=row["comfort_performance"],
            preferred_behavior=row["preferred_behavior"],
            experience_level=row["experience_level"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else datetime.now()
        )
    
    # ═══════════════════════════════════════════════════════════════
    # SETUP METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def save_setup(self, setup: Setup, profile_id: Optional[int] = None, file_path: Optional[str] = None) -> int:
        """
        Save a setup to the database.
        Returns the setup ID.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Serialize sections to JSON
        sections_dict = {}
        for name, section in setup.sections.items():
            sections_dict[name] = section.values
        sections_json = json.dumps(sections_dict)
        
        if setup.setup_id:
            # Update existing
            cursor.execute("""
                UPDATE setups SET
                    name = ?,
                    car_id = ?,
                    track_id = ?,
                    behavior = ?,
                    sections_json = ?,
                    notes = ?,
                    ai_score = ?,
                    ai_confidence = ?,
                    profile_id = ?,
                    file_path = ?
                WHERE setup_id = ?
            """, (
                setup.name,
                setup.car_id,
                setup.track_id,
                setup.behavior,
                sections_json,
                setup.notes,
                setup.ai_score,
                setup.ai_confidence,
                profile_id,
                file_path,
                setup.setup_id
            ))
            setup_id = setup.setup_id
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO setups 
                (name, car_id, track_id, behavior, sections_json,
                 created_at, notes, ai_score, ai_confidence, profile_id, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                setup.name,
                setup.car_id,
                setup.track_id,
                setup.behavior,
                sections_json,
                setup.created_at.isoformat(),
                setup.notes,
                setup.ai_score,
                setup.ai_confidence,
                profile_id,
                file_path
            ))
            setup_id = cursor.lastrowid
        
        conn.commit()
        return setup_id
    
    def get_setup(self, setup_id: int) -> Optional[Setup]:
        """Get a setup by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM setups WHERE setup_id = ?", (setup_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_setup(row)
    
    def get_setups_for_car_track(self, car_id: str, track_id: str) -> list[Setup]:
        """Get all setups for a car/track combination."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM setups WHERE car_id = ? AND track_id = ? ORDER BY created_at DESC",
            (car_id, track_id)
        )
        rows = cursor.fetchall()
        
        return [self._row_to_setup(row) for row in rows]
    
    def get_recent_setups(self, limit: int = 10) -> list[Setup]:
        """Get most recent setups."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM setups ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        
        return [self._row_to_setup(row) for row in rows]
    
    def delete_setup(self, setup_id: int) -> bool:
        """Delete a setup."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM setups WHERE setup_id = ?", (setup_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def _row_to_setup(self, row: sqlite3.Row) -> Setup:
        """Convert a database row to a Setup."""
        # Parse sections JSON
        sections_dict = json.loads(row["sections_json"]) if row["sections_json"] else {}
        
        setup_data = {
            "setup_id": row["setup_id"],
            "name": row["name"],
            "car_id": row["car_id"],
            "track_id": row["track_id"],
            "behavior": row["behavior"],
            "sections": sections_dict,
            "created_at": row["created_at"],
            "notes": row["notes"],
            "ai_score": row["ai_score"],
            "ai_confidence": row["ai_confidence"]
        }
        
        return Setup.from_dict(setup_data)
    
    # ═══════════════════════════════════════════════════════════════
    # FEEDBACK METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def save_feedback(self, feedback: FeedbackEntry) -> int:
        """Save feedback entry."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        issues_json = json.dumps(feedback.issues)
        
        cursor.execute("""
            INSERT INTO feedback 
            (setup_id, profile_id, feedback_type, rating, issues_json,
             comments, behavior, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.setup_id,
            feedback.profile_id,
            feedback.feedback_type,
            feedback.rating,
            issues_json,
            feedback.comments,
            feedback.behavior,
            feedback.created_at.isoformat()
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_feedback_for_profile(self, profile_id: int) -> list[FeedbackEntry]:
        """Get all feedback for a profile."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM feedback WHERE profile_id = ? ORDER BY created_at DESC",
            (profile_id,)
        )
        rows = cursor.fetchall()
        
        return [self._row_to_feedback(row) for row in rows]
    
    def _row_to_feedback(self, row: sqlite3.Row) -> FeedbackEntry:
        """Convert a database row to a FeedbackEntry."""
        issues = json.loads(row["issues_json"]) if row["issues_json"] else []
        
        return FeedbackEntry(
            feedback_id=row["feedback_id"],
            setup_id=row["setup_id"],
            profile_id=row["profile_id"],
            feedback_type=row["feedback_type"],
            rating=row["rating"],
            issues=issues,
            comments=row["comments"],
            behavior=row["behavior"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
    
    # ═══════════════════════════════════════════════════════════════
    # SETTINGS METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            return row["value"]
        return default
    
    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
    
    def delete_setting(self, key: str) -> bool:
        """Delete a setting."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
        conn.commit()
        
        return cursor.rowcount > 0
