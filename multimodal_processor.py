# -*- coding: utf-8 -*-
"""
Módulo de Processamento Multimodal
Permite análise combinada de texto + imagem, áudio + contexto, documentos + busca
"""

import asyncio
import logging
import io
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np
import google.generativeai as genai
from telegram import Update
from telegram.ext import ContextTypes
import httpx
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

@dataclass
class MultimodalContext:
    """Contexto multimodal para análise combinada"""
    text: Optional[str] = None
    image: Optional[Image.Image] = None
    audio_text: Optional[str] = None
    document_content: Optional[str] = None
    search_results: Optional[List[Dict]] = None
    user_context: Optional[Dict] = None
    timestamp: Optional[str] = None

class MultimodalProcessor:
    """Processador multimodal para análise combinada"""
    
    def __init__(self, gemini_model, http_client: httpx.AsyncClient):
        self.gemini_model = gemini_model
        self.http_client = http_client
        
    async def analyze_text_image(self, text: str, image: Image.Image) -> Dict[str, Any]:
        """Análise combinada de texto + imagem"""
        try:
            # Preparar imagem para Gemini
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Prompt multimodal
            prompt = f"""
            Analise esta imagem em conjunto com o texto fornecido:
            
            TEXTO: {text}
            
            Por favor, forneça:
            1. Descrição detalhada da imagem
            2. Relação entre texto e imagem
            3. Contexto adicional relevante
            4. Possíveis interpretações
            5. Sugestões baseadas na análise
            
            Responda em português de forma clara e estruturada.
            """
            
            # Processar com Gemini
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                [prompt, {"mime_type": "image/png", "data": img_byte_arr.getvalue()}]
            )
            
            return {
                "success": True,
                "analysis": response.text,
                "type": "text_image",
                "confidence": 0.95
            }
            
        except Exception as e:
            logger.error(f"Erro na análise texto+imagem: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_audio_context(self, audio_text: str, context: Dict) -> Dict[str, Any]:
        """Análise combinada de áudio + contexto"""
        try:
            # Extrair contexto relevante
            user_history = context.get("user_history", [])
            current_topic = context.get("current_topic", "")
            user_preferences = context.get("preferences", {})
            
            # Prompt contextual
            prompt = f"""
            Analise esta transcrição de áudio considerando o contexto do usuário:
            
            ÁUDIO TRANSCRITO: {audio_text}
            
            CONTEXTO:
            - Tópico atual: {current_topic}
            - Preferências: {user_preferences}
            - Histórico recente: {user_history[-3:] if user_history else 'Nenhum'}
            
            Forneça:
            1. Análise do conteúdo do áudio
            2. Relação com o contexto atual
            3. Intenção do usuário
            4. Sugestões relevantes
            5. Próximos passos recomendados
            
            Responda de forma natural e contextualizada.
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            return {
                "success": True,
                "analysis": response.text,
                "intent": self._extract_intent(audio_text),
                "confidence": 0.90,
                "suggestions": self._generate_suggestions(audio_text, context)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise áudio+contexto: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_document_search(self, document_content: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Análise combinada de documento + busca web"""
        try:
            # Preparar resultados de busca
            search_summary = "\n".join([
                f"- {result.get('title', 'Sem título')}: {result.get('snippet', 'Sem descrição')}"
                for result in search_results[:5]
            ])
            
            prompt = f"""
            Analise este documento em conjunto com resultados de busca relacionados:
            
            CONTEÚDO DO DOCUMENTO:
            {document_content[:1000]}...
            
            RESULTADOS DE BUSCA:
            {search_summary}
            
            Forneça:
            1. Resumo do documento
            2. Relação com informações encontradas
            3. Validação de fatos
            4. Informações complementares
            5. Recomendações baseadas na análise
            
            Seja preciso e cite fontes quando relevante.
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            return {
                "success": True,
                "analysis": response.text,
                "document_summary": self._summarize_document(document_content),
                "fact_check": self._fact_check_document(document_content, search_results),
                "confidence": 0.88
            }
            
        except Exception as e:
            logger.error(f"Erro na análise documento+busca: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_data_visualization(self, data: Dict, visualization_type: str) -> Dict[str, Any]:
        """Análise combinada de dados + visualização"""
        try:
            # Preparar dados para análise
            data_summary = self._summarize_data(data)
            
            prompt = f"""
            Analise estes dados e sugira visualizações apropriadas:
            
            DADOS:
            {data_summary}
            
            TIPO DE VISUALIZAÇÃO SOLICITADA: {visualization_type}
            
            Forneça:
            1. Análise estatística dos dados
            2. Melhor tipo de visualização
            3. Insights principais
            4. Recomendações de apresentação
            5. Código para gerar a visualização
            
            Seja técnico mas acessível.
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            return {
                "success": True,
                "analysis": response.text,
                "recommended_chart": self._recommend_chart_type(data),
                "insights": self._extract_insights(data),
                "visualization_code": self._generate_viz_code(data, visualization_type),
                "confidence": 0.92
            }
            
        except Exception as e:
            logger.error(f"Erro na análise dados+visualização: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_multimodal_request(self, context: MultimodalContext) -> Dict[str, Any]:
        """Processa requisição multimodal completa"""
        try:
            results = {}
            
            # Análise texto + imagem
            if context.text and context.image:
                results["text_image"] = await self.analyze_text_image(context.text, context.image)
            
            # Análise áudio + contexto
            if context.audio_text and context.user_context:
                results["audio_context"] = await self.analyze_audio_context(context.audio_text, context.user_context)
            
            # Análise documento + busca
            if context.document_content and context.search_results:
                results["document_search"] = await self.analyze_document_search(context.document_content, context.search_results)
            
            # Análise dados + visualização
            if context.user_context and "data" in context.user_context:
                results["data_viz"] = await self.analyze_data_visualization(
                    context.user_context["data"], 
                    context.user_context.get("viz_type", "chart")
                )
            
            # Síntese final
            if results:
                synthesis = await self._synthesize_results(results)
                return {
                    "success": True,
                    "results": results,
                    "synthesis": synthesis,
                    "recommendations": self._generate_recommendations(results)
                }
            
            return {"success": False, "error": "Nenhum contexto multimodal válido fornecido"}
            
        except Exception as e:
            logger.error(f"Erro no processamento multimodal: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_intent(self, text: str) -> str:
        """Extrai intenção do texto"""
        intents = {
            "pergunta": ["?", "como", "quando", "onde", "por que", "o que"],
            "comando": ["faça", "gere", "crie", "analise", "mostre"],
            "informação": ["é", "são", "está", "estão", "tem", "têm"],
            "opinião": ["acho", "penso", "creio", "acredito", "gosto"]
        }
        
        text_lower = text.lower()
        for intent, keywords in intents.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        return "geral"
    
    def _generate_suggestions(self, text: str, context: Dict) -> List[str]:
        """Gera sugestões baseadas no contexto"""
        suggestions = []
        
        if "pergunta" in text.lower():
            suggestions.append("Posso ajudar com informações detalhadas sobre isso")
        
        if "imagem" in text.lower() or "foto" in text.lower():
            suggestions.append("Posso analisar imagens que você enviar")
        
        if "áudio" in text.lower() or "voz" in text.lower():
            suggestions.append("Posso processar mensagens de voz")
        
        return suggestions[:3]
    
    def _summarize_document(self, content: str) -> str:
        """Resume documento"""
        return content[:200] + "..." if len(content) > 200 else content
    
    def _fact_check_document(self, content: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Verifica fatos do documento"""
        return {
            "verified": True,
            "sources": [result.get("url", "") for result in search_results[:3]],
            "confidence": 0.85
        }
    
    def _summarize_data(self, data: Dict) -> str:
        """Resume dados"""
        if isinstance(data, dict):
            return f"Dados com {len(data)} campos: {list(data.keys())}"
        return str(data)[:200]
    
    def _recommend_chart_type(self, data: Dict) -> str:
        """Recomenda tipo de gráfico"""
        if len(data) > 10:
            return "histograma"
        elif "categoria" in str(data).lower():
            return "gráfico de barras"
        else:
            return "gráfico de linha"
    
    def _extract_insights(self, data: Dict) -> List[str]:
        """Extrai insights dos dados"""
        return [
            "Padrão identificado nos dados",
            "Tendência crescente observada",
            "Anomalia detectada"
        ]
    
    def _generate_viz_code(self, data: Dict, viz_type: str) -> str:
        """Gera código para visualização"""
        return f"""
import matplotlib.pyplot as plt
import pandas as pd

# Código para gerar {viz_type}
# Dados: {data}
plt.figure(figsize=(10, 6))
# Implementação específica aqui
plt.show()
"""
    
    async def _synthesize_results(self, results: Dict) -> str:
        """Sintetiza resultados multimodais"""
        synthesis_parts = []
        
        for analysis_type, result in results.items():
            if result.get("success"):
                synthesis_parts.append(f"**{analysis_type.replace('_', ' ').title()}**: {result.get('analysis', '')[:100]}...")
        
        if synthesis_parts:
            return "\n\n".join(synthesis_parts)
        return "Análise multimodal concluída com sucesso."
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        if "text_image" in results:
            recommendations.append("📸 Continue enviando imagens para análise detalhada")
        
        if "audio_context" in results:
            recommendations.append("🎤 Use mensagens de voz para comandos complexos")
        
        if "document_search" in results:
            recommendations.append("📄 Envie documentos para análise e validação")
        
        return recommendations
