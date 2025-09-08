import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResponseTemplate:
    """Sistema de templates de resposta personalizáveis"""
    
    def __init__(self, template_file: str = "templates.json"):
        self.template_file = template_file
        self.templates: Dict[str, Dict] = {}
        self.user_templates: Dict[int, Dict] = {}
        self.load_templates()
    
    def load_templates(self):
        """Carrega templates do arquivo"""
        try:
            if os.path.exists(self.template_file):
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                logger.info(f"Templates carregados de {self.template_file}")
            else:
                self._create_default_templates()
                self.save_templates()
        except Exception as e:
            logger.error(f"Erro ao carregar templates: {e}")
            self._create_default_templates()
    
    def save_templates(self):
        """Salva templates no arquivo"""
        try:
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            logger.info(f"Templates salvos em {self.template_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar templates: {e}")
    
    def _create_default_templates(self):
        """Cria templates padrão"""
        self.templates = {
            "welcome": {
                "text": "🎉 Olá! Sou seu assistente IA. Como posso ajudar?",
                "variables": [],
                "category": "system"
            },
            "error": {
                "text": "❌ Ops! Algo deu errado. Tente novamente.",
                "variables": [],
                "category": "system"
            },
            "processing": {
                "text": "⏳ Processando sua solicitação...",
                "variables": [],
                "category": "system"
            },
            "success": {
                "text": "✅ Pronto! Aqui está o resultado:",
                "variables": [],
                "category": "system"
            },
            "ai_response": {
                "text": "🤖 **Resposta da IA:**\n\n{response}",
                "variables": ["response"],
                "category": "ai"
            },
            "image_generated": {
                "text": "🎨 **Imagem Gerada:**\n\n{description}\n\n{image_url}",
                "variables": ["description", "image_url"],
                "category": "image"
            },
            "code_generated": {
                "text": "🔧 **Código Gerado:**\n\n```{language}\n{code}\n```\n\n**Linguagem:** {language}\n**Descrição:** {description}",
                "variables": ["language", "code", "description"],
                "category": "code"
            },
            "web_search": {
                "text": "🔍 **Resultado da Busca:**\n\n{query}\n\n{results}",
                "variables": ["query", "results"],
                "category": "search"
            },
            "voice_transcribed": {
                "text": "🎵 **Áudio Processado**\n\n📝 **Transcrição:** \"_{transcription}_\"\n🌍 **Idioma:** {language}\n🔧 **Formato:** {format}",
                "variables": ["transcription", "language", "format"],
                "category": "voice"
            },
            "security_check": {
                "text": "🛡️ **Verificação de Segurança**\n\n{item}\n\n{result}\n\n{recommendations}",
                "variables": ["item", "result", "recommendations"],
                "category": "security"
            },
            "help": {
                "text": "❓ **Ajuda - {command}**\n\n{description}\n\n**Uso:** {usage}\n**Exemplo:** {example}",
                "variables": ["command", "description", "usage", "example"],
                "category": "help"
            },
            "progress": {
                "text": "⏳ **{status}**\n\n{progress_bar} {percentage}%\n⏱️ Tempo: {elapsed_time}s",
                "variables": ["status", "progress_bar", "percentage", "elapsed_time"],
                "category": "progress"
            },
            "menu": {
                "text": "🤖 **Menu Principal**\n\nEscolha uma opção:",
                "variables": [],
                "category": "menu"
            },
            "settings": {
                "text": "⚙️ **Configurações**\n\n{settings_list}",
                "variables": ["settings_list"],
                "category": "settings"
            },
            "analytics": {
                "text": "📊 **Estatísticas**\n\n{stats_summary}",
                "variables": ["stats_summary"],
                "category": "analytics"
            }
        }
    
    def get_template(self, template_name: str, **kwargs) -> str:
        """Retorna template formatado com variáveis"""
        if template_name not in self.templates:
            logger.warning(f"Template {template_name} não encontrado")
            return f"Template {template_name} não encontrado"
        
        template = self.templates[template_name]
        text = template["text"]
        
        try:
            # Substituir variáveis
            for key, value in kwargs.items():
                placeholder = f"{{{key}}}"
                if placeholder in text:
                    text = text.replace(placeholder, str(value))
            
            return text
        except Exception as e:
            logger.error(f"Erro ao formatar template {template_name}: {e}")
            return template["text"]
    
    def add_template(self, name: str, text: str, variables: List[str] = None, 
                    category: str = "custom") -> bool:
        """Adiciona novo template"""
        try:
            self.templates[name] = {
                "text": text,
                "variables": variables or [],
                "category": category
            }
            self.save_templates()
            logger.info(f"Template {name} adicionado")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar template {name}: {e}")
            return False
    
    def update_template(self, name: str, text: str = None, variables: List[str] = None,
                       category: str = None) -> bool:
        """Atualiza template existente"""
        if name not in self.templates:
            return False
        
        try:
            if text is not None:
                self.templates[name]["text"] = text
            if variables is not None:
                self.templates[name]["variables"] = variables
            if category is not None:
                self.templates[name]["category"] = category
            
            self.save_templates()
            logger.info(f"Template {name} atualizado")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar template {name}: {e}")
            return False
    
    def remove_template(self, name: str) -> bool:
        """Remove template"""
        if name in self.templates:
            del self.templates[name]
            self.save_templates()
            logger.info(f"Template {name} removido")
            return True
        return False
    
    def get_templates_by_category(self, category: str) -> Dict[str, Dict]:
        """Retorna templates por categoria"""
        return {
            name: template for name, template in self.templates.items()
            if template.get("category") == category
        }
    
    def list_templates(self) -> List[Dict]:
        """Lista todos os templates"""
        return [
            {
                "name": name,
                "text": template["text"],
                "variables": template["variables"],
                "category": template["category"]
            }
            for name, template in self.templates.items()
        ]
    
    def get_user_template(self, user_id: int, template_name: str) -> Optional[str]:
        """Obtém template personalizado do usuário"""
        if user_id in self.user_templates and template_name in self.user_templates[user_id]:
            return self.user_templates[user_id][template_name]
        return None
    
    def set_user_template(self, user_id: int, template_name: str, text: str) -> bool:
        """Define template personalizado para usuário"""
        try:
            if user_id not in self.user_templates:
                self.user_templates[user_id] = {}
            
            self.user_templates[user_id][template_name] = text
            logger.info(f"Template personalizado {template_name} definido para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao definir template personalizado: {e}")
            return False

class TemplateManager:
    """Gerenciador avançado de templates com funcionalidades extras"""
    
    def __init__(self):
        self.templates = ResponseTemplate()
        self.response_cache = {}
    
    def get_smart_response(self, context: str, user_id: int = None, **kwargs) -> str:
        """Retorna resposta inteligente baseada no contexto"""
        # Verificar template personalizado do usuário primeiro
        if user_id:
            user_template = self.templates.get_user_template(user_id, context)
            if user_template:
                return self.templates.get_template(context, **kwargs)
        
        # Usar template padrão
        return self.templates.get_template(context, **kwargs)
    
    def get_progress_template(self, status: str, percentage: int, elapsed_time: float) -> str:
        """Gera template de progresso"""
        bars = "▰" * (percentage // 10) + "▱" * (10 - percentage // 10)
        return self.templates.get_template("progress", 
                                         status=status,
                                         progress_bar=bars,
                                         percentage=percentage,
                                         elapsed_time=f"{elapsed_time:.1f}")
    
    def get_ai_response_template(self, response: str, model: str = "Gemini") -> str:
        """Gera template de resposta da IA"""
        return self.templates.get_template("ai_response", 
                                         response=response,
                                         model=model)
    
    def get_error_template(self, error_type: str = "general", details: str = None) -> str:
        """Gera template de erro"""
        if error_type == "api":
            return "🔌 Erro de API. Serviço temporariamente indisponível."
        elif error_type == "timeout":
            return "⏰ Tempo limite excedido. Tente novamente."
        elif error_type == "permission":
            return "🚫 Permissão negada. Verifique suas credenciais."
        else:
            return self.templates.get_template("error")

# Instância global do gerenciador de templates
template_manager = TemplateManager()
response_templates = ResponseTemplate()

