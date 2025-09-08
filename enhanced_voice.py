import asyncio
import io
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VoiceAnalysisResult:
    """Resultado da análise de voz"""
    transcription: str
    language: str
    confidence: float
    duration: float
    word_count: int
    sentiment: str
    intent: str
    entities: List[Dict]
    audio_format: str
    sample_rate: int

class EnhancedVoiceHandler:
    """Sistema de comandos de voz melhorados"""
    
    def __init__(self):
        self.supported_languages = {
            'pt': 'Português',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano'
        }
        self.voice_commands = {
            'gerar_imagem': ['criar imagem', 'gerar foto', 'desenhar'],
            'buscar_web': ['pesquisar', 'buscar', 'encontrar'],
            'gerar_codigo': ['criar código', 'programar', 'desenvolver'],
            'resumir': ['resumir', 'sumarizar', 'sintetizar'],
            'traduzir': ['traduzir', 'tradução', 'idioma'],
            'ajuda': ['ajuda', 'help', 'comandos', 'menu']
        }
    
    async def process_voice_message(self, update, context, voice_bytes: bytes, 
                                  mime_type: str = "audio/ogg") -> VoiceAnalysisResult:
        """Processa mensagem de voz com análise completa"""
        start_time = time.time()
        
        try:
            # 1. Transcrição com Gemini
            transcription = await self._transcribe_with_gemini(context, voice_bytes, mime_type)
            
            # 2. Análise de linguagem
            language = await self._detect_language(transcription)
            
            # 3. Análise de sentimento
            sentiment = await self._analyze_sentiment(transcription)
            
            # 4. Detecção de intenção
            intent = await self._detect_intent(transcription)
            
            # 5. Extração de entidades
            entities = await self._extract_entities(transcription)
            
            # 6. Análise de áudio
            audio_info = await self._analyze_audio(voice_bytes, mime_type)
            
            duration = time.time() - start_time
            word_count = len(transcription.split())
            
            result = VoiceAnalysisResult(
                transcription=transcription,
                language=language,
                confidence=0.85,  # Placeholder
                duration=duration,
                word_count=word_count,
                sentiment=sentiment,
                intent=intent,
                entities=entities,
                audio_format=mime_type,
                sample_rate=audio_info.get('sample_rate', 44100)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar voz: {e}")
            raise
    
    async def _transcribe_with_gemini(self, context, voice_bytes: bytes, mime_type: str) -> str:
        """Transcreve áudio usando Gemini"""
        try:
            gemini_model = context.bot_data["gemini_model"]
            audio_io = io.BytesIO(voice_bytes)
            audio_file = genai.upload_file(audio_io, mime_type=mime_type)
            
            # Prompt melhorado para transcrição
            prompt = """
            Transcreva este áudio com precisão, mantendo:
            - Pontuação correta
            - Capitalização apropriada
            - Identificação de números e datas
            - Preservação de nomes próprios
            
            Se houver múltiplos idiomas, identifique e transcreva cada um.
            """
            
            response = await asyncio.wait_for(
                gemini_model.generate_content_async([prompt, audio_file]),
                timeout=60.0
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return "Erro na transcrição do áudio"
    
    async def _detect_language(self, text: str) -> str:
        """Detecta idioma do texto"""
        try:
            # Análise baseada em palavras-chave e padrões
            text_lower = text.lower()
            
            # Português
            pt_patterns = ['português', 'portuguese', 'brasil', 'brazil', 'olá', 'oi', 'tudo bem', 'obrigado']
            if any(pattern in text_lower for pattern in pt_patterns):
                return 'pt'
            
            # Inglês
            en_patterns = ['english', 'hello', 'hi', 'how are you', 'the', 'and', 'is', 'you']
            if any(pattern in text_lower for pattern in en_patterns):
                return 'en'
            
            # Espanhol
            es_patterns = ['español', 'hola', 'buenos días', 'gracias', 'por favor', 'que tal']
            if any(pattern in text_lower for pattern in es_patterns):
                return 'es'
            
            # Francês
            fr_patterns = ['français', 'bonjour', 'merci', 's\'il vous plaît', 'oui', 'non']
            if any(pattern in text_lower for pattern in fr_patterns):
                return 'fr'
            
            # Alemão
            de_patterns = ['deutsch', 'hallo', 'danke', 'bitte', 'ja', 'nein']
            if any(pattern in text_lower for pattern in de_patterns):
                return 'de'
            
            # Italiano
            it_patterns = ['italiano', 'ciao', 'grazie', 'prego', 'sì', 'no']
            if any(pattern in text_lower for pattern in it_patterns):
                return 'it'
            
            return 'pt'  # Padrão
            
        except Exception as e:
            logger.error(f"Erro na detecção de idioma: {e}")
            return 'pt'
    
    async def _analyze_sentiment(self, text: str) -> str:
        """Analisa sentimento do texto"""
        try:
            # Análise simples de sentimento
            positive_words = ['bom', 'ótimo', 'excelente', 'maravilhoso', 'feliz', 'satisfeito', 'gosto']
            negative_words = ['ruim', 'péssimo', 'terrível', 'triste', 'insatisfeito', 'não gosto', 'problema']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            return 'neutral'
    
    async def _detect_intent(self, text: str) -> str:
        """Detecta intenção do usuário"""
        try:
            text_lower = text.lower()
            
            # Verificar comandos de voz
            for intent, keywords in self.voice_commands.items():
                if any(keyword in text_lower for keyword in keywords):
                    return intent
            
            # Análise de padrões
            if any(word in text_lower for word in ['pergunta', 'questão', 'como', 'quando', 'onde', 'por que']):
                return 'question'
            
            if any(word in text_lower for word in ['obrigado', 'valeu', 'agradeço']):
                return 'gratitude'
            
            if any(word in text_lower for word in ['tchau', 'adeus', 'até logo', 'bye']):
                return 'farewell'
            
            return 'general'
            
        except Exception as e:
            logger.error(f"Erro na detecção de intenção: {e}")
            return 'general'
    
    async def _extract_entities(self, text: str) -> List[Dict]:
        """Extrai entidades do texto"""
        try:
            entities = []
            
            # Detectar emails
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            for email in emails:
                entities.append({
                    'type': 'email',
                    'value': email,
                    'start': text.find(email),
                    'end': text.find(email) + len(email)
                })
            
            # Detectar URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, text)
            for url in urls:
                entities.append({
                    'type': 'url',
                    'value': url,
                    'start': text.find(url),
                    'end': text.find(url) + len(url)
                })
            
            # Detectar números
            number_pattern = r'\b\d+(?:\.\d+)?\b'
            numbers = re.findall(number_pattern, text)
            for number in numbers:
                entities.append({
                    'type': 'number',
                    'value': number,
                    'start': text.find(number),
                    'end': text.find(number) + len(number)
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Erro na extração de entidades: {e}")
            return []
    
    async def _analyze_audio(self, voice_bytes: bytes, mime_type: str) -> Dict:
        """Analisa informações do áudio"""
        try:
            from pydub import AudioSegment
            import io
            
            # Converter bytes para AudioSegment
            audio_io = io.BytesIO(voice_bytes)
            
            if mime_type == "audio/ogg":
                audio = AudioSegment.from_ogg(audio_io)
            elif mime_type == "audio/mp3":
                audio = AudioSegment.from_mp3(audio_io)
            elif mime_type == "audio/wav":
                audio = AudioSegment.from_wav(audio_io)
            else:
                # Tentar detectar automaticamente
                audio = AudioSegment.from_file(audio_io)
            
            return {
                'duration_ms': len(audio),
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'frame_width': audio.frame_width,
                'max_amplitude': audio.max_possible_amplitude
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de áudio: {e}")
            return {
                'duration_ms': 0,
                'sample_rate': 44100,
                'channels': 1,
                'frame_width': 2,
                'max_amplitude': 32767
            }
    
    async def generate_voice_response(self, text: str, language: str = 'pt') -> bytes:
        """Gera resposta em áudio"""
        try:
            from gtts import gTTS
            
            # Configurar TTS
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Gerar áudio
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            
            return audio_io.read()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta em áudio: {e}")
            return b""
    
    def get_language_display_name(self, lang_code: str) -> str:
        """Retorna nome do idioma para exibição"""
        return self.supported_languages.get(lang_code, 'Desconhecido')
    
    def get_sentiment_emoji(self, sentiment: str) -> str:
        """Retorna emoji baseado no sentimento"""
        sentiment_emojis = {
            'positive': '😊',
            'negative': '😔',
            'neutral': '😐'
        }
        return sentiment_emojis.get(sentiment, '😐')
    
    def get_intent_description(self, intent: str) -> str:
        """Retorna descrição da intenção"""
        intent_descriptions = {
            'gerar_imagem': 'Gerar imagem',
            'buscar_web': 'Buscar na web',
            'gerar_codigo': 'Gerar código',
            'resumir': 'Resumir conteúdo',
            'traduzir': 'Traduzir texto',
            'ajuda': 'Solicitar ajuda',
            'question': 'Fazer pergunta',
            'gratitude': 'Expressar gratidão',
            'farewell': 'Despedida',
            'general': 'Conversa geral'
        }
        return intent_descriptions.get(intent, 'Intenção desconhecida')

# Instância global do handler de voz
enhanced_voice_handler = EnhancedVoiceHandler()

# Funções auxiliares
async def process_voice_message(update, context, voice_bytes: bytes, mime_type: str = "audio/ogg"):
    """Função auxiliar para processar mensagem de voz"""
    return await enhanced_voice_handler.process_voice_message(update, context, voice_bytes, mime_type)

async def generate_voice_response(text: str, language: str = 'pt'):
    """Função auxiliar para gerar resposta em áudio"""
    return await enhanced_voice_handler.generate_voice_response(text, language)

