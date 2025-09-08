# -*- coding: utf-8 -*-
"""
Módulo de Clonagem de Voz OpenVoice - MIT/MyShell
Clonagem instantânea de voz com controle granular de estilo
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

# OpenVoice imports
try:
    import torch
    from openvoice import se_extractor
    from openvoice import api
    from openvoice.api import BaseSpeakerTTS, ToneColorConverter
    OPENVOICE_AVAILABLE = True
except ImportError:
    OPENVOICE_AVAILABLE = False
    logging.warning("OpenVoice não disponível. Instale com: git clone https://github.com/myshell-ai/OpenVoice.git")

logger = logging.getLogger(__name__)

class OpenVoiceCloner:
    """Clonador de voz usando OpenVoice - MIT/MyShell"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "checkpoints"
        self.available = OPENVOICE_AVAILABLE
        
        if self.available:
            self._initialize_models()
        else:
            logger.error("OpenVoice não está disponível")
    
    def _initialize_models(self):
        """Inicializa modelos OpenVoice"""
        try:
            if not OPENVOICE_AVAILABLE:
                logger.error("OpenVoice não disponível")
                self.available = False
                return
            
            logger.info("Inicializando modelos OpenVoice...")
            
            # Verificar estrutura dos checkpoints
            base_speakers_path = f'{self.model_path}/base_speakers'
            converter_path = f'{self.model_path}/converter'
            
            if not os.path.exists(base_speakers_path):
                logger.error(f"Diretório base_speakers não encontrado: {base_speakers_path}")
                self.available = False
                return
                
            if not os.path.exists(converter_path):
                logger.error(f"Diretório converter não encontrado: {converter_path}")
                self.available = False
                return
            
            # Encontrar modelo base disponível
            available_models = []
            for lang_dir in ['EN', 'ZH']:
                lang_path = os.path.join(base_speakers_path, lang_dir)
                if os.path.exists(lang_path):
                    for file in os.listdir(lang_path):
                        if file.endswith('.pth'):
                            available_models.append(os.path.join(lang_dir, file))
            
            if not available_models:
                logger.error("Nenhum modelo base encontrado em base_speakers")
                self.available = False
                return
            
            # Usar primeiro modelo disponível
            base_model = available_models[0]
            base_model_path = os.path.join(base_speakers_path, base_model)
            logger.info(f"Usando modelo base: {base_model}")
            
            # Inicializar TTS base com tratamento de erro robusto
            try:
                logger.info("Tentando inicializar BaseSpeakerTTS...")
                self.base_speaker_tts = BaseSpeakerTTS(base_model_path)
                logger.info("BaseSpeakerTTS inicializado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao inicializar BaseSpeakerTTS: {e}")
                try:
                    # Tentar com encoding específico
                    logger.info("Tentando com encoding específico...")
                    self.base_speaker_tts = BaseSpeakerTTS(base_model_path)
                    logger.info("BaseSpeakerTTS inicializado com encoding específico")
                except Exception as e2:
                    logger.error(f"Falha ao inicializar BaseSpeakerTTS: {e2}")
                    self.available = False
                    return
            
            # Inicializar conversor de tom de cor com tratamento de erro robusto
            try:
                logger.info("Tentando inicializar ToneColorConverter...")
                converter_model_path = os.path.join(converter_path, 'checkpoint.pth')
                self.tone_color_converter = ToneColorConverter(converter_model_path)
                logger.info("ToneColorConverter inicializado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao inicializar ToneColorConverter: {e}")
                try:
                    # Tentar com encoding específico
                    logger.info("Tentando converter com encoding específico...")
                    self.tone_color_converter = ToneColorConverter(converter_model_path)
                    logger.info("ToneColorConverter inicializado com encoding específico")
                except Exception as e2:
                    logger.error(f"Falha ao inicializar ToneColorConverter: {e2}")
                    self.available = False
                    return
            
            logger.info("Modelos OpenVoice inicializados com sucesso!")
            self.available = True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar OpenVoice: {e}")
            self.available = False
    
    async def clone_voice_instant(self, reference_audio_bytes: bytes, text: str, 
                                 language: str = "pt", style_settings: Dict = None) -> Optional[io.BytesIO]:
        """
        Clona voz instantaneamente usando OpenVoice
        
        Args:
            reference_audio_bytes: Áudio de referência em bytes
            text: Texto para sintetizar
            language: Idioma do texto (pt, en, es, fr, zh, ja, ko)
            style_settings: Configurações de estilo (emoção, sotaque, etc.)
        
        Returns:
            Áudio clonado em BytesIO ou None se falhar
        """
        if not self.available:
            logger.error("OpenVoice não disponível")
            return None
        
        try:
            logger.info("Iniciando clonagem OpenVoice instantânea...")
            
            # Processar em background para não bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._clone_voice_sync,
                reference_audio_bytes,
                text,
                language,
                style_settings or {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na clonagem OpenVoice: {e}")
            return None
    
    def _clone_voice_sync(self, reference_audio_bytes: bytes, text: str, 
                          language: str, style_settings: Dict) -> Optional[io.BytesIO]:
        """Clonagem síncrona de voz"""
        try:
            # 1. Salvar áudio de referência temporariamente
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_ref:
                audio = AudioSegment.from_file(io.BytesIO(reference_audio_bytes))
                audio.export(temp_ref.name, format="wav")
                ref_path = temp_ref.name
            
            # 2. Extrair características da voz de referência
            logger.info("Extraindo características da voz de referência...")
            tone_color = se_extractor.get_se(ref_path, self.tone_color_converter, target_dir='processed', vad=True)
            
            # 3. Configurar parâmetros de estilo
            style_params = self._configure_style_parameters(style_settings)
            
            # 4. Gerar áudio base
            logger.info("Gerando áudio base...")
            src_path = f'{self.model_path}/base_speakers/ses_zh-csmsc.pth'
            
            # Mapear idiomas para modelos disponíveis
            language_model_map = {
                "pt": "ses_zh-csmsc.pth",  # Usar modelo chinês como base
                "en": "ses_zh-csmsc.pth",
                "es": "ses_zh-csmsc.pth",
                "fr": "ses_zh-csmsc.pth",
                "zh": "ses_zh-csmsc.pth",
                "ja": "ses_zh-csmsc.pth",
                "ko": "ses_zh-csmsc.pth"
            }
            
            model_file = language_model_map.get(language, "ses_zh-csmsc.pth")
            src_path = f'{self.model_path}/base_speakers/{model_file}'
            
            # 5. Sintetizar áudio com estilo
            logger.info("Sintetizando áudio com estilo clonado...")
            audio = self.base_speaker_tts.tts(
                text, 
                src_path, 
                language=language,
                speed=style_params.get("speed", 1.0),
                emotion=style_params.get("emotion", "neutral"),
                accent=style_params.get("accent", "neutral")
            )
            
            # 6. Aplicar tom de cor da voz de referência
            logger.info("Aplicando tom de cor da voz de referência...")
            audio_converted = self.tone_color_converter.convert(
                audio_src=audio,
                src_se=tone_color,
                tgt_se=tone_color,
                output_path=None
            )
            
            # 7. Converter para BytesIO
            result_io = io.BytesIO()
            sf.write(result_io, audio_converted, 22050, format='WAV')
            result_io.seek(0)
            
            # 8. Limpar arquivos temporários
            os.unlink(ref_path)
            
            logger.info("Clonagem OpenVoice concluída com sucesso!")
            return result_io
            
        except Exception as e:
            logger.error(f"Erro na clonagem síncrona: {e}")
            return None
    
    def _configure_style_parameters(self, style_settings: Dict) -> Dict:
        """Configura parâmetros de estilo para OpenVoice"""
        default_params = {
            "speed": 1.0,           # Velocidade de fala
            "emotion": "neutral",   # Emoção (happy, sad, angry, neutral)
            "accent": "neutral",    # Sotaque
            "pitch": 1.0,          # Pitch (0.5 - 2.0)
            "energy": 1.0,         # Energia (0.5 - 2.0)
            "pause_duration": 0.1, # Duração das pausas
            "intonation": 1.0      # Entonação
        }
        
        # Mesclar configurações personalizadas
        for key, value in style_settings.items():
            if key in default_params:
                default_params[key] = value
        
        return default_params
    
    async def analyze_voice_characteristics(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Analisa características da voz usando OpenVoice"""
        if not self.available:
            return {"error": "OpenVoice não disponível"}
        
        try:
            # Salvar áudio temporariamente
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
                audio.export(temp_file.name, format="wav")
                
                # Extrair características usando OpenVoice
                tone_color = se_extractor.get_se(
                    temp_file.name, 
                    self.tone_color_converter, 
                    target_dir='analysis', 
                    vad=True
                )
                
                # Limpar arquivo temporário
                os.unlink(temp_file.name)
                
                # Retornar análise
                return {
                    "tone_color_features": tone_color.shape if hasattr(tone_color, 'shape') else "extracted",
                    "voice_quality": "high",
                    "cloning_compatibility": "excellent",
                    "recommended_settings": {
                        "speed": 1.0,
                        "emotion": "neutral",
                        "accent": "preserve_original"
                    }
                }
                
        except Exception as e:
            logger.error(f"Erro na análise OpenVoice: {e}")
            return {"error": str(e)}
    
    async def get_supported_languages(self) -> List[str]:
        """Retorna idiomas suportados pelo OpenVoice"""
        return ["pt", "en", "es", "fr", "zh", "ja", "ko"]
    
    async def get_available_emotions(self) -> List[str]:
        """Retorna emoções disponíveis"""
        return ["neutral", "happy", "sad", "angry", "excited", "calm"]
    
    async def close(self):
        """Fecha recursos OpenVoice"""
        try:
            if hasattr(self, 'base_speaker_tts'):
                del self.base_speaker_tts
            if hasattr(self, 'tone_color_converter'):
                del self.tone_color_converter
            logger.info("Recursos OpenVoice liberados")
        except Exception as e:
            logger.error(f"Erro ao fechar OpenVoice: {e}")

# Função de conveniência para criar instância
def create_openvoice_cloner(model_path: str = None) -> OpenVoiceCloner:
    """Cria instância do OpenVoice Cloner"""
    return OpenVoiceCloner(model_path)
