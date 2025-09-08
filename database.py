import sqlite3
import logging
import json
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Any

DB_FILE = "bot_data.db"
logger = logging.getLogger(__name__)

def initialize_db():
    """Cria as tabelas do banco de dados se elas não existirem."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Tabela para armazenar o histórico de conversas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para contexto multimodal
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS multimodal_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    conversation_id INTEGER NOT NULL,
                    last_image_description TEXT,
                    last_audio_transcription TEXT,
                    last_video_analysis TEXT,
                    last_research_topic TEXT,
                    last_generated_image_prompt TEXT,
                    context_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para estados de conversa
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    conversation_id INTEGER NOT NULL,
                    current_state TEXT NOT NULL DEFAULT 'chat_geral',
                    state_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, conversation_id)
                )
            """)
            
            # Tabela para personalidades de usuário
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_personalities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    personality_type TEXT NOT NULL DEFAULT 'assistente',
                    personality_description TEXT NOT NULL,
                    custom_instructions TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para configurações de usuário
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    language TEXT DEFAULT 'pt',
                    voice_type TEXT DEFAULT 'feminina',
                    theme TEXT DEFAULT 'escuro',
                    notifications_enabled BOOLEAN DEFAULT 1,
                    privacy_level TEXT DEFAULT 'normal',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_chat_id ON chat_history(chat_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_multimodal_context_user_id ON multimodal_context(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_multimodal_context_timestamp ON multimodal_context(context_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_states_user_id ON conversation_states(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_personalities_user_id ON user_personalities(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)")
            
            conn.commit()
            logger.info("Banco de dados avançado inicializado com sucesso.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise

def add_message_to_history(chat_id: int, role: str, content: str):
    """Adiciona uma nova mensagem ao histórico de um chat."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content)
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Erro ao adicionar mensagem ao histórico: {e}")

def get_chat_history(chat_id: int) -> List[Tuple[str, str]]:
    """Recupera o histórico de um chat, formatado para o Gemini."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE chat_id = ? ORDER BY timestamp ASC",
                (chat_id,)
            )
            # Formata como uma lista de dicionários para o Gemini
            history = [{"role": row[0], "parts": [row[1]]} for row in cursor.fetchall()]
            return history
    except sqlite3.Error as e:
        logger.error(f"Erro ao recuperar histórico: {e}")
        return []

def reset_chat_history(chat_id: int):
    """Apaga o histórico de um chat específico."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
            conn.commit()
            logger.info(f"Histórico do chat {chat_id} resetado no banco de dados.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao resetar histórico: {e}")

# Funções para contexto multimodal
def save_multimodal_context(user_id: str, conversation_id: int, context_data: Dict[str, Any]):
    """Salva contexto multimodal no banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Verificar se já existe contexto para este usuário
            cursor.execute("""
                SELECT id FROM multimodal_context 
                WHERE user_id = ? AND conversation_id = ?
            """, (user_id, conversation_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualizar contexto existente
                cursor.execute("""
                    UPDATE multimodal_context SET
                        last_image_description = ?,
                        last_audio_transcription = ?,
                        last_video_analysis = ?,
                        last_research_topic = ?,
                        last_generated_image_prompt = ?,
                        context_timestamp = ?,
                        context_type = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND conversation_id = ?
                """, (
                    context_data.get('last_image_description'),
                    context_data.get('last_audio_transcription'),
                    context_data.get('last_video_analysis'),
                    context_data.get('last_research_topic'),
                    context_data.get('last_generated_image_prompt'),
                    context_data.get('context_timestamp'),
                    context_data.get('context_type'),
                    user_id,
                    conversation_id
                ))
            else:
                # Criar novo contexto
                cursor.execute("""
                    INSERT INTO multimodal_context (
                        user_id, conversation_id, last_image_description,
                        last_audio_transcription, last_video_analysis,
                        last_research_topic, last_generated_image_prompt,
                        context_timestamp, context_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, conversation_id,
                    context_data.get('last_image_description'),
                    context_data.get('last_audio_transcription'),
                    context_data.get('last_video_analysis'),
                    context_data.get('last_research_topic'),
                    context_data.get('last_generated_image_prompt'),
                    context_data.get('context_timestamp'),
                    context_data.get('context_type')
                ))
            
            conn.commit()
            logger.info(f"Contexto multimodal salvo para usuário {user_id}")
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar contexto multimodal: {e}")

def get_multimodal_context(user_id: str, conversation_id: int) -> Optional[Dict[str, Any]]:
    """Obtém contexto multimodal do banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT last_image_description, last_audio_transcription,
                       last_video_analysis, last_research_topic,
                       last_generated_image_prompt, context_timestamp, context_type
                FROM multimodal_context
                WHERE user_id = ? AND conversation_id = ?
                ORDER BY context_timestamp DESC LIMIT 1
            """, (user_id, conversation_id))
            
            result = cursor.fetchone()
            if result:
                return {
                    'last_image_description': result[0],
                    'last_audio_transcription': result[1],
                    'last_video_analysis': result[2],
                    'last_research_topic': result[3],
                    'last_generated_image_prompt': result[4],
                    'context_timestamp': result[5],
                    'context_type': result[6]
                }
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao obter contexto multimodal: {e}")
        return None

def clear_multimodal_context(user_id: str, conversation_id: int = None):
    """Limpa contexto multimodal do banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            if conversation_id:
                cursor.execute("""
                    DELETE FROM multimodal_context 
                    WHERE user_id = ? AND conversation_id = ?
                """, (user_id, conversation_id))
            else:
                cursor.execute("""
                    DELETE FROM multimodal_context WHERE user_id = ?
                """, (user_id,))
            
            conn.commit()
            logger.info(f"Contexto multimodal limpo para usuário {user_id}")
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao limpar contexto multimodal: {e}")

# Funções para estados de conversa
def save_conversation_state(user_id: str, conversation_id: int, state: str, state_data: str = None):
    """Salva estado da conversa no banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Verificar se já existe estado para este usuário
            cursor.execute("""
                SELECT id FROM conversation_states 
                WHERE user_id = ? AND conversation_id = ?
            """, (user_id, conversation_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualizar estado existente
                cursor.execute("""
                    UPDATE conversation_states SET
                        current_state = ?,
                        state_data = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND conversation_id = ?
                """, (state, state_data, user_id, conversation_id))
            else:
                # Criar novo estado
                cursor.execute("""
                    INSERT INTO conversation_states (
                        user_id, conversation_id, current_state, state_data
                    ) VALUES (?, ?, ?, ?)
                """, (user_id, conversation_id, state, state_data))
            
            conn.commit()
            logger.info(f"Estado da conversa salvo para usuário {user_id}: {state}")
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar estado da conversa: {e}")

def get_conversation_state(user_id: str, conversation_id: int) -> Optional[str]:
    """Obtém estado da conversa do banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT current_state FROM conversation_states
                WHERE user_id = ? AND conversation_id = ?
                ORDER BY updated_at DESC LIMIT 1
            """, (user_id, conversation_id))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao obter estado da conversa: {e}")
        return None

def reset_conversation_state(user_id: str, conversation_id: int):
    """Reseta estado da conversa para padrão."""
    save_conversation_state(user_id, conversation_id, "chat_geral")

# Funções para personalidades
def save_user_personality(user_id: str, personality_type: str, personality_description: str, custom_instructions: str = None):
    """Salva personalidade do usuário no banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Verificar se já existe personalidade para este usuário
            cursor.execute("""
                SELECT id FROM user_personalities WHERE user_id = ?
            """, (user_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualizar personalidade existente
                cursor.execute("""
                    UPDATE user_personalities SET
                        personality_type = ?,
                        personality_description = ?,
                        custom_instructions = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (personality_type, personality_description, custom_instructions, user_id))
            else:
                # Criar nova personalidade
                cursor.execute("""
                    INSERT INTO user_personalities (
                        user_id, personality_type, personality_description, custom_instructions
                    ) VALUES (?, ?, ?, ?)
                """, (user_id, personality_type, personality_description, custom_instructions))
            
            conn.commit()
            logger.info(f"Personalidade salva para usuário {user_id}: {personality_type}")
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar personalidade: {e}")

def get_user_personality(user_id: str) -> Optional[Dict[str, Any]]:
    """Obtém personalidade do usuário do banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT personality_type, personality_description, custom_instructions
                FROM user_personalities WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'personality_type': result[0],
                    'personality_description': result[1],
                    'custom_instructions': result[2]
                }
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao obter personalidade: {e}")
        return None

# Funções para configurações de usuário
def save_user_settings(user_id: str, settings: Dict[str, Any]):
    """Salva configurações do usuário no banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Verificar se já existem configurações para este usuário
            cursor.execute("""
                SELECT id FROM user_settings WHERE user_id = ?
            """, (user_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualizar configurações existentes
                cursor.execute("""
                    UPDATE user_settings SET
                        language = ?,
                        voice_type = ?,
                        theme = ?,
                        notifications_enabled = ?,
                        privacy_level = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (
                    settings.get('language', 'pt'),
                    settings.get('voice_type', 'feminina'),
                    settings.get('theme', 'escuro'),
                    settings.get('notifications_enabled', 1),
                    settings.get('privacy_level', 'normal'),
                    user_id
                ))
            else:
                # Criar novas configurações
                cursor.execute("""
                    INSERT INTO user_settings (
                        user_id, language, voice_type, theme,
                        notifications_enabled, privacy_level
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    settings.get('language', 'pt'),
                    settings.get('voice_type', 'feminina'),
                    settings.get('theme', 'escuro'),
                    settings.get('notifications_enabled', 1),
                    settings.get('privacy_level', 'normal')
                ))
            
            conn.commit()
            logger.info(f"Configurações salvas para usuário {user_id}")
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar configurações: {e}")

def get_user_settings(user_id: str) -> Optional[Dict[str, Any]]:
    """Obtém configurações do usuário do banco de dados."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT language, voice_type, theme, notifications_enabled, privacy_level
                FROM user_settings WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'language': result[0],
                    'voice_type': result[1],
                    'theme': result[2],
                    'notifications_enabled': bool(result[3]),
                    'privacy_level': result[4]
                }
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao obter configurações: {e}")
        return None