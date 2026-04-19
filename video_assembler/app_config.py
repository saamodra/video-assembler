import json
import os
from pathlib import Path
from typing import Dict, Any

class AppConfig:
    """Handles parsing and configuration values (SRP)."""
    
    def __init__(self, config_file: str = "config.json"):
        self.settings: Dict[str, Any] = {
            "output_path": "output/final_video.mp4",
            "resolution": [1280, 720],
            "fps": 30,
            "title_duration": 4,
            "text_duration": 3,
            "font_path": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "crop_padding": 0.3
        }
        self.load(config_file)
        self._resolve_font_path()

    def load(self, config_file: str):
        path = Path(config_file)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.settings.update(json.load(f))

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def _resolve_font_path(self):
        configured_path = self.settings.get("font_path")
        if configured_path and os.path.exists(configured_path):
            return

        fallbacks = [
            str(Path(__file__).parent.parent / "assets" / "font.ttf"),
        ]

        for path in fallbacks:
            if os.path.exists(path):
                print(f"[Config] Configured font not found. Falling back to {path}")
                self.settings["font_path"] = path
                return

        raise RuntimeError(
            f"Font file not found: {configured_path}. "
            "Please specify a valid 'font_path' in your config.json."
        )
