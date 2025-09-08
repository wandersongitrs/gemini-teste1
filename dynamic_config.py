import json
import os
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Configuração principal do bot"""
    # Configurações de IA
    max_response_length: int = 4000
    temperature: float = 0.7
    max_tokens: int = 1000
    model_name: str = "gemini-1.5-flash"
    
    # Configurações de Rate Limiting
    max_requests_per_minute: int = 15
    max_requests_per_hour: int = 100
    
    # Configurações de Cache
    cache_enabled: bool = True
    cache_ttl: int = 1800  # 30 minutos
    cache_max_size: int = 500
    
    # Configurações de UI
    show_progress: bool = True
    progress_update_interval: float = 0.5
    max_progress_steps: int = 10
    
    # Configurações de Plugins
    plugins_enabled: bool = True
    auto_load_plugins: bool = True
    
    # Configurações de Webhooks
    webhooks_enabled: bool = True
    webhook_timeout: float = 10.0
    webhook_retry_count: int = 3
    
    # Configurações de Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file: str = "bot.log"
    
    # Configurações de Segurança
    content_moderation: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = None
    
    # Configurações de Performance
    max_concurrent_tasks: int = 5
    task_timeout: float = 60.0
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = [
                'image/jpeg', 'image/png', 'image/gif', 
                'audio/ogg', 'audio/mp3', 'audio/wav',
                'text/plain', 'application/pdf'
            ]

class DynamicConfigManager:
    """Gerenciador de configuração dinâmica"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.config = BotConfig()
        self.user_configs: Dict[int, Dict] = {}
        self.config_watchers: List[callable] = []
        self.load_config()
    
    def load_config(self):
        """Carrega configuração do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Atualizar configuração com dados do arquivo
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                logger.info(f"Configuração carregada de {self.config_file}")
            else:
                self.save_config()
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
    
    def save_config(self):
        """Salva configuração no arquivo"""
        try:
            config_data = asdict(self.config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuração salva em {self.config_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração"""
        return getattr(self.config, key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """Define valor de configuração"""
        try:
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.save_config()
                self._notify_watchers(key, value)
                logger.info(f"Configuração {key} atualizada para {value}")
                return True
            else:
                logger.warning(f"Configuração {key} não existe")
                return False
        except Exception as e:
            logger.error(f"Erro ao definir configuração {key}: {e}")
            return False
    
    def get_user_config(self, user_id: int, key: str, default: Any = None) -> Any:
        """Obtém configuração específica do usuário"""
        if user_id in self.user_configs and key in self.user_configs[user_id]:
            return self.user_configs[user_id][key]
        return self.get_config(key, default)
    
    def set_user_config(self, user_id: int, key: str, value: Any) -> bool:
        """Define configuração específica do usuário"""
        try:
            if user_id not in self.user_configs:
                self.user_configs[user_id] = {}
            
            self.user_configs[user_id][key] = value
            logger.info(f"Configuração {key} definida para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao definir configuração do usuário: {e}")
            return False
    
    def add_config_watcher(self, callback: callable):
        """Adiciona observador de mudanças de configuração"""
        self.config_watchers.append(callback)
    
    def _notify_watchers(self, key: str, value: Any):
        """Notifica observadores sobre mudanças"""
        for watcher in self.config_watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logger.error(f"Erro no watcher de configuração: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Retorna resumo da configuração atual"""
        return {
            'ai_settings': {
                'max_response_length': self.config.max_response_length,
                'temperature': self.config.temperature,
                'model_name': self.config.model_name
            },
            'performance_settings': {
                'max_requests_per_minute': self.config.max_requests_per_minute,
                'cache_enabled': self.config.cache_enabled,
                'max_concurrent_tasks': self.config.max_concurrent_tasks
            },
            'ui_settings': {
                'show_progress': self.config.show_progress,
                'progress_update_interval': self.config.progress_update_interval
            },
            'security_settings': {
                'content_moderation': self.config.content_moderation,
                'max_file_size': self.config.max_file_size
            }
        }
    
    def reset_to_defaults(self):
        """Reseta configuração para valores padrão"""
        self.config = BotConfig()
        self.save_config()
        logger.info("Configuração resetada para valores padrão")
    
    def export_config(self) -> Dict[str, Any]:
        """Exporta configuração completa"""
        return {
            'global_config': asdict(self.config),
            'user_configs': self.user_configs,
            'exported_at': datetime.now().isoformat()
        }
    
    def import_config(self, config_data: Dict[str, Any]) -> bool:
        """Importa configuração"""
        try:
            if 'global_config' in config_data:
                for key, value in config_data['global_config'].items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            
            if 'user_configs' in config_data:
                self.user_configs.update(config_data['user_configs'])
            
            self.save_config()
            logger.info("Configuração importada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao importar configuração: {e}")
            return False

class ConfigValidator:
    """Validador de configurações"""
    
    @staticmethod
    def validate_config(config: BotConfig) -> List[str]:
        """Valida configuração e retorna lista de erros"""
        errors = []
        
        # Validar configurações de IA
        if config.max_response_length <= 0:
            errors.append("max_response_length deve ser maior que 0")
        
        if not 0 <= config.temperature <= 2:
            errors.append("temperature deve estar entre 0 e 2")
        
        if config.max_tokens <= 0:
            errors.append("max_tokens deve ser maior que 0")
        
        # Validar configurações de rate limiting
        if config.max_requests_per_minute <= 0:
            errors.append("max_requests_per_minute deve ser maior que 0")
        
        if config.max_requests_per_hour <= 0:
            errors.append("max_requests_per_hour deve ser maior que 0")
        
        # Validar configurações de cache
        if config.cache_ttl <= 0:
            errors.append("cache_ttl deve ser maior que 0")
        
        if config.cache_max_size <= 0:
            errors.append("cache_max_size deve ser maior que 0")
        
        # Validar configurações de performance
        if config.max_concurrent_tasks <= 0:
            errors.append("max_concurrent_tasks deve ser maior que 0")
        
        if config.task_timeout <= 0:
            errors.append("task_timeout deve ser maior que 0")
        
        return errors

# Instância global do gerenciador de configuração
config_manager = DynamicConfigManager()

# Funções auxiliares para configuração
def get_bot_config(key: str, default: Any = None) -> Any:
    """Função auxiliar para obter configuração"""
    return config_manager.get_config(key, default)

def set_bot_config(key: str, value: Any) -> bool:
    """Função auxiliar para definir configuração"""
    return config_manager.set_config(key, value)

def get_user_config(user_id: int, key: str, default: Any = None) -> Any:
    """Função auxiliar para obter configuração do usuário"""
    return config_manager.get_user_config(user_id, key, default)

def set_user_config(user_id: int, key: str, value: Any) -> bool:
    """Função auxiliar para definir configuração do usuário"""
    return config_manager.set_user_config(user_id, key, value)

# Configurações padrão específicas
DEFAULT_AI_CONFIG = {
    'max_response_length': 4000,
    'temperature': 0.7,
    'max_tokens': 1000,
    'model_name': 'gemini-1.5-flash'
}

DEFAULT_PERFORMANCE_CONFIG = {
    'max_requests_per_minute': 15,
    'max_requests_per_hour': 100,
    'cache_enabled': True,
    'cache_ttl': 1800,
    'cache_max_size': 500,
    'max_concurrent_tasks': 5,
    'task_timeout': 60.0
}

DEFAULT_UI_CONFIG = {
    'show_progress': True,
    'progress_update_interval': 0.5,
    'max_progress_steps': 10
}

DEFAULT_SECURITY_CONFIG = {
    'content_moderation': True,
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_file_types': [
        'image/jpeg', 'image/png', 'image/gif',
        'audio/ogg', 'audio/mp3', 'audio/wav',
        'text/plain', 'application/pdf'
    ]
}

