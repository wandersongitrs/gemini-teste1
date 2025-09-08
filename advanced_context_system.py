# -*- coding: utf-8 -*-
"""
Sistema de Contexto Multimodal Avançado
======================================

Este módulo implementa um sistema inteligente de contexto que permite ao bot
"lembrar" de interações multimodais anteriores e usar esse contexto para
enriquecer respostas futuras.

Funcionalidades:
- Contexto multimodal persistente
- Estados de conversa inteligentes
- Personalização de personalidade
- Memória contextual entre interações
- Sistema de modos de conversa

Características:
- Contexto salvo após cada interação multimodal
- Estados automáticos baseados em comandos
- Personalidade configurável por usuário
- Integração com sistema de persistência
- Enriquecimento automático de respostas
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from conversation_persistence import ConversationManager, ChatMessage

logger = logging.getLogger('gemini_bot')

class ConversationState(Enum):
    """Estados possíveis de uma conversa"""
    CHAT_GERAL = "chat_geral"
    AGUARDANDO_AUDIO_CLONE = "aguardando_audio_clone"
    AGUARDANDO_IMAGEM_ANALISE = "aguardando_imagem_analise"
    AGUARDANDO_VIDEO_ANALISE = "aguardando_video_analise"
    PESQUISANDO = "pesquisando"
    GERANDO_IMAGEM = "gerando_imagem"
    CONFIGURANDO = "configurando"
    AGUARDANDO_PERSONALIDADE = "aguardando_personalidade"

@dataclass
class MultimodalContext:
    """Contexto multimodal de uma conversa"""
    user_id: str
    conversation_id: int
    last_image_description: Optional[str] = None
    last_audio_transcription: Optional[str] = None
    last_video_analysis: Optional[str] = None
    last_research_topic: Optional[str] = None
    last_generated_image_prompt: Optional[str] = None
    context_timestamp: Optional[str] = None
    context_type: Optional[str] = None  # "image", "audio", "video", "research", "image_generation"

@dataclass
class UserPersonality:
    """Personalidade configurada do usuário"""
    user_id: str
    personality_type: str = "assistente"
    personality_description: str = "Você é um assistente de IA prestativo e útil."
    custom_instructions: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

class MultimodalContextManager:
    """Gerenciador de contexto multimodal"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
        self.context_cache: Dict[str, MultimodalContext] = {}
        self.personality_cache: Dict[str, UserPersonality] = {}
        
        logger.info("Gerenciador de contexto multimodal inicializado")
    
    def save_image_context(self, user_id: str, description: str, conversation_id: int):
        """Salva contexto de análise de imagem"""
        try:
            context = self._get_or_create_context(user_id, conversation_id)
            context.last_image_description = description
            context.context_timestamp = datetime.now().isoformat()
            context.context_type = "image"
            
            self._save_context_to_db(context)
            self.context_cache[user_id] = context
            
            logger.info(f"Contexto de imagem salvo para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar contexto de imagem: {e}")
    
    def save_audio_context(self, user_id: str, transcription: str, conversation_id: int):
        """Salva contexto de transcrição de áudio"""
        try:
            context = self._get_or_create_context(user_id, conversation_id)
            context.last_audio_transcription = transcription
            context.context_timestamp = datetime.now().isoformat()
            context.context_type = "audio"
            
            self._save_context_to_db(context)
            self.context_cache[user_id] = context
            
            logger.info(f"Contexto de áudio salvo para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar contexto de áudio: {e}")
    
    def save_video_context(self, user_id: str, analysis: str, conversation_id: int):
        """Salva contexto de análise de vídeo"""
        try:
            context = self._get_or_create_context(user_id, conversation_id)
            context.last_video_analysis = analysis
            context.context_timestamp = datetime.now().isoformat()
            context.context_type = "video"
            
            self._save_context_to_db(context)
            self.context_cache[user_id] = context
            
            logger.info(f"Contexto de vídeo salvo para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar contexto de vídeo: {e}")
    
    def save_research_context(self, user_id: str, topic: str, conversation_id: int):
        """Salva contexto de pesquisa"""
        try:
            context = self._get_or_create_context(user_id, conversation_id)
            context.last_research_topic = topic
            context.context_timestamp = datetime.now().isoformat()
            context.context_type = "research"
            
            self._save_context_to_db(context)
            self.context_cache[user_id] = context
            
            logger.info(f"Contexto de pesquisa salvo para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar contexto de pesquisa: {e}")
    
    def save_image_generation_context(self, user_id: str, prompt: str, conversation_id: int):
        """Salva contexto de geração de imagem"""
        try:
            context = self._get_or_create_context(user_id, conversation_id)
            context.last_generated_image_prompt = prompt
            context.context_timestamp = datetime.now().isoformat()
            context.context_type = "image_generation"
            
            self._save_context_to_db(context)
            self.context_cache[user_id] = context
            
            logger.info(f"Contexto de geração de imagem salvo para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar contexto de geração de imagem: {e}")
    
    def get_context_for_response(self, user_id: str) -> Optional[str]:
        """Obtém contexto relevante para enriquecer resposta"""
        try:
            context = self.context_cache.get(user_id)
            if not context:
                context = self._load_context_from_db(user_id)
                if context:
                    self.context_cache[user_id] = context
            
            if not context:
                return None
            
            # Verificar se o contexto ainda é relevante (últimas 10 minutos)
            if context.context_timestamp:
                context_time = datetime.fromisoformat(context.context_timestamp)
                if datetime.now() - context_time > timedelta(minutes=10):
                    return None
            
            # Construir contexto baseado no tipo
            context_text = ""
            
            if context.last_image_description:
                context_text += f"Contexto de imagem recente: {context.last_image_description}\n"
            
            if context.last_audio_transcription:
                context_text += f"Transcrição de áudio recente: {context.last_audio_transcription}\n"
            
            if context.last_video_analysis:
                context_text += f"Análise de vídeo recente: {context.last_video_analysis}\n"
            
            if context.last_research_topic:
                context_text += f"Tópico de pesquisa recente: {context.last_research_topic}\n"
            
            if context.last_generated_image_prompt:
                context_text += f"Prompt de imagem recente: {context.last_generated_image_prompt}\n"
            
            return context_text.strip() if context_text else None
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto: {e}")
            return None
    
    def clear_context(self, user_id: str):
        """Limpa contexto do usuário"""
        try:
            if user_id in self.context_cache:
                del self.context_cache[user_id]
            
            # Limpar do banco de dados
            self._clear_context_from_db(user_id)
            
            logger.info(f"Contexto limpo para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao limpar contexto: {e}")
    
    def _get_or_create_context(self, user_id: str, conversation_id: int) -> MultimodalContext:
        """Obtém ou cria contexto para o usuário"""
        if user_id in self.context_cache:
            return self.context_cache[user_id]
        
        return MultimodalContext(
            user_id=user_id,
            conversation_id=conversation_id,
            context_timestamp=datetime.now().isoformat()
        )
    
    def _save_context_to_db(self, context: MultimodalContext):
        """Salva contexto no banco de dados"""
        try:
            # Implementar salvamento no banco de dados
            # Por enquanto, usar o sistema de persistência existente
            context_data = asdict(context)
            context_json = json.dumps(context_data, ensure_ascii=False)
            
            # Salvar como mensagem especial no histórico
            context_message = ChatMessage(
                timestamp=datetime.now().isoformat(),
                role="system",
                content=f"CONTEXT_DATA:{context_json}",
                message_id=f"ctx_{int(datetime.now().timestamp())}"
            )
            
            self.conversation_manager.add_message(context.user_id, context_message)
            
        except Exception as e:
            logger.error(f"Erro ao salvar contexto no DB: {e}")
    
    def _load_context_from_db(self, user_id: str) -> Optional[MultimodalContext]:
        """Carrega contexto do banco de dados"""
        try:
            # Carregar do histórico de mensagens
            history = self.conversation_manager.get_conversation_history(user_id, limit=50)
            
            for message in reversed(history):  # Buscar do mais recente
                if message.role == "system" and message.content.startswith("CONTEXT_DATA:"):
                    context_json = message.content.replace("CONTEXT_DATA:", "")
                    context_data = json.loads(context_json)
                    
                    context = MultimodalContext(**context_data)
                    self.context_cache[user_id] = context
                    return context
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar contexto do DB: {e}")
            return None
    
    def _clear_context_from_db(self, user_id: str):
        """Limpa contexto do banco de dados"""
        try:
            # Implementar limpeza no banco de dados
            # Por enquanto, apenas limpar cache
            pass
            
        except Exception as e:
            logger.error(f"Erro ao limpar contexto do DB: {e}")

class ConversationStateManager:
    """Gerenciador de estados de conversa"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
        self.state_cache: Dict[str, ConversationState] = {}
        
        logger.info("Gerenciador de estados de conversa inicializado")
    
    def set_state(self, user_id: str, state: ConversationState):
        """Define estado da conversa"""
        try:
            self.state_cache[user_id] = state
            
            # Salvar estado no banco de dados
            self._save_state_to_db(user_id, state)
            
            logger.info(f"Estado definido para usuário {user_id}: {state.value}")
            
        except Exception as e:
            logger.error(f"Erro ao definir estado: {e}")
    
    def get_state(self, user_id: str) -> ConversationState:
        """Obtém estado atual da conversa"""
        try:
            if user_id in self.state_cache:
                return self.state_cache[user_id]
            
            # Carregar do banco de dados
            state = self._load_state_from_db(user_id)
            if state:
                self.state_cache[user_id] = state
                return state
            
            # Estado padrão
            default_state = ConversationState.CHAT_GERAL
            self.state_cache[user_id] = default_state
            return default_state
            
        except Exception as e:
            logger.error(f"Erro ao obter estado: {e}")
            return ConversationState.CHAT_GERAL
    
    def reset_state(self, user_id: str):
        """Reseta estado para padrão"""
        try:
            self.set_state(user_id, ConversationState.CHAT_GERAL)
            logger.info(f"Estado resetado para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao resetar estado: {e}")
    
    def is_in_state(self, user_id: str, state: ConversationState) -> bool:
        """Verifica se usuário está em estado específico"""
        return self.get_state(user_id) == state
    
    def _save_state_to_db(self, user_id: str, state: ConversationState):
        """Salva estado no banco de dados"""
        try:
            # Salvar como mensagem especial no histórico
            state_message = ChatMessage(
                timestamp=datetime.now().isoformat(),
                role="system",
                content=f"STATE_DATA:{state.value}",
                message_id=f"state_{int(datetime.now().timestamp())}"
            )
            
            self.conversation_manager.add_message(user_id, state_message)
            
        except Exception as e:
            logger.error(f"Erro ao salvar estado no DB: {e}")
    
    def _load_state_from_db(self, user_id: str) -> Optional[ConversationState]:
        """Carrega estado do banco de dados"""
        try:
            # Carregar do histórico de mensagens
            history = self.conversation_manager.get_conversation_history(user_id, limit=50)
            
            for message in reversed(history):  # Buscar do mais recente
                if message.role == "system" and message.content.startswith("STATE_DATA:"):
                    state_value = message.content.replace("STATE_DATA:", "")
                    return ConversationState(state_value)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar estado do DB: {e}")
            return None

class PersonalityManager:
    """Gerenciador de personalidades"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
        self.personality_cache: Dict[str, UserPersonality] = {}
        
        # Personalidades pré-definidas
        self.predefined_personalities = {
            "assistente": "Você é um assistente de IA prestativo e útil.",
            "cientista": "Você é um cientista cético e analítico, sempre baseando suas respostas em evidências e dados.",
            "pirata": "Você é um pirata aventureiro e carismático, falando com entusiasmo sobre aventuras e tesouros.",
            "professor": "Você é um professor paciente e didático, explicando conceitos de forma clara e educativa.",
            "artista": "Você é um artista criativo e inspirador, sempre buscando beleza e expressão artística.",
            "filósofo": "Você é um filósofo profundo e reflexivo, questionando e explorando ideias complexas.",
            "médico": "Você é um médico cuidadoso e preciso, sempre preocupado com a saúde e bem-estar.",
            "engenheiro": "Você é um engenheiro prático e lógico, sempre buscando soluções eficientes e funcionais.",
            "historiador": "Você é um historiador erudito e detalhista, sempre contextualizando eventos históricos.",
            "escritor": "Você é um escritor criativo e expressivo, sempre buscando a melhor forma de contar uma história."
        }
        
        logger.info("Gerenciador de personalidades inicializado")
    
    def set_personality(self, user_id: str, personality_type: str, custom_description: str = None):
        """Define personalidade do usuário"""
        try:
            if personality_type in self.predefined_personalities:
                description = self.predefined_personalities[personality_type]
            elif custom_description:
                description = custom_description
            else:
                description = self.predefined_personalities["assistente"]
            
            personality = UserPersonality(
                user_id=user_id,
                personality_type=personality_type,
                personality_description=description,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            self.personality_cache[user_id] = personality
            self._save_personality_to_db(personality)
            
            logger.info(f"Personalidade definida para usuário {user_id}: {personality_type}")
            
        except Exception as e:
            logger.error(f"Erro ao definir personalidade: {e}")
    
    def get_personality(self, user_id: str) -> UserPersonality:
        """Obtém personalidade do usuário"""
        try:
            if user_id in self.personality_cache:
                return self.personality_cache[user_id]
            
            # Carregar do banco de dados
            personality = self._load_personality_from_db(user_id)
            if personality:
                self.personality_cache[user_id] = personality
                return personality
            
            # Personalidade padrão
            default_personality = UserPersonality(
                user_id=user_id,
                personality_type="assistente",
                personality_description=self.predefined_personalities["assistente"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            self.personality_cache[user_id] = default_personality
            return default_personality
            
        except Exception as e:
            logger.error(f"Erro ao obter personalidade: {e}")
            return UserPersonality(
                user_id=user_id,
                personality_type="assistente",
                personality_description=self.predefined_personalities["assistente"]
            )
    
    def get_personality_description(self, user_id: str) -> str:
        """Obtém descrição da personalidade para usar no Gemini"""
        personality = self.get_personality(user_id)
        return personality.personality_description
    
    def get_available_personalities(self) -> Dict[str, str]:
        """Obtém personalidades disponíveis"""
        return self.predefined_personalities.copy()
    
    def _save_personality_to_db(self, personality: UserPersonality):
        """Salva personalidade no banco de dados"""
        try:
            # Salvar como mensagem especial no histórico
            personality_data = asdict(personality)
            personality_json = json.dumps(personality_data, ensure_ascii=False)
            
            personality_message = ChatMessage(
                timestamp=datetime.now().isoformat(),
                role="system",
                content=f"PERSONALITY_DATA:{personality_json}",
                message_id=f"personality_{int(datetime.now().timestamp())}"
            )
            
            self.conversation_manager.add_message(personality.user_id, personality_message)
            
        except Exception as e:
            logger.error(f"Erro ao salvar personalidade no DB: {e}")
    
    def _load_personality_from_db(self, user_id: str) -> Optional[UserPersonality]:
        """Carrega personalidade do banco de dados"""
        try:
            # Carregar do histórico de mensagens
            history = self.conversation_manager.get_conversation_history(user_id, limit=100)
            
            for message in reversed(history):  # Buscar do mais recente
                if message.role == "system" and message.content.startswith("PERSONALITY_DATA:"):
                    personality_json = message.content.replace("PERSONALITY_DATA:", "")
                    personality_data = json.loads(personality_json)
                    
                    personality = UserPersonality(**personality_data)
                    self.personality_cache[user_id] = personality
                    return personality
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar personalidade do DB: {e}")
            return None

class AdvancedContextSystem:
    """Sistema avançado de contexto integrado"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
        self.context_manager = MultimodalContextManager(conversation_manager)
        self.state_manager = ConversationStateManager(conversation_manager)
        self.personality_manager = PersonalityManager(conversation_manager)
        
        logger.info("Sistema avançado de contexto inicializado")
    
    def enrich_message_with_context(self, user_id: str, message: str) -> str:
        """Enriquece mensagem com contexto multimodal"""
        try:
            # Obter contexto multimodal
            multimodal_context = self.context_manager.get_context_for_response(user_id)
            
            # Obter personalidade
            personality = self.personality_manager.get_personality_description(user_id)
            
            # Obter estado atual
            current_state = self.state_manager.get_state(user_id)
            
            # Construir mensagem enriquecida
            enriched_message = message
            
            if multimodal_context:
                enriched_message = f"Contexto recente: {multimodal_context}\n\nMensagem do usuário: {message}"
            
            if current_state != ConversationState.CHAT_GERAL:
                enriched_message = f"Estado atual: {current_state.value}\n\n{enriched_message}"
            
            return enriched_message
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer mensagem: {e}")
            return message
    
    def get_system_instruction(self, user_id: str) -> str:
        """Obtém instrução do sistema baseada na personalidade"""
        return self.personality_manager.get_personality_description(user_id)
    
    def handle_multimodal_interaction(self, user_id: str, interaction_type: str, content: str, conversation_id: int):
        """Processa interação multimodal e salva contexto"""
        try:
            if interaction_type == "image":
                self.context_manager.save_image_context(user_id, content, conversation_id)
            elif interaction_type == "audio":
                self.context_manager.save_audio_context(user_id, content, conversation_id)
            elif interaction_type == "video":
                self.context_manager.save_video_context(user_id, content, conversation_id)
            elif interaction_type == "research":
                self.context_manager.save_research_context(user_id, content, conversation_id)
            elif interaction_type == "image_generation":
                self.context_manager.save_image_generation_context(user_id, content, conversation_id)
            
            logger.info(f"Interação multimodal processada: {interaction_type} para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar interação multimodal: {e}")
    
    def set_conversation_state(self, user_id: str, state: ConversationState):
        """Define estado da conversa"""
        self.state_manager.set_state(user_id, state)
    
    def get_conversation_state(self, user_id: str) -> ConversationState:
        """Obtém estado atual da conversa"""
        return self.state_manager.get_state(user_id)
    
    def set_user_personality(self, user_id: str, personality_type: str, custom_description: str = None):
        """Define personalidade do usuário"""
        self.personality_manager.set_personality(user_id, personality_type, custom_description)
    
    def get_user_personality(self, user_id: str) -> UserPersonality:
        """Obtém personalidade do usuário"""
        return self.personality_manager.get_personality(user_id)
    
    def get_available_personalities(self) -> Dict[str, str]:
        """Obtém personalidades disponíveis"""
        return self.personality_manager.get_available_personalities()
    
    def clear_user_context(self, user_id: str):
        """Limpa todo o contexto do usuário"""
        self.context_manager.clear_context(user_id)
        self.state_manager.reset_state(user_id)

# Instância global do sistema
advanced_context_system = None

def get_advanced_context_system(conversation_manager: ConversationManager = None) -> AdvancedContextSystem:
    """Obtém instância global do sistema de contexto avançado"""
    global advanced_context_system
    
    if advanced_context_system is None and conversation_manager:
        advanced_context_system = AdvancedContextSystem(conversation_manager)
    
    return advanced_context_system
