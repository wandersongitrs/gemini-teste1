# -*- coding: utf-8 -*-
"""
Interface de Usuário para Geração de Imagens com Face Swapping
Sistema de botões exclusivos para funcionalidades avançadas
"""

import logging
from typing import Dict, List, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from face_swapper_advanced import face_swapper
from scenario_generator import scenario_generator

logger = logging.getLogger(__name__)

class ImageGenerationUI:
    """Interface de usuário para geração de imagens"""
    
    def __init__(self):
        self.user_sessions = {}  # Armazenar sessões de usuário
        self.face_swapper = face_swapper
        self.scenario_generator = scenario_generator
    
    def get_main_image_menu(self) -> Dict[str, Any]:
        """Menu principal de geração de imagens"""
        return {
            "title": "🎭 **Geração Avançada de Imagens**",
            "description": "Escolha uma funcionalidade:",
            "buttons": [
                ["🔄 Face Swapping", "face_swap_menu"],
                ["🎭 Rosto + Cenário", "face_scenario_menu"],
                ["🎨 Estilos Artísticos", "artistic_styles_menu"],
                ["🌅 Templates de Cenários", "scenario_templates_menu"],
                ["📸 Análise Facial", "face_analysis_menu"],
                ["⚙️ Configurações", "image_settings_menu"],
                ["🔙 Voltar ao Menu Principal", "main_menu"]
            ]
        }
    
    def get_face_swap_menu(self) -> Dict[str, Any]:
        """Menu de face swapping"""
        return {
            "title": "🔄 **Face Swapping Avançado**",
            "description": "Troque rostos entre imagens:",
            "buttons": [
                ["🔄 Trocar Rostos", "swap_faces"],
                ["🎯 Qualidade Ultra", "ultra_quality"],
                ["⚡ Processamento Rápido", "fast_processing"],
                ["📊 Análise de Qualidade", "quality_analysis"],
                ["🔙 Voltar", "image_main_menu"]
            ]
        }
    
    def get_face_scenario_menu(self) -> Dict[str, Any]:
        """Menu de rosto + cenário"""
        return {
            "title": "🎭 **Rosto + Cenário**",
            "description": "Coloque seu rosto em cenários incríveis:",
            "buttons": [
                ["🌅 Cenário Personalizado", "custom_scenario"],
                ["🎨 Estilo Realista", "realistic_style"],
                ["✨ Estilo Fantasia", "fantasy_style"],
                ["🚀 Estilo Cyberpunk", "cyberpunk_style"],
                ["📸 Estilo Vintage", "vintage_style"],
                ["🔙 Voltar", "image_main_menu"]
            ]
        }
    
    def get_scenario_templates_menu(self) -> Dict[str, Any]:
        """Menu de templates de cenários"""
        templates = self.scenario_generator.get_available_templates()
        
        buttons = []
        for i in range(0, len(templates), 2):
            row = []
            for j in range(2):
                if i + j < len(templates):
                    template = templates[i + j]
                    emoji = self._get_template_emoji(template)
                    row.append([f"{emoji} {template.title()}", f"template_{template}"])
            buttons.extend(row)
        
        buttons.append([["🔙 Voltar", "image_main_menu"]])
        
        return {
            "title": "🌅 **Templates de Cenários**",
            "description": "Escolha um cenário pré-definido:",
            "buttons": buttons
        }
    
    def get_artistic_styles_menu(self) -> Dict[str, Any]:
        """Menu de estilos artísticos"""
        return {
            "title": "🎨 **Estilos Artísticos**",
            "description": "Aplique estilos artísticos ao seu rosto:",
            "buttons": [
                ["🎭 Estilo Anime", "anime_style"],
                ["🖼️ Estilo Pintura", "painting_style"],
                ["📸 Estilo Fotográfico", "photographic_style"],
                ["🎪 Estilo Cartoon", "cartoon_style"],
                ["🌟 Estilo Surrealista", "surreal_style"],
                ["🔙 Voltar", "image_main_menu"]
            ]
        }
    
    def _get_template_emoji(self, template: str) -> str:
        """Retorna emoji para template"""
        emoji_map = {
            'praia': '🏖️',
            'escritorio': '🏢',
            'floresta': '🌲',
            'restaurante': '🍽️',
            'espaço': '🌌',
            'montanha': '⛰️',
            'cidade': '🏙️',
            'castelo': '🏰',
            'laboratorio': '🔬',
            'biblioteca': '📚'
        }
        return emoji_map.get(template, '🌅')
    
    async def handle_image_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handler para callbacks de geração de imagens"""
        try:
            callback_data = query.data
            logger.info(f"Processando callback: {callback_data}")
            
            if callback_data == "image_main_menu":
                await self._show_menu(query, context, self.get_main_image_menu())
            
            elif callback_data == "face_swap_menu":
                await self._show_menu(query, context, self.get_face_swap_menu())
            
            elif callback_data == "face_scenario_menu":
                await self._show_menu(query, context, self.get_face_scenario_menu())
            
            elif callback_data == "scenario_templates_menu":
                await self._show_menu(query, context, self.get_scenario_templates_menu())
            
            elif callback_data == "artistic_styles_menu":
                await self._show_menu(query, context, self.get_artistic_styles_menu())
            
            elif callback_data == "swap_faces":
                logger.info("Executando swap_faces")
                await self._show_swap_faces_instructions(query, context)
            
            elif callback_data == "custom_scenario":
                await self._show_custom_scenario_instructions(query, context)
            
            elif callback_data.startswith("template_"):
                template_name = callback_data.replace("template_", "")
                await self._show_template_instructions(query, context, template_name)
            
            elif callback_data == "ultra_quality":
                await self._show_quality_options(query, context, "ultra")
            
            elif callback_data == "fast_processing":
                await self._show_quality_options(query, context, "fast")
            
            elif callback_data == "quality_analysis":
                await self._show_quality_analysis(query, context)
            
            elif callback_data == "try_swap_faces":
                await self._show_try_swap_faces(query, context)
            
            elif callback_data == "swap_examples":
                await self._show_swap_examples(query, context)
            
            elif callback_data == "choose_style":
                await self._show_choose_style(query, context)
            
            elif callback_data.startswith("use_template_"):
                template_name = callback_data.replace("use_template_", "")
                await self._use_template(query, context, template_name)
            
            elif callback_data.startswith("customize_template_"):
                template_name = callback_data.replace("customize_template_", "")
                await self._customize_template(query, context, template_name)
            
            elif callback_data.startswith("confirm_"):
                quality_type = callback_data.replace("confirm_", "")
                await self._confirm_quality(query, context, quality_type)
            
            elif callback_data.startswith("realistic_style"):
                await self._apply_style(query, context, "realistic")
            
            elif callback_data.startswith("fantasy_style"):
                await self._apply_style(query, context, "fantasy")
            
            elif callback_data.startswith("cyberpunk_style"):
                await self._apply_style(query, context, "cyberpunk")
            
            elif callback_data.startswith("vintage_style"):
                await self._apply_style(query, context, "vintage")
            
            elif callback_data.startswith("anime_style"):
                await self._apply_style(query, context, "anime")
            
            elif callback_data.startswith("painting_style"):
                await self._apply_style(query, context, "painting")
            
            elif callback_data.startswith("photographic_style"):
                await self._apply_style(query, context, "photographic")
            
            elif callback_data.startswith("cartoon_style"):
                await self._apply_style(query, context, "cartoon")
            
            elif callback_data.startswith("surreal_style"):
                await self._apply_style(query, context, "surreal")
            
            else:
                logger.warning(f"Callback não tratado: {callback_data}")
                await query.answer(f"Funcionalidade '{callback_data}' em desenvolvimento!")
                
        except Exception as e:
            logger.error(f"Erro no callback de imagem: {e}")
            await query.answer("❌ Erro ao processar comando!")
    
    async def _show_menu(self, query, context: ContextTypes.DEFAULT_TYPE, menu_data: Dict):
        """Mostra menu específico"""
        keyboard = []
        for button_row in menu_data["buttons"]:
            if isinstance(button_row[0], list):
                # Múltiplos botões na linha
                keyboard.append([InlineKeyboardButton(btn[0], callback_data=btn[1]) for btn in button_row])
            else:
                # Botão único na linha
                keyboard.append([InlineKeyboardButton(button_row[0], callback_data=button_row[1])])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"{menu_data['title']}\n\n{menu_data['description']}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_swap_faces_instructions(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Mostra instruções para face swapping"""
        instructions = """
🔄 **Como Trocar Rostos:**

**Passo 1:** Envie a primeira imagem (rosto fonte)
**Passo 2:** Responda com `/trocar_rosto`
**Passo 3:** Envie a segunda imagem (rosto destino)
**Passo 4:** Aguarde o processamento

**Dicas:**
• Use fotos com boa iluminação
• Rostos devem estar bem visíveis
• Evite ângulos muito extremos
• Qualidade mínima: 512x512 pixels

**Comandos Rápidos:**
• `/trocar_rosto` - Troca básica
• `/trocar_rosto_ultra` - Qualidade máxima
• `/trocar_rosto_rapido` - Processamento rápido
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Tentar Agora", callback_data="try_swap_faces")],
            [InlineKeyboardButton("📊 Ver Exemplos", callback_data="swap_examples")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_custom_scenario_instructions(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Mostra instruções para cenário personalizado"""
        instructions = """
🎭 **Rosto + Cenário Personalizado:**

**Como usar:**
1. Envie uma foto com rosto
2. Use `/rosto_cenario <descrição>`
3. Aguarde a geração

**Exemplos:**
• `/rosto_cenario praia tropical com coqueiros`
• `/rosto_cenario escritório moderno com vista da cidade`
• `/rosto_cenario floresta mágica com fadas`

**Estilos disponíveis:**
• `realistic` - Realismo fotográfico
• `fantasy` - Estilo fantasia
• `cyberpunk` - Futurista
• `vintage` - Retrô
• `artistic` - Artístico
        """
        
        keyboard = [
            [InlineKeyboardButton("🎨 Escolher Estilo", callback_data="choose_style")],
            [InlineKeyboardButton("🌅 Ver Templates", callback_data="scenario_templates_menu")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_scenario_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_template_instructions(self, query, context: ContextTypes.DEFAULT_TYPE, template_name: str):
        """Mostra instruções para template específico"""
        template_info = self.scenario_generator.get_template_info(template_name)
        
        if not template_info:
            await query.answer("Template não encontrado!")
            return
        
        emoji = self._get_template_emoji(template_name)
        
        instructions = f"""
{emoji} **Template: {template_name.title()}**

**Descrição:** {template_info['prompt']}
**Estilo:** {template_info['style']}
**Qualidade:** {template_info['guidance_scale']}/10

**Como usar:**
1. Envie uma foto com rosto
2. Use `/template {template_name}`
3. Aguarde o processamento

**Resultado esperado:**
Cenário {template_name} com seu rosto integrado
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{emoji} Usar Template", callback_data=f"use_template_{template_name}")],
            [InlineKeyboardButton("🎨 Personalizar", callback_data=f"customize_template_{template_name}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="scenario_templates_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_quality_options(self, query, context: ContextTypes.DEFAULT_TYPE, quality_type: str):
        """Mostra opções de qualidade"""
        if quality_type == "ultra":
            instructions = """
⚡ **Qualidade Ultra:**

**Características:**
• Processamento mais lento (2-3 minutos)
• Qualidade máxima de face swap
• Blending perfeito entre rostos
• Detalhes preservados

**Recomendado para:**
• Fotos profissionais
• Resultados de alta qualidade
• Quando tempo não é crítico
            """
        else:  # fast
            instructions = """
🚀 **Processamento Rápido:**

**Características:**
• Processamento rápido (30-60 segundos)
• Qualidade boa
• Ideal para testes
• Menos recursos utilizados

**Recomendado para:**
• Testes rápidos
• Quando tempo é crítico
• Múltiplas tentativas
            """
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{quality_type}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_quality_analysis(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Mostra análise de qualidade"""
        instructions = """
📊 **Análise de Qualidade do Face Swap:**

**Fatores Analisados:**
• Detecção de rostos (0-1.0)
• Alinhamento facial (0-1.0)
• Iluminação (0-1.0)
• Resolução da imagem (0-1.0)
• Pose do rosto (0-1.0)

**Score Final:**
• 0.9-1.0: Excelente ✅
• 0.8-0.9: Muito bom ✅
• 0.7-0.8: Bom ⚠️
• 0.6-0.7: Regular ⚠️
• <0.6: Baixo ❌

**Como melhorar:**
• Use fotos com boa iluminação
• Certifique-se de que o rosto está bem visível
• Evite ângulos muito extremos
• Use resolução mínima de 512x512 pixels
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 Analisar Imagem", callback_data="analyze_current_image")],
            [InlineKeyboardButton("📊 Ver Histórico", callback_data="view_quality_history")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_try_swap_faces(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Inicia processo de face swap"""
        instructions = """
🔄 **Iniciando Face Swap:**

**Passo 1:** Envie a primeira imagem (rosto fonte)
**Passo 2:** Aguarde confirmação
**Passo 3:** Envie a segunda imagem (rosto destino)
**Passo 4:** Receba o resultado

**Dicas para melhor resultado:**
• Use fotos com boa iluminação
• Rostos devem estar bem visíveis
• Evite ângulos muito extremos
• Qualidade mínima: 512x512 pixels

**Status:** Aguardando primeira imagem...
        """
        
        keyboard = [
            [InlineKeyboardButton("📸 Enviar Primeira Imagem", callback_data="send_first_image")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_swap")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_swap_examples(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Mostra exemplos de face swap"""
        instructions = """
📊 **Exemplos de Face Swap:**

**Exemplo 1: Troca Básica**
• Rosto A: Foto frontal, boa iluminação
• Rosto B: Foto frontal, boa iluminação
• Resultado: Troca perfeita ✅

**Exemplo 2: Qualidade Ultra**
• Rosto A: Foto profissional, alta resolução
• Rosto B: Foto profissional, alta resolução
• Resultado: Qualidade máxima ⚡

**Exemplo 3: Processamento Rápido**
• Rosto A: Foto simples, resolução média
• Rosto B: Foto simples, resolução média
• Resultado: Processamento rápido 🚀

**Dicas dos Exemplos:**
• Fotos frontais funcionam melhor
• Boa iluminação é essencial
• Resolução alta melhora qualidade
• Evite fotos com óculos ou acessórios
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Tentar Agora", callback_data="try_swap_faces")],
            [InlineKeyboardButton("📊 Análise de Qualidade", callback_data="quality_analysis")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_choose_style(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Mostra opções de estilo"""
        instructions = """
🎨 **Escolher Estilo:**

**Estilos Disponíveis:**
• **Realista** - Realismo fotográfico
• **Fantasia** - Estilo mágico e etéreo
• **Cyberpunk** - Futurista com neon
• **Vintage** - Estilo retrô e nostálgico
• **Artístico** - Pintura clássica

**Como usar:**
1. Escolha o estilo desejado
2. Envie uma foto com rosto
3. Receba resultado com estilo aplicado

**Recomendações:**
• Realista: Para fotos profissionais
• Fantasia: Para arte conceitual
• Cyberpunk: Para temas futuristas
• Vintage: Para nostalgia
• Artístico: Para pinturas
        """
        
        keyboard = [
            [InlineKeyboardButton("📸 Realista", callback_data="realistic_style")],
            [InlineKeyboardButton("✨ Fantasia", callback_data="fantasy_style")],
            [InlineKeyboardButton("🚀 Cyberpunk", callback_data="cyberpunk_style")],
            [InlineKeyboardButton("📸 Vintage", callback_data="vintage_style")],
            [InlineKeyboardButton("🎨 Artístico", callback_data="artistic_style")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_scenario_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _use_template(self, query, context: ContextTypes.DEFAULT_TYPE, template_name: str):
        """Usa template específico"""
        template_info = self.scenario_generator.get_template_info(template_name)
        
        if not template_info:
            await query.answer("Template não encontrado!")
            return
        
        emoji = self._get_template_emoji(template_name)
        
        instructions = f"""
{emoji} **Usando Template: {template_name.title()}**

**Template Aplicado:**
• **Descrição:** {template_info['prompt']}
• **Estilo:** {template_info['style']}
• **Qualidade:** {template_info['guidance_scale']}/10

**Como usar:**
1. Envie uma foto com rosto
2. O template será aplicado automaticamente
3. Receba resultado com seu rosto no cenário

**Status:** Aguardando foto com rosto...
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{emoji} Aplicar Template", callback_data=f"apply_template_{template_name}")],
            [InlineKeyboardButton("🎨 Personalizar", callback_data=f"customize_template_{template_name}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="scenario_templates_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _customize_template(self, query, context: ContextTypes.DEFAULT_TYPE, template_name: str):
        """Personaliza template"""
        template_info = self.scenario_generator.get_template_info(template_name)
        
        if not template_info:
            await query.answer("Template não encontrado!")
            return
        
        emoji = self._get_template_emoji(template_name)
        
        instructions = f"""
🎨 **Personalizar Template: {template_name.title()}**

**Template Base:**
• **Descrição:** {template_info['prompt']}
• **Estilo:** {template_info['style']}

**Personalizações Disponíveis:**
• **Iluminação:** Manhã, Tarde, Noite
• **Clima:** Ensolarado, Nublado, Chuvoso
• **Cores:** Quentes, Frias, Neutras
• **Atmosfera:** Alegre, Melancólica, Dramática

**Como personalizar:**
1. Escolha as opções desejadas
2. Envie uma foto com rosto
3. Receba resultado personalizado
        """
        
        keyboard = [
            [InlineKeyboardButton("☀️ Iluminação", callback_data=f"customize_lighting_{template_name}")],
            [InlineKeyboardButton("🌤️ Clima", callback_data=f"customize_weather_{template_name}")],
            [InlineKeyboardButton("🎨 Cores", callback_data=f"customize_colors_{template_name}")],
            [InlineKeyboardButton("🎭 Atmosfera", callback_data=f"customize_mood_{template_name}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data=f"template_{template_name}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _confirm_quality(self, query, context: ContextTypes.DEFAULT_TYPE, quality_type: str):
        """Confirma qualidade selecionada"""
        if quality_type == "ultra":
            instructions = """
⚡ **Qualidade Ultra Confirmada!**

**Configurações Aplicadas:**
• Processamento: Ultra (2-3 minutos)
• Qualidade: Máxima
• Blending: Perfeito
• Detalhes: Preservados

**Próximos passos:**
1. Envie a primeira imagem (rosto fonte)
2. Aguarde confirmação
3. Envie a segunda imagem (rosto destino)
4. Receba resultado com qualidade ultra

**Status:** Aguardando primeira imagem...
            """
        else:  # fast
            instructions = """
🚀 **Processamento Rápido Confirmado!**

**Configurações Aplicadas:**
• Processamento: Rápido (30-60 segundos)
• Qualidade: Boa
• Recursos: Otimizados
• Ideal para: Testes rápidos

**Próximos passos:**
1. Envie a primeira imagem (rosto fonte)
2. Aguarde confirmação
3. Envie a segunda imagem (rosto destino)
4. Receba resultado rapidamente

**Status:** Aguardando primeira imagem...
            """
        
        keyboard = [
            [InlineKeyboardButton("📸 Enviar Primeira Imagem", callback_data="send_first_image")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_swap")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _apply_style(self, query, context: ContextTypes.DEFAULT_TYPE, style: str):
        """Aplica estilo específico"""
        style_info = {
            "realistic": "📸 Realismo fotográfico com alta qualidade",
            "fantasy": "✨ Estilo mágico e etéreo",
            "cyberpunk": "🚀 Futurista com neon e tecnologia",
            "vintage": "📸 Estilo retrô e nostálgico",
            "anime": "🎭 Estilo anime/mangá",
            "painting": "🖼️ Estilo pintura clássica",
            "photographic": "📸 Estilo fotográfico profissional",
            "cartoon": "🎪 Desenho animado",
            "surreal": "🌟 Estilo surrealista"
        }
        
        description = style_info.get(style, f"Estilo {style}")
        
        instructions = f"""
🎨 **Estilo {style.title()} Aplicado!**

**Descrição:** {description}

**Como usar:**
1. Envie uma foto com rosto
2. O estilo será aplicado automaticamente
3. Receba resultado com estilo {style}

**Status:** Aguardando foto com rosto...
        """
        
        keyboard = [
            [InlineKeyboardButton(f"🎨 Aplicar {style.title()}", callback_data=f"apply_style_{style}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="artistic_styles_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Instância global
image_generation_ui = ImageGenerationUI()
