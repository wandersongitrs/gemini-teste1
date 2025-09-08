import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Coroutine
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Task:
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    user_id: Optional[int] = None
    chat_id: Optional[int] = None

class AsyncTaskQueue:
    """Sistema de filas assíncronas para gerenciamento de tarefas"""
    
    def __init__(self, max_workers: int = 5, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.tasks: Dict[str, Task] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'avg_completion_time': 0.0
        }
    
    async def start(self):
        """Inicia o sistema de filas"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"Iniciando sistema de filas com {self.max_workers} workers")
        
        # Criar workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Para o sistema de filas"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Parando sistema de filas...")
        
        # Cancelar workers
        for worker in self.workers:
            worker.cancel()
        
        # Aguardar workers terminarem
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Sistema de filas parado")
    
    async def add_task(self, name: str, func: Callable, priority: TaskPriority = TaskPriority.NORMAL,
                      user_id: Optional[int] = None, chat_id: Optional[int] = None,
                      *args, **kwargs) -> str:
        """Adiciona uma nova tarefa à fila"""
        if self.queue.qsize() >= self.max_queue_size:
            raise ValueError("Fila está cheia")
        
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=time.time(),
            user_id=user_id,
            chat_id=chat_id
        )
        
        self.tasks[task_id] = task
        self.stats['total_tasks'] += 1
        
        # Adicionar à fila com prioridade
        priority_value = priority.value
        await self.queue.put((priority_value, task))
        
        logger.info(f"Tarefa {name} (ID: {task_id}) adicionada à fila com prioridade {priority.name}")
        return task_id
    
    async def _worker(self, worker_name: str):
        """Worker que processa tarefas da fila"""
        logger.info(f"Worker {worker_name} iniciado")
        
        while self.running:
            try:
                # Aguardar tarefa da fila
                priority, task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                logger.info(f"Worker {worker_name} processando tarefa {task.name}")
                
                # Atualizar status
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                
                # Executar tarefa
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        result = await task.func(*task.args, **task.kwargs)
                    else:
                        # Executar função síncrona em thread separada
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, task.func, *task.args, **task.kwargs)
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = time.time()
                    self.stats['completed_tasks'] += 1
                    
                    logger.info(f"Tarefa {task.name} concluída com sucesso")
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = time.time()
                    self.stats['failed_tasks'] += 1
                    
                    logger.error(f"Erro na tarefa {task.name}: {e}")
                
                finally:
                    # Marcar tarefa como concluída na fila
                    self.queue.task_done()
                    
                    # Atualizar estatísticas
                    self._update_stats()
            
            except asyncio.TimeoutError:
                # Timeout - continuar loop
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelado")
                break
            except Exception as e:
                logger.error(f"Erro no worker {worker_name}: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Retorna status de uma tarefa específica"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            'id': task.id,
            'name': task.name,
            'status': task.status.value,
            'priority': task.priority.name,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'result': task.result,
            'error': task.error,
            'user_id': task.user_id,
            'chat_id': task.chat_id
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa específica"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            self.stats['cancelled_tasks'] += 1
            logger.info(f"Tarefa {task.name} cancelada")
            return True
        
        return False
    
    def get_user_tasks(self, user_id: int) -> List[Dict]:
        """Retorna todas as tarefas de um usuário específico"""
        user_tasks = []
        for task in self.tasks.values():
            if task.user_id == user_id:
                user_tasks.append(self.get_task_status(task.id))
        return user_tasks
    
    def get_queue_stats(self) -> Dict:
        """Retorna estatísticas da fila"""
        return {
            'queue_size': self.queue.qsize(),
            'max_queue_size': self.max_queue_size,
            'active_workers': len([w for w in self.workers if not w.done()]),
            'max_workers': self.max_workers,
            'running': self.running,
            **self.stats
        }
    
    def _update_stats(self):
        """Atualiza estatísticas de tempo médio de conclusão"""
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        if completed_tasks:
            completion_times = [t.completed_at - t.created_at for t in completed_tasks]
            self.stats['avg_completion_time'] = sum(completion_times) / len(completion_times)
    
    async def wait_for_task(self, task_id: str, timeout: float = 60.0) -> Optional[Any]:
        """Aguarda conclusão de uma tarefa específica"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task_status = self.get_task_status(task_id)
            if not task_status:
                return None
            
            if task_status['status'] in ['completed', 'failed', 'cancelled']:
                return task_status['result'] if task_status['status'] == 'completed' else None
            
            await asyncio.sleep(0.1)
        
        return None

# Instância global do sistema de filas
task_queue = AsyncTaskQueue(max_workers=3, max_queue_size=50)

# Funções auxiliares para tarefas comuns
async def add_ai_task(name: str, func: Callable, user_id: int, chat_id: int, 
                     priority: TaskPriority = TaskPriority.NORMAL, *args, **kwargs) -> str:
    """Adiciona tarefa de IA à fila"""
    return await task_queue.add_task(name, func, priority, user_id, chat_id, *args, **kwargs)

async def add_image_task(name: str, func: Callable, user_id: int, chat_id: int,
                        priority: TaskPriority = TaskPriority.NORMAL, *args, **kwargs) -> str:
    """Adiciona tarefa de processamento de imagem à fila"""
    return await task_queue.add_task(name, func, priority, user_id, chat_id, *args, **kwargs)

async def add_web_task(name: str, func: Callable, user_id: int, chat_id: int,
                      priority: TaskPriority = TaskPriority.NORMAL, *args, **kwargs) -> str:
    """Adiciona tarefa de busca web à fila"""
    return await task_queue.add_task(name, func, priority, user_id, chat_id, *args, **kwargs)

