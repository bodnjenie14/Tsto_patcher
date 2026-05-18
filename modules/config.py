import json
from pathlib import Path

CONFIG_PATH = Path("profiles.json")

DEFAULT_PROFILES = {
    "Bods": {
        "gameserver": "http://192.168.0.162:8080",
        "dlc": "http://192.168.0.162:8080/static",
    },
    "Beta": {
        "gameserver": "https://test.pjtsto.com/",
        "dlc": "https://cdn.projectspringfield.com/static/",
    },
}


def load_profiles():
    if not CONFIG_PATH.exists():
        save_profiles(DEFAULT_PROFILES)
        return dict(DEFAULT_PROFILES)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        profiles = data.get("profiles", {})
        if isinstance(profiles, dict) and profiles:
            return profiles
        return dict(DEFAULT_PROFILES)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Failed to read profiles.json ({e}). Using defaults.")
        return dict(DEFAULT_PROFILES)


def save_profiles(profiles):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"profiles": profiles}, f, indent=2)
    except OSError as e:
        print(f"Failed to write profiles.json: {e}")
