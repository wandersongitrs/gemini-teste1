# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    env = os.getenv("APP_ENV", "dev").lower()
    filename = "config.prod.json" if env in ("prod", "production") else "config.dev.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "app_name": "gemini-bot",
            "env": env,
            "logging": {"level": "INFO", "log_file": "bot.log"},
            "telegram": {"admin_user_ids": []},
            "cache": {"ttl_seconds": 3600},
        }
