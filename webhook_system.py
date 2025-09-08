import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
import logging

logger = logging.getLogger(__name__)

@dataclass
class WebhookConfig:
    url: str
    name: str
    enabled: bool = True
    timeout: float = 10.0
    retry_count: int = 3
    retry_delay: float = 1.0
    headers: Dict[str, str] = None

class NotificationType:
    ERROR = "error"
    USAGE = "usage"
    ALERT = "alert"
    INFO = "info"
    SUCCESS = "success"

class WebhookManager:
    """Sistema de webhooks para notificações e integrações"""
    
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.stats = {
            'total_notifications': 0,
            'successful_notifications': 0,
            'failed_notifications': 0,
            'last_notification': None
        }
    
    def add_webhook(self, name: str, url: str, notification_type: str = "all", 
                   timeout: float = 10.0, retry_count: int = 3, 
                   headers: Dict[str, str] = None) -> bool:
        """Adiciona um novo webhook"""
        try:
            webhook = WebhookConfig(
                url=url,
                name=name,
                timeout=timeout,
                retry_count=retry_count,
                headers=headers or {}
            )
            
            self.webhooks[name] = webhook
            logger.info(f"Webhook {name} adicionado: {url}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar webhook {name}: {e}")
            return False
    
    def remove_webhook(self, name: str) -> bool:
        """Remove um webhook"""
        if name in self.webhooks:
            del self.webhooks[name]
            logger.info(f"Webhook {name} removido")
            return True
        return False
    
    def enable_webhook(self, name: str) -> bool:
        """Habilita um webhook"""
        if name in self.webhooks:
            self.webhooks[name].enabled = True
            return True
        return False
    
    def disable_webhook(self, name: str) -> bool:
        """Desabilita um webhook"""
        if name in self.webhooks:
            self.webhooks[name].enabled = False
            return True
        return False
    
    async def start(self):
        """Inicia o sistema de webhooks"""
        if self.running:
            return
        
        self.running = True
        logger.info("Sistema de webhooks iniciado")
        
        # Iniciar worker de processamento
        asyncio.create_task(self._notification_worker())
    
    async def stop(self):
        """Para o sistema de webhooks"""
        self.running = False
        logger.info("Sistema de webhooks parado")
    
    async def send_notification(self, notification_type: str, data: Dict[str, Any], 
                              priority: str = "normal") -> bool:
        """Envia notificação para todos os webhooks habilitados"""
        try:
            notification = {
                'type': notification_type,
                'data': data,
                'priority': priority,
                'timestamp': time.time(),
                'id': f"notif_{int(time.time())}"
            }
            
            await self.notification_queue.put(notification)
            self.stats['total_notifications'] += 1
            self.stats['last_notification'] = time.time()
            
            logger.info(f"Notificação {notification_type} adicionada à fila")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
            return False
    
    async def _notification_worker(self):
        """Worker que processa notificações da fila"""
        logger.info("Worker de notificações iniciado")
        
        async with httpx.AsyncClient() as client:
            while self.running:
                try:
                    # Aguardar notificação da fila
                    notification = await asyncio.wait_for(
                        self.notification_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Enviar para todos os webhooks habilitados
                    await self._send_to_webhooks(client, notification)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Erro no worker de notificações: {e}")
    
    async def _send_to_webhooks(self, client: httpx.AsyncClient, notification: Dict):
        """Envia notificação para todos os webhooks"""
        tasks = []
        
        for name, webhook in self.webhooks.items():
            if webhook.enabled:
                task = asyncio.create_task(
                    self._send_webhook(client, webhook, notification)
                )
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Contar sucessos e falhas
            for result in results:
                if isinstance(result, Exception):
                    self.stats['failed_notifications'] += 1
                    logger.error(f"Erro ao enviar webhook: {result}")
                else:
                    self.stats['successful_notifications'] += 1
    
    async def _send_webhook(self, client: httpx.AsyncClient, webhook: WebhookConfig, 
                          notification: Dict) -> bool:
        """Envia notificação para um webhook específico"""
        for attempt in range(webhook.retry_count):
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'GeminiBot/1.0',
                    **webhook.headers
                }
                
                payload = {
                    'webhook_name': webhook.name,
                    'notification': notification
                }
                
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout
                )
                
                response.raise_for_status()
                logger.info(f"Webhook {webhook.name} enviado com sucesso")
                return True
                
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} falhou para {webhook.name}: {e}")
                
                if attempt < webhook.retry_count - 1:
                    await asyncio.sleep(webhook.retry_delay * (attempt + 1))
        
        logger.error(f"Webhook {webhook.name} falhou após {webhook.retry_count} tentativas")
        return False
    
    def get_webhook_stats(self) -> Dict:
        """Retorna estatísticas dos webhooks"""
        return {
            'total_webhooks': len(self.webhooks),
            'enabled_webhooks': len([w for w in self.webhooks.values() if w.enabled]),
            'queue_size': self.notification_queue.qsize(),
            **self.stats
        }
    
    def list_webhooks(self) -> List[Dict]:
        """Lista todos os webhooks configurados"""
        return [
            {
                'name': name,
                'url': webhook.url,
                'enabled': webhook.enabled,
                'timeout': webhook.timeout,
                'retry_count': webhook.retry_count
            }
            for name, webhook in self.webhooks.items()
        ]

# Instância global do gerenciador de webhooks
webhook_manager = WebhookManager()

# Funções auxiliares para notificações específicas
async def notify_error(error_message: str, context: str = "bot", user_id: Optional[int] = None):
    """Envia notificação de erro"""
    data = {
        'error_message': error_message,
        'context': context,
        'user_id': user_id,
        'timestamp': time.time()
    }
    await webhook_manager.send_notification(NotificationType.ERROR, data, "high")

async def notify_usage(action: str, user_id: int, chat_id: int, duration: float = None):
    """Envia notificação de uso"""
    data = {
        'action': action,
        'user_id': user_id,
        'chat_id': chat_id,
        'duration': duration,
        'timestamp': time.time()
    }
    await webhook_manager.send_notification(NotificationType.USAGE, data)

async def notify_alert(alert_type: str, message: str, severity: str = "medium"):
    """Envia notificação de alerta"""
    data = {
        'alert_type': alert_type,
        'message': message,
        'severity': severity,
        'timestamp': time.time()
    }
    await webhook_manager.send_notification(NotificationType.ALERT, data, "high")

async def notify_success(action: str, details: str = None):
    """Envia notificação de sucesso"""
    data = {
        'action': action,
        'details': details,
        'timestamp': time.time()
    }
    await webhook_manager.send_notification(NotificationType.SUCCESS, data)

# Configuração de webhooks padrão
def setup_default_webhooks():
    """Configura webhooks padrão para monitoramento"""
    # Slack para erros
    webhook_manager.add_webhook(
        "slack_errors",
        "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        timeout=5.0,
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    
    # Discord para notificações gerais
    webhook_manager.add_webhook(
        "discord_notifications",
        "https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK",
        timeout=8.0
    )
    
    # Email via webhook (se disponível)
    webhook_manager.add_webhook(
        "email_alerts",
        "https://your-email-service.com/webhook",
        timeout=15.0,
        retry_count=5
    )
    
    logger.info("Webhooks padrão configurados")

