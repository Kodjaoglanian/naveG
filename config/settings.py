import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")

DEFAULT_SETTINGS = {
    "general": {
        "home_page": "https://www.google.com",
        "search_engine": "https://www.google.com/search?q={}",
        "download_path": os.path.expanduser("~/Downloads"),
        "save_session": True
    },
    "privacy": {
        "clear_on_exit": False,
        "do_not_track": True,
        "block_ads": False
    },
    "appearance": {
        "theme": "light",
        "font_size": 14,
        "show_bookmarks_bar": True,
        "show_status_bar": True
    },
    "advanced": {
        "hardware_acceleration": True,
        "proxy_enabled": False,
        "proxy_address": "",
        "proxy_port": "",
        "user_agent": ""
    }
}

class Settings:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def get(self, section, key):
        return self.settings.get(section, {}).get(key)

    def set(self, section, key, value):
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        self.save_settings()

# Create a global instance
settings = Settings()
