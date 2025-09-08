# -*- coding: utf-8 -*-
"""
Sistema de Geração de Cenários com Stable Diffusion + ControlNet
"""

import asyncio
import io
import logging
import os
import json
import time
from typing import Dict, List, Optional, Any
import httpx
from PIL import Image
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ScenarioGenerator:
    """Gerador de cenários com Stable Diffusion"""
    
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models"
        self.models = {
            'realistic': 'stabilityai/stable-diffusion-xl-base-1.0',
            'artistic': 'runwayml/stable-diffusion-v1-5',
            'fantasy': 'stabilityai/stable-diffusion-xl-base-1.0',
            'cyberpunk': 'stabilityai/stable-diffusion-xl-base-1.0',
            'vintage': 'stabilityai/stable-diffusion-xl-base-1.0'
        }
        self.templates = self._load_scenario_templates()
        
    def _load_scenario_templates(self) -> Dict[str, Dict]:
        """Carrega templates de cenários"""
        return {
            'praia': {
                'prompt': 'praia tropical com coqueiros, mar azul cristalino, areia branca, céu ensolarado, ondas suaves',
                'style': 'realistic',
                'negative_prompt': 'people, faces, buildings, cars',
                'guidance_scale': 7.5
            },
            'escritorio': {
                'prompt': 'escritório moderno com vista da cidade, mesa de vidro, plantas, iluminação profissional, ambiente corporativo',
                'style': 'realistic',
                'negative_prompt': 'people, faces, messy, cluttered',
                'guidance_scale': 8.0
            },
            'floresta': {
                'prompt': 'floresta mágica com árvores antigas, raios de sol, fadas, atmosfera mística, cores vibrantes',
                'style': 'fantasy',
                'negative_prompt': 'people, faces, modern, urban',
                'guidance_scale': 7.0
            },
            'restaurante': {
                'prompt': 'restaurante elegante à noite, mesa com toalha branca, velas, ambiente romântico, iluminação suave',
                'style': 'realistic',
                'negative_prompt': 'people, faces, messy, bright lights',
                'guidance_scale': 8.5
            },
            'espaço': {
                'prompt': 'espaço sideral com estrelas, nebulosa colorida, planeta ao fundo, atmosfera cósmica, cores vibrantes',
                'style': 'fantasy',
                'negative_prompt': 'people, faces, earth, buildings',
                'guidance_scale': 7.5
            },
            'montanha': {
                'prompt': 'paisagem de montanha com picos nevados, lago cristalino, céu azul, natureza selvagem',
                'style': 'realistic',
                'negative_prompt': 'people, faces, buildings, cars',
                'guidance_scale': 7.0
            },
            'cidade': {
                'prompt': 'vista aérea de cidade moderna à noite, arranha-céus iluminados, ruas movimentadas, atmosfera urbana',
                'style': 'realistic',
                'negative_prompt': 'people, faces, daytime, nature',
                'guidance_scale': 8.0
            },
            'castelo': {
                'prompt': 'castelo medieval em uma colina, torres altas, bandeiras, atmosfera épica, céu dramático',
                'style': 'fantasy',
                'negative_prompt': 'people, faces, modern, cars',
                'guidance_scale': 7.5
            },
            'laboratorio': {
                'prompt': 'laboratório científico moderno, equipamentos de alta tecnologia, iluminação azul, ambiente futurista',
                'style': 'cyberpunk',
                'negative_prompt': 'people, faces, messy, old',
                'guidance_scale': 8.0
            },
            'biblioteca': {
                'prompt': 'biblioteca antiga com estantes altas, livros antigos, iluminação dourada, atmosfera acolhedora',
                'style': 'vintage',
                'negative_prompt': 'people, faces, modern, bright',
                'guidance_scale': 7.5
            }
        }
    
    async def generate_scenario(self, prompt: str, style: str = "realistic", 
                              template: Optional[str] = None) -> Dict[str, Any]:
        """Gera cenário baseado no prompt"""
        try:
            # Usar template se especificado
            if template and template in self.templates:
                template_data = self.templates[template]
                enhanced_prompt = template_data['prompt']
                style = template_data['style']
                negative_prompt = template_data.get('negative_prompt', '')
                guidance_scale = template_data.get('guidance_scale', 7.5)
            else:
                enhanced_prompt = self._enhance_prompt(prompt, style)
                negative_prompt = self._get_negative_prompt(style)
                guidance_scale = 7.5
            
            # Gerar imagem
            image_bytes = await self._generate_image(
                enhanced_prompt, 
                negative_prompt, 
                style, 
                guidance_scale
            )
            
            if image_bytes:
                return {
                    'success': True,
                    'image': image_bytes,
                    'prompt_used': enhanced_prompt,
                    'style': style,
                    'template': template
                }
            else:
                return {'success': False, 'error': 'Erro na geração da imagem'}
                
        except Exception as e:
            logger.error(f"Erro na geração de cenário: {e}")
            return {'success': False, 'error': str(e)}
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Melhora o prompt baseado no estilo"""
        style_enhancements = {
            'realistic': 'photorealistic, high quality, detailed, professional photography, sharp focus',
            'artistic': 'artistic, painterly style, beautiful composition, artistic lighting',
            'fantasy': 'fantasy, magical, ethereal, mystical atmosphere, vibrant colors',
            'cyberpunk': 'cyberpunk, futuristic, neon lights, dark atmosphere, high tech',
            'vintage': 'vintage, retro style, film photography, nostalgic atmosphere'
        }
        
        enhancement = style_enhancements.get(style, 'high quality, detailed')
        return f"{enhancement}, {prompt}"
    
    def _get_negative_prompt(self, style: str) -> str:
        """Retorna negative prompt baseado no estilo"""
        negative_prompts = {
            'realistic': 'people, faces, cartoon, anime, low quality, blurry',
            'artistic': 'photorealistic, realistic, people, faces, low quality',
            'fantasy': 'realistic, photorealistic, people, faces, modern, urban',
            'cyberpunk': 'nature, natural, people, faces, vintage, retro',
            'vintage': 'modern, futuristic, people, faces, neon, high tech'
        }
        
        return negative_prompts.get(style, 'people, faces, low quality')
    
    async def _generate_image(self, prompt: str, negative_prompt: str, 
                            style: str, guidance_scale: float) -> Optional[bytes]:
        """Gera imagem usando Hugging Face API"""
        try:
            model_name = self.models.get(style, self.models['realistic'])
            api_url = f"{self.api_url}/{model_name}"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": negative_prompt,
                    "num_inference_steps": 50,
                    "guidance_scale": guidance_scale,
                    "width": 1024,
                    "height": 1024,
                    "seed": int(time.time()) % 1000000
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    return response.content
                elif response.status_code == 503:
                    # Modelo carregando, aguardar
                    logger.info("Modelo carregando, aguardando...")
                    await asyncio.sleep(30)
                    response = await client.post(api_url, headers=headers, json=payload, timeout=120)
                    if response.status_code == 200:
                        return response.content
                
                logger.error(f"Erro na API: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na geração de imagem: {e}")
            return None
    
    def get_available_templates(self) -> List[str]:
        """Retorna templates disponíveis"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict]:
        """Retorna informações do template"""
        return self.templates.get(template_name)
    
    def get_available_styles(self) -> List[str]:
        """Retorna estilos disponíveis"""
        return list(self.models.keys())

# Instância global
scenario_generator = ScenarioGenerator()

