import os
import json

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "isaac_sim_path": os.environ.get("ISAAC_SIM_PATH", r"C:\Users\bruni\isaacsim"),
        "logging_enabled": False
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
