# -*- coding: utf-8 -*-
"""
Comandos de Face Swapping Funcionais
Substitui os comandos antigos por versões funcionais
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from face_swap_handler import face_swap_handler

logger = logging.getLogger(__name__)

async def trocar_rosto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Troca rostos entre duas imagens - FUNCIONAL"""
    try:
        await face_swap_handler.handle_face_swap_request(update, context)
    except Exception as e:
        logger.error(f"Erro no face swap: {e}")
        await update.message.reply_text(f"❌ Erro na troca de rostos: {str(e)}")

async def trocar_rosto_ultra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Troca rostos com qualidade ultra - FUNCIONAL"""
    try:
        await face_swap_handler.handle_ultra_quality(update, context)
    except Exception as e:
        logger.error(f"Erro no face swap ultra: {e}")
        await update.message.reply_text(f"❌ Erro na troca de rostos ultra: {str(e)}")

async def trocar_rosto_rapido(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Troca rostos com processamento rápido - FUNCIONAL"""
    try:
        await face_swap_handler.handle_fast_processing(update, context)
    except Exception as e:
        logger.error(f"Erro no face swap rápido: {e}")
        await update.message.reply_text(f"❌ Erro na troca de rostos rápida: {str(e)}")

async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para upload de imagens durante face swap"""
    try:
        await face_swap_handler.handle_image_upload(update, context)
    except Exception as e:
        logger.error(f"Erro no upload de imagem: {e}")
        await update.message.reply_text("❌ Erro ao processar imagem. Tente novamente.")

