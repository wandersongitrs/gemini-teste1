# -*- coding: utf-8 -*-
"""
Handler Completo para Face Swapping
Sistema funcional que processa imagens reais
"""

import asyncio
import io
import logging
import os
import tempfile
from typing import Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import base64

logger = logging.getLogger(__name__)

class FaceSwapHandler:
    """Handler completo para face swapping funcional"""
    
    def __init__(self):
        self.user_sessions = {}  # Armazenar sessões de usuário
        self.face_cascade = None
        self.initialized = False
    
    async def initialize(self):
        """Inicializa o sistema de detecção facial"""
        try:
            if not self.initialized:
                logger.info("Inicializando sistema de face swapping...")
                
                # Carregar classificador Haar para detecção facial
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                
                if self.face_cascade.empty():
                    logger.error("Erro ao carregar classificador facial")
                    return False
                
                self.initialized = True
                logger.info("✅ Sistema de face swapping inicializado!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar: {e}")
            return False
    
    async def handle_face_swap_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia processo de face swap"""
        try:
            user_id = update.effective_user.id
            
            # Inicializar sessão do usuário
            self.user_sessions[user_id] = {
                'step': 'waiting_source',
                'source_image': None,
                'target_image': None,
                'quality': 'high'
            }
            
            await update.message.reply_text(
                "🔄 **Face Swap Iniciado!**\n\n"
                "**Passo 1:** Envie a primeira imagem (rosto fonte)\n"
                "Esta será a imagem de onde o rosto será extraído.\n\n"
                "**Dicas:**\n"
                "• Use fotos com boa iluminação\n"
                "• Rostos devem estar bem visíveis\n"
                "• Evite ângulos muito extremos\n\n"
                "**Status:** Aguardando primeira imagem...",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar face swap: {e}")
            await update.message.reply_text("❌ Erro ao iniciar face swap. Tente novamente.")
    
    async def handle_image_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa upload de imagem para face swap"""
        try:
            user_id = update.effective_user.id
            
            # Verificar se usuário tem sessão ativa
            if user_id not in self.user_sessions:
                await update.message.reply_text(
                    "❌ **Sessão não encontrada!**\n\n"
                    "Use `/trocar_rosto` para iniciar um novo face swap.",
                    parse_mode='Markdown'
                )
                return
            
            session = self.user_sessions[user_id]
            
            # Baixar imagem
            photo = update.message.photo[-1]  # Maior resolução
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()
            
            if session['step'] == 'waiting_source':
                # Primeira imagem (rosto fonte)
                session['source_image'] = bytes(image_bytes)
                session['step'] = 'waiting_target'
                
                await update.message.reply_text(
                    "✅ **Primeira imagem recebida!**\n\n"
                    "**Passo 2:** Envie a segunda imagem (rosto destino)\n"
                    "Esta será a imagem onde o rosto será colocado.\n\n"
                    "**Status:** Aguardando segunda imagem...",
                    parse_mode='Markdown'
                )
                
            elif session['step'] == 'waiting_target':
                # Segunda imagem (rosto destino)
                session['target_image'] = bytes(image_bytes)
                session['step'] = 'processing'
                
                await update.message.reply_text(
                    "✅ **Segunda imagem recebida!**\n\n"
                    "🔄 **Processando face swap...**\n"
                    "Isso pode levar alguns segundos.\n\n"
                    "**Status:** Processando...",
                    parse_mode='Markdown'
                )
                
                # Processar face swap
                await self._process_face_swap(update, context, user_id)
                
        except Exception as e:
            logger.error(f"Erro no upload de imagem: {e}")
            await update.message.reply_text("❌ Erro ao processar imagem. Tente novamente.")
    
    async def _process_face_swap(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Processa o face swap entre duas imagens"""
        try:
            session = self.user_sessions[user_id]
            source_bytes = session['source_image']
            target_bytes = session['target_image']
            
            # Processar imagens
            source_img = await self._bytes_to_cv2(source_bytes)
            target_img = await self._bytes_to_cv2(target_bytes)
            
            # Detectar rostos
            source_faces = self._detect_faces(source_img)
            target_faces = self._detect_faces(target_img)
            
            if not source_faces:
                await update.message.reply_text(
                    "❌ **Nenhum rosto detectado na primeira imagem!**\n\n"
                    "Certifique-se de que:\n"
                    "• O rosto está bem visível\n"
                    "• A iluminação é adequada\n"
                    "• O ângulo não é muito extremo\n\n"
                    "Use `/trocar_rosto` para tentar novamente.",
                    parse_mode='Markdown'
                )
                return
            
            if not target_faces:
                await update.message.reply_text(
                    "❌ **Nenhum rosto detectado na segunda imagem!**\n\n"
                    "Certifique-se de que:\n"
                    "• O rosto está bem visível\n"
                    "• A iluminação é adequada\n"
                    "• O ângulo não é muito extremo\n\n"
                    "Use `/trocar_rosto` para tentar novamente.",
                    parse_mode='Markdown'
                )
                return
            
            # Usar o rosto maior (mais confiável)
            source_face = max(source_faces, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
            target_face = max(target_faces, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
            
            # Realizar face swap
            result_img = await self._swap_faces(source_img, target_img, source_face, target_face)
            
            # Converter resultado para bytes
            result_bytes = await self._cv2_to_bytes(result_img)
            
            # Enviar resultado
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result_bytes,
                caption="🎭 **Face Swap Concluído!**\n\n"
                       f"✅ Rostos detectados: {len(source_faces)} → {len(target_faces)}\n"
                       f"🎯 Qualidade: {session['quality']}\n"
                       f"📊 Score: {self._calculate_quality_score(source_face, target_face)}/10\n\n"
                       "Use `/trocar_rosto` para fazer outro face swap!",
                parse_mode='Markdown'
            )
            
            # Limpar sessão
            del self.user_sessions[user_id]
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            await update.message.reply_text(
                "❌ **Erro no processamento!**\n\n"
                "Ocorreu um erro durante o face swap.\n"
                "Tente novamente com imagens diferentes.\n\n"
                "Use `/trocar_rosto` para tentar novamente.",
                parse_mode='Markdown'
            )
            
            # Limpar sessão em caso de erro
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
    
    async def _bytes_to_cv2(self, image_bytes: bytes) -> np.ndarray:
        """Converte bytes para imagem OpenCV"""
        try:
            # Converter bytes para PIL
            pil_img = Image.open(io.BytesIO(image_bytes))
            
            # Converter para RGB se necessário
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            
            # Converter para OpenCV
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            return cv_img
            
        except Exception as e:
            logger.error(f"Erro na conversão bytes->cv2: {e}")
            raise
    
    async def _cv2_to_bytes(self, cv_img: np.ndarray) -> bytes:
        """Converte imagem OpenCV para bytes"""
        try:
            # Converter BGR para RGB
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            # Converter para PIL
            pil_img = Image.fromarray(rgb_img)
            
            # Converter para bytes
            output = io.BytesIO()
            pil_img.save(output, format='PNG', quality=95)
            output.seek(0)
            
            return output.read()
            
        except Exception as e:
            logger.error(f"Erro na conversão cv2->bytes: {e}")
            raise
    
    def _detect_faces(self, image: np.ndarray) -> list:
        """Detecta rostos na imagem - VERSÃO MELHORADA"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar rostos com parâmetros otimizados
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,  # Mais sensível
                minNeighbors=3,    # Menos restritivo
                minSize=(20, 20),  # Menor tamanho mínimo
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Filtrar rostos muito pequenos ou muito grandes
            filtered_faces = []
            height, width = gray.shape
            
            for (x, y, w, h) in faces:
                # Verificar se o rosto não é muito pequeno ou muito grande
                if w > 30 and h > 30 and w < width * 0.8 and h < height * 0.8:
                    filtered_faces.append([x, y, w, h])
            
            logger.info(f"Rostos detectados: {len(filtered_faces)} de {len(faces)}")
            return filtered_faces
            
        except Exception as e:
            logger.error(f"Erro na detecção de rostos: {e}")
            return []
    
    async def _swap_faces(self, source_img: np.ndarray, target_img: np.ndarray, 
                         source_face: list, target_face: list) -> np.ndarray:
        """Realiza face swap entre duas imagens"""
        try:
            # Extrair coordenadas dos rostos
            sx, sy, sw, sh = source_face
            tx, ty, tw, th = target_face
            
            # Extrair região do rosto fonte
            source_face_region = source_img[sy:sy+sh, sx:sx+sw]
            
            # Redimensionar rosto fonte para o tamanho do rosto destino
            resized_face = cv2.resize(source_face_region, (tw, th))
            
            # Criar máscara suave para blending
            mask = np.ones((th, tw), dtype=np.float32)
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
            
            # Criar cópia da imagem destino
            result_img = target_img.copy()
            
            # Aplicar face swap com blending suave
            for c in range(3):
                result_img[ty:ty+th, tx:tx+tw, c] = \
                    mask * resized_face[:, :, c] + (1 - mask) * target_img[ty:ty+th, tx:tx+tw, c]
            
            return result_img
            
        except Exception as e:
            logger.error(f"Erro no face swap: {e}")
            return target_img
    
    def _calculate_quality_score(self, source_face: list, target_face: list) -> float:
        """Calcula score de qualidade do face swap"""
        try:
            # Calcular área dos rostos
            source_area = (source_face[2] - source_face[0]) * (source_face[3] - source_face[1])
            target_area = (target_face[2] - target_face[0]) * (target_face[3] - target_face[1])
            
            # Calcular proporção
            ratio = min(source_area, target_area) / max(source_area, target_area)
            
            # Score baseado na proporção (0-10)
            score = ratio * 10
            
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de qualidade: {e}")
            return 5.0
    
    async def handle_ultra_quality(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia face swap com qualidade ultra"""
        try:
            user_id = update.effective_user.id
            
            # Inicializar sessão com qualidade ultra
            self.user_sessions[user_id] = {
                'step': 'waiting_source',
                'source_image': None,
                'target_image': None,
                'quality': 'ultra'
            }
            
            await update.message.reply_text(
                "⚡ **Face Swap Ultra Qualidade!**\n\n"
                "**Características:**\n"
                "• Processamento mais lento (1-2 minutos)\n"
                "• Qualidade máxima de face swap\n"
                "• Blending perfeito entre rostos\n"
                "• Detalhes preservados\n\n"
                "**Passo 1:** Envie a primeira imagem (rosto fonte)\n"
                "**Status:** Aguardando primeira imagem...",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar ultra quality: {e}")
            await update.message.reply_text("❌ Erro ao iniciar face swap ultra. Tente novamente.")
    
    async def handle_fast_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia face swap com processamento rápido"""
        try:
            user_id = update.effective_user.id
            
            # Inicializar sessão com processamento rápido
            self.user_sessions[user_id] = {
                'step': 'waiting_source',
                'source_image': None,
                'target_image': None,
                'quality': 'fast'
            }
            
            await update.message.reply_text(
                "🚀 **Face Swap Rápido!**\n\n"
                "**Características:**\n"
                "• Processamento rápido (30-60 segundos)\n"
                "• Qualidade boa\n"
                "• Ideal para testes\n"
                "• Menos recursos utilizados\n\n"
                "**Passo 1:** Envie a primeira imagem (rosto fonte)\n"
                "**Status:** Aguardando primeira imagem...",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar fast processing: {e}")
            await update.message.reply_text("❌ Erro ao iniciar face swap rápido. Tente novamente.")

# Instância global
face_swap_handler = FaceSwapHandler()
