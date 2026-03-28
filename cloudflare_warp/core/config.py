"""Persistent configuration stored in a JSON file."""

import json
import os
from pathlib import Path


_CONFIG_DIR = Path.home() / ".config" / "cloudflare-warp-py"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS = {
    "theme": "dark",
    "start_minimized": False,
    "start_on_login": False,
    "dns_mode": "warp",       # warp | doh | dot | off
    "split_tunnel_mode": "exclude",
    "split_tunnel_ips": [],
    "account_type": "free",   # free | warp_plus
    "show_notifications": True,
}


class Config:
    def __init__(self):
        self._data = dict(_DEFAULTS)
        self._load()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self._save()

    def all(self) -> dict:
        return dict(self._data)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if _CONFIG_FILE.exists():
            try:
                with open(_CONFIG_FILE, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(_CONFIG_FILE, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
        except OSError:
            pass
