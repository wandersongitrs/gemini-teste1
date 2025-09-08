# -*- coding: utf-8 -*-
"""
Sistema de Interface de Usuário Avançado
Menus dinâmicos, comandos de voz e shortcuts personalizáveis
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

logger = logging.getLogger(__name__)

class DynamicMenuSystem:
    """Sistema de menus dinâmicos baseados no contexto do usuário"""
    
    def __init__(self):
        self.menu_templates = self._load_menu_templates()
        self.user_contexts = {}  # Cache de contextos por usuário
        self.menu_history = {}   # Histórico de menus por usuário
        
    def _load_menu_templates(self) -> Dict[str, Dict]:
        """Carrega templates de menu predefinidos"""
        return {
            "main_menu": {
                "title": "🎭 **Bot de Voz e IA - Menu Principal**",
                "description": "Escolha uma funcionalidade:",
                "buttons": [
                    ["🎭 Clonagem de Voz", "voice_clone"],
                    ["🤖 IA e Chat", "ai_chat"],
                    ["🖼️ Geração de Imagens", "image_gen"],
                    ["🔍 Verificação de Vazamentos", "breach_check"],
                    ["⚙️ Configurações", "settings"],
                    ["📚 Ajuda", "help"]
                ]
            },
            "voice_clone": {
                "title": "🎭 **Sistema de Clonagem de Voz**",
                "description": "Funcionalidades de voz disponíveis:",
                "buttons": [
                    ["🎤 Gravar Áudio de Referência", "record_reference"],
                    ["📝 Clonar Voz", "clone_voice"],
                    ["🎵 Análise de Voz", "voice_analysis"],
                    ["⚙️ Configurações de Voz", "voice_settings"],
                    ["📊 Histórico de Clonagens", "voice_history"],
                    ["🔙 Voltar ao Menu Principal", "main_menu"]
                ]
            },
            "ai_chat": {
                "title": "🤖 **Chat Inteligente com IA**",
                "description": "Interaja com diferentes modelos de IA:",
                "buttons": [
                    ["💬 Chat com Gemini", "gemini_chat"],
                    ["🧠 Análise de Código", "code_analysis"],
                    ["📊 Análise de Dados", "data_analysis"],
                    ["🔍 Pesquisa Web", "web_search"],
                    ["🌐 Tradução", "translation"],
                    ["🔙 Voltar ao Menu Principal", "main_menu"]
                ]
            },
            "image_gen": {
                "title": "🖼️ **Geração de Imagens com IA**",
                "description": "Crie imagens incríveis:",
                "buttons": [
                    ["🎨 Gerar Imagem", "generate_image"],
                    ["🖼️ Editar Imagem", "edit_image"],
                    ["📸 Análise de Imagem", "analyze_image"],
                    ["🎭 Estilos Artísticos", "art_styles"],
                    ["🔙 Voltar ao Menu Principal", "main_menu"]
                ]
            },
            "breach_check": {
                "title": "🔍 **Verificação de Vazamentos**",
                "description": "Verifique a segurança dos seus dados:",
                "buttons": [
                    ["📧 Verificar Email", "check_email"],
                    ["🔑 Verificar Senha", "check_password"],
                    ["📱 Verificar Telefone", "check_phone"],
                    ["🏢 Verificar Empresa", "check_company"],
                    ["📊 Relatório de Segurança", "security_report"],
                    ["🔙 Voltar ao Menu Principal", "main_menu"]
                ]
            },
            "settings": {
                "title": "⚙️ **Configurações do Bot**",
                "description": "Personalize sua experiência:",
                "buttons": [
                    ["🎵 Configurações de Voz", "voice_settings"],
                    ["🤖 Configurações de IA", "ai_settings"],
                    ["🔔 Notificações", "notifications"],
                    ["🎨 Tema da Interface", "theme_settings"],
                    ["📱 Shortcuts Personalizados", "custom_shortcuts"],
                    ["🔙 Voltar ao Menu Principal", "main_menu"]
                ]
            },
            "help": {
                "title": "📚 **Central de Ajuda**",
                "description": "Recursos de suporte disponíveis:",
                "buttons": [
                    ["📖 Tutorial Interativo", "interactive_tutorial"],
                    ["❓ FAQ", "faq"],
                    ["🎯 Exemplos Práticos", "examples"],
                    ["🔧 Solução de Problemas", "troubleshooting"],
                    ["📞 Suporte Técnico", "support"],
                    ["🔙 Voltar ao Menu Principal", "main_menu"]
                ]
            }
        }
    
    def get_dynamic_menu(self, user_id: int, context_name: str, user_data: Dict = None) -> Dict[str, Any]:
        """Gera menu dinâmico baseado no contexto do usuário"""
        try:
            # Obter template base
            template = self.menu_templates.get(context_name, self.menu_templates["main_menu"])
            
            # Personalizar baseado no contexto do usuário
            personalized_menu = self._personalize_menu(template, user_id, user_data)
            
            # Atualizar histórico
            self._update_menu_history(user_id, context_name)
            
            return personalized_menu
            
        except Exception as e:
            logger.error(f"Erro ao gerar menu dinâmico: {e}")
            return self.menu_templates["main_menu"]
    
    def _personalize_menu(self, template: Dict, user_id: int, user_data: Dict = None) -> Dict:
        """Personaliza menu baseado nos dados do usuário"""
        try:
            personalized = template.copy()
            
            # Adicionar informações personalizadas
            if user_data:
                # Mostrar estatísticas do usuário
                if 'voice_clones_count' in user_data:
                    personalized["description"] += f"\n\n📊 **Suas Estatísticas:**\n• Clonagens realizadas: {user_data['voice_clones_count']}"
                
                if 'preferred_voice_gender' in user_data:
                    personalized["description"] += f"\n• Voz preferida: {user_data['preferred_voice_gender']}"
                
                if 'ai_chat_count' in user_data:
                    personalized["description"] += f"\n• Conversas com IA: {user_data['ai_chat_count']}"
            
            # Adicionar botões contextuais
            contextual_buttons = self._get_contextual_buttons(user_id, template.get("name", ""))
            if contextual_buttons:
                personalized["buttons"].extend(contextual_buttons)
            
            return personalized
            
        except Exception as e:
            logger.error(f"Erro ao personalizar menu: {e}")
            return template
    
    def _get_contextual_buttons(self, user_id: int, menu_name: str) -> List[List[str]]:
        """Adiciona botões contextuais baseados no comportamento do usuário"""
        contextual_buttons = []
        
        try:
            user_context = self.user_contexts.get(user_id, {})
            
            # Botões para usuários frequentes
            if user_context.get('usage_frequency', 0) > 10:
                if menu_name == "voice_clone":
                    contextual_buttons.append(["⭐ Favoritos", "voice_favorites"])
                    contextual_buttons.append(["🚀 Modo Rápido", "quick_mode"])
            
            # Botões para usuários novos
            if user_context.get('is_new_user', True):
                contextual_buttons.append(["🎓 Tour Interativo", "interactive_tour"])
                contextual_buttons.append(["💡 Dicas", "tips"])
            
            # Botões para usuários premium (se implementado)
            if user_context.get('is_premium', False):
                contextual_buttons.append(["💎 Recursos Premium", "premium_features"])
            
            return contextual_buttons
            
        except Exception as e:
            logger.error(f"Erro ao gerar botões contextuais: {e}")
            return []
    
    def _update_menu_history(self, user_id: int, menu_name: str):
        """Atualiza histórico de menus do usuário"""
        try:
            if user_id not in self.menu_history:
                self.menu_history[user_id] = []
            
            # Adicionar menu atual ao histórico
            self.menu_history[user_id].append({
                'menu': menu_name,
                'timestamp': datetime.now(),
                'action': 'accessed'
            })
            
            # Manter apenas os últimos 10 menus
            if len(self.menu_history[user_id]) > 10:
                self.menu_history[user_id] = self.menu_history[user_id][-10:]
                
        except Exception as e:
            logger.error(f"Erro ao atualizar histórico de menus: {e}")

class VoiceCommandSystem:
    """Sistema de comandos de voz para controle do bot"""
    
    def __init__(self):
        self.voice_commands = self._load_voice_commands()
        self.command_patterns = self._load_command_patterns()
        self.user_voice_preferences = {}
        
    def _load_voice_commands(self) -> Dict[str, Dict]:
        """Carrega comandos de voz disponíveis"""
        return {
            "clonar_voz": {
                "keywords": ["clonar", "voz", "imitar", "copiar", "reproduzir"],
                "description": "Clona a voz do usuário",
                "action": "voice_clone",
                "examples": ["clonar minha voz", "imitar voz", "copiar voz"]
            },
            "gerar_imagem": {
                "keywords": ["gerar", "imagem", "criar", "desenhar", "fazer"],
                "description": "Gera imagem com IA",
                "action": "image_generation",
                "examples": ["gerar imagem", "criar desenho", "fazer foto"]
            },
            "chat_ia": {
                "keywords": ["chat", "conversar", "perguntar", "ajuda", "assistente"],
                "description": "Inicia chat com IA",
                "action": "ai_chat",
                "examples": ["quero conversar", "preciso de ajuda", "perguntar algo"]
            },
            "verificar_seguranca": {
                "keywords": ["verificar", "segurança", "vazamento", "proteger", "checar"],
                "description": "Verifica segurança de dados",
                "action": "security_check",
                "examples": ["verificar segurança", "checar vazamento", "proteger dados"]
            },
            "configuracoes": {
                "keywords": ["configurar", "ajustar", "personalizar", "preferências", "configurações"],
                "description": "Abre configurações",
                "action": "settings",
                "examples": ["abrir configurações", "ajustar preferências", "personalizar bot"]
            },
            "ajuda": {
                "keywords": ["ajuda", "socorro", "como usar", "tutorial", "guia"],
                "description": "Mostra ajuda",
                "action": "help",
                "examples": ["preciso de ajuda", "como usar", "mostrar tutorial"]
            }
        }
    
    def _load_command_patterns(self) -> Dict[str, List[str]]:
        """Carrega padrões de reconhecimento de voz"""
        return {
            "greeting": [
                "olá", "oi", "bom dia", "boa tarde", "boa noite",
                "hello", "hi", "good morning", "good afternoon", "good evening"
            ],
            "farewell": [
                "tchau", "até logo", "até mais", "adeus", "sair",
                "bye", "goodbye", "see you", "farewell"
            ],
            "confirmation": [
                "sim", "claro", "certo", "ok", "perfeito", "excelente",
                "yes", "sure", "okay", "perfect", "excellent"
            ],
            "negation": [
                "não", "nada", "cancelar", "parar", "desistir",
                "no", "not", "cancel", "stop", "quit"
            ]
        }
    
    def process_voice_command(self, audio_text: str, user_id: int) -> Dict[str, Any]:
        """Processa comando de voz e retorna ação correspondente"""
        try:
            audio_text_lower = audio_text.lower().strip()
            
            # Verificar padrões especiais
            if self._is_greeting(audio_text_lower):
                return {
                    "action": "greeting",
                    "response": "Olá! Como posso ajudá-lo hoje?",
                    "menu": "main_menu"
                }
            
            if self._is_farewell(audio_text_lower):
                return {
                    "action": "farewell",
                    "response": "Até logo! Foi um prazer ajudá-lo!",
                    "menu": None
                }
            
            # Buscar comando correspondente
            for command_name, command_info in self.voice_commands.items():
                if self._matches_command(audio_text_lower, command_info):
                    return {
                        "action": command_info["action"],
                        "response": f"Executando: {command_info['description']}",
                        "menu": command_info.get("menu", "main_menu"),
                        "command": command_name
                    }
            
            # Comando não reconhecido
            return {
                "action": "unknown",
                "response": "Desculpe, não entendi esse comando. Pode repetir?",
                "menu": "help",
                "suggestions": self._get_command_suggestions(audio_text_lower)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar comando de voz: {e}")
            return {
                "action": "error",
                "response": "Ocorreu um erro ao processar seu comando. Tente novamente.",
                "menu": "help"
            }
    
    def _is_greeting(self, text: str) -> bool:
        """Verifica se é uma saudação"""
        return any(greeting in text for greeting in self.command_patterns["greeting"])
    
    def _is_farewell(self, text: str) -> bool:
        """Verifica se é uma despedida"""
        return any(farewell in text for farewell in self.command_patterns["farewell"])
    
    def _matches_command(self, text: str, command_info: Dict) -> bool:
        """Verifica se o texto corresponde ao comando"""
        keywords = command_info["keywords"]
        return any(keyword in text for keyword in keywords)
    
    def _get_command_suggestions(self, text: str) -> List[str]:
        """Retorna sugestões de comandos baseadas no texto"""
        suggestions = []
        
        # Buscar comandos similares
        for command_name, command_info in self.voice_commands.items():
            for keyword in command_info["keywords"]:
                if keyword in text or any(word in keyword for word in text.split()):
                    suggestions.extend(command_info["examples"])
                    break
        
        # Retornar até 3 sugestões únicas
        return list(set(suggestions))[:3]

class CustomShortcutsSystem:
    """Sistema de shortcuts personalizáveis para o usuário"""
    
    def __init__(self):
        self.user_shortcuts = {}
        self.default_shortcuts = self._load_default_shortcuts()
        
    def _load_default_shortcuts(self) -> Dict[str, Dict]:
        """Carrega shortcuts padrão"""
        return {
            "voz": {
                "command": "/clonar_voz",
                "description": "Clonagem rápida de voz",
                "category": "voice"
            },
            "imagem": {
                "command": "/gerar_imagem",
                "description": "Geração rápida de imagem",
                "category": "image"
            },
            "chat": {
                "command": "/chat",
                "description": "Chat rápido com IA",
                "category": "ai"
            },
            "seguranca": {
                "command": "/verificar_vazamento",
                "description": "Verificação rápida de segurança",
                "category": "security"
            },
            "ajuda": {
                "command": "/ajuda",
                "description": "Ajuda rápida",
                "category": "help"
            }
        }
    
    def add_user_shortcut(self, user_id: int, shortcut_name: str, command: str, description: str = ""):
        """Adiciona shortcut personalizado para o usuário"""
        try:
            if user_id not in self.user_shortcuts:
                self.user_shortcuts[user_id] = {}
            
            self.user_shortcuts[user_id][shortcut_name] = {
                "command": command,
                "description": description or f"Shortcut para {command}",
                "created_at": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            logger.info(f"Shortcut '{shortcut_name}' adicionado para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar shortcut: {e}")
    
    def remove_user_shortcut(self, user_id: int, shortcut_name: str) -> bool:
        """Remove shortcut personalizado do usuário"""
        try:
            if user_id in self.user_shortcuts and shortcut_name in self.user_shortcuts[user_id]:
                del self.user_shortcuts[user_id][shortcut_name]
                logger.info(f"Shortcut '{shortcut_name}' removido para usuário {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover shortcut: {e}")
            return False
    
    def get_user_shortcuts(self, user_id: int) -> Dict[str, Dict]:
        """Retorna todos os shortcuts do usuário"""
        try:
            user_shortcuts = self.user_shortcuts.get(user_id, {})
            
            # Combinar com shortcuts padrão
            all_shortcuts = self.default_shortcuts.copy()
            all_shortcuts.update(user_shortcuts)
            
            return all_shortcuts
            
        except Exception as e:
            logger.error(f"Erro ao obter shortcuts: {e}")
            return self.default_shortcuts.copy()
    
    def increment_usage(self, user_id: int, shortcut_name: str):
        """Incrementa contador de uso do shortcut"""
        try:
            if user_id in self.user_shortcuts and shortcut_name in self.user_shortcuts[user_id]:
                self.user_shortcuts[user_id][shortcut_name]["usage_count"] += 1
                
        except Exception as e:
            logger.error(f"Erro ao incrementar uso: {e}")

class InteractiveTourSystem:
    """Sistema de tour interativo para novos usuários"""
    
    def __init__(self):
        self.tour_steps = self._load_tour_steps()
        self.user_tour_progress = {}
        
    def _load_tour_steps(self) -> List[Dict[str, Any]]:
        """Carrega passos do tour interativo"""
        return [
            {
                "step": 1,
                "title": "🎭 **Bem-vindo ao Bot de Voz e IA!**",
                "description": "Vou te guiar pelas principais funcionalidades em apenas alguns passos.",
                "action": "show_welcome",
                "buttons": [["👉 Começar Tour", "tour_next"]]
            },
            {
                "step": 2,
                "title": "🎤 **Clonagem de Voz**",
                "description": "Grave um áudio de referência e clone sua voz para qualquer texto!",
                "action": "show_voice_clone",
                "buttons": [
                    ["🎤 Testar Agora", "test_voice_clone"],
                    ["👉 Próximo", "tour_next"]
                ]
            },
            {
                "step": 3,
                "title": "🤖 **Chat Inteligente**",
                "description": "Converse com IA avançada para análises, códigos e muito mais!",
                "action": "show_ai_chat",
                "buttons": [
                    ["💬 Testar Chat", "test_ai_chat"],
                    ["👉 Próximo", "tour_next"]
                ]
            },
            {
                "step": 4,
                "title": "🖼️ **Geração de Imagens**",
                "description": "Crie imagens incríveis apenas descrevendo o que deseja!",
                "action": "show_image_gen",
                "buttons": [
                    ["🎨 Testar Geração", "test_image_gen"],
                    ["👉 Próximo", "tour_next"]
                ]
            },
            {
                "step": 5,
                "title": "🔍 **Verificação de Segurança**",
                "description": "Verifique se seus dados foram comprometidos em vazamentos!",
                "action": "show_security",
                "buttons": [
                    ["🔍 Testar Verificação", "test_security"],
                    ["👉 Próximo", "tour_next"]
                ]
            },
            {
                "step": 6,
                "title": "🎉 **Tour Concluído!**",
                "description": "Parabéns! Agora você conhece todas as funcionalidades principais.",
                "action": "show_completion",
                "buttons": [
                    ["🚀 Começar a Usar", "start_using"],
                    ["📚 Ver Mais Ajuda", "more_help"]
                ]
            }
        ]
    
    def start_tour(self, user_id: int) -> Dict[str, Any]:
        """Inicia tour para o usuário"""
        try:
            self.user_tour_progress[user_id] = {
                "current_step": 1,
                "started_at": datetime.now(),
                "completed_steps": []
            }
            
            return self.get_tour_step(user_id, 1)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar tour: {e}")
            return None
    
    def get_tour_step(self, user_id: int, step: int) -> Dict[str, Any]:
        """Retorna passo específico do tour"""
        try:
            if step <= 0 or step > len(self.tour_steps):
                return None
            
            tour_step = self.tour_steps[step - 1]
            
            # Personalizar baseado no usuário
            if step == 1:
                tour_step["description"] += f"\n\n👤 **Usuário:** {user_id}"
            
            return tour_step
            
        except Exception as e:
            logger.error(f"Erro ao obter passo do tour: {e}")
            return None
    
    def next_tour_step(self, user_id: int) -> Dict[str, Any]:
        """Avança para o próximo passo do tour"""
        try:
            if user_id not in self.user_tour_progress:
                return None
            
            progress = self.user_tour_progress[user_id]
            current_step = progress["current_step"]
            
            # Marcar passo atual como completo
            if current_step not in progress["completed_steps"]:
                progress["completed_steps"].append(current_step)
            
            # Avançar para próximo passo
            next_step = current_step + 1
            if next_step <= len(self.tour_steps):
                progress["current_step"] = next_step
                return self.get_tour_step(user_id, next_step)
            else:
                # Tour concluído
                progress["completed_at"] = datetime.now()
                return self.get_tour_step(user_id, len(self.tour_steps))
                
        except Exception as e:
            logger.error(f"Erro ao avançar tour: {e}")
            return None
    
    def get_tour_progress(self, user_id: int) -> Dict[str, Any]:
        """Retorna progresso atual do tour"""
        try:
            if user_id not in self.user_tour_progress:
                return {"status": "not_started"}
            
            progress = self.user_tour_progress[user_id]
            total_steps = len(self.tour_steps)
            completed_steps = len(progress["completed_steps"])
            
            return {
                "status": "in_progress" if "completed_at" not in progress else "completed",
                "current_step": progress["current_step"],
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "progress_percentage": (completed_steps / total_steps) * 100,
                "started_at": progress.get("started_at"),
                "completed_at": progress.get("completed_at")
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter progresso do tour: {e}")
            return {"status": "error"}

class UIManager:
    """Gerenciador principal da interface do usuário"""
    
    def __init__(self):
        self.dynamic_menus = DynamicMenuSystem()
        self.voice_commands = VoiceCommandSystem()
        self.custom_shortcuts = CustomShortcutsSystem()
        self.interactive_tour = InteractiveTourSystem()
        
    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, menu_name: str = "main_menu"):
        """Mostra menu dinâmico para o usuário"""
        try:
            user_id = update.effective_user.id
            user_data = context.user_data
            
            # Obter menu personalizado
            menu_data = self.dynamic_menus.get_dynamic_menu(user_id, menu_name, user_data)
            
            # Criar botões do menu
            keyboard = []
            for button_row in menu_data["buttons"]:
                if len(button_row) == 2:
                    keyboard.append([InlineKeyboardButton(button_row[0], callback_data=button_row[1])])
                else:
                    keyboard.append([InlineKeyboardButton(btn, callback_data=btn) for btn in button_row])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Enviar menu
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=f"{menu_data['title']}\n\n{menu_data['description']}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    text=f"{menu_data['title']}\n\n{menu_data['description']}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Erro ao mostrar menu: {e}")
            await update.message.reply_text("❌ Erro ao carregar menu. Tente novamente.")
    
    async def process_voice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, audio_text: str):
        """Processa comando de voz e executa ação correspondente"""
        try:
            user_id = update.effective_user.id
            
            # Processar comando
            result = self.voice_commands.process_voice_command(audio_text, user_id)
            
            # Mostrar resposta
            await update.message.reply_text(f"🎤 **Comando de Voz:** {result['response']}")
            
            # Executar ação se necessário
            if result["action"] not in ["greeting", "farewell", "unknown", "error"]:
                # Navegar para menu correspondente
                if result["menu"]:
                    await self.show_menu(update, context, result["menu"])
            
            # Mostrar sugestões se comando não reconhecido
            if result["action"] == "unknown" and "suggestions" in result:
                suggestions_text = "\n".join([f"• {suggestion}" for suggestion in result["suggestions"]])
                await update.message.reply_text(f"💡 **Sugestões:**\n{suggestions_text}")
                
        except Exception as e:
            logger.error(f"Erro ao processar comando de voz: {e}")
            await update.message.reply_text("❌ Erro ao processar comando de voz. Tente novamente.")
    
    async def show_shortcuts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra shortcuts personalizados do usuário"""
        try:
            user_id = update.effective_user.id
            shortcuts = self.custom_shortcuts.get_user_shortcuts(user_id)
            
            shortcuts_text = "🎯 **Seus Shortcuts Personalizados:**\n\n"
            
            for name, shortcut in shortcuts.items():
                shortcuts_text += f"**{name.title()}:** {shortcut['command']}\n"
                shortcuts_text += f"└ {shortcut['description']}\n\n"
            
            # Botões para gerenciar shortcuts
            keyboard = [
                [InlineKeyboardButton("➕ Adicionar Shortcut", callback_data="add_shortcut")],
                [InlineKeyboardButton("✏️ Editar Shortcuts", callback_data="edit_shortcuts")],
                [InlineKeyboardButton("🗑️ Remover Shortcut", callback_data="remove_shortcut")],
                [InlineKeyboardButton("🔙 Voltar", callback_data="settings")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text=shortcuts_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao mostrar shortcuts: {e}")
            await update.message.reply_text("❌ Erro ao carregar shortcuts. Tente novamente.")
    
    async def start_interactive_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia tour interativo para o usuário"""
        try:
            user_id = update.effective_user.id
            
            # Iniciar tour
            tour_step = self.interactive_tour.start_tour(user_id)
            
            if tour_step:
                # Criar botões do tour
                keyboard = []
                for button_row in tour_step["buttons"]:
                    if len(button_row) == 2:
                        keyboard.append([InlineKeyboardButton(button_row[0], callback_data=button_row[1])])
                    else:
                        keyboard.append([InlineKeyboardButton(btn, callback_data=btn) for btn in button_row])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    text=f"{tour_step['title']}\n\n{tour_step['description']}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Erro ao iniciar tour. Tente novamente.")
                
        except Exception as e:
            logger.error(f"Erro ao iniciar tour: {e}")
            await update.message.reply_text("❌ Erro ao iniciar tour. Tente novamente.")

# Instância global do gerenciador de UI
ui_manager = UIManager()
