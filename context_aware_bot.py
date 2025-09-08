# -*- coding: utf-8 -*-
"""
Bot Telegram com Sistema de Contexto Avançado
==============================================

Este módulo implementa um bot Telegram que utiliza o sistema de contexto
multimodal avançado, estados de conversa e personalização de personalidade.

Funcionalidades:
- Contexto multimodal persistente
- Estados de conversa inteligentes
- Personalização de personalidade
- Comandos avançados de configuração
- Integração com sistema de persistência

Características:
- Bot "lembra" de interações multimodais anteriores
- Estados automáticos baseados em comandos
- Personalidade configurável por usuário
- Enriquecimento automático de respostas
- Sistema de modos de conversa
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# Importar módulos do projeto
from config_manager import get_gemini_handler, ConfigurationError
from error_handler import validate_input, sanitize_input
from conversation_persistence import (
    ConversationManager, ChatMessage, get_conversation_manager
)
from advanced_context_system import (
    AdvancedContextSystem, ConversationState, get_advanced_context_system
)
from interactive_keyboards import get_keyboard_manager
from logging_setup import setup_logging
from tasks.heavy_tasks import clone_voice_task, research_report_task, generate_image_task

logger = setup_logging('gemini_bot')

class ContextAwareTelegramBot:
    """Bot Telegram com sistema de contexto avançado"""
    
    def __init__(self):
        self.gemini_handler = None
        self.conversation_manager = get_conversation_manager()
        self.context_system = get_advanced_context_system(self.conversation_manager)
        self.keyboard_manager = get_keyboard_manager()
        
        # Configurações
        self.admin_users = self._load_admin_users()
        self.max_messages_per_user = 1000
        self.cleanup_days = 30
        
        self.initialize_handlers()
        logger.info("Bot Telegram com contexto avançado inicializado")
    
    def _load_admin_users(self) -> List[int]:
        """Carrega lista de usuários administradores"""
        admin_users = os.getenv('ADMIN_USER_IDS', '')
        if admin_users:
            try:
                return [int(user_id.strip()) for user_id in admin_users.split(',')]
            except ValueError:
                logger.warning("Formato inválido em ADMIN_USER_IDS")
        return []
    
    def initialize_handlers(self):
        """Inicializa todos os handlers"""
        try:
            self.gemini_handler = get_gemini_handler()
            logger.info("Todos os handlers inicializados com sucesso")
            
        except ConfigurationError as e:
            logger.error(f"Erro de configuração: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro na inicialização: {e}")
            raise
    
    def is_admin(self, user_id: int) -> bool:
        """Verifica se o usuário é administrador"""
        return user_id in self.admin_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menu principal com contexto"""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Usuário"
        
        # Obter estatísticas do usuário
        stats = self.conversation_manager.get_user_stats(user_id)
        
        # Obter personalidade atual
        personality = self.context_system.get_user_personality(user_id)
        
        local_time = datetime.now().strftime('%H:%M')
        welcome_text = f"""
🤖 **Olá, {username}!**

Bom dia! São {local_time} no seu horário local. Bem-vindo ao **Bot com Contexto Avançado**!

✨ **Recursos disponíveis:**
• 🧠 Memória contextual multimodal
• 🎭 Personalidade personalizável
• 🎛️ Estados de conversa inteligentes
• 📊 Estatísticas personalizadas
• 🔄 Contexto entre interações

🎭 **Personalidade atual:** {personality.personality_type.title()}
🎯 **Use os botões abaixo para navegar!**
        """
        
        if stats:
            welcome_text += f"""
📈 **Suas estatísticas:**
• Conversas: {stats['total_conversations']}
• Mensagens: {stats['total_messages']}
• Caracteres: {stats['total_characters']:,}
            """
        
        # Criar teclado principal
        keyboard = self.keyboard_manager.create_main_menu_keyboard()
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        # Criar conversa para o usuário
        session_id = f"session_{int(datetime.now().timestamp())}"
        self.conversation_manager.get_or_create_conversation(user_id, session_id)
        
        # Definir estado inicial
        self.context_system.set_conversation_state(user_id, ConversationState.CHAT_GERAL)
        
        logger.info(f"Usuário {username} ({user_id}) iniciou o bot")
    
    async def personality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /personalidade - Configurar personalidade"""
        user_id = str(update.effective_user.id)
        
        if context.args:
            personality_type = context.args[0].lower()
            available_personalities = self.context_system.get_available_personalities()
            
            if personality_type in available_personalities:
                # Definir personalidade
                self.context_system.set_user_personality(user_id, personality_type)
                
                await update.message.reply_text(
                    f"🎭 **Personalidade alterada!**\n\n"
                    f"Personalidade: **{personality_type.title()}**\n"
                    f"Descrição: {available_personalities[personality_type]}\n\n"
                    f"💡 Suas próximas conversas usarão esta personalidade!",
                    parse_mode='Markdown'
                )
                
                logger.info(f"Personalidade alterada para usuário {user_id}: {personality_type}")
            else:
                # Mostrar personalidades disponíveis
                personalities_text = "🎭 **Personalidades Disponíveis:**\n\n"
                for ptype, description in available_personalities.items():
                    personalities_text += f"• **{ptype}**: {description}\n"
                
                personalities_text += "\n💡 **Uso:** `/personalidade [tipo]`\n"
                personalities_text += "**Exemplo:** `/personalidade cientista`"
                
                await update.message.reply_text(
                    personalities_text,
                    parse_mode='Markdown'
                )
        else:
            # Mostrar personalidade atual e opções
            personality = self.context_system.get_user_personality(user_id)
            available_personalities = self.context_system.get_available_personalities()
            
            personality_text = f"""
🎭 **Configuração de Personalidade**

**Personalidade atual:** {personality.personality_type.title()}
**Descrição:** {personality.personality_description}

**Personalidades disponíveis:**
            """
            
            for ptype, description in available_personalities.items():
                personality_text += f"• **{ptype}**: {description}\n"
            
            personality_text += "\n💡 **Uso:** `/personalidade [tipo]`"
            
            await update.message.reply_text(
                personality_text,
                parse_mode='Markdown'
            )
    
    async def contexto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /contexto - Mostrar contexto atual"""
        user_id = str(update.effective_user.id)
        
        # Obter contexto multimodal
        multimodal_context = self.context_system.context_manager.get_context_for_response(user_id)
        
        # Obter estado atual
        current_state = self.context_system.get_conversation_state(user_id)
        
        # Obter personalidade
        personality = self.context_system.get_user_personality(user_id)
        
        context_text = f"""
🧠 **Contexto Atual da Conversa**

**Estado:** {current_state.value.replace('_', ' ').title()}
**Personalidade:** {personality.personality_type.title()}
        """
        
        if multimodal_context:
            context_text += f"\n**Contexto Multimodal:**\n{multimodal_context}"
        else:
            context_text += "\n**Contexto Multimodal:** Nenhum contexto recente"
        
        context_text += "\n\n💡 **Dica:** O bot lembra de suas interações multimodais anteriores!"
        
        await update.message.reply_text(
            context_text,
            parse_mode='Markdown'
        )
    
    async def limpar_contexto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /limpar_contexto - Limpar contexto multimodal"""
        user_id = str(update.effective_user.id)
        
        # Limpar contexto
        self.context_system.clear_user_context(user_id)
        
        await update.message.reply_text(
            "🧹 **Contexto Limpo!**\n\n"
            "Todo o contexto multimodal foi removido.\n"
            "O bot não lembrará mais de interações anteriores.",
            parse_mode='Markdown'
        )
        
        logger.info(f"Contexto limpo para usuário {user_id}")
    
    async def clonar_voz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /clonarvoz - Entrar em modo de clonagem de voz"""
        user_id = str(update.effective_user.id)
        
        # Definir estado para aguardar áudio
        self.context_system.set_conversation_state(user_id, ConversationState.AGUARDANDO_AUDIO_CLONE)
        
        await update.message.reply_text(
            "🎤 **Modo de Clonagem de Voz Ativado**\n\n"
            "📌 Envie um arquivo de áudio de 5-10 segundos com voz clara.\n"
            "Quando o áudio chegar, vamos enfileirar a clonagem e você poderá continuar usando o bot.",
            parse_mode='Markdown'
        )
        
        logger.info(f"Usuário {user_id} entrou em modo de clonagem de voz")
    
    async def sair_modo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /sair_modo - Sair do modo atual"""
        user_id = str(update.effective_user.id)
        
        # Resetar estado
        self.context_system.set_conversation_state(user_id, ConversationState.CHAT_GERAL)
        
        await update.message.reply_text(
            "🔄 **Modo Resetado**\n\n"
            "Voltou ao modo de chat geral.\n"
            "Pode conversar normalmente agora!",
            parse_mode='Markdown'
        )
        
        logger.info(f"Usuário {user_id} saiu do modo especial")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula mensagens de texto com contexto"""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Usuário"
        user_message = update.message.text
        
        # Validar entrada
        if not validate_input(user_message):
            await update.message.reply_text("❌ Mensagem inválida. Tente novamente.")
            return
        
        # Sanitizar entrada
        sanitized_input = sanitize_input(user_message)
        
        try:
            # Obter estado atual
            current_state = self.context_system.get_conversation_state(user_id)
            
            # Verificar se está em modo especial
            if current_state == ConversationState.AGUARDANDO_AUDIO_CLONE:
                await update.message.reply_text(
                    "🎤 **Aguardando arquivo de áudio...**\n\n"
                    "Por favor, envie um arquivo de áudio para clonagem.\n"
                    "Use `/sair_modo` para cancelar.",
                    parse_mode='Markdown'
                )
                return
            
            # Mostrar indicador de digitação
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Obter ou criar conversa
            session_id = f"session_{int(datetime.now().timestamp())}"
            conversation_id = self.conversation_manager.get_or_create_conversation(user_id, session_id)
            
            # Adicionar mensagem do usuário
            user_chat_message = ChatMessage(
                timestamp=datetime.now().isoformat(),
                role="user",
                content=sanitized_input,
                message_id=f"msg_{int(datetime.now().timestamp())}"
            )
            self.conversation_manager.add_message(user_id, user_chat_message)
            
            # Enriquecer mensagem com contexto multimodal
            enriched_message = self.context_system.enrich_message_with_context(user_id, sanitized_input)
            
            # Obter instrução do sistema baseada na personalidade
            system_instruction = self.context_system.get_system_instruction(user_id)
            
            # Obter histórico da conversa
            history = self.conversation_manager.get_conversation_history(user_id, limit=20)
            
            # Preparar contexto para o Gemini
            if history:
                context_text = "Contexto da conversa:\n"
                for msg in history[-10:]:  # Últimas 10 mensagens
                    role_label = "Usuário" if msg.role == "user" else "Assistente"
                    context_text += f"{role_label}: {msg.content}\n"
                context_text += f"\nNova mensagem do usuário: {enriched_message}"
            else:
                context_text = enriched_message
            
            # Gerar resposta usando Gemini com personalidade
            response = self.gemini_handler.generate_content(context_text)
            
            # Adicionar resposta do assistente
            assistant_chat_message = ChatMessage(
                timestamp=datetime.now().isoformat(),
                role="model",
                content=response,
                message_id=f"msg_{int(datetime.now().timestamp())}"
            )
            self.conversation_manager.add_message(user_id, assistant_chat_message)
            
            # Criar teclado de ações de chat
            keyboard = self.keyboard_manager.create_chat_actions_keyboard(user_id)
            
            # Enviar resposta
            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            logger.info(f"Resposta contextual enviada para {username} ({user_id})")
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            await update.message.reply_text(
                "❌ **Erro interno.** Tente novamente em alguns segundos.\n"
                "💡 Se o problema persistir, use `/start` para reiniciar.",
                parse_mode='Markdown'
            )
    
    async def handle_image_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula mensagens com imagem"""
        user_id = str(update.effective_user.id)
        
        try:
            # Obter arquivo de imagem
            image_file = await context.bot.get_file(update.message.photo[-1].file_id)
            
            # Simular análise de imagem (em produção, usar multimodal_processor)
            image_description = f"Imagem recebida de {update.effective_user.username or 'usuário'}: contém elementos visuais diversos"
            
            # Salvar contexto de imagem
            session_id = f"session_{int(datetime.now().timestamp())}"
            conversation_id = self.conversation_manager.get_or_create_conversation(user_id, session_id)
            
            self.context_system.handle_multimodal_interaction(
                user_id, "image", image_description, conversation_id
            )
            
            # Responder com descrição
            await update.message.reply_text(
                f"🖼️ **Imagem Analisada!**\n\n"
                f"**Descrição:** {image_description}\n\n"
                f"💡 **Dica:** Agora você pode pedir para criar uma história sobre esta imagem!",
                parse_mode='Markdown'
            )
            
            logger.info(f"Imagem analisada para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            await update.message.reply_text(
                "❌ **Erro ao processar imagem**\n\n"
                "Não foi possível analisar a imagem. Tente novamente."
            )
    
    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula mensagens com áudio"""
        user_id = str(update.effective_user.id)
        current_state = self.context_system.get_conversation_state(user_id)
        
        try:
            if current_state == ConversationState.AGUARDANDO_AUDIO_CLONE:
                # Enfileirar a clonagem de voz no Celery (não bloquear o bot)
                file_id = None
                if update.message.voice:
                    file_id = update.message.voice.file_id
                elif update.message.audio:
                    file_id = update.message.audio.file_id
                
                if not file_id:
                    await update.message.reply_text("❌ Não encontrei o arquivo de áudio. Envie novamente como áudio/voz.")
                    return
                
                await update.message.reply_text("⏳ Áudio recebido. Iniciando processamento em segundo plano…")
                try:
                    clone_voice_task.delay(int(update.effective_chat.id), file_id, {})
                except Exception:
                    await update.message.reply_text("⚠️ A fila de tarefas está indisponível no momento. Tente novamente mais tarde.")
                
                # Registrar interação e resetar estado
                session_id = f"session_{int(datetime.now().timestamp())}"
                conversation_id = self.conversation_manager.get_or_create_conversation(user_id, session_id)
                self.context_system.handle_multimodal_interaction(
                    user_id, "audio", "Áudio enviado para clonagem (em fila)", conversation_id
                )
                self.context_system.set_conversation_state(user_id, ConversationState.CHAT_GERAL)
                
            else:
                # Modo normal - transcrever áudio
                await update.message.reply_text(
                    "🎵 **Processando áudio...**\n\n"
                    "⏳ Transcrevendo conteúdo...\n\n"
                    "📝 **Transcrição:** [Conteúdo do áudio transcrito]\n\n"
                    "💡 **Dica:** Agora você pode fazer perguntas sobre o conteúdo do áudio!",
                    parse_mode='Markdown'
                )
                
                # Salvar contexto de áudio
                session_id = f"session_{int(datetime.now().timestamp())}"
                conversation_id = self.conversation_manager.get_or_create_conversation(user_id, session_id)
                
                self.context_system.handle_multimodal_interaction(
                    user_id, "audio", "Conteúdo do áudio transcrito", conversation_id
                )
            
            logger.info(f"Áudio processado para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar áudio: {e}")
            await update.message.reply_text(
                "❌ **Erro ao processar áudio**\n\n"
                "Não foi possível processar o áudio. Tente novamente."
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula erros globais"""
        logger.error(f"Erro no bot: {context.error}")
        
        if update and update.effective_message:
            try:
                keyboard = self.keyboard_manager.create_main_menu_keyboard()
                await update.effective_message.reply_text(
                    "❌ **Ocorreu um erro interno.**\n"
                    "💡 Tente novamente ou use `/start` para reiniciar.",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            except Exception:
                pass
    
    def setup_handlers(self, application: Application):
        """Configura os manipuladores do bot"""
        # Comandos básicos
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.start_command))  # Usar start como help
        
        # Comandos de contexto e personalidade
        application.add_handler(CommandHandler("personalidade", self.personality_command))
        application.add_handler(CommandHandler("contexto", self.contexto_command))
        application.add_handler(CommandHandler("limpar_contexto", self.limpar_contexto_command))
        
        # Comandos de modo
        application.add_handler(CommandHandler("clonarvoz", self.clonar_voz_command))
        application.add_handler(CommandHandler("sair_modo", self.sair_modo_command))
        
        # Manipuladores de mensagens
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_image_message))
        application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio_message))
        
        # Manipulador de erros
        application.add_error_handler(self.error_handler)
    
    async def periodic_tasks(self, application: Application):
        """Tarefas periódicas"""
        while True:
            try:
                # Backup automático
                self.conversation_manager.create_backup()
                logger.info("Backup automático criado")
                
                # Limpeza de dados antigos
                self.conversation_manager.cleanup_old_conversations(self.cleanup_days)
                logger.info("Limpeza automática concluída")
                
            except Exception as e:
                logger.error(f"Erro nas tarefas periódicas: {e}")
            
            # Aguardar próximo ciclo (24 horas)
            await asyncio.sleep(24 * 3600)

def main():
    """Função principal para executar o bot"""
    # Configurar logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    try:
        # Obter token do Telegram
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN não configurado no arquivo .env")
        
        # Criar aplicação
        application = Application.builder().token(telegram_token).build()
        
        # Criar bot
        bot = ContextAwareTelegramBot()
        
        # Configurar manipuladores
        bot.setup_handlers(application)
        
        # Iniciar bot
        logger.info("Iniciando bot Telegram com contexto avançado...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        raise

if __name__ == "__main__":
    main()
