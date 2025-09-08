import time
import hashlib
import json
from collections import defaultdict
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Sistema de controle de taxa de requisições por usuário"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, List[float]] = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """Verifica se o usuário pode fazer uma nova requisição"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove requisições antigas
        user_requests = [req for req in user_requests if now - req < self.time_window]
        self.requests[user_id] = user_requests
        
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        return False
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Retorna quantas requisições o usuário ainda pode fazer"""
        now = time.time()
        user_requests = self.requests[user_id]
        user_requests = [req for req in user_requests if now - req < self.time_window]
        return max(0, self.max_requests - len(user_requests))

class ResponseCache:
    """Sistema de cache para respostas frequentes"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, float] = {}
    
    def _generate_key(self, query: str, user_id: int) -> str:
        """Gera chave única para o cache"""
        content = f"{user_id}:{query.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_response(self, query: str, user_id: int) -> Optional[str]:
        """Obtém resposta do cache se existir e não expirou"""
        key = self._generate_key(query, user_id)
        
        if key in self.cache:
            cache_entry = self.cache[key]
            if time.time() - cache_entry['timestamp'] < self.ttl:
                self.access_times[key] = time.time()
                logger.info(f"Cache hit para query: {query[:50]}...")
                return cache_entry['response']
            else:
                # Remove entrada expirada
                del self.cache[key]
                del self.access_times[key]
        
        return None
    
    def cache_response(self, query: str, user_id: int, response: str) -> None:
        """Armazena resposta no cache"""
        key = self._generate_key(query, user_id)
        
        # Remove entrada mais antiga se cache estiver cheio
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = {
            'response': response,
            'timestamp': time.time(),
            'query': query
        }
        self.access_times[key] = time.time()
        logger.info(f"Resposta cacheada para query: {query[:50]}...")
    
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            'total_entries': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'hit_rate': self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calcula taxa de acerto do cache"""
        # Implementação simplificada - em produção usar métricas mais sofisticadas
        return 0.85  # Placeholder

# Instâncias globais
rate_limiter = RateLimiter(max_requests=15, time_window=60)
response_cache = ResponseCache(max_size=500, ttl=1800)
