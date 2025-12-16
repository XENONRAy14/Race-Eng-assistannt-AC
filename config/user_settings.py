"""
User Settings - Persistent user configuration storage.
Saves user preferences to a JSON file in Documents/Assetto Corsa/race_engineer_config.json
"""

import json
from pathlib import Path
from typing import Optional, Any


class UserSettings:
    """
    Manages persistent user settings.
    Settings are saved to Documents folder for persistence.
    """
    
    def __init__(self):
        """Initialize user settings."""
        self._settings: dict = {}
        self._config_path = self._get_config_path()
        self._load()
    
    def _get_config_path(self) -> Path:
        """Get the path to the user config file."""
        # Save in Documents/Assetto Corsa for easy access
        docs_path = Path.home() / "Documents" / "Assetto Corsa"
        docs_path.mkdir(parents=True, exist_ok=True)
        return docs_path / "race_engineer_config.json"
    
    def _load(self) -> None:
        """Load settings from disk."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._settings = {}
        else:
            self._settings = {}
    
    def _save(self) -> None:
        """Save settings to disk."""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Silently fail if we can't write
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save."""
        self._settings[key] = value
        self._save()
    
    def get_ac_game_path(self) -> Optional[Path]:
        """Get the saved AC game path."""
        path_str = self.get("ac_game_path")
        if path_str:
            return Path(path_str)
        return None
    
    def set_ac_game_path(self, path: Path) -> None:
        """Save the AC game path."""
        self.set("ac_game_path", str(path))
    
    def get_ac_documents_path(self) -> Optional[Path]:
        """Get the saved AC documents path."""
        path_str = self.get("ac_documents_path")
        if path_str:
            return Path(path_str)
        return None
    
    def set_ac_documents_path(self, path: Path) -> None:
        """Save the AC documents path."""
        self.set("ac_documents_path", str(path))


# Global instance
_user_settings: Optional[UserSettings] = None


def get_user_settings() -> UserSettings:
    """Get the global user settings instance."""
    global _user_settings
    if _user_settings is None:
        _user_settings = UserSettings()
    return _user_settings
