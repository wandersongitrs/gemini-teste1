# -*- coding: utf-8 -*-
"""
Sistema Avançado de Face Swapping com InsightFace
Integração completa com bot do Telegram
"""

import asyncio
import io
import logging
import os
import tempfile
import time
from typing import Dict, List, Optional, Tuple, Any
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import insightface
import onnxruntime as ort
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import httpx

logger = logging.getLogger(__name__)

class AdvancedFaceSwapper:
    """Sistema avançado de face swapping com InsightFace"""
    
    def __init__(self):
        self.app = None
        self.swapper = None
        self.initialized = False
        self.model_path = "models/face_swap"
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
    async def initialize(self):
        """Inicializa os modelos de IA"""
        try:
            if not self.initialized:
                logger.info("Inicializando modelos InsightFace...")
                
                # Configurar contexto (CPU ou GPU)
                ctx_id = 0 if ort.get_device() == 'CPU' else 0
                
                # Inicializar FaceAnalysis
                self.app = insightface.app.FaceAnalysis(
                    name='buffalo_l',
                    providers=['CPUExecutionProvider'] if ort.get_device() == 'CPU' else ['CUDAExecutionProvider']
                )
                self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))
                
                # Inicializar Face Swapper (modelo será baixado automaticamente)
                try:
                    self.swapper = insightface.model_zoo.get_model('inswapper_128.onnx')
                except Exception as e:
                    logger.warning(f"Modelo inswapper não encontrado: {e}")
                    # Usar modelo alternativo ou implementação básica
                    self.swapper = None
                
                self.initialized = True
                logger.info("✅ Modelos InsightFace inicializados com sucesso!")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar modelos: {e}")
            raise
    
    async def swap_faces(self, source_image: bytes, target_image: bytes, 
                        quality: str = "high", blend_factor: float = 0.8) -> Dict[str, Any]:
        """Realiza face swap entre duas imagens"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Processar imagens
            source_img = await self._process_image(source_image)
            target_img = await self._process_image(target_image)
            
            # Detectar rostos
            source_faces = self.app.get(source_img)
            target_faces = self.app.get(target_img)
            
            if not source_faces:
                return {'success': False, 'error': 'Nenhum rosto detectado na imagem fonte'}
            if not target_faces:
                return {'success': False, 'error': 'Nenhum rosto detectado na imagem destino'}
            
            # Usar o rosto com maior confiança
            source_face = max(source_faces, key=lambda x: x.det_score)
            target_face = max(target_faces, key=lambda x: x.det_score)
            
            # Realizar face swap
            if self.swapper:
                result_img = self.swapper.get(target_img, target_face, source_face, paste_back=True)
            else:
                # Implementação básica usando apenas detecção de rostos
                result_img = await self._basic_face_swap(target_img, source_img, source_face, target_face)
            
            # Aplicar pós-processamento baseado na qualidade
            if quality == "ultra":
                result_img = await self._enhance_quality(result_img)
            elif quality == "high":
                result_img = await self._apply_blending(result_img, target_img, blend_factor)
            
            # Converter para bytes
            result_bytes = await self._image_to_bytes(result_img)
            
            return {
                'success': True,
                'image': result_bytes,
                'source_faces_count': len(source_faces),
                'target_faces_count': len(target_faces),
                'quality_score': self._calculate_quality_score(source_face, target_face)
            }
            
        except Exception as e:
            logger.error(f"Erro no face swap: {e}")
            return {'success': False, 'error': str(e)}
    
    async def swap_face_to_scenario(self, face_image: bytes, scenario_prompt: str, 
                                   style: str = "realistic") -> Dict[str, Any]:
        """Coloca rosto em um cenário gerado"""
        try:
            # Gerar cenário usando Stable Diffusion
            scenario_image = await self._generate_scenario(scenario_prompt, style)
            
            if not scenario_image:
                return {'success': False, 'error': 'Erro na geração do cenário'}
            
            # Realizar face swap
            result = await self.swap_faces(face_image, scenario_image, quality="high")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na geração de cenário: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _basic_face_swap(self, target_img: np.ndarray, source_img: np.ndarray, 
                              source_face, target_face) -> np.ndarray:
        """Implementação básica de face swap usando apenas detecção"""
        try:
            # Extrair região do rosto fonte
            source_bbox = source_face.bbox.astype(int)
            source_face_region = source_img[source_bbox[1]:source_bbox[3], source_bbox[0]:source_bbox[2]]
            
            # Redimensionar para o tamanho do rosto destino
            target_bbox = target_face.bbox.astype(int)
            target_size = (target_bbox[2] - target_bbox[0], target_bbox[3] - target_bbox[1])
            resized_face = cv2.resize(source_face_region, target_size)
            
            # Criar máscara suave
            mask = np.ones((target_size[1], target_size[0]), dtype=np.float32)
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
            
            # Aplicar face swap com blending
            result_img = target_img.copy()
            for c in range(3):
                result_img[target_bbox[1]:target_bbox[3], target_bbox[0]:target_bbox[2], c] = \
                    mask * resized_face[:, :, c] + (1 - mask) * target_img[target_bbox[1]:target_bbox[3], target_bbox[0]:target_bbox[2], c]
            
            return result_img
            
        except Exception as e:
            logger.error(f"Erro no face swap básico: {e}")
            return target_img
    
    async def _process_image(self, image_bytes: bytes) -> np.ndarray:
        """Processa imagem para análise"""
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
            logger.error(f"Erro no processamento de imagem: {e}")
            raise
    
    async def _generate_scenario(self, prompt: str, style: str) -> Optional[bytes]:
        """Gera cenário usando Stable Diffusion"""
        try:
            # Configurar prompt baseado no estilo
            style_prompts = {
                'realistic': f"photorealistic, high quality, detailed, {prompt}",
                'artistic': f"artistic, painterly style, {prompt}",
                'fantasy': f"fantasy, magical, ethereal, {prompt}",
                'cyberpunk': f"cyberpunk, futuristic, neon lights, {prompt}",
                'vintage': f"vintage, retro style, film photography, {prompt}"
            }
            
            enhanced_prompt = style_prompts.get(style, f"high quality, {prompt}")
            
            # Usar Hugging Face API para Stable Diffusion
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
            
            payload = {
                "inputs": enhanced_prompt,
                "parameters": {
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                    "width": 1024,
                    "height": 1024
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Erro na API: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro na geração de cenário: {e}")
            return None
    
    async def _enhance_quality(self, image: np.ndarray) -> np.ndarray:
        """Melhora a qualidade da imagem"""
        try:
            # Aplicar filtros de melhoria
            enhanced = cv2.bilateralFilter(image, 9, 75, 75)
            enhanced = cv2.addWeighted(image, 0.7, enhanced, 0.3, 0)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Erro na melhoria de qualidade: {e}")
            return image
    
    async def _apply_blending(self, result_img: np.ndarray, target_img: np.ndarray, 
                            blend_factor: float) -> np.ndarray:
        """Aplica blending suave entre imagens"""
        try:
            # Criar máscara para blending
            mask = np.ones_like(result_img, dtype=np.float32) * blend_factor
            
            # Aplicar blending
            blended = cv2.addWeighted(result_img, blend_factor, target_img, 1 - blend_factor, 0)
            
            return blended
            
        except Exception as e:
            logger.error(f"Erro no blending: {e}")
            return result_img
    
    async def _image_to_bytes(self, image: np.ndarray) -> bytes:
        """Converte imagem OpenCV para bytes"""
        try:
            # Converter BGR para RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Converter para PIL
            pil_image = Image.fromarray(rgb_image)
            
            # Converter para bytes
            output = io.BytesIO()
            pil_image.save(output, format='PNG', quality=95)
            output.seek(0)
            
            return output.read()
            
        except Exception as e:
            logger.error(f"Erro na conversão para bytes: {e}")
            raise
    
    def _calculate_quality_score(self, source_face, target_face) -> float:
        """Calcula score de qualidade do face swap"""
        try:
            # Fatores de qualidade
            source_score = source_face.det_score
            target_score = target_face.det_score
            
            # Calcular score médio
            quality_score = (source_score + target_score) / 2
            
            return round(quality_score, 2)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de qualidade: {e}")
            return 0.0

# Instância global
face_swapper = AdvancedFaceSwapper()
