"""User preferences independent of the shortcut's working directory."""

import json
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NeuroIntent" / "IsaacLauncher"
SETTINGS_FILE = DATA_ROOT / "settings.json"


def defaults() -> dict:
    return {
        "conda_env_path": str(Path.home() / "anaconda3/envs/neurointent-isaac"),
        "isaac_lab_path": "C:/IsaacLab-3.0",
        "template": "isaacsim.exp.full.kit",
        "gpu_uuid": "",
        "headless": False,
        "num_envs": 16,
        "iterations": 50,
    }


def load_settings(path: Path = SETTINGS_FILE) -> dict:
    settings = defaults()
    if path.exists():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as error:
            raise ValueError(f"Cannot read settings at {path}: {error}") from error
        if not isinstance(saved, dict):
            raise ValueError(f"Settings must be a JSON object: {path}")
        settings.update(saved)
    return settings


def save_settings(settings: dict, path: Path = SETTINGS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    temporary.replace(path)
