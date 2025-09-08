# -*- coding: utf-8 -*-
import os
import json
import time
from typing import Optional, Dict, Any
import requests
from tasks.celery_app import celery_app

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def _send_telegram_message(chat_id: int, text: str) -> None:
    if not TELEGRAM_TOKEN:
        return
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
    except Exception:
        pass


@celery_app.task(name="tasks.clone_voice")
def clone_voice_task(chat_id: int, audio_file_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _send_telegram_message(chat_id, "🎤 Processando clonagem de voz… isso pode levar alguns minutos.")
    # Simulação de processamento pesado
    time.sleep(8)
    result = {
        "status": "ok",
        "voice_id": f"voice_{int(time.time())}",
        "details": "Voz clonada com sucesso (simulada)",
    }
    _send_telegram_message(chat_id, "✅ Clonagem concluída! Use /falar para gerar áudio com a nova voz.")
    return result


@celery_app.task(name="tasks.research_report")
def research_report_task(chat_id: int, query: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _send_telegram_message(chat_id, f"🔎 Pesquisando: {query}\nIsso pode levar 1-2 minutos…")
    time.sleep(5)
    result_text = f"Relatório sobre '{query}' (simulado). Inclua aqui síntese e fontes."
    _send_telegram_message(chat_id, f"📄 Resultado:\n{result_text}")
    return {"status": "ok", "text": result_text}


@celery_app.task(name="tasks.generate_image")
def generate_image_task(chat_id: int, prompt: str) -> Dict[str, Any]:
    _send_telegram_message(chat_id, f"🎨 Gerando imagem para: {prompt}")
    time.sleep(6)
    _send_telegram_message(chat_id, "🖼️ Imagem gerada (simulada).")
    return {"status": "ok"}
