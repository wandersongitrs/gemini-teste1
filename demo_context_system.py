# -*- coding: utf-8 -*-
"""
Demonstração do Sistema de Contexto Avançado
============================================

Este script demonstra as funcionalidades do sistema de contexto multimodal,
estados de conversa e personalização de personalidade.

Funcionalidades demonstradas:
- Contexto multimodal persistente
- Estados de conversa inteligentes
- Personalização de personalidade
- Integração com sistema de persistência
- Exemplos práticos de uso

Características:
- Simulação de interações multimodais
- Demonstração de estados de conversa
- Teste de personalidades diferentes
- Exemplos de contexto enriquecido
"""

import os
import logging
from datetime import datetime
from typing import Dict, List

# Importar módulos do projeto
from conversation_persistence import ConversationManager, ChatMessage
from advanced_context_system import (
    AdvancedContextSystem, ConversationState, get_advanced_context_system
)

logger = logging.getLogger('demo_context')

class ContextSystemDemo:
    """Demonstração do sistema de contexto avançado"""
    
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.context_system = get_advanced_context_system(self.conversation_manager)
        
        # Usuário de demonstração
        self.demo_user_id = "demo_user_123"
        
        logger.info("Demonstração do sistema de contexto inicializada")
    
    def demo_multimodal_context(self):
        """Demonstra contexto multimodal"""
        print("\n" + "="*60)
        print("🧠 DEMONSTRAÇÃO: CONTEXTO MULTIMODAL")
        print("="*60)
        
        # Simular análise de imagem
        print("\n📸 Simulando análise de imagem...")
        image_description = "Uma paisagem montanhosa com um lago cristalino ao centro, cercada por árvores verdes e um céu azul com nuvens brancas"
        
        session_id = f"demo_session_{int(datetime.now().timestamp())}"
        conversation_id = self.conversation_manager.get_or_create_conversation(self.demo_user_id, session_id)
        
        self.context_system.handle_multimodal_interaction(
            self.demo_user_id, "image", image_description, conversation_id
        )
        
        print(f"✅ Contexto de imagem salvo: {image_description[:50]}...")
        
        # Simular transcrição de áudio
        print("\n🎤 Simulando transcrição de áudio...")
        audio_transcription = "Olá, estou falando sobre as montanhas e como elas são importantes para o meio ambiente"
        
        self.context_system.handle_multimodal_interaction(
            self.demo_user_id, "audio", audio_transcription, conversation_id
        )
        
        print(f"✅ Contexto de áudio salvo: {audio_transcription[:50]}...")
        
        # Simular análise de vídeo
        print("\n🎬 Simulando análise de vídeo...")
        video_analysis = "Vídeo mostra uma caminhada pela montanha, com vistas panorâmicas e explicações sobre geologia"
        
        self.context_system.handle_multimodal_interaction(
            self.demo_user_id, "video", video_analysis, conversation_id
        )
        
        print(f"✅ Contexto de vídeo salvo: {video_analysis[:50]}...")
        
        # Demonstrar enriquecimento de mensagem
        print("\n💬 Demonstração de enriquecimento de mensagem...")
        user_message = "Crie uma história sobre isso"
        
        enriched_message = self.context_system.enrich_message_with_context(self.demo_user_id, user_message)
        
        print(f"📝 Mensagem original: {user_message}")
        print(f"🧠 Mensagem enriquecida:")
        print(f"   {enriched_message}")
        
        return enriched_message
    
    def demo_conversation_states(self):
        """Demonstra estados de conversa"""
        print("\n" + "="*60)
        print("🎛️ DEMONSTRAÇÃO: ESTADOS DE CONVERSA")
        print("="*60)
        
        # Estado inicial
        current_state = self.context_system.get_conversation_state(self.demo_user_id)
        print(f"\n📍 Estado inicial: {current_state.value}")
        
        # Simular comando /clonarvoz
        print("\n🎤 Simulando comando /clonarvoz...")
        self.context_system.set_conversation_state(self.demo_user_id, ConversationState.AGUARDANDO_AUDIO_CLONE)
        
        current_state = self.context_system.get_conversation_state(self.demo_user_id)
        print(f"📍 Estado após /clonarvoz: {current_state.value}")
        
        # Simular envio de áudio
        print("\n📤 Simulando envio de áudio...")
        if self.context_system.is_in_state(self.demo_user_id, ConversationState.AGUARDANDO_AUDIO_CLONE):
            print("✅ Bot está aguardando áudio - comportamento correto!")
            
            # Processar áudio e voltar ao estado normal
            self.context_system.set_conversation_state(self.demo_user_id, ConversationState.CHAT_GERAL)
            print("🔄 Estado resetado para chat geral")
        
        # Simular comando /pesquisar
        print("\n🔍 Simulando comando /pesquisar...")
        self.context_system.set_conversation_state(self.demo_user_id, ConversationState.PESQUISANDO)
        
        current_state = self.context_system.get_conversation_state(self.demo_user_id)
        print(f"📍 Estado durante pesquisa: {current_state.value}")
        
        # Resetar estado
        self.context_system.set_conversation_state(self.demo_user_id, ConversationState.CHAT_GERAL)
        print("🔄 Estado resetado para chat geral")
    
    def demo_personality_system(self):
        """Demonstra sistema de personalidades"""
        print("\n" + "="*60)
        print("🎭 DEMONSTRAÇÃO: SISTEMA DE PERSONALIDADES")
        print("="*60)
        
        # Mostrar personalidades disponíveis
        available_personalities = self.context_system.get_available_personalities()
        
        print("\n🎭 Personalidades disponíveis:")
        for ptype, description in available_personalities.items():
            print(f"   • {ptype.title()}: {description}")
        
        # Testar diferentes personalidades
        personalities_to_test = ["cientista", "pirata", "artista", "professor"]
        
        for personality_type in personalities_to_test:
            print(f"\n🎭 Testando personalidade: {personality_type.title()}")
            
            # Definir personalidade
            self.context_system.set_user_personality(self.demo_user_id, personality_type)
            
            # Obter instrução do sistema
            system_instruction = self.context_system.get_system_instruction(self.demo_user_id)
            
            print(f"   📝 Instrução do sistema: {system_instruction[:100]}...")
            
            # Simular resposta com personalidade
            test_message = "Explique o que é inteligência artificial"
            enriched_message = self.context_system.enrich_message_with_context(self.demo_user_id, test_message)
            
            print(f"   💬 Mensagem enriquecida: {enriched_message[:100]}...")
        
        # Mostrar personalidade atual
        current_personality = self.context_system.get_user_personality(self.demo_user_id)
        print(f"\n🎭 Personalidade atual: {current_personality.personality_type.title()}")
    
    def demo_context_persistence(self):
        """Demonstra persistência de contexto"""
        print("\n" + "="*60)
        print("💾 DEMONSTRAÇÃO: PERSISTÊNCIA DE CONTEXTO")
        print("="*60)
        
        # Simular múltiplas interações
        interactions = [
            ("image", "Foto de um gato dormindo no sofá"),
            ("audio", "Áudio explicando sobre cuidados com gatos"),
            ("video", "Vídeo mostrando brincadeiras com gatos"),
            ("research", "Pesquisa sobre comportamento felino")
        ]
        
        session_id = f"persistence_demo_{int(datetime.now().timestamp())}"
        conversation_id = self.conversation_manager.get_or_create_conversation(self.demo_user_id, session_id)
        
        print("\n📝 Simulando múltiplas interações...")
        for interaction_type, content in interactions:
            self.context_system.handle_multimodal_interaction(
                self.demo_user_id, interaction_type, content, conversation_id
            )
            print(f"   ✅ {interaction_type.title()}: {content[:30]}...")
        
        # Demonstrar recuperação de contexto
        print("\n🔄 Demonstração de recuperação de contexto...")
        
        # Simular "reinicialização" do sistema
        print("   🔄 Simulando reinicialização do sistema...")
        
        # Recriar sistema (simulando restart)
        new_context_system = get_advanced_context_system(self.conversation_manager)
        
        # Verificar se contexto foi recuperado
        recovered_context = new_context_system.context_manager.get_context_for_response(self.demo_user_id)
        
        if recovered_context:
            print("   ✅ Contexto recuperado com sucesso!")
            print(f"   📄 Contexto: {recovered_context[:100]}...")
        else:
            print("   ❌ Contexto não foi recuperado")
        
        # Demonstrar limpeza de contexto
        print("\n🧹 Demonstração de limpeza de contexto...")
        self.context_system.clear_user_context(self.demo_user_id)
        
        cleared_context = self.context_system.context_manager.get_context_for_response(self.demo_user_id)
        
        if not cleared_context:
            print("   ✅ Contexto limpo com sucesso!")
        else:
            print("   ❌ Contexto não foi limpo")
    
    def demo_integrated_workflow(self):
        """Demonstra fluxo integrado completo"""
        print("\n" + "="*60)
        print("🔄 DEMONSTRAÇÃO: FLUXO INTEGRADO COMPLETO")
        print("="*60)
        
        # Cenário: Usuário envia imagem, depois pede história
        print("\n📖 Cenário: Usuário envia imagem e pede história")
        
        # 1. Usuário envia imagem
        print("\n1️⃣ Usuário envia imagem...")
        image_description = "Uma floresta mágica com árvores altas, luzes douradas entre as folhas e um caminho de pedras brilhantes"
        
        session_id = f"workflow_demo_{int(datetime.now().timestamp())}"
        conversation_id = self.conversation_manager.get_or_create_conversation(self.demo_user_id, session_id)
        
        self.context_system.handle_multimodal_interaction(
            self.demo_user_id, "image", image_description, conversation_id
        )
        print(f"   ✅ Imagem analisada: {image_description[:50]}...")
        
        # 2. Usuário pede história
        print("\n2️⃣ Usuário pede: 'Crie uma história sobre isso'")
        user_message = "Crie uma história sobre isso"
        
        # 3. Sistema enriquece mensagem com contexto
        enriched_message = self.context_system.enrich_message_with_context(self.demo_user_id, user_message)
        print(f"   🧠 Mensagem enriquecida:")
        print(f"      {enriched_message}")
        
        # 4. Sistema responde com contexto
        print("\n3️⃣ Sistema responde com contexto da imagem...")
        print("   📝 Resposta simulada:")
        print("   'Baseado na imagem da floresta mágica que você enviou, aqui está uma história...'")
        
        # 5. Usuário muda de personalidade
        print("\n4️⃣ Usuário muda personalidade para 'pirata'...")
        self.context_system.set_user_personality(self.demo_user_id, "pirata")
        
        # 6. Usuário pede mais detalhes
        print("\n5️⃣ Usuário pede: 'Adicione mais aventura'")
        adventure_message = "Adicione mais aventura"
        
        enriched_adventure = self.context_system.enrich_message_with_context(self.demo_user_id, adventure_message)
        print(f"   🧠 Mensagem enriquecida:")
        print(f"      {enriched_adventure}")
        
        # 7. Sistema responde com personalidade de pirata
        print("\n6️⃣ Sistema responde como pirata...")
        print("   📝 Resposta simulada:")
        print("   'Ahoy! Vamos adicionar tesouros escondidos e batalhas épicas nesta aventura...'")
        
        print("\n✅ Fluxo integrado demonstrado com sucesso!")
    
    def run_complete_demo(self):
        """Executa demonstração completa"""
        print("🚀 INICIANDO DEMONSTRAÇÃO COMPLETA DO SISTEMA DE CONTEXTO AVANÇADO")
        print("="*80)
        
        try:
            # Executar todas as demonstrações
            self.demo_multimodal_context()
            self.demo_conversation_states()
            self.demo_personality_system()
            self.demo_context_persistence()
            self.demo_integrated_workflow()
            
            print("\n" + "="*80)
            print("🎉 DEMONSTRAÇÃO COMPLETA FINALIZADA COM SUCESSO!")
            print("="*80)
            
            print("\n📋 RESUMO DAS FUNCIONALIDADES DEMONSTRADAS:")
            print("   ✅ Contexto multimodal persistente")
            print("   ✅ Estados de conversa inteligentes")
            print("   ✅ Personalização de personalidade")
            print("   ✅ Persistência entre sessões")
            print("   ✅ Fluxo integrado completo")
            
            print("\n💡 PRÓXIMOS PASSOS:")
            print("   1. Execute o bot: python context_aware_bot.py")
            print("   2. Teste as funcionalidades no Telegram")
            print("   3. Configure personalidades com /personalidade")
            print("   4. Use /contexto para ver estado atual")
            print("   5. Experimente comandos como /clonarvoz")
            
        except Exception as e:
            logger.error(f"Erro na demonstração: {e}")
            print(f"\n❌ Erro na demonstração: {e}")

def main():
    """Função principal"""
    # Configurar logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("🎯 DEMONSTRAÇÃO DO SISTEMA DE CONTEXTO AVANÇADO")
    print("="*50)
    
    # Criar e executar demonstração
    demo = ContextSystemDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()
