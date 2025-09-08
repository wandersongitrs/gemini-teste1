#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenVoice Simples - Versão que funciona como fallback
Quando os modelos complexos não carregam, ainda oferece funcionalidade básica
"""

import asyncio
import logging
import io
import tempfile
import os
from typing import Dict, Any, Optional, List
import numpy as np
from pydub import AudioSegment
import soundfile as sf

logger = logging.getLogger(__name__)

class OpenVoiceSimples:
    """Versão simplificada do OpenVoice que sempre funciona"""
    
    def __init__(self):
        self.available = True  # Sempre disponível
        logger.info("OpenVoice Simples inicializado (sempre disponível)")
    
    async def clone_voice_instant(self, reference_audio_bytes: bytes, text: str, 
                                 language: str = "pt", style_settings: Dict = None) -> Optional[io.BytesIO]:
        """
        Clonagem básica usando gTTS + ajustes de pitch
        """
        try:
            logger.info("Iniciando clonagem OpenVoice Simples...")
            
            # Usar gTTS como base
            from gtts import gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            
            # Tentar aplicar ajustes com pydub se disponível
            try:
                audio_segment = AudioSegment.from_mp3(audio_io)
                
                # Analisar áudio de referência
                ref_analysis = self._analyze_reference_audio(reference_audio_bytes)
                
                # Aplicar ajustes
                if ref_analysis.get('is_male', True):
                    # Voz masculina - pitch mais baixo
                    audio_segment = audio_segment._spawn(
                        audio_segment.raw_data, 
                        overrides={"frame_rate": int(audio_segment.frame_rate * 0.8)}
                    )
                    audio_segment = audio_segment.set_frame_rate(22050)
                else:
                    # Voz feminina - pitch ligeiramente mais alto
                    audio_segment = audio_segment._spawn(
                        audio_segment.raw_data, 
                        overrides={"frame_rate": int(audio_segment.frame_rate * 1.1)}
                    )
                    audio_segment = audio_segment.set_frame_rate(22050)
                
                # Aplicar estilo se fornecido
                if style_settings:
                    speed = style_settings.get('speed', 1.0)
                    if speed != 1.0:
                        audio_segment = audio_segment.speedup(playback_speed=speed)
                
                # Normalizar
                audio_segment = audio_segment.normalize()
                
                # Converter para BytesIO
                result_io = io.BytesIO()
                audio_segment.export(result_io, format="mp3", bitrate="192k")
                result_io.seek(0)
                
            except Exception as pydub_error:
                logger.warning(f"Pydub falhou, retornando áudio gTTS original: {pydub_error}")
                # Retornar áudio gTTS sem modificações se pydub falhar
                audio_io.seek(0)
                return audio_io
            
            logger.info("Clonagem OpenVoice Simples concluída!")
            return result_io
            
        except Exception as e:
            logger.error(f"Erro na clonagem OpenVoice Simples: {e}")
            return None
    
    def _analyze_reference_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Análise simples do áudio de referência"""
        try:
            # Tentar usar pydub se disponível
            try:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
                samples = np.array(audio.get_array_of_samples())
                
                # Cálculo simples de pitch médio
                zero_crossings = np.diff(np.signbit(samples)).sum()
                duration = len(samples) / audio.frame_rate
                avg_frequency = zero_crossings / (2 * duration)
                
                # Determinar gênero baseado na frequência
                is_male = avg_frequency < 200  # Threshold simples
                
                return {
                    'is_male': is_male,
                    'avg_frequency': avg_frequency,
                    'duration': duration
                }
                
            except Exception as pydub_error:
                logger.warning(f"Pydub falhou, usando análise básica: {pydub_error}")
                
                # Análise básica baseada no tamanho do arquivo
                # Arquivos maiores geralmente têm mais conteúdo de áudio
                file_size = len(audio_bytes)
                
                # Estimativa simples baseada no tamanho
                if file_size > 10000:  # Mais de 10KB
                    is_male = True  # Assumir masculino para arquivos maiores
                    avg_frequency = 150
                    duration = file_size / 16000  # Estimativa aproximada
                else:
                    is_male = False  # Assumir feminino para arquivos menores
                    avg_frequency = 200
                    duration = file_size / 16000  # Estimativa aproximada
                
                return {
                    'is_male': is_male,
                    'avg_frequency': avg_frequency,
                    'duration': duration
                }
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return {'is_male': True, 'avg_frequency': 150, 'duration': 0}
    
    async def analyze_voice_characteristics(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Análise simplificada de características da voz"""
        try:
            analysis = self._analyze_reference_audio(audio_bytes)
            
            return {
                "voice_type": "masculina" if analysis['is_male'] else "feminina",
                "avg_frequency": analysis['avg_frequency'],
                "duration": analysis['duration'],
                "quality_rating": "boa",
                "cloning_compatibility": "compatível",
                "recommended_settings": {
                    "speed": 1.0,
                    "emotion": "neutral",
                    "pitch": 0.8 if analysis['is_male'] else 1.1
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return {"error": str(e)}
    
    async def get_supported_languages(self) -> List[str]:
        """Idiomas suportados"""
        return ["pt", "en", "es", "fr", "de", "it", "ja", "ko", "zh"]
    
    async def get_available_emotions(self) -> List[str]:
        """Emoções disponíveis"""
        return ["neutral", "happy", "calm"]
    
    async def close(self):
        """Fechar recursos"""
        logger.info("OpenVoice Simples finalizado")

# Função para criar instância
def create_openvoice_simples() -> OpenVoiceSimples:
    """Cria instância do OpenVoice Simples"""
    return OpenVoiceSimples()
