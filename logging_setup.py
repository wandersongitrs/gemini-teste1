# -*- coding: utf-8 -*-
import logging
import os
import requests
from logging.handlers import RotatingFileHandler
from typing import List


class TelegramErrorHandler(logging.Handler):
    """Handler que envia mensagens de erro para admins no Telegram."""

    def __init__(self, bot_token: str, admin_ids: List[int]) -> None:
        super().__init__(level=logging.ERROR)
        self.bot_token = bot_token
        self.admin_ids = admin_ids
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage" if bot_token else None

    def emit(self, record: logging.LogRecord) -> None:
        if not self.bot_token or not self.admin_ids:
            return
        try:
            msg = self.format(record)
            for admin_id in self.admin_ids:
                try:
                    requests.post(
                        self.api_url,
                        json={
                            "chat_id": admin_id,
                            "text": f"🚨 ERRO no bot:\n{msg}",
                            "parse_mode": "Markdown",
                        },
                        timeout=10,
                    )
                except Exception:
                    continue
        except Exception:
            pass


def setup_logging(logger_name: str = "gemini_bot") -> logging.Logger:
    """Configura logging com arquivo rotativo, console e alerta Telegram para ERROR."""
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Formatação
    fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Arquivo rotativo
    log_file = os.getenv("BOT_LOG_FILE", "bot.log")
    fh = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Telegram (apenas ERROR)
    token = os.getenv("TELEGRAM_TOKEN", "")
    admin_env = os.getenv("ADMIN_USER_IDS", "")
    admin_ids: List[int] = []
    if admin_env:
        try:
            admin_ids = [int(x.strip()) for x in admin_env.split(",") if x.strip()]
        except Exception:
            admin_ids = []

    tg_handler = TelegramErrorHandler(token, admin_ids)
    tg_handler.setLevel(logging.ERROR)
    tg_handler.setFormatter(fmt)
    logger.addHandler(tg_handler)

    logger.info("Logging configurado (console, arquivo e alertas Telegram em ERROR)")
    return logger
