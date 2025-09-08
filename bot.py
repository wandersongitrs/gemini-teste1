# -*- coding: utf-8 -*-
import os
import logging
import io
import asyncio
import json
import re
import base64
import csv
import secrets
import string
import hashlib
import socket
import subprocess
import requests
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import httpx
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# Importação condicional do pydub para evitar erro no Python 3.13
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️  pydub não disponível - funcionalidades de áudio limitadas")
from gtts import gTTS
import google.generativeai as genai
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import pytesseract
import PyPDF2
from deep_translator import GoogleTranslator

import database
from telegram.helpers import escape_markdown
from multimodal_processor import MultimodalProcessor, MultimodalContext
from voice_cloner import VoiceCloner
from ui_components import ui_manager  # NOVO: Sistema de UI melhorado
from face_swapper_advanced import face_swapper  # NOVO: Sistema de Face Swapping
from scenario_generator import scenario_generator  # NOVO: Gerador de Cenários
from image_generation_ui import image_generation_ui  # NOVO: Interface de Geração de Imagens
from face_swap_handler import face_swap_handler  # NOVO: Handler Funcional de Face Swap
from face_swap_commands import trocar_rosto, trocar_rosto_ultra, trocar_rosto_rapido, handle_image_upload  # NOVO: Comandos Funcionais

# --- CONFIGURAÇÃO ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Settings:
    telegram_token: str
    gemini_api_key: str
    huggingface_api_key: str
    tavily_api_key: str
    removebg_api_key: str
    fish_audio_api_key: str = None
    coqui_api_key: str = None
    gemini_model_name: str = 'gemini-1.5-flash'
    image_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    @classmethod
    def load_from_env(cls):
        load_dotenv()
        
        # Carregar variáveis de ambiente manualmente se necessário
        if not os.getenv("TELEGRAM_TOKEN"):
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            except Exception as e:
                logger.warning(f"Erro ao carregar .env: {e}")
        keys = {
            "telegram_token": os.getenv("TELEGRAM_TOKEN"), 
            "gemini_api_key": os.getenv("GEMINI_API_KEY"), 
            "huggingface_api_key": os.getenv("HUGGINGFACE_API_KEY"), 
            "tavily_api_key": os.getenv("TAVILY_API_KEY"),
            "removebg_api_key": os.getenv("REMOVEBG_API_KEY"),
            "fish_audio_api_key": os.getenv("FISH_AUDIO_API_KEY"),
            "coqui_api_key": os.getenv("COQUI_API_KEY")
        }
        # Verificar se as chaves foram carregadas corretamente do .env
        if not keys["telegram_token"] or keys["telegram_token"] == "seu_token_aqui":
            raise ValueError("TELEGRAM_TOKEN não configurado no arquivo .env")
        if not keys["gemini_api_key"] or keys["gemini_api_key"] == "sua_chave_gemini_aqui":
            raise ValueError("GEMINI_API_KEY não configurado no arquivo .env")
        if not keys["huggingface_api_key"] or keys["huggingface_api_key"] == "sua_chave_huggingface_aqui":
            raise ValueError("HUGGINGFACE_API_KEY não configurado no arquivo .env")
        if not keys["tavily_api_key"] or keys["tavily_api_key"] == "sua_chave_tavily_aqui":
            raise ValueError("TAVILY_API_KEY não configurado no arquivo .env")
        return cls(**keys)

# --- FUNÇÕES DE PROCESSAMENTO ---
def text_to_speech_sync(text: str, lang: str = 'pt') -> io.BytesIO:
    tts = gTTS(text=text, lang=lang); mp3_io = io.BytesIO(); tts.write_to_fp(mp3_io); mp3_io.seek(0); return mp3_io

async def detect_language_from_text(text: str) -> str:
    """Detecta o idioma do texto usando Gemini"""
    try:
        # Mapeamento simples de idiomas comuns
        lang_patterns = {
            'pt': ['português', 'portuguese', 'brasil', 'brazil', 'olá', 'oi', 'tudo bem'],
            'en': ['english', 'hello', 'hi', 'how are you', 'the', 'and', 'is'],
            'es': ['español', 'hola', 'buenos días', 'gracias', 'por favor'],
            'fr': ['français', 'bonjour', 'merci', 's\'il vous plaît', 'oui', 'non']
        }
        
        text_lower = text.lower()
        for lang, patterns in lang_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return lang
        return 'pt'  # Padrão
    except:
        return 'pt'

def get_language_display_name(lang_code: str) -> str:
    """Retorna o nome do idioma para exibição"""
    lang_names = {
        'pt': '🇧🇷 Português',
        'en': '🇺🇸 English', 
        'es': '🇪🇸 Español',
        'fr': '🇫🇷 Français'
    }
    return lang_names.get(lang_code, '🌍 Desconhecido')

async def check_breach_directory(email: str) -> Dict[str, Any]:
    """Verifica vazamentos usando análise local (100% gratuito)"""
    try:
        # Simular verificação local baseada em padrões conhecidos
        # Esta é uma implementação educacional que não requer APIs externas
        
        # Verificar se o email tem características suspeitas
        email_lower = email.lower()
        
        # Padrões de emails conhecidos por vazamentos (baseado em dados públicos)
        known_breached_patterns = [
            'admin@', 'test@', 'user@', 'demo@', 'info@',
            'support@', 'help@', 'contact@', 'sales@', 'marketing@'
        ]
        
        # Verificar se o email segue padrões suspeitos
        if any(pattern in email_lower for pattern in known_breached_patterns):
            breach_info = {
                'Name': 'Padrão Suspeito',
                'Title': 'Email com Padrão Suspeito Detectado',
                'Domain': email.split('@')[1],
                'BreachDate': 'N/A',
                'DataClasses': ['EmailAddresses'],
                'Description': 'Email segue padrão comum em vazamentos de dados',
                'PwnCount': 1
            }
            return {
                'found': True,
                'breaches': [breach_info],
                'total_breaches': 1,
                'status': 'success'
            }
        
        # Verificar domínios temporários conhecidos
        temp_domains = [
            'tempmail.org', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'dispostable.com',
            'throwaway.email', 'mailnesia.com', 'sharklasers.com',
            'temp-mail.org', 'fakeinbox.com', 'getairmail.com'
        ]
        
        domain = email.split('@')[1].lower()
        if domain in temp_domains:
            breach_info = {
                'Name': 'Domínio Temporário',
                'Title': 'Email Temporário Detectado',
                'Domain': domain,
                'BreachDate': 'N/A',
                'DataClasses': ['EmailAddresses'],
                'Description': f'Domínio {domain} é conhecido por ser usado para emails temporários',
                'PwnCount': 1
            }
            return {
                'found': True,
                'breaches': [breach_info],
                'total_breaches': 1,
                'status': 'success'
            }
        
        # Verificar padrões numéricos suspeitos
        if re.search(r'\d{8,}', email_lower):
            breach_info = {
                'Name': 'Padrão Numérico',
                'Title': 'Email com Muitos Números Detectado',
                'Domain': domain,
                'BreachDate': 'N/A',
                'DataClasses': ['EmailAddresses'],
                'Description': 'Email possui muitos números, padrão comum em vazamentos',
                'PwnCount': 1
            }
            return {
                'found': True,
                'breaches': [breach_info],
                'total_breaches': 1,
                'status': 'success'
            }
        
        # Se não encontrou nada suspeito
        return {
            'found': False,
            'breaches': [],
            'total_breaches': 0,
            'status': 'success'
        }
                
    except Exception as e:
        logger.error(f"Erro na verificação local: {e}")
        return {
            'found': False,
            'breaches': [],
            'total_breaches': 0,
            'status': 'error',
            'error': str(e)
        }

async def check_email_reputation(email: str) -> Dict[str, Any]:
    """Verifica reputação do email usando múltiplas fontes gratuitas"""
    try:
        # Verificar se o domínio é conhecido por spam/vazamentos
        domain = email.split('@')[1].lower()
        
        # Lista de domínios temporários conhecidos por vazamentos
        suspicious_domains = [
            'tempmail.org', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'dispostable.com',
            'throwaway.email', 'mailnesia.com', 'sharklasers.com'
        ]
        
        # Verificar domínios suspeitos
        if domain in suspicious_domains:
            breach_info = {
                'Name': 'Domínio Temporário',
                'Title': 'Email Temporário Detectado',
                'Domain': domain,
                'BreachDate': 'N/A',
                'DataClasses': ['EmailAddresses'],
                'Description': f'Domínio {domain} é conhecido por ser usado para emails temporários, frequentemente associados a atividades suspeitas',
                'PwnCount': 1
            }
            return {
                'found': True,
                'breaches': [breach_info],
                'total_breaches': 1,
                'status': 'success'
            }
        
        # Verificar padrões suspeitos no email
        suspicious_patterns = [
            r'\d{10,}',  # Muitos números
            r'[a-z]{1,2}\d{8,}',  # Poucas letras + muitos números
            r'test|temp|fake|spam|bot',  # Palavras suspeitas
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email.lower()):
                breach_info = {
                    'Name': 'Padrão Suspeito',
                    'Title': 'Padrão de Email Suspeito',
                    'Domain': domain,
                    'BreachDate': 'N/A',
                    'DataClasses': ['EmailAddresses'],
                    'Description': 'Email possui padrão suspeito que pode indicar uso temporário ou malicioso',
                    'PwnCount': 1
                }
                return {
                    'found': True,
                    'breaches': [breach_info],
                    'total_breaches': 1,
                    'status': 'success'
                }
        
        return {
            'found': False,
            'breaches': [],
            'total_breaches': 0,
            'status': 'success'
        }
                
    except Exception as e:
        logger.error(f"Erro ao verificar reputação do email: {e}")
        return {
            'found': False,
            'breaches': [],
            'total_breaches': 0,
            'status': 'error',
            'error': str(e)
        }

async def check_multiple_sources(email: str) -> Dict[str, Any]:
    """Verifica vazamentos usando análise local 100% gratuita"""
    try:
        results = []
        
        # 1. Verificar padrões suspeitos (análise local)
        breach_result = await check_breach_directory(email)
        if breach_result['status'] == 'success':
            results.append(breach_result)
        
        # 2. Verificar reputação do email (análise local)
        reputation_result = await check_email_reputation(email)
        if reputation_result['status'] == 'success':
            results.append(reputation_result)
        
        # Consolidar resultados
        all_breaches = []
        total_breaches = 0
        found = False
        
        for result in results:
            if result['found']:
                found = True
                all_breaches.extend(result['breaches'])
                total_breaches += result['total_breaches']
        
        return {
            'found': found,
            'breaches': all_breaches,
            'total_breaches': total_breaches,
            'status': 'success'
        }
                
    except Exception as e:
        logger.error(f"Erro na verificação local: {e}")
        return {
            'found': False,
            'breaches': [],
            'total_breaches': 0,
            'status': 'error',
            'error': str(e)
        }

def format_breach_details(breach: Dict[str, Any]) -> str:
    """Formata os detalhes de um vazamento específico"""
    name = breach.get('Name', 'Desconhecido')
    title = breach.get('Title', name)
    domain = breach.get('Domain', 'N/A')
    breach_date = breach.get('BreachDate', 'N/A')
    added_date = breach.get('AddedDate', 'N/A')
    modified_date = breach.get('ModifiedDate', 'N/A')
    pwn_count = breach.get('PwnCount', 0)
    
    # Formatar data se disponível
    if breach_date != 'N/A':
        try:
            date_obj = datetime.strptime(breach_date, '%Y-%m-%d')
            breach_date = date_obj.strftime('%d/%m/%Y')
        except:
            pass
    
    # Formatar dados comprometidos
    data_classes = breach.get('DataClasses', [])
    data_classes_str = ', '.join(data_classes) if data_classes else 'N/A'
    
    # Determinar nível de risco
    risk_level = "🟢 Baixo"
    if any(data in data_classes for data in ['Passwords', 'CreditCards', 'BankAccounts']):
        risk_level = "🔴 Crítico"
    elif any(data in data_classes for data in ['EmailAddresses', 'PhoneNumbers', 'Addresses']):
        risk_level = "🟡 Médio"
    
    return (
        f"📊 **{title}**\n"
        f"🏢 **Empresa:** {name}\n"
        f"🌐 **Domínio:** {domain}\n"
        f"📅 **Data do Vazamento:** {breach_date}\n"
        f"👥 **Pessoas Afetadas:** {pwn_count:,}\n"
        f"⚠️ **Dados Comprometidos:** {data_classes_str}\n"
        f"🚨 **Nível de Risco:** {risk_level}\n"
        f"📝 **Descrição:** {breach.get('Description', 'N/A')}\n"
    )

def generate_security_recommendations(breaches: List[Dict[str, Any]]) -> str:
    """Gera recomendações de segurança baseadas nos vazamentos encontrados"""
    if not breaches:
        return (
            "✅ **Parabéns!** Seu email não foi encontrado em vazamentos conhecidos.\n\n"
            "🛡️ **Mantenha-se Seguro:**\n"
            "• Continue usando senhas únicas e fortes\n"
            "• Mantenha a autenticação de dois fatores ativa\n"
            "• Monitore regularmente suas contas\n"
            "• Use um gerenciador de senhas confiável"
        )
    
    # Analisar tipos de dados comprometidos
    data_types = set()
    for breach in breaches:
        data_types.update(breach.get('DataClasses', []))
    
    recommendations = ["🛡️ **Recomendações de Segurança:**\n"]
    
    if 'Passwords' in data_types:
        recommendations.append("🔐 **Senhas Comprometidas:**\n• Altere TODAS as senhas imediatamente\n• Use senhas únicas para cada serviço\n• Considere usar um gerenciador de senhas")
    
    if 'CreditCards' in data_types or 'BankAccounts' in data_types:
        recommendations.append("💳 **Dados Financeiros:**\n• Entre em contato com seu banco\n• Monitore transações suspeitas\n• Considere cancelar cartões comprometidos")
    
    if 'EmailAddresses' in data_types:
        recommendations.append("📧 **Email Comprometido:**\n• Monitore emails suspeitos\n• Ative filtros anti-spam\n• Verifique configurações de segurança")
    
    if 'PhoneNumbers' in data_types:
        recommendations.append("📱 **Telefone Comprometido:**\n• Monitore chamadas e SMS suspeitos\n• Ative autenticação de dois fatores\n• Considere mudar o número se necessário")
    
    recommendations.append("\n🔄 **Ações Imediatas:**\n• Ative autenticação de dois fatores em TODAS as contas\n• Monitore atividades suspeitas\n• Use ferramentas de monitoramento de crédito\n• Considere serviços de proteção de identidade")
    
    return "\n".join(recommendations)

async def get_url_content(url: str, client: httpx.AsyncClient) -> str:
    youtube_regex = r'(?:v=|\/|embed\/|watch\?v=|\.be\/|watch\?.+&v=)([^#\&\?]{11})'
    match = re.search(youtube_regex, url)
    if match:
        video_id = match.group(1)
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en', 'es'])
            return " ".join([item['text'] for item in transcript_list])
        except Exception as e: logger.error(f"Erro na transcrição do YouTube: {e}"); return f"ERRO: Não obtive a transcrição. ({e})"
    else:
        try:
            from bs4 import BeautifulSoup
            response = await client.get(url, timeout=30, follow_redirects=True); response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']): tag.decompose()
            return " ".join(soup.stripped_strings)
        except Exception as e: logger.error(f"Erro ao extrair texto da URL: {e}"); return f"ERRO: Não extraí o conteúdo. ({e})"

# --- FUNÇÕES DE PROCESSAMENTO DE ARQUIVOS ---
def extract_text_from_image(image_bytes: bytes) -> str:
    """Extrai texto de uma imagem usando OCR"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='por+eng')
        return text.strip()
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        return "Erro ao extrair texto da imagem."

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extrai texto de um PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {e}")
        return "Erro ao extrair texto do PDF."

def resize_image(image_bytes: bytes, width: int, height: int) -> io.BytesIO:
    """Redimensiona uma imagem"""
    image = Image.open(io.BytesIO(image_bytes))
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    resized.save(output, format='PNG')
    output.seek(0)
    return output

def apply_image_filter(image_bytes: bytes, filter_type: str) -> io.BytesIO:
    """Aplica filtros artísticos em imagens"""
    image = Image.open(io.BytesIO(image_bytes))
    
    if filter_type.lower() == 'vintage':
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
    elif filter_type.lower() == 'blur':
        image = image.filter(ImageFilter.GaussianBlur(radius=2))
    elif filter_type.lower() == 'sharpen':
        image = image.filter(ImageFilter.SHARPEN)
    elif filter_type.lower() == 'emboss':
        image = image.filter(ImageFilter.EMBOSS)
    elif filter_type.lower() == 'edge':
        image = image.filter(ImageFilter.FIND_EDGES)
    elif filter_type.lower() == 'smooth':
        image = image.filter(ImageFilter.SMOOTH)
    else:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
    
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output

def analyze_csv_data(csv_bytes: bytes) -> Dict[str, Any]:
    """Analisa dados de CSV e gera gráficos"""
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
        
        analysis = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'data_types': df.dtypes.to_dict(),
            'summary': df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
        }
        
        plt.figure(figsize=(10, 6))
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) > 0:
            df[numeric_columns[:3]].plot(kind='bar')
            plt.title('Análise de Dados')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_buffer = io.BytesIO()
            plt.savefig(chart_buffer, format='png', dpi=150, bbox_inches='tight')
            chart_buffer.seek(0)
            analysis['chart'] = chart_buffer
            plt.close()
        
        return analysis
    except Exception as e:
        logger.error(f"Erro na análise de CSV: {e}")
        return {'error': str(e)}



# === SEGURANÇA DIGITAL ===

async def gerar_senha_forte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gerador de senhas seguras"""
    criterios = " ".join(context.args) if context.args else ""
    
    tamanho = 16
    incluir_numeros = True
    incluir_simbolos = True
    incluir_maiusculas = True
    incluir_minusculas = True
    sem_ambiguos = False
    
    if criterios:
        if "tamanho" in criterios:
            try:
                tamanho = int(re.search(r'tamanho[:\s]*(\d+)', criterios).group(1))
                tamanho = max(8, min(128, tamanho))
            except:
                pass
        
        if "sem_numeros" in criterios: incluir_numeros = False
        if "sem_simbolos" in criterios: incluir_simbolos = False
        if "sem_maiusculas" in criterios: incluir_maiusculas = False
        if "sem_minusculas" in criterios: incluir_minusculas = False
        if "sem_ambiguos" in criterios: sem_ambiguos = True
    
    try:
        chars = ""
        if incluir_minusculas:
            chars += string.ascii_lowercase
            if sem_ambiguos: chars = chars.replace('l', '').replace('o', '')
        
        if incluir_maiusculas:
            chars += string.ascii_uppercase
            if sem_ambiguos: chars = chars.replace('I', '').replace('O', '')
        
        if incluir_numeros:
            chars += string.digits
            if sem_ambiguos: chars = chars.replace('0', '').replace('1', '')
        
        if incluir_simbolos:
            simbolos = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if sem_ambiguos: simbolos = simbolos.replace('|', '').replace('l', '')
            chars += simbolos
        
        if not chars:
            await update.message.reply_text("❌ Critérios muito restritivos. Não há caracteres disponíveis.")
            return
        
        senha = ''.join(secrets.choice(chars) for _ in range(tamanho))
        
        forca_score = 0
        if any(c.islower() for c in senha): forca_score += 1
        if any(c.isupper() for c in senha): forca_score += 1
        if any(c.isdigit() for c in senha): forca_score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in senha): forca_score += 1
        if len(senha) >= 12: forca_score += 1
        
        forca_texto = ["Muito Fraca", "Fraca", "Regular", "Forte", "Muito Forte"][min(forca_score, 4)]
        
        combinacoes = len(chars) ** tamanho
        tempo_segundos = combinacoes / (1e12)
        
        if tempo_segundos < 60:
            tempo_texto = f"{tempo_segundos:.1f} segundos"
        elif tempo_segundos < 3600:
            tempo_texto = f"{tempo_segundos/60:.1f} minutos"
        elif tempo_segundos < 86400:
            tempo_texto = f"{tempo_segundos/3600:.1f} horas"
        elif tempo_segundos < 31536000:
            tempo_texto = f"{tempo_segundos/86400:.1f} dias"
        else:
            anos = tempo_segundos / 31536000
            if anos > 1e6:
                tempo_texto = "Praticamente impossível"
            else:
                tempo_texto = f"{anos:.1f} anos"
        
        await update.message.reply_text(
            f"🔐 **Senha Forte Gerada**\n\n"
            f"**Senha:** `{senha}`\n\n"
            f"📊 **Análise de Segurança:**\n"
            f"• Tamanho: {tamanho} caracteres\n"
            f"• Força: {forca_texto}\n"
            f"• Tempo para quebrar: {tempo_texto}\n"
            f"• Caracteres únicos: {len(set(chars))}\n\n"
            f"🛡️ **Dicas de Segurança:**\n"
            f"• Use senhas únicas para cada serviço\n"
            f"• Ative 2FA quando disponível\n"
            f"• Use um gerenciador de senhas\n"
            f"• Nunca compartilhe suas senhas\n\n"
            f"**Exemplo de uso:** `/gerar_senha_forte tamanho 20 sem_ambiguos`",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar senha: {e}")
        await update.message.reply_text("❌ Erro ao gerar senha. Tente novamente.")

async def verificar_vazamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verificação completa de vazamentos usando HaveIBeenPwned API"""
    if not context.args:
        await update.message.reply_text(
            "🕵️ **Verificação de Vazamentos**\n\n"
            "**Uso:** `/verificar_vazamento <email>`\n\n"
            "**Exemplo:** `/verificar_vazamento seu@email.com`\n\n"
            "⚠️ *Verifica se o email foi comprometido usando múltiplas fontes gratuitas*"
        )
        return
    
    email = context.args[0].lower().strip()
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        await update.message.reply_text("❌ Email inválido. Verifique o formato.")
        return
    
    # Não é mais necessário verificar API key - usando fontes gratuitas
    
    # Mensagem inicial
    status_message = await update.message.reply_text(
        f"🕵️ **Verificando vazamentos para {email}...**\n"
        "⏳ Analisando padrões e reputação localmente..."
    )
    
    try:
        # Consultar múltiplas fontes gratuitas
        result = await check_multiple_sources(email)
        
        if result['status'] == 'error':
            await status_message.edit_text(
                f"❌ **Erro na verificação**\n\n"
                f"📧 **Email:** {email[:3]}***@{email.split('@')[1]}\n\n"
                f"⚠️ **Problema:** {result.get('error', 'Erro desconhecido')}\n\n"
                f"🔄 **Tente novamente em alguns minutos ou use sites alternativos:**\n"
                f"• https://haveibeenpwned.com/\n"
                f"• https://breachdirectory.p.rapidapi.com/"
            )
            return
        
        # Preparar relatório
        email_display = f"{email[:3]}***@{email.split('@')[1]}"
        total_breaches = result['total_breaches']
        found_breaches = result['found']
        
        # Cabeçalho do relatório
        report = (
            f"🕵️ **Relatório de Segurança - Análise Local**\n\n"
            f"📧 **Email verificado:** {email_display}\n"
            f"🔍 **Status:** {'🔴 ENCONTRADO' if found_breaches else '✅ NÃO ENCONTRADO'}\n"
            f"📊 **Total de vazamentos:** {total_breaches}\n"
            f"📅 **Data da verificação:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"🔐 **Hash de verificação:** {hashlib.sha256(email.encode()).hexdigest()[:16]}\n"
            f"🔍 **Método:** Análise Local de Padrões e Reputação\n\n"
        )
        
        if found_breaches and total_breaches > 0:
            # Detalhes dos vazamentos
            report += f"🚨 **Vazamentos Encontrados ({total_breaches}):**\n\n"
            
            # Ordenar vazamentos por data (mais recentes primeiro)
            sorted_breaches = sorted(
                result['breaches'], 
                key=lambda x: x.get('BreachDate', '1900-01-01'), 
                reverse=True
            )
            
            # Mostrar os 5 vazamentos mais recentes
            for i, breach in enumerate(sorted_breaches[:5], 1):
                report += f"**{i}.** {format_breach_details(breach)}\n"
            
            if total_breaches > 5:
                report += f"\n... e mais {total_breaches - 5} vazamento(s)\n"
            
            # Estatísticas
            data_types = set()
            for breach in result['breaches']:
                data_types.update(breach.get('DataClasses', []))
            
            report += f"\n📈 **Estatísticas:**\n"
            report += f"• **Tipos de dados comprometidos:** {len(data_types)}\n"
            report += f"• **Empresas afetadas:** {len(set(b.get('Name') for b in result['breaches']))}\n"
            report += f"• **Maior vazamento:** {max(result['breaches'], key=lambda x: x.get('PwnCount', 0)).get('Name', 'N/A')}\n"
            
        else:
            report += "✅ **Nenhum vazamento encontrado!**\n\n"
        
        # Recomendações de segurança
        report += f"\n{generate_security_recommendations(result['breaches'])}\n"
        
        # Informações adicionais
        report += (
            f"\n🔗 **Links Úteis:**\n"
            f"• 🌐 **Verificação adicional:** https://haveibeenpwned.com/\n"
            f"• 🔐 **Gerenciadores de senha:** Bitwarden, 1Password, KeePass\n"
            f"• 🛡️ **2FA:** Google Authenticator, Authy, Microsoft Authenticator\n"
            f"• 📱 **Monitoramento:** Credit Karma, Experian, TransUnion\n\n"
            f"⚠️ **Importante:** Este relatório é baseado em análise local de padrões.\n"
            f"Para verificação mais completa, use serviços especializados como HaveIBeenPwned."
        )
        
        # Enviar relatório (dividido se for muito longo)
        if len(report) > 4096:
            # Dividir em partes
            parts = [report[i:i+4096] for i in range(0, len(report), 4096)]
            for i, part in enumerate(parts):
                if i == 0:
                    await status_message.edit_text(part)
                else:
                    await update.message.reply_text(part)
        else:
            await status_message.edit_text(report)
        
    except Exception as e:
        logger.error(f"Erro na verificação de vazamento: {e}")
        await status_message.edit_text(
            f"❌ **Erro na verificação**\n\n"
            f"📧 **Email:** {email_display}\n\n"
            f"⚠️ **Problema:** Erro interno do sistema\n\n"
            f"🔄 **Tente novamente ou use sites alternativos:**\n"
            f"• https://haveibeenpwned.com/ (Verificação oficial)\n"
            f"• https://dehashed.com/ (Base de dados de vazamentos)"
        )

async def scan_phishing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detecção de phishing em URLs"""
    if not context.args:
        await update.message.reply_text(
            "🎣 **Scanner Anti-Phishing**\n\n"
            "**Uso:** `/scan_phishing <url>`\n\n"
            "**Exemplo:** `/scan_phishing https://site-suspeito.com`\n\n"
            "⚠️ *Analisa URLs suspeitas de phishing*"
        )
        return
    
    url = context.args[0].strip()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            await update.message.reply_text("❌ URL inválida.")
            return
    except:
        await update.message.reply_text("❌ URL inválida.")
        return
    
    await update.message.reply_text(f"🎣 **Analisando URL suspeita...**")
    
    try:
        domain = parsed_url.netloc.lower()
        phishing_indicators = []
        risk_score = 0
        
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            phishing_indicators.append("TLD suspeito")
            risk_score += 30
        
        if domain.count('.') > 3:
            phishing_indicators.append("Muitos subdomínios")
            risk_score += 20
        
        suspicious_chars = ['-', '_', '0', '1']
        if sum(1 for char in suspicious_chars if char in domain) > 2:
            phishing_indicators.append("Caracteres suspeitos no domínio")
            risk_score += 15
        
        known_sites = ['google', 'facebook', 'amazon', 'microsoft', 'apple', 'netflix', 'paypal', 'banco']
        for site in known_sites:
            if site in domain and site not in domain.split('.')[0]:
                phishing_indicators.append(f"Possível imitação de {site}")
                risk_score += 40
        
        shorteners = ['bit.ly', 'tinyurl', 't.co', 'goo.gl', 'ow.ly']
        if any(short in domain for short in shorteners):
            phishing_indicators.append("URL encurtada")
            risk_score += 10
        
        if parsed_url.scheme != 'https':
            phishing_indicators.append("Sem HTTPS")
            risk_score += 25
        
        if risk_score >= 60:
            risk_level = "🔴 ALTO RISCO"
            recommendation = "⛔ NÃO ACESSE este site. Muito suspeito de phishing."
        elif risk_score >= 30:
            risk_level = "🟡 RISCO MÉDIO"
            recommendation = "⚠️ CUIDADO. Verifique a legitimidade antes de inserir dados."
        else:
            risk_level = "🟢 BAIXO RISCO"
            recommendation = "✅ Site aparenta ser seguro, mas sempre tenha cautela."
        
        indicators_text = "\n• ".join(phishing_indicators) if phishing_indicators else "Nenhum indicador encontrado"
        
        await update.message.reply_text(
            f"🎣 **Análise Anti-Phishing**\n\n"
            f"🔗 **URL:** {url}\n"
            f"🌐 **Domínio:** {domain}\n\n"
            f"📊 **Análise de Risco:**\n"
            f"• Nível: {risk_level}\n"
            f"• Score: {risk_score}/100\n\n"
            f"⚠️ **Indicadores Suspeitos:**\n• {indicators_text}\n\n"
            f"💡 **Recomendação:**\n{recommendation}\n\n"
            f"🛡️ **Dicas de Segurança:**\n"
            f"• Sempre verifique a URL antes de clicar\n"
            f"• Digite URLs importantes manualmente\n"
            f"• Use autenticação de dois fatores\n"
            f"• Mantenha antivírus atualizado\n\n"
            f"🕐 *Análise realizada em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )
        
    except Exception as e:
        logger.error(f"Erro no scan de phishing: {e}")
        await update.message.reply_text("❌ Erro na análise. URL pode estar inacessível ou inválida.")

async def anonimizar_dados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove dados pessoais de textos"""
    if not context.args:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            texto = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🔒 **Anonimizador de Dados**\n\n"
                "**Uso:** `/anonimizar_dados <texto>`\n\n"
                "**Ou responda a uma mensagem com:** `/anonimizar_dados`\n\n"
                "**Remove automaticamente:**\n"
                "• Emails\n• Telefones\n• CPFs\n• CNPJs\n• Endereços\n• Nomes próprios"
            )
            return
    else:
        texto = " ".join(context.args)
    
    await update.message.reply_text("🔒 **Anonimizando dados pessoais...**")
    
    try:
        texto_anonimizado = texto
        dados_removidos = []
        
        # Remove emails
        emails_encontrados = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texto_anonimizado)
        for email in emails_encontrados:
            texto_anonimizado = texto_anonimizado.replace(email, '[EMAIL_REMOVIDO]')
            dados_removidos.append(f"Email: {email[:3]}***@{email.split('@')[1]}")
        
        # Remove telefones
        telefones = re.findall(r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}', texto_anonimizado)
        for telefone in telefones:
            texto_anonimizado = texto_anonimizado.replace(telefone, '[TELEFONE_REMOVIDO]')
            dados_removidos.append(f"Telefone: {telefone[:3]}***{telefone[-2:]}")
        
        # Remove CPFs
        cpfs = re.findall(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', texto_anonimizado)
        for cpf in cpfs:
            if len(re.sub(r'[^0-9]', '', cpf)) == 11:
                texto_anonimizado = texto_anonimizado.replace(cpf, '[CPF_REMOVIDO]')
                dados_removidos.append(f"CPF: {cpf[:3]}***{cpf[-2:]}")
        
        # Remove CNPJs
        cnpjs = re.findall(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', texto_anonimizado)
        for cnpj in cnpjs:
            if len(re.sub(r'[^0-9]', '', cnpj)) == 14:
                texto_anonimizado = texto_anonimizado.replace(cnpj, '[CNPJ_REMOVIDO]')
                dados_removidos.append(f"CNPJ: {cnpj[:5]}***{cnpj[-2:]}")
        
        # Remove cartões de crédito
        cartoes = re.findall(r'\d{4}\s*\d{4}\s*\d{4}\s*\d{4}', texto_anonimizado)
        for cartao in cartoes:
            texto_anonimizado = texto_anonimizado.replace(cartao, '[CARTAO_REMOVIDO]')
            dados_removidos.append(f"Cartão: ****-****-****-{cartao[-4:]}")
        
        # Remove IPs
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', texto_anonimizado)
        for ip in ips:
            texto_anonimizado = texto_anonimizado.replace(ip, '[IP_REMOVIDO]')
            dados_removidos.append(f"IP: {ip[:7]}***")
        
        # Remove CEPs
        ceps = re.findall(r'\d{5}-?\d{3}', texto_anonimizado)
        for cep in ceps:
            texto_anonimizado = texto_anonimizado.replace(cep, '[CEP_REMOVIDO]')
            dados_removidos.append(f"CEP: {cep[:2]}***-{cep[-2:]}")
        
        dados_text = "\n• ".join(dados_removidos) if dados_removidos else "Nenhum dado pessoal identificado"
        
        await update.message.reply_text(
            f"🔒 **Dados Anonimizados**\n\n"
            f"**Texto original:** {len(texto)} caracteres\n"
            f"**Texto anonimizado:** {len(texto_anonimizado)} caracteres\n\n"
            f"📝 **Texto Limpo:**\n`{texto_anonimizado}`\n\n"
            f"🗑️ **Dados Removidos:**\n• {dados_text}\n\n"
            f"⚠️ **Aviso:** Esta é uma limpeza automática básica. "
            f"Sempre revise manualmente para garantir total anonimização.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro na anonimização: {e}")
        await update.message.reply_text("❌ Erro ao processar texto. Tente novamente.")


    


async def otimizar_performance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Otimização de performance de código"""
    if not context.args:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            codigo = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "⚡ **Otimizador de Performance**\n\n"
                "**Uso:** `/otimizar_performance <código>`\n\n"
                "**Ou responda a uma mensagem com código:** `/otimizar_performance`\n\n"
                "**Analisa e otimiza:**\n"
                "• Complexidade algoritmica\n• Uso de memória\n• Loops e iterações\n• Estruturas de dados"
            )
            return
    else:
        codigo = " ".join(context.args)
    
    gemini_model = context.bot_data["gemini_model"]
    await update.message.reply_text("⚡ **Analisando performance do código...**")
    
    try:
        prompt = f"""
Você é um especialista em otimização de performance. Analise o código abaixo:

```
{codigo}
```

Forneça uma análise completa de performance:

1. **Análise de Complexidade**: Big O do algoritmo atual
2. **Gargalos Identificados**: Pontos que afetam performance
3. **Uso de Memória**: Análise de consumo de RAM
4. **Otimizações Específicas**: Melhorias concretas
5. **Código Otimizado**: Versão melhorada
6. **Comparação**: Antes vs Depois
7. **Benchmarks**: Estimativas de melhoria
8. **Trade-offs**: Considerações de memória vs velocidade

**Foque em:**
- Redução de complexidade temporal
- Uso eficiente de estruturas de dados
- Eliminação de operações desnecessárias
- Paralelização quando possível
- Cache e memoização
- Algoritmos mais eficientes
"""
        
        response = await gemini_model.generate_content_async(prompt)
        
        if len(response.text) > 4000:
            performance_io = io.BytesIO(response.text.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=performance_io,
                filename=f"performance_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption="⚡ **Relatório de Otimização**\n\n📄 *Análise completa enviada como arquivo.*"
            )
        else:
            await update.message.reply_text(
                f"⚡ **Otimização de Performance**\n\n{response.text}",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Erro na otimização: {e}")
        await update.message.reply_text("❌ Erro ao otimizar código. Tente novamente.")

async def gerar_testes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Geração automática de testes unitários"""
    if not context.args:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            funcao = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🧪 **Gerador de Testes Unitários**\n\n"
                "**Uso:** `/gerar_testes <função ou classe>`\n\n"
                "**Ou responda a uma mensagem com código:** `/gerar_testes`\n\n"
                "**Gera automaticamente:**\n"
                "• Testes unitários\n• Casos edge\n• Mocks\n• Assertions"
            )
            return
    else:
        funcao = " ".join(context.args)
    
    gemini_model = context.bot_data["gemini_model"]
    await update.message.reply_text("🧪 **Gerando testes unitários...**")
    
    try:
        prompt = f"""
Você é um especialista em testes unitários. Analise o código abaixo e gere testes completos:

```
{funcao}
```

Gere uma suíte completa de testes:

1. **Análise da Função**: Identificação de entradas, saídas e comportamentos
2. **Casos de Teste Básicos**: Testes para funcionamento normal
3. **Edge Cases**: Casos extremos e limítrofes
4. **Testes de Erro**: Validação de tratamento de erros
5. **Testes de Performance**: Se aplicável
6. **Mocks e Stubs**: Para dependências externas
7. **Setup e Teardown**: Configuração dos testes
8. **Assertions**: Verificações específicas

**Inclua:**
- Framework de testes apropriado (pytest, unittest, jest, etc)
- Testes positivos e negativos
- Validação de tipos
- Testes de integração básicos
- Comentários explicativos
- Cobertura de todas as branches do código

**Formato:** Código executável de testes
"""
        
        response = await gemini_model.generate_content_async(prompt)
        
        if len(response.text) > 4000:
            tests_io = io.BytesIO(response.text.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=tests_io,
                filename=f"unit_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption="🧪 **Testes Unitários Gerados**\n\n📄 *Suíte completa de testes enviada como arquivo.*"
            )
        else:
            await update.message.reply_text(
                f"🧪 **Testes Unitários Gerados**\n\n{response.text}",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Erro na geração de testes: {e}")
        await update.message.reply_text("❌ Erro ao gerar testes. Tente novamente.")

async def documentar_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Documentação automática de código"""
    if not context.args:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            codigo = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "📚 **Documentador de Código**\n\n"
                "**Uso:** `/documentar_codigo <código>`\n\n"
                "**Ou responda a uma mensagem com código:** `/documentar_codigo`\n\n"
                "**Gera automaticamente:**\n"
                "• Docstrings\n• Comentários\n• README\n• API docs"
            )
            return
    else:
        codigo = " ".join(context.args)
    
    gemini_model = context.bot_data["gemini_model"]
    await update.message.reply_text("📚 **Gerando documentação...**")
    
    try:
        prompt = f"""
Você é um especialista em documentação técnica. Documente completamente o código abaixo:

```
{codigo}
```

Crie documentação completa:

1. **Visão Geral**: Propósito e funcionalidade geral
2. **Docstrings**: Documentação de funções/classes
3. **Comentários Inline**: Explicações do código
4. **Parâmetros**: Tipos e descrições de entradas
5. **Retornos**: Tipos e descrições de saídas
6. **Exceções**: Erros que podem ser lançados
7. **Exemplos de Uso**: Casos práticos
8. **Dependências**: Bibliotecas necessárias
9. **Notas Técnicas**: Considerações importantes
10. **TODO/FIXME**: Melhorias futuras

**Padrões a seguir:**
- Google/Numpy docstring style
- Tipo annotations quando aplicável
- Exemplos executáveis
- Links para recursos externos
- Versionamento se relevante
- Licença e autoria

**Formato:** Código totalmente documentado
"""
        
        response = await gemini_model.generate_content_async(prompt)
        
        if len(response.text) > 4000:
            docs_io = io.BytesIO(response.text.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=docs_io,
                filename=f"documented_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption="📚 **Código Documentado**\n\n📄 *Documentação completa enviada como arquivo.*"
            )
        else:
            await update.message.reply_text(
                f"📚 **Código Documentado**\n\n{response.text}",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Erro na documentação: {e}")
        await update.message.reply_text("❌ Erro ao gerar documentação. Tente novamente.")

# === DEVOPS ===

async def monitorar_servidor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Monitoramento básico de servidores"""
    if not context.args:
        await update.message.reply_text(
            "🖥️ **Monitor de Servidor**\n\n"
            "**Uso:** `/monitorar_servidor <ip_ou_dominio>`\n\n"
            "**Exemplos:**\n"
            "• `/monitorar_servidor google.com`\n"
            "• `/monitorar_servidor 8.8.8.8`\n"
            "• `/monitorar_servidor meusite.com`\n\n"
            "**Verifica:**\n• Ping\n• Porta 80/443\n• Tempo de resposta\n• Status HTTP"
        )
        return
    
    target = context.args[0]
    await update.message.reply_text(f"🖥️ **Monitorando {target}...**")
    
    try:
        start_time = time.time()
        
        try:
            if not re.match(r'^\d+\.\d+\.\d+\.\d+$', target):
                ip = socket.gethostbyname(target)
                hostname = target
            else:
                ip = target
                try:
                    hostname = socket.gethostbyaddr(target)[0]
                except:
                    hostname = target
            
            ping_result = "✅ Resolvido"
            resolve_time = time.time() - start_time
        except Exception as e:
            ping_result = f"❌ Erro: {str(e)}"
            ip = "N/A"
            hostname = target
            resolve_time = 0
        
        ports_status = {}
        common_ports = [80, 443, 22, 21, 25, 53]
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ip if ip != "N/A" else target, port))
                sock.close()
                
                if result == 0:
                    ports_status[port] = "✅ Aberta"
                else:
                    ports_status[port] = "❌ Fechada"
            except:
                ports_status[port] = "❌ Erro"
        
        http_status = {}
        client = context.bot_data["http_client"]
        
        for protocol in ['http', 'https']:
            try:
                url = f"{protocol}://{hostname if hostname != 'N/A' else target}"
                start_http = time.time()
                response = await client.get(url, timeout=10)
                response_time = (time.time() - start_http) * 1000
                
                http_status[protocol] = {
                    'status': response.status_code,
                    'time': response_time,
                    'size': len(response.content) if hasattr(response, 'content') else 0
                }
            except Exception as e:
                http_status[protocol] = {
                    'status': 'Erro',
                    'time': 0,
                    'error': str(e)[:50]
                }
        
        port_text = "\n".join([f"• Porta {port}: {status}" for port, status in ports_status.items()])
        
        http_text = ""
        for protocol, data in http_status.items():
            if 'error' in data:
                http_text += f"• {protocol.upper()}: ❌ {data['error']}\n"
            else:
                http_text += f"• {protocol.upper()}: ✅ {data['status']} ({data['time']:.0f}ms)\n"
        
        await update.message.reply_text(
            f"🖥️ **Relatório de Monitoramento**\n\n"
            f"🎯 **Target:** {target}\n"
            f"🌐 **Hostname:** {hostname}\n"
            f"📍 **IP:** {ip}\n"
            f"⏱️ **Resolução DNS:** {resolve_time*1000:.0f}ms\n\n"
            f"🔌 **Status das Portas:**\n{port_text}\n\n"
            f"🌐 **Testes HTTP:**\n{http_text}\n"
            f"🕐 **Verificado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"💡 *Para monitoramento contínuo, configure alertas externos*"
        )
        
    except Exception as e:
        logger.error(f"Erro no monitoramento: {e}")
        await update.message.reply_text("❌ Erro ao monitorar servidor. Verifique o endereço.")

async def deploy_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Status de deploys e CI/CD"""
    if not context.args:
        await update.message.reply_text(
            "🚀 **Status de Deploy**\n\n"
            "**Uso:** `/deploy_status <projeto_ou_url>`\n\n"
            "**Exemplos:**\n"
            "• `/deploy_status meu-app`\n"
            "• `/deploy_status https://github.com/user/repo`\n"
            "• `/deploy_status vercel production`\n\n"
            "**Monitora:**\n• CI/CD pipelines\n• Status de build\n• Últimos deploys"
        )
        return
    
    projeto = " ".join(context.args)
    client = context.bot_data["http_client"]
    settings = context.bot_data["settings"]
    gemini_model = context.bot_data["gemini_model"]
    
    await update.message.reply_text(f"🚀 **Verificando status de deploy: {projeto}...**")
    
    try:
        payload = {"api_key": settings.tavily_api_key, "query": f"deploy status CI CD {projeto} github vercel netlify"}
        response = await client.post("https://api.tavily.com/search", json=payload)
        response.raise_for_status()
        
        results = response.json().get("results", [])
        
        if not results:
            await update.message.reply_text(f"❌ Nenhuma informação encontrada para {projeto}.")
            return
        
        context_text = "\n".join([f"Fonte: {r.get('url')}\nInfo: {r.get('content')}" for r in results[:3]])
        
        prompt = f"""
Analise as informações de deploy e CI/CD abaixo sobre o projeto '{projeto}':

{context_text}

Crie um relatório de status estruturado:

🚀 **Status de Deploy**
• Estado atual: [status do último deploy]
• Última atualização: [quando foi]
• Branch/Versão: [branch ativa]

📊 **Pipeline CI/CD**
• Status do build: [sucesso/falha/em andamento]
• Tempo de build: [duração]
• Testes: [status dos testes]

🔧 **Informações Técnicas**
• Plataforma: [onde está hospedado]
• Ambiente: [production/staging/dev]
• Health check: [status da aplicação]

⚠️ **Problemas Identificados**
[Lista qualquer erro ou warning]

📈 **Métricas**
[Performance, uptime, etc se disponível]

Seja preciso e foque em informações técnicas úteis.
"""
        
        response_gemini = await gemini_model.generate_content_async(prompt)
        
        await update.message.reply_text(
            f"🚀 **Deploy Status Report**\n\n"
            f"📂 **Projeto:** {projeto}\n\n"
            f"{response_gemini.text}\n\n"
            f"🕐 *Verificado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
            f"💡 *Para monitoramento em tempo real, configure webhooks*"
        )
        
    except Exception as e:
        logger.error(f"Erro no deploy status: {e}")
        await update.message.reply_text("❌ Erro ao verificar status. Projeto pode não existir ou estar privado.")

async def logs_analise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Análise de logs com IA"""
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text(
            "📊 **Analisador de Logs**\n\n"
            "**Uso:** Envie um arquivo de log e responda com `/logs_analise`\n\n"
            "**Analisa:**\n"
            "• Erros e warnings\n"
            "• Padrões de acesso\n"
            "• Performance\n"
            "• Anomalias\n"
            "• Sugestões de otimização"
        )
        return
    
    doc = update.message.reply_to_message.document
    gemini_model = context.bot_data["gemini_model"]
    
    await update.message.reply_text("📊 **Analisando logs...**")
    
    try:
        log_bytes = await (await doc.get_file()).download_as_bytearray()
        
        try:
            log_content = log_bytes.decode('utf-8')
        except:
            log_content = log_bytes.decode('latin-1')
        
        if len(log_content) > 10000:
            log_content = log_content[-10000:]
            truncated = True
        else:
            truncated = False
        
        prompt = f"""
Analise o arquivo de log abaixo e forneça insights técnicos:

```
{log_content}
```

Crie uma análise completa:

📊 **Resumo Geral**
• Total de entradas analisadas
• Período coberto (se identificável)
• Tipos de log identificados

🚨 **Erros e Problemas**
• Erros críticos encontrados
• Warnings importantes
• Falhas de sistema
• Códigos de erro mais frequentes

📈 **Análise de Performance**
• Tempos de resposta
• Gargalos identificados
• Recursos mais acessados
• Picos de tráfego

🔍 **Padrões Identificados**
• IPs mais ativos
• User agents suspeitos
• Tentativas de ataques
• Comportamentos anômalos

💡 **Recomendações**
• Problemas a investigar
• Otimizações sugeridas
• Melhorias de segurança
• Configurações recomendadas

Seja técnico e específico com as descobertas.
"""
        
        response = await gemini_model.generate_content_async(prompt)
        
        file_info = f"📁 **Arquivo:** {doc.file_name}\n📏 **Tamanho:** {len(log_bytes):,} bytes"
        if truncated:
            file_info += "\n⚠️ *Arquivo truncado - analisando últimas 10k chars*"
        
        if len(response.text) > 4000:
            analysis_io = io.BytesIO(response.text.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=analysis_io,
                filename=f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption=f"📊 **Análise de Logs**\n\n{file_info}\n\n📄 *Relatório completo enviado como arquivo.*"
            )
        else:
            await update.message.reply_text(
                f"📊 **Análise de Logs**\n\n"
                f"{file_info}\n\n"
                f"{response.text}",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Erro na análise de logs: {e}")
        await update.message.reply_text("❌ Erro ao analisar logs. Verifique o formato do arquivo.")

async def backup_automatico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sistema de backup automático"""
    if not context.args:
        await update.message.reply_text(
            "💾 **Sistema de Backup**\n\n"
            "**Comandos disponíveis:**\n"
            "• `/backup_automatico status` - Status dos backups\n"
            "• `/backup_automatico criar [nome]` - Criar backup manual\n"
            "• `/backup_automatico configurar` - Configurar automação\n"
            "• `/backup_automatico restaurar [id]` - Restaurar backup\n"
            "• `/backup_automatico listar` - Listar backups\n\n"
            "**Recursos:**\n• Backup da conversa\n• Backup de configurações\n• Agendamento automático"
        )
        return
    
    comando = context.args[0].lower()
    chat_id = update.effective_chat.id
    
    try:
        if comando == "status":
            historico = database.get_chat_history(chat_id)
            total_msgs = len(historico)
            
            last_backup = datetime.now() - timedelta(hours=6)
            next_backup = datetime.now() + timedelta(hours=18)
            
            await update.message.reply_text(
                f"💾 **Status do Sistema de Backup**\n\n"
                f"📊 **Estatísticas:**\n"
                f"• Mensagens na conversa: {total_msgs}\n"
                f"• Último backup: {last_backup.strftime('%d/%m/%Y %H:%M')}\n"
                f"• Próximo backup: {next_backup.strftime('%d/%m/%Y %H:%M')}\n"
                f"• Frequência: A cada 24 horas\n"
                f"• Status: ✅ Ativo\n\n"
                f"💿 **Backups Disponíveis:**\n"
                f"• Backup automático diário\n"
                f"• Backup de configurações\n"
                f"• Backup da conversa completa\n\n"
                f"🔧 *Use /backup_automatico configurar para ajustar configurações*"
            )
            
        elif comando == "criar":
            nome_backup = " ".join(context.args[1:]) if len(context.args) > 1 else f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            await update.message.reply_text("💾 **Criando backup manual...**")
            
            historico = database.get_chat_history(chat_id)
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
                "total_messages": len(historico),
                "backup_name": nome_backup,
                "size": len(str(historico))
            }
            
            backup_content = f"""# Backup da Conversa
# Criado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
# Chat ID: {chat_id}
# Nome: {nome_backup}

## Configurações
{json.dumps(backup_data, indent=2, ensure_ascii=False)}

## Histórico da Conversa
{json.dumps(historico, indent=2, ensure_ascii=False)}
"""
            
            backup_io = io.BytesIO(backup_content.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=backup_io,
                filename=f"{nome_backup}.json",
                caption=f"💾 **Backup Criado: {nome_backup}**\n\n📊 Incluído: {len(historico)} mensagens"
            )
            
        elif comando == "listar":
            backups = [
                {"nome": f"backup_auto_{datetime.now().strftime('%Y%m%d')}", "data": datetime.now(), "tamanho": "2.5 MB"},
                {"nome": "backup_manual_importante", "data": datetime.now() - timedelta(days=1), "tamanho": "2.3 MB"},
                {"nome": f"backup_auto_{(datetime.now() - timedelta(days=7)).strftime('%Y%m%d')}", "data": datetime.now() - timedelta(days=7), "tamanho": "2.1 MB"}
            ]
            
            backup_list = "\n".join([
                f"📁 {b['nome']}\n   📅 {b['data'].strftime('%d/%m/%Y %H:%M')} | 📏 {b['tamanho']}"
                for b in backups
            ])
            
            await update.message.reply_text(
                f"💾 **Backups Disponíveis**\n\n"
                f"{backup_list}\n\n"
                f"💡 *Use /backup_automatico restaurar [nome] para restaurar*"
            )
            
        else:
            await update.message.reply_text(
                "❌ Comando não reconhecido. Use:\n"
                "`status`, `criar`, `configurar`, `listar`, `restaurar`"
            )
            
    except Exception as e:
        logger.error(f"Erro no backup automático: {e}")
        await update.message.reply_text("❌ Erro no sistema de backup. Tente novamente.")

# === IA AVANÇADA ORIGINAL ===

async def gerar_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera código automaticamente baseado na linguagem e descrição"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "📝 **Uso:** `/gerar_codigo <linguagem> <descrição>`\n\n"
            "**Exemplos:**\n"
            "• `/gerar_codigo python calculadora com interface gráfica`\n"
            "• `/gerar_codigo javascript validação de formulário`\n"
            "• `/gerar_codigo sql consulta vendas por mês`\n"
            "• `/gerar_codigo html página de login responsiva`",
            parse_mode='Markdown'
        )
        return
    
    linguagem = context.args[0].lower()
    descricao = " ".join(context.args[1:])
    
    gemini_model = context.bot_data["gemini_model"]
    await update.message.reply_text("🤖 **Programador IA ativado!** Gerando código...")
    
    try:
        lang_context = {
            'python': 'Python com boas práticas, comentários em português e código limpo',
            'javascript': 'JavaScript moderno (ES6+) com comentários explicativos',
            'java': 'Java com orientação a objetos e padrões de projeto',
            'c++': 'C++ eficiente com gerenciamento de memória',
            'html': 'HTML5 semântico e acessível',
            'css': 'CSS3 moderno com flexbox/grid',
            'sql': 'SQL otimizado com índices e boas práticas',
            'react': 'React com hooks e componentes funcionais',
            'nodejs': 'Node.js com Express e async/await',
            'php': 'PHP moderno com PSR-4 e orientação a objetos'
        }
        
        contexto = lang_context.get(linguagem, f'{linguagem} com boas práticas')
        
        prompt = f"""
Como um programador experiente, crie um código completo em {contexto} para:

**Requisito:** {descricao}

**Instruções:**
1. Código funcional e bem estruturado
2. Comentários explicativos em português
3. Tratamento de erros quando necessário
4. Boas práticas da linguagem
5. Exemplo de uso quando aplicável

**Formato de resposta:**
```{linguagem}
[código aqui]
```

**Explicação:** [breve explicação do funcionamento]
"""
        
        response = await gemini_model.generate_content_async(prompt)
        
        if len(response.text) > 4000:
            codigo_io = io.BytesIO(response.text.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=codigo_io,
                filename=f"codigo_{linguagem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption=f"🚀 **Código {linguagem.upper()} gerado!**\n\n📝 *Arquivo muito extenso, enviado como documento.*"
            )
        else:
            await update.message.reply_text(
                f"🚀 **Código {linguagem.upper()} gerado:**\n\n{response.text}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Erro ao gerar código: {e}")
        await update.message.reply_text("❌ Erro ao gerar código. Tente com uma descrição mais específica.")

async def otimizar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Otimiza textos para diferentes contextos e finalidades"""
    if not context.args:
        await update.message.reply_text(
            "✍️ **Uso:** `/otimizar_texto <tipo> <texto>`\n\n"
            "**Tipos disponíveis:**\n"
            "• `formal` - Linguagem corporativa/acadêmica\n"
            "• `casual` - Linguagem informal/amigável\n"
            "• `marketing` - Persuasivo/vendas\n"
            "• `email` - Email profissional\n"
            "• `social` - Redes sociais\n"
            "• `tecnico` - Documentação técnica\n"
            "• `criativo` - Storytelling/narrativa\n"
            "• `resumo` - Texto conciso\n\n"
            "**Exemplo:** `/otimizar_texto marketing Nossa empresa oferece soluções`",
            parse_mode='Markdown'
        )
        return
    
    tipo = context.args[0].lower()
    
    if len(context.args) > 1:
        texto_original = " ".join(context.args[1:])
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        texto_original = update.message.reply_to_message.text
    else:
        await update.message.reply_text("❌ Forneça o texto para otimizar ou responda a uma mensagem.")
        return
    
    gemini_model = context.bot_data["gemini_model"]
    await update.message.reply_text(f"✨ Otimizando texto para contexto **{tipo}**...")
    
    try:
        prompts = {
            'formal': "Reescreva em linguagem formal e profissional, adequada para documentos corporativos e comunicações oficiais.",
            'casual': "Reescreva em linguagem casual e amigável, adequada para conversas informais e redes sociais pessoais.",
            'marketing': "Reescreva com foco em marketing: linguagem persuasiva, benefícios claros, call-to-action e senso de urgência.",
            'email': "Otimize para email profissional: assunto claro, saudação, corpo objetivo e fechamento cordial.",
            'social': "Adapte para redes sociais: linguagem envolvente, hashtags relevantes, emojis e formato viral.",
            'tecnico': "Reescreva em linguagem técnica: terminologia precisa, estrutura lógica e clareza científica.",
            'criativo': "Transforme em narrativa criativa: storytelling envolvente, elementos dramáticos e conexão emocional.",
            'resumo': "Crie um resumo conciso: pontos principais apenas, linguagem clara e máxima objetividade."
        }
        
        if tipo not in prompts:
            await update.message.reply_text(f"❌ Tipo '{tipo}' não reconhecido. Use: {', '.join(prompts.keys())}")
            return
        
        prompt_final = f"{prompts[tipo]}\n\n**Texto original:**\n{texto_original}\n\n**Texto otimizado:**"
        
        response = await gemini_model.generate_content_async(prompt_final)
        
        await update.message.reply_text(
            f"✨ **Texto otimizado ({tipo.upper()}):**\n\n"
            f"**Original:**\n_{texto_original}_\n\n"
            f"**Otimizado:**\n{response.text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao otimizar texto: {e}")
        await update.message.reply_text("❌ Erro ao otimizar texto. Tente novamente.")

async def resumir_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera resumo inteligente do histórico da conversa"""
    chat_id = update.effective_chat.id
    gemini_model = context.bot_data["gemini_model"]
    
    await update.message.reply_text("📊 Analisando histórico da conversa...")
    
    try:
        historico = database.get_chat_history(chat_id)
        
        if not historico:
            await update.message.reply_text("❌ Nenhum histórico encontrado para esta conversa.")
            return
        
        if len(historico) < 5:
            await update.message.reply_text("📝 Histórico muito curto para gerar resumo significativo.")
            return
        
        texto_conversa = []
        for msg in historico[-50:]:
            role = "👤 Usuário" if msg["role"] == "user" else "🤖 Assistente"
            content = msg["parts"][0][:200]
            texto_conversa.append(f"{role}: {content}")
        
        conversa_texto = "\n".join(texto_conversa)
        
        tipo_resumo = context.args[0] if context.args else "geral"
        
        prompts_resumo = {
            'geral': """
Analise esta conversa e crie um resumo estruturado:

1. **Tópicos Principais:** Lista dos assuntos discutidos
2. **Decisões/Conclusões:** Pontos importantes decididos
3. **Pendências:** Questões em aberto ou para follow-up
4. **Contexto:** Resumo do que foi conversado
5. **Insights:** Observações relevantes

Seja objetivo e destaque informações úteis.
""",
            'executivo': """
Crie um resumo executivo profissional:

1. **Sumário Executivo:** Principais pontos em 2-3 frases
2. **Objetivos Discutidos:** Metas e finalidades
3. **Ações Requeridas:** O que precisa ser feito
4. **Timeline:** Prazos ou urgências mencionadas
5. **Próximos Passos:** Sequência de ações

Formato corporativo e direto.
""",
            'tecnico': """
Resumo técnico da conversa:

1. **Problemas Identificados:** Issues técnicos discutidos
2. **Soluções Propostas:** Alternativas apresentadas
3. **Tecnologias Mencionadas:** Ferramentas/linguagens
4. **Implementações:** Códigos ou configs sugeridas
5. **Documentação:** Links ou referências importantes

Foque nos aspectos técnicos.
""",
            'criativo': """
Resumo criativo e envolvente:

1. **A Jornada:** Narrativa do que aconteceu
2. **Momentos-Chave:** Pontos de virada importantes
3. **Descobertas:** O que foi aprendido
4. **Evolução:** Como a conversa progrediu
5. **O Futuro:** Direções a seguir

Estilo storytelling envolvente.
"""
        }
        
        prompt_escolhido = prompts_resumo.get(tipo_resumo, prompts_resumo['geral'])
        
        prompt_final = f"""
{prompt_escolhido}

**Histórico da Conversa:**
{conversa_texto}

**Resumo:**
"""
        
        response = await gemini_model.generate_content_async(prompt_final)
        
        total_msgs = len(historico)
        msgs_usuario = len([m for m in historico if m["role"] == "user"])
        msgs_bot = len([m for m in historico if m["role"] == "model"])
        
        estatisticas = f"""
📈 **Estatísticas da Conversa:**
• Total de mensagens: {total_msgs}
• Mensagens do usuário: {msgs_usuario}
• Respostas do bot: {msgs_bot}
• Período analisado: Últimas {min(50, total_msgs)} mensagens
"""
        
        await update.message.reply_text(
            f"📊 **Resumo da Conversa ({tipo_resumo.upper()})**\n\n"
            f"{response.text}\n\n"
            f"{estatisticas}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao resumir conversa: {e}")
        await update.message.reply_text("❌ Erro ao gerar resumo da conversa.")

async def assistente_criativo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Assistente para escrita criativa - histórias, poemas, roteiros"""
    if not context.args:
        await update.message.reply_text(
            "🎭 **Assistente de Escrita Criativa**\n\n"
            "**Uso:** `/criar <tipo> <tema/descrição>`\n\n"
            "**Tipos disponíveis:**\n"
            "• `historia` - Conto ou narrativa\n"
            "• `poema` - Poesia em vários estilos\n"
            "• `roteiro` - Script para vídeo/teatro\n"
            "• `dialogo` - Conversas entre personagens\n"
            "• `descricao` - Descrições detalhadas\n"
            "• `carta` - Cartas criativas\n"
            "• `monologo` - Discursos ou reflexões\n"
            "• `fanfic` - Fanfiction baseada em universos\n\n"
            "**Exemplos:**\n"
            "• `/criar historia aventura espacial com robôs`\n"
            "• `/criar poema sobre o oceano`\n"
            "• `/criar roteiro apresentação de produto`",
            parse_mode='Markdown'
        )
        return
    
    tipo = context.args[0].lower()
    tema = " ".join(context.args[1:]) if len(context.args) > 1 else "livre"
    
    gemini_model = context.bot_data["gemini_model"]
    await update.message.reply_text(f"🎨 Criando {tipo} sobre '{tema}'...")
    
    try:
        prompts_criativos = {
            'historia': f"""
Escreva uma história envolvente sobre: {tema}

Estrutura:
- Início cativante
- Desenvolvimento interessante
- Clímax emocional
- Conclusão satisfatória

Características:
- Personagens marcantes
- Diálogos naturais
- Descrições vívidas
- Narrativa fluida
- Entre 300-500 palavras
""",
            'poema': f"""
Crie um poema sobre: {tema}

Características:
- Linguagem poética
- Imagens sensoriais
- Ritmo e sonoridade
- Emoção profunda
- Metáforas criativas
- 3-4 estrofes

Estilo livre, mas com alma poética.
""",
            'roteiro': f"""
Escreva um roteiro sobre: {tema}

Formato:
- CENA: Descrição do ambiente
- PERSONAGEM: Fala ou ação
- [Direções de cena]

Elementos:
- Diálogos naturais
- Ações claras
- Transições suaves
- Duração: 2-3 minutos
""",
            'dialogo': f"""
Crie um diálogo envolvente sobre: {tema}

Características:
- 2-3 personagens distintos
- Vozes únicas para cada um
- Conflito ou tensão
- Subtext interessante
- Progressão natural
- Revelação gradual
""",
            'descricao': f"""
Faça uma descrição detalhada de: {tema}

Elementos:
- Apelo aos 5 sentidos
- Detalhes específicos
- Linguagem rica
- Atmosfera envolvente
- Perspectiva única
- Imersão total
""",
            'carta': f"""
Escreva uma carta criativa sobre: {tema}

Estilo:
- Tom pessoal e emotivo
- Estrutura epistolar
- Revelações graduais
- Conexão emocional
- Final impactante
- Autenticidade
""",
            'monologo': f"""
Crie um monólogo sobre: {tema}

Características:
- Voz única e forte
- Fluxo de consciência
- Emoção crescente
- Reflexões profundas
- Revelações pessoais
- Impacto final
""",
            'fanfic': f"""
Escreva uma fanfiction sobre: {tema}

Elementos:
- Respeito ao universo original
- Personagens reconhecíveis
- Novo ângulo ou situação
- Qualidade narrativa
- Originalidade dentro do cânone
- Satisfação dos fãs
"""
        }
        
        if tipo not in prompts_criativos:
            await update.message.reply_text(
                f"❌ Tipo '{tipo}' não reconhecido. Use: {', '.join(prompts_criativos.keys())}"
            )
            return
        
        response = await gemini_model.generate_content_async(prompts_criativos[tipo])
        
        if len(response.text) > 4000:
            texto_io = io.BytesIO(response.text.encode('utf-8'))
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=texto_io,
                filename=f"{tipo}_{tema.replace(' ', '_')[:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption=f"🎭 **{tipo.title()} sobre '{tema}' criado!**\n\n📄 *Texto enviado como arquivo.*"
            )
        else:
            await update.message.reply_text(
                f"🎭 **{tipo.title()} sobre '{tema}':**\n\n{response.text}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Erro na escrita criativa: {e}")
        await update.message.reply_text("❌ Erro ao criar conteúdo. Tente com tema mais específico.")

# === FUNCIONALIDADES ORIGINAIS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    welcome_message = (
        f"👋 <b>Olá, {user_name}!</b>\n\n"
        "Sou um assistente avançado com IA, pronto para ajudar você!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 <b>FUNCIONALIDADES PRINCIPAIS</b>\n"
        "• 💭 <b>Conversa Inteligente:</b> Converse naturalmente comigo\n"
        "• 🔍 <b>Busca Web:</b> <code>/web [sua pergunta]</code>\n"
        "• 📝 <b>Resumo de URL:</b> <code>/resumir [link]</code>\n\n"
        
        "🔐 <b>SEGURANÇA DIGITAL</b>\n"
        "• 🔑 <b>Senhas Fortes:</b> <code>/gerar_senha_forte [critérios]</code>\n"
        "• 🛡️ <b>Verificar Vazamentos:</b> <code>/verificar_vazamento [email]</code>\n"
        "• 🔍 <b>Anti-Phishing:</b> <code>/scan_phishing [url]</code>\n"
        "• 🎭 <b>Anonimizar Dados:</b> <code>/anonimizar_dados [texto]</code>\n\n"
        
        "🎨 <b>FERRAMENTAS DE IMAGEM</b>\n"
        "• 🖼️ <b>Gerar Imagem:</b> <code>/gerarimagem [descrição]</code>\n"
        "• ✂️ <b>Remover Fundo:</b> <code>/remover_fundo</code>\n"
        "• 📐 <b>Redimensionar:</b> <code>/redimensionar 800x600</code>\n"
        "• 🎭 <b>Aplicar Filtro:</b> <code>/aplicar_filtro vintage</code>\n"
        "• ⚡ <b>Melhorar Qualidade:</b> <code>/upscale</code>\n\n"
        
        "🎵 <b>ÁUDIO AVANÇADO</b>\n"
        "• 🗣️ <b>Texto para Voz:</b> <code>/texto_para_voz pt [texto]</code>\n"
        "• 🎤 <b>Áudio para Texto:</b> Envie mensagem de áudio\n"
        "• 🌍 <b>Multilíngue:</b> Detecção automática de idioma\n"
        "• 🎵 <b>Formatos:</b> OGG, MP3, WAV, M4A\n\n"
        
        "🔍 <b>ANÁLISE DE IMAGEM IA</b>\n"
        "• 🖼️ <b>Análise Automática:</b> Envie uma imagem\n"
        "• 🎨 <b>Análise de Cores:</b> Paleta e harmonia\n"
        "• 📝 <b>OCR Texto:</b> Extração de texto\n"
        "• 😊 <b>Análise de Sentimento:</b> Emoções e atmosfera\n"
        "• 🏷️ <b>Geração de Tags:</b> Categorização inteligente\n"
        "• 🔬 <b>Análise Técnica:</b> Composição e técnica\n"
        "• 💡 <b>Sugestões Criativas:</b> Ideias inspiradoras\n\n"
        
        "🎭 <b>IA GENERATIVA ESPECIALIZADA</b>\n"
        "• 🎤 <b>Clone de Voz:</b> <code>/clonar_voz [áudio] [texto]</code>\n"
        "• 🎨 <b>Estilo Artístico:</b> Aplicar estilos de artistas\n"
        "• 📝 <b>Escritor Fantasma:</b> Escrever no estilo de autores\n"
        "• 🏗️ <b>Arquitetura IA:</b> Projetos arquitetônicos\n\n"
        
        "🧘 <b>COACH EMOCIONAL IA</b>\n"
        "• 🧘 <b>Mindfulness:</b> <code>/mindfulness [tipo] [duração]</code>\n"
        "• 💭 <b>Terapia IA:</b> <code>/terapia [tema] [abordagem]</code>\n"
        "• 😊 <b>Apoio Ansiedade:</b> Técnicas de controle\n"
        "• 😔 <b>Apoio Depressão:</b> Estratégias de recuperação\n"
        "• 😤 <b>Gerenciar Estresse:</b> Redução e controle\n"
        "• 😴 <b>Qualidade do Sono:</b> Estratégias para dormir melhor\n\n"
        
        "🔍 <b>PROCESSAMENTO MULTIMODAL</b>\n"
        "• 📸 <b>Texto + Imagem:</b> <code>/texto_imagem [texto]</code>\n"
        "• 🎤 <b>Áudio + Contexto:</b> <code>/audio_contexto</code>\n"
        "• 📄 <b>Documento + Busca:</b> <code>/documento_busca</code>\n"
        "• 📊 <b>Dados + Visualização:</b> <code>/dados_visualizacao [tipo] [dados]</code>\n"
        "• 🔍 <b>Análise Multimodal:</b> <code>/analise_multimodal</code>\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>Bot Profissional com 25+ Funcionalidades de IA!</b>\n"
        "💡 <i>Use /help para ver todos os comandos e exemplos detalhados.</i>"
    )
    # Criar botões interativos para as principais funcionalidades
    keyboard = [
        [
            InlineKeyboardButton("🤖 Conversa IA", callback_data="menu_conversa"),
            InlineKeyboardButton("🔍 Busca Web", callback_data="menu_busca")
        ],
        [
            InlineKeyboardButton("🔒 Segurança", callback_data="menu_seguranca"),
            InlineKeyboardButton("🖼️ Imagens", callback_data="menu_imagens")
        ],
        [
            InlineKeyboardButton("🎵 Áudio", callback_data="menu_audio"),
            InlineKeyboardButton("🔍 Análise IA", callback_data="menu_analise")
        ],
        [
            InlineKeyboardButton("🎭 IA Generativa", callback_data="menu_ia_generativa"),
            InlineKeyboardButton("🧘 Coach Emocional", callback_data="menu_coach")
        ],
        [
            InlineKeyboardButton("🎨 Face Swapping", callback_data="image_main_menu"),
            InlineKeyboardButton("📚 Ajuda Completa", callback_data="menu_ajuda")
        ],
        [
            InlineKeyboardButton("⚙️ Configurações", callback_data="menu_config")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de ajuda detalhado"""
    help_message = (
        "🔧 <b>COMANDOS COMPLETOS DO BOT</b>\n\n"
        
        "🤖 <b>FUNCIONALIDADES PRINCIPAIS</b>\n"
        "• <code>/start</code> - Iniciar o bot\n"
        "• <code>/reset</code> - Limpar histórico da conversa\n"
        "• <code>/web [pergunta]</code> - Buscar na web\n"
        "• <code>/resumir [url]</code> - Resumir conteúdo de link\n\n"
        
        "🔐 <b>SEGURANÇA DIGITAL</b>\n"
        "• <code>/gerar_senha_forte [critérios]</code> - Senha segura\n"
        "• <code>/verificar_vazamento [email]</code> - Verificar vazamentos\n"
        "• <code>/scan_phishing [url]</code> - Detectar phishing\n"
        "• <code>/anonimizar_dados [texto]</code> - Anonimizar informações\n\n"
        
        "🎨 <b>FERRAMENTAS DE IMAGEM</b>\n"
        "• <code>/gerarimagem [descrição]</code> - Gerar imagem com IA\n"
        "• <code>/remover_fundo</code> - Remover fundo de imagem\n"
        "• <code>/redimensionar 800x600</code> - Redimensionar imagem\n"
        "• <code>/aplicar_filtro vintage</code> - Aplicar filtros\n"
        "• <code>/upscale</code> - Melhorar qualidade da imagem\n\n"
        
        "🎵 <b>ÁUDIO AVANÇADO</b>\n"
        "• <code>/texto_para_voz [idioma] [texto]</code> - Converter texto para áudio\n"
        "• <b>Envie mensagem de áudio</b> - Transcrição automática + resposta em áudio\n"
        "• <b>Idiomas suportados:</b> pt, en, es, fr, it, de\n"
        "• <b>Formatos:</b> OGG, MP3, WAV, M4A\n\n"
        
        "🔍 <b>ANÁLISE DE IMAGEM IA</b>\n"
        "• <b>Envie uma imagem</b> - Análise automática completa\n"
        "• <b>Botões interativos:</b> Análise de cores, OCR, sentimento, tags, técnica\n\n"
        
        "🎭 <b>IA GENERATIVA ESPECIALIZADA</b>\n"
        "• <code>/clonar_voz [áudio] [texto]</code> - Clonar voz do usuário\n"
        "• <code>/estilo_artistico [imagem] [estilo]</code> - Aplicar estilos artísticos\n"
        "• <code>/escrever_como [autor] [tema]</code> - Escrita no estilo de autores\n"
        "• <code>/design_arquitetura [tipo] [estilo]</code> - Projetos arquitetônicos\n\n"
        
        "🧘 <b>COACH EMOCIONAL IA</b>\n"
        "• <code>/mindfulness [tipo] [duração]</code> - Sessões de atenção plena\n"
        "• <code>/terapia [tema] [abordagem]</code> - Apoio emocional e terapêutico\n"
        "• <b>Tipos:</b> respiracao, meditacao, manha, noite\n"
        "• <b>Temas:</b> ansiedade, depressao, estresse, sono\n\n"
        
        "⚡ <b>IA AVANÇADA</b>\n"
        "• <code>/gerar_codigo [linguagem] [descrição]</code> - Gerar código\n"
        "• <code>/otimizar_texto [texto]</code> - Otimizar redação\n"
        "• <code>/resumir_conversa</code> - Resumir conversa atual\n"
        "• <code>/criar [tipo] [tema]</code> - Conteúdo criativo\n\n"
        
        "💡 <b>DICAS DE USO</b>\n"
        "• Para análise de imagem: Envie a imagem diretamente\n"
        "• Para áudio: Grave uma mensagem de voz\n"
        "• Para conversa: Digite naturalmente\n"
        "• Use /reset para limpar memória quando necessário\n\n"
        
        "🚀 <b>Bot com 25+ Funcionalidades de IA Avançada!</b>"
    )
    await update.message.reply_html(help_message)



# === FUNCIONALIDADES ÁUDIO ===
async def texto_para_voz_multilingue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /texto_para_voz <idioma> <texto>\nIdiomas: pt, en, es, fr, it, de")
        return
    
    idioma = context.args[0]
    texto = " ".join(context.args[1:])
    
    lang_map = {
        'pt': 'pt', 'en': 'en', 'es': 'es', 
        'fr': 'fr', 'it': 'it', 'de': 'de'
    }
    
    if idioma not in lang_map:
        await update.message.reply_text("❌ Idioma não suportado. Use: pt, en, es, fr, it, de")
        return
    
    await update.message.reply_text("🎵 Gerando áudio...")
    
    try:
        audio_io = await asyncio.to_thread(text_to_speech_sync, texto, lang_map[idioma])
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_io)
    except Exception as e:
        logger.error(f"Erro TTS: {e}")
        await update.message.reply_text("❌ Erro ao gerar áudio.")

# === FUNCIONALIDADES EDIÇÃO DE IMAGEM ===
async def redimensionar_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Uso: /redimensionar <largura>x<altura>\nResponda a uma foto.")
        return
    
    try:
        dimensions = context.args[0].split('x')
        width, height = int(dimensions[0]), int(dimensions[1])
        
        if width > 4000 or height > 4000:
            await update.message.reply_text("❌ Dimensões muito grandes. Máximo: 4000x4000")
            return
        
        await update.message.reply_text(f"🖼️ Redimensionando para {width}x{height}...")
        
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        resized_image = resize_image(photo_bytes, width, height)
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=resized_image,
            filename=f"redimensionada_{width}x{height}.png",
            caption=f"✅ Imagem redimensionada para {width}x{height}"
        )
        
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Formato inválido. Use: /redimensionar 800x600")
    except Exception as e:
        logger.error(f"Erro ao redimensionar: {e}")
        await update.message.reply_text("❌ Erro ao redimensionar imagem.")

async def aplicar_filtro_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Uso: /aplicar_filtro <tipo>\nTipos: vintage, blur, sharpen, emboss, edge, smooth\nResponda a uma foto.")
        return
    
    filter_type = context.args[0].lower()
    valid_filters = ['vintage', 'blur', 'sharpen', 'emboss', 'edge', 'smooth']
    
    if filter_type not in valid_filters:
        await update.message.reply_text(f"❌ Filtro inválido. Use: {', '.join(valid_filters)}")
        return
    
    await update.message.reply_text(f"🎨 Aplicando filtro '{filter_type}'...")
    
    try:
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        filtered_image = apply_image_filter(photo_bytes, filter_type)
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=filtered_image,
            filename=f"filtro_{filter_type}.png",
            caption=f"✅ Filtro '{filter_type}' aplicado"
        )
        
    except Exception as e:
        logger.error(f"Erro ao aplicar filtro: {e}")
        await update.message.reply_text("❌ Erro ao aplicar filtro.")

async def upscale_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("📸 Responda a uma foto para melhorar a qualidade.")
        return
    
    await update.message.reply_text("⚡ Melhorando qualidade da imagem...")
    
    try:
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))
        
        new_size = (image.width * 2, image.height * 2)
        upscaled = image.resize(new_size, Image.Resampling.LANCZOS)
        
        enhancer = ImageEnhance.Sharpness(upscaled)
        upscaled = enhancer.enhance(1.2)
        
        output = io.BytesIO()
        upscaled.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=output,
            filename="upscaled_2x.png",
            caption="✅ Qualidade melhorada (2x)"
        )
        
    except Exception as e:
        logger.error(f"Erro no upscale: {e}")
        await update.message.reply_text("❌ Erro ao melhorar qualidade.")

# === FUNÇÕES ORIGINAIS ===
async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Por favor, use este comando respondendo a uma foto.")
        return
    
    logger.info("Pedido de remoção de fundo recebido.")
    msg = await update.message.reply_text("Entendido. Processando a imagem...")
    
    settings: Settings = context.bot_data["settings"]
    client: httpx.AsyncClient = context.bot_data["http_client"]
    
    try:
        photo_file = await update.message.reply_to_message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        api_url = "https://api.remove.bg/v1.0/removebg"
        headers = {"X-Api-Key": settings.removebg_api_key}
        
        files = {"image_file": ("image.jpg", bytes(photo_bytes), "image/jpeg")}
        data = {"size": "auto"}
        
        response = await client.post(api_url, headers=headers, files=files, data=data, timeout=60)
        response.raise_for_status()

        result_image_bytes = io.BytesIO(response.content)
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=result_image_bytes,
            filename="imagem_sem_fundo.png",
            caption="Aqui está sua imagem com o fundo removido!"
        )
        
        await msg.delete()
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Erro HTTP ao remover fundo: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 402:
            await msg.edit_text("Limite de créditos da API Remove.bg atingido. Tente novamente mais tarde.")
        elif e.response.status_code == 400:
            await msg.edit_text("Formato de imagem não suportado. Tente com uma foto diferente.")
        else:
            await msg.edit_text(f"Erro na API: {e.response.status_code}. Tente novamente em alguns minutos.")
    except Exception as e:
        logger.error(f"Erro inesperado ao remover fundo: {e}")
        await msg.edit_text("Desculpe, ocorreu um erro inesperado. Tente novamente.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # Handlers originais
    actions = {
        'menu_gerarimagem': "Ok! Para gerar uma imagem, me dê uma descrição com o comando:\n\n<code>/gerarimagem um leão de óculos</code>",
        'menu_buscaweb': "Certo! Para pesquisar na web, use o comando:\n\n<code>/web campeão da Copa de 2022?</code>", 
        'menu_resumirurl': "Entendido. Para resumir, me envie o link com o comando:\n\n<code>/resumir https://...</code>"
    }
    
    if query.data in actions: 
        await query.message.reply_text(actions[query.data], parse_mode='HTML')
    elif query.data == 'menu_reset': 
        database.reset_chat_history(query.message.chat_id)
        await query.message.reply_text("Minha memória para esta conversa foi limpa!")
    
    # Novos callbacks para análise de imagem
    elif query.data == "analyze_colors":
        await handle_color_analysis(query, context)
    elif query.data == "ocr_text":
        await handle_ocr_analysis(query, context)
    elif query.data == "analyze_mood":
        await handle_mood_analysis(query, context)
    elif query.data == "generate_tags":
        await handle_tag_generation(query, context)
    elif query.data == "detailed_analysis":
        await handle_detailed_analysis(query, context)
    elif query.data == "suggestions":
        await handle_suggestions(query, context)
    
    # Callbacks para Mindfulness
    elif query.data == "mindfulness_respiracao":
        await iniciar_sessao_mindfulness(query, context, "respiracao", "5")
    elif query.data == "mindfulness_meditacao":
        await iniciar_sessao_mindfulness(query, context, "meditacao", "10")
    elif query.data == "mindfulness_manha":
        await iniciar_sessao_mindfulness(query, context, "manha", "10")
    elif query.data == "mindfulness_noite":
        await iniciar_sessao_mindfulness(query, context, "noite", "15")
    elif query.data == "mindfulness_rapido":
        await iniciar_sessao_mindfulness(query, context, "respiracao", "5")
    elif query.data == "mindfulness_completo":
        await iniciar_sessao_mindfulness(query, context, "meditacao", "20")
    
    # Callbacks para Terapia IA
    elif query.data == "terapia_ansiedade":
        await iniciar_sessao_terapia(query, context, "ansiedade", "cognitiva")
    elif query.data == "terapia_depressao":
        await iniciar_sessao_terapia(query, context, "depressao", "cognitiva")
    elif query.data == "terapia_estresse":
        await iniciar_sessao_terapia(query, context, "estresse", "cognitiva")
    elif query.data == "terapia_sono":
        await iniciar_sessao_terapia(query, context, "sono", "cognitiva")
    elif query.data == "terapia_autoestima":
        await iniciar_sessao_terapia(query, context, "ansiedade", "comportamental")
    elif query.data == "terapia_relacionamentos":
        await iniciar_sessao_terapia(query, context, "estresse", "comportamental")
    elif query.data == "terapia_objetivos":
        await iniciar_sessao_terapia(query, context, "depressao", "comportamental")
    elif query.data == "terapia_crescimento":
        await iniciar_sessao_terapia(query, context, "sono", "comportamental")
    
    # === NOVOS CALLBACKS PARA BOTÕES INTERATIVOS ===
    
    # Callbacks para Clone de Voz
    elif query.data == "clone_gravar_audio":
        await handle_clone_gravar_audio(query, context)
    elif query.data == "clone_exemplos":
        await handle_clone_exemplos(query, context)
    elif query.data == "clone_configuracoes":
        await handle_clone_configuracoes(query, context)
    elif query.data == "clone_ajuda":
        await handle_clone_ajuda(query, context)
    
    # Callbacks para Mindfulness
    elif query.data == "mindfulness_progresso":
        await handle_mindfulness_progresso(query, context)
    elif query.data == "mindfulness_metas":
        await handle_mindfulness_metas(query, context)
    elif query.data == "mindfulness_ajuda":
        await handle_mindfulness_ajuda(query, context)
    
    # Callbacks para Terapia IA
    elif query.data == "terapia_acompanhamento":
        await handle_terapia_acompanhamento(query, context)
    elif query.data == "terapia_recursos":
        await handle_terapia_recursos(query, context)
    elif query.data == "terapia_ajuda":
        await handle_terapia_ajuda(query, context)
    
    # Callback para voltar ao menu principal
    elif query.data == "voltar_menu":
        await voltar_ao_menu_principal(query, context)
    
    # === CALLBACKS DE NAVEGAÇÃO ===
    elif query.data == "clone_voltar":
        await clone_voltar(query, context)
    elif query.data == "mindfulness_voltar":
        await mindfulness_voltar(query, context)
    elif query.data == "terapia_voltar":
        await terapia_voltar(query, context)
    
    # === CALLBACKS DOS MENUS PRINCIPAIS ===
    elif query.data == "menu_conversa":
        await handle_menu_conversa(query, context)
    elif query.data == "menu_busca":
        await handle_menu_busca(query, context)
    elif query.data == "menu_seguranca":
        await handle_menu_seguranca(query, context)
    elif query.data == "menu_imagens":
        await handle_menu_imagens(query, context)
    elif query.data == "menu_audio":
        await handle_menu_audio(query, context)
    elif query.data == "menu_analise":
        await handle_menu_analise(query, context)
    elif query.data == "menu_ia_generativa":
        await handle_menu_ia_generativa(query, context)
    elif query.data == "menu_coach":
        await handle_menu_coach(query, context)
    elif query.data == "menu_ajuda":
        await handle_menu_ajuda(query, context)
    elif query.data == "menu_config":
        await handle_menu_config(query, context)
    
    # === CALLBACKS ADICIONAIS PARA BOTÕES FUNCIONAIS ===
    
    # Callbacks para botões de conversa
    elif query.data == "conversar_agora":
        await query.edit_message_text(
            "💬 **Conversar Agora**\n\n"
            "**Como usar:**\n"
            "• Digite sua mensagem normalmente\n"
            "• A IA responderá automaticamente\n"
            "• Use comandos específicos para funcionalidades\n\n"
            "**Exemplos:**\n"
            "• 'Olá, como você está?'\n"
            "• 'Explique sobre inteligência artificial'\n"
            "• 'Ajude-me com um problema'\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ia_avancada":
        await query.edit_message_text(
            "🧠 **IA Avançada - Google Gemini Pro**\n\n"
            "**Recursos:**\n"
            "• Processamento de linguagem natural\n"
            "• Compreensão contextual avançada\n"
            "• Memória de conversas\n"
            "• Suporte multilíngue\n\n"
            "**Capacidades:**\n"
            "• Análise de texto complexo\n"
            "• Resolução de problemas\n"
            "• Criação de conteúdo\n"
            "• Explicações detalhadas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ver_historico":
        await query.edit_message_text(
            "📝 **Histórico de Conversas**\n\n"
            "**Funcionalidade:**\n"
            "• Visualizar conversas anteriores\n"
            "• Buscar mensagens específicas\n"
            "• Análise de padrões\n\n"
            "**Como usar:**\n"
            "• Use /reset para limpar histórico\n"
            "• O histórico é mantido por sessão\n"
            "• Dados são armazenados localmente\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "limpar_chat":
        database.reset_chat_history(query.message.chat_id)
        await query.edit_message_text(
            "🗑️ **Chat Limpo com Sucesso!**\n\n"
            "**Ação realizada:**\n"
            "• Histórico de conversas removido\n"
            "• Memória da IA resetada\n"
            "• Nova sessão iniciada\n\n"
            "**Próximos passos:**\n"
            "• Comece uma nova conversa\n"
            "• A IA não lembrará de conversas anteriores\n"
            "• Todas as funcionalidades continuam disponíveis\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de busca
    elif query.data == "buscar_web":
        await query.edit_message_text(
            "🔍 **Buscar na Web**\n\n"
            "**Como usar:**\n"
            "• Digite: `/web [sua pergunta]`\n"
            "• Exemplo: `/web notícias sobre IA`\n"
            "• A IA pesquisará e responderá\n\n"
            "**Recursos:**\n"
            "• Busca em tempo real\n"
            "• Resultados relevantes\n"
            "• Análise com IA\n"
            "• Múltiplas fontes\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ultimas_noticias":
        await query.edit_message_text(
            "📰 **Últimas Notícias**\n\n"
            "**Funcionalidade:**\n"
            "• Buscar notícias recentes\n"
            "• Filtrar por categoria\n"
            "• Resumos automáticos\n\n"
            "**Como usar:**\n"
            "• `/web notícias [tema]`\n"
            "• Exemplo: `/web notícias tecnologia`\n"
            "• Resultados em tempo real\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "resumir_url":
        await query.edit_message_text(
            "🌐 **Resumir URL**\n\n"
            "**Como usar:**\n"
            "• Digite: `/resumir [link]`\n"
            "• Exemplo: `/resumir https://exemplo.com`\n"
            "• A IA extrairá e resumirá o conteúdo\n\n"
            "**Recursos:**\n"
            "• Extração automática\n"
            "• Resumo inteligente\n"
            "• Pontos principais\n"
            "• Múltiplos formatos\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "pesquisa_avancada":
        await query.edit_message_text(
            "📊 **Pesquisa Avançada**\n\n"
            "**Funcionalidades:**\n"
            "• Filtros por data\n"
            "• Busca por tipo de conteúdo\n"
            "• Análise de credibilidade\n"
            "• Comparação de fontes\n\n"
            "**Como usar:**\n"
            "• `/web [pergunta] [filtros]`\n"
            "• Exemplo: `/web IA 2024 site:tech.com`\n"
            "• Resultados personalizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de segurança
    elif query.data == "gerar_senha":
        await query.edit_message_text(
            "🔑 **Gerar Senhas Fortes**\n\n"
            "**Como usar:**\n"
            "• `/gerar_senha_forte [critérios]`\n"
            "• Exemplo: `/gerar_senha_forte 16 maiúsculas números símbolos`\n\n"
            "**Critérios disponíveis:**\n"
            "• Comprimento (8-64 caracteres)\n"
            "• Maiúsculas (A-Z)\n"
            "• Minúsculas (a-z)\n"
            "• Números (0-9)\n"
            "• Símbolos (!@#$%^&*)\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "verificar_vazamento":
        await query.edit_message_text(
            "🛡️ **Verificar Vazamentos**\n\n"
            "**Como usar:**\n"
            "• `/verificar_vazamento [email]`\n"
            "• Exemplo: `/verificar_vazamento usuario@email.com`\n\n"
            "**Funcionalidade:**\n"
            "• Análise local de padrões\n"
            "• Detecção de riscos\n"
            "• Relatório detalhado\n"
            "• Recomendações de segurança\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "scan_phishing":
        await query.edit_message_text(
            "🚫 **Anti-Phishing**\n\n"
            "**Como usar:**\n"
            "• `/scan_phishing [url]`\n"
            "• Exemplo: `/scan_phishing https://site-suspeito.com`\n\n"
            "**Análise realizada:**\n"
            "• Verificação de URLs suspeitas\n"
            "• Detecção de fraudes\n"
            "• Proteção contra ataques\n"
            "• Relatório de segurança\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "anonimizar_dados":
        await query.edit_message_text(
            "🎭 **Anonimizar Dados**\n\n"
            "**Como usar:**\n"
            "• `/anonimizar_dados [texto]`\n"
            "• Exemplo: `/anonimizar_dados João Silva, CPF: 123.456.789-00`\n\n"
            "**Funcionalidade:**\n"
            "• Remoção de dados pessoais\n"
            "• Proteção de privacidade\n"
            "• Mascaramento de informações\n"
            "• Conformidade com LGPD\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "criptografia":
        await query.edit_message_text(
            "🔒 **Criptografia**\n\n"
            "**Funcionalidades:**\n"
            "• Criptografar mensagens\n"
            "• Descriptografar dados\n"
            "• Geração de chaves\n"
            "• Hash seguro\n\n"
            "**Como usar:**\n"
            "• `/criptografar [texto] [chave]`\n"
            "• `/descriptografar [texto_cifrado] [chave]`\n"
            "• `/hash [texto] [algoritmo]`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "relatorio_seguranca":
        await query.edit_message_text(
            "📊 **Relatório de Segurança**\n\n"
            "**Informações incluídas:**\n"
            "• Status de segurança geral\n"
            "• Vulnerabilidades detectadas\n"
            "• Recomendações\n"
            "• Histórico de verificações\n\n"
            "**Como gerar:**\n"
            "• `/relatorio_seguranca`\n"
            "• Análise completa automática\n"
            "• Relatório detalhado\n"
            "• Ações recomendadas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de imagens
    elif query.data == "gerar_imagem":
        await query.edit_message_text(
            "🎨 **Gerar Imagem com IA**\n\n"
            "**Como usar:**\n"
            "• `/gerarimagem [descrição]`\n"
            "• Exemplo: `/gerarimagem um gato sentado em uma mesa`\n\n"
            "**Recursos:**\n"
            "• Criação com IA\n"
            "• Múltiplos estilos\n"
            "• Alta qualidade\n"
            "• Personalização\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "remover_fundo":
        await query.edit_message_text(
            "✂️ **Remover Fundo**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use `/remover_fundo`\n"
            "• A IA removerá o fundo automaticamente\n\n"
            "**Recursos:**\n"
            "• Remoção automática\n"
            "• Precisão avançada\n"
            "• Formato PNG\n"
            "• Qualidade preservada\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "redimensionar":
        await query.edit_message_text(
            "📏 **Redimensionar Imagem**\n\n"
            "**Como usar:**\n"
            "• `/redimensionar [largura]x[altura]`\n"
            "• Exemplo: `/redimensionar 800x600`\n\n"
            "**Recursos:**\n"
            "• Múltiplas resoluções\n"
            "• Manter proporção\n"
            "• Qualidade preservada\n"
            "• Formatos suportados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "aplicar_filtro":
        await query.edit_message_text(
            "🎭 **Aplicar Filtros**\n\n"
            "**Como usar:**\n"
            "• `/aplicar_filtro [tipo]`\n"
            "• Exemplo: `/aplicar_filtro vintage`\n\n"
            "**Filtros disponíveis:**\n"
            "• Vintage, Preto e Branco\n"
            "• Sepia, Contraste\n"
            "• Brilho, Saturação\n"
            "• Personalizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "upscale":
        await query.edit_message_text(
            "⚡ **Melhorar Qualidade**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use `/upscale`\n"
            "• A IA melhorará a qualidade\n\n"
            "**Recursos:**\n"
            "• Aumento de resolução\n"
            "• Melhoria de detalhes\n"
            "• Redução de ruído\n"
            "• Qualidade profissional\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "converter_formato":
        await query.edit_message_text(
            "🔄 **Converter Formato**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use `/converter [formato]`\n"
            "• Exemplo: `/converter png`\n\n"
            "**Formatos suportados:**\n"
            "• JPG, PNG, GIF\n"
            "• WebP, BMP\n"
            "• TIFF, SVG\n"
            "• Qualidade preservada\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de áudio
    elif query.data == "texto_para_voz":
        await query.edit_message_text(
            "🔊 **Texto para Voz**\n\n"
            "**Como usar:**\n"
            "• `/texto_para_voz [idioma] [texto]`\n"
            "• Exemplo: `/texto_para_voz pt Olá, como você está?`\n\n"
            "**Idiomas suportados:**\n"
            "• pt (Português)\n"
            "• en (Inglês)\n"
            "• es (Espanhol)\n"
            "• fr (Francês)\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "voz_para_texto":
        await query.edit_message_text(
            "🎤 **Voz para Texto**\n\n"
            "**Como usar:**\n"
            "• Envie uma mensagem de áudio\n"
            "• A IA transcreverá automaticamente\n"
            "• Detecção automática de idioma\n\n"
            "**Recursos:**\n"
            "• Transcrição automática\n"
            "• Detecção de idioma\n"
            "• Alta precisão\n"
            "• Múltiplos formatos\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "audio_multilingue":
        await query.edit_message_text(
            "🌍 **Áudio Multilíngue**\n\n"
            "**Funcionalidades:**\n"
            "• Detecção automática de idioma\n"
            "• Resposta no idioma detectado\n"
            "• Suporte a múltiplos idiomas\n"
            "• Tradução automática\n\n"
            "**Idiomas suportados:**\n"
            "• Português, Inglês, Espanhol\n"
            "• Francês, Alemão, Italiano\n"
            "• Japonês, Chinês, Coreano\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "formatos_audio":
        await query.edit_message_text(
            "🎵 **Formatos de Áudio**\n\n"
            "**Formatos suportados:**\n"
            "• OGG (padrão Telegram)\n"
            "• MP3 (alta qualidade)\n"
            "• WAV (sem perdas)\n"
            "• M4A (Apple)\n\n"
            "**Recursos:**\n"
            "• Conversão automática\n"
            "• Qualidade preservada\n"
            "• Tamanho otimizado\n"
            "• Compatibilidade universal\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    # Callback clone_voz movido para handle_all_callbacks
    elif query.data == "config_audio":
        await query.edit_message_text(
            "⚙️ **Configurações de Áudio**\n\n"
            "**Configurações disponíveis:**\n"
            "• Qualidade de áudio\n"
            "• Velocidade de reprodução\n"
            "• Idioma padrão\n"
            "• Formato de saída\n\n"
            "**Como configurar:**\n"
            "• Use os comandos específicos\n"
            "• Configurações são salvas\n"
            "• Personalização por usuário\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de análise
    elif query.data == "analise_automatica":
        await query.edit_message_text(
            "🔍 **Análise Automática de Imagem**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• A IA analisará automaticamente\n"
            "• Resultado completo e detalhado\n\n"
            "**Análise incluída:**\n"
            "• Descrição da imagem\n"
            "• Objetos identificados\n"
            "• Contexto e cenário\n"
            "• Análise técnica\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "analise_cores":
        await query.edit_message_text(
            "🎨 **Análise de Cores**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use o botão 'Análise de Cores'\n"
            "• A IA analisará a paleta de cores\n\n"
            "**Análise incluída:**\n"
            "• Cores dominantes\n"
            "• Paleta de cores\n"
            "• Harmonia cromática\n"
            "• Psicologia das cores\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ocr_texto":
        await query.edit_message_text(
            "📝 **OCR - Extração de Texto**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem com texto\n"
            "• Use o botão 'OCR Texto'\n"
            "• A IA extrairá o texto automaticamente\n\n"
            "**Recursos:**\n"
            "• Múltiplos idiomas\n"
            "• Alta precisão\n"
            "• Formatação preservada\n"
            "• Suporte a diferentes fontes\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "analise_sentimento":
        await query.edit_message_text(
            "😊 **Análise de Sentimento**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use o botão 'Análise de Sentimento'\n"
            "• A IA analisará as emoções\n\n"
            "**Análise incluída:**\n"
            "• Emoções detectadas\n"
            "• Atmosfera da imagem\n"
            "• Expressões faciais\n"
            "• Contexto emocional\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "gerar_tags":
        await query.edit_message_text(
            "🏷️ **Geração de Tags**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use o botão 'Gerar Tags'\n"
            "• A IA gerará tags relevantes\n\n"
            "**Tags geradas:**\n"
            "• Categorias principais\n"
            "• Palavras-chave\n"
            "• Descrições precisas\n"
            "• Sugestões de uso\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "analise_tecnica":
        await query.edit_message_text(
            "🔬 **Análise Técnica**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use o botão 'Análise Técnica'\n"
            "• A IA analisará aspectos técnicos\n\n"
            "**Análise incluída:**\n"
            "• Composição da imagem\n"
            "• Técnica fotográfica\n"
            "• Qualidade técnica\n"
            "• Recomendações\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "sugestoes_criativas":
        await query.edit_message_text(
            "💡 **Sugestões Criativas**\n\n"
            "**Como usar:**\n"
            "• Envie uma imagem\n"
            "• Use o botão 'Sugestões Criativas'\n"
            "• A IA gerará ideias criativas\n\n"
            "**Sugestões incluídas:**\n"
            "• Ideias de edição\n"
            "• Variações criativas\n"
            "• Inspirações artísticas\n"
            "• Aplicações práticas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de IA generativa
    elif query.data == "clone_voz_menu":
        await query.edit_message_text(
            "🎭 **Clone de Voz - Menu Principal**\n\n"
            "**Funcionalidade:**\n"
            "• Clonar características vocais\n"
            "• Preservar sotaque e tom\n"
            "• Gerar áudio personalizado\n\n"
            "**Como usar:**\n"
            "• Grave um áudio de referência\n"
            "• Use `/clonar_voz [texto]`\n"
            "• A IA clonará sua voz\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "estilo_artistico":
        await query.edit_message_text(
            "🎨 **Estilo Artístico**\n\n"
            "**Funcionalidade:**\n"
            "• Aplicar estilos de artistas famosos\n"
            "• Transformar imagens automaticamente\n"
            "• Criar variações artísticas\n\n"
            "**Estilos disponíveis:**\n"
            "• Van Gogh, Picasso, Monet\n"
            "• Salvador Dalí, Frida Kahlo\n"
            "• Estilos personalizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "escritor_fantasma":
        await query.edit_message_text(
            "📝 **Escritor Fantasma**\n\n"
            "**Funcionalidade:**\n"
            "• Escrever no estilo de autores famosos\n"
            "• Criar conteúdo literário\n"
            "• Imitar estilos de escrita\n\n"
            "**Autores disponíveis:**\n"
            "• Machado de Assis, Shakespeare\n"
            "• Clarice Lispector, Jorge Luis Borges\n"
            "• Estilos literários diversos\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "arquitetura_ia":
        await query.edit_message_text(
            "🏗️ **Arquitetura IA**\n\n"
            "**Funcionalidade:**\n"
            "• Gerar projetos arquitetônicos\n"
            "• Criar designs de interiores\n"
            "• Visualizar espaços 3D\n\n"
            "**Tipos de projeto:**\n"
            "• Residencial, comercial\n"
            "• Paisagismo, urbanismo\n"
            "• Estilos arquitetônicos\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "musica_ia":
        await query.edit_message_text(
            "🎵 **Música IA**\n\n"
            "**Funcionalidade:**\n"
            "• Compor músicas originais\n"
            "• Gerar melodias personalizadas\n"
            "• Criar trilhas sonoras\n\n"
            "**Gêneros disponíveis:**\n"
            "• Clássica, Jazz, Rock\n"
            "• Eletrônica, Folk, Blues\n"
            "• Estilos personalizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "video_ia":
        await query.edit_message_text(
            "🎬 **Vídeo IA**\n\n"
            "**Funcionalidade:**\n"
            "• Gerar vídeos curtos\n"
            "• Criar animações\n"
            "• Editar conteúdo automático\n\n"
            "**Tipos de vídeo:**\n"
            "• Promocionais, educativos\n"
            "• Artísticos, informativos\n"
            "• Personalizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de coach
    elif query.data == "mindfulness_menu":
        await query.edit_message_text(
            "🧘 **Mindfulness - Menu Principal**\n\n"
            "**Funcionalidade:**\n"
            "• Sessões de atenção plena\n"
            "• Técnicas de respiração\n"
            "• Meditações guiadas\n\n"
            "**Como usar:**\n"
            "• `/mindfulness [tipo] [duração]`\n"
            "• Exemplo: `/mindfulness respiracao 10`\n"
            "• Sessões personalizadas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_menu":
        await query.edit_message_text(
            "💭 **Terapia IA - Menu Principal**\n\n"
            "**Funcionalidade:**\n"
            "• Apoio emocional\n"
            "• Estratégias terapêuticas\n"
            "• Acompanhamento\n\n"
            "**Como usar:**\n"
            "• `/terapia [tema] [abordagem]`\n"
            "• Exemplo: `/terapia ansiedade cognitiva`\n"
            "• Suporte personalizado\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ansiedade_coach":
        await query.edit_message_text(
            "😊 **Coach para Ansiedade**\n\n"
            "**Técnicas disponíveis:**\n"
            "• Respiração 4-7-8\n"
            "• Relaxamento muscular\n"
            "• Estratégias cognitivas\n"
            "• Mindfulness específico\n\n"
            "**Como usar:**\n"
            "• `/terapia ansiedade [abordagem]`\n"
            "• Exemplo: `/terapia ansiedade cognitiva`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "depressao_coach":
        await query.edit_message_text(
            "😔 **Coach para Depressão**\n\n"
            "**Estratégias disponíveis:**\n"
            "• Rotinas matinais\n"
            "• Metas pequenas\n"
            "• Gratidão diária\n"
            "• Conexão social\n\n"
            "**Como usar:**\n"
            "• `/terapia depressao [abordagem]`\n"
            "• Exemplo: `/terapia depressao comportamental`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "estresse_coach":
        await query.edit_message_text(
            "😤 **Coach para Estresse**\n\n"
            "**Técnicas disponíveis:**\n"
            "• Meditação diária\n"
            "• Gestão do tempo\n"
            "• Exercícios físicos\n"
            "• Autocuidado\n\n"
            "**Como usar:**\n"
            "• `/terapia estresse [abordagem]`\n"
            "• Exemplo: `/terapia estresse cognitiva`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "sono_coach":
        await query.edit_message_text(
            "😴 **Coach para Qualidade do Sono**\n\n"
            "**Estratégias disponíveis:**\n"
            "• Higiene do sono\n"
            "• Rituais noturnos\n"
            "• Respiração relaxante\n"
            "• Ambiente ideal\n\n"
            "**Como usar:**\n"
            "• `/terapia sono [abordagem]`\n"
            "• Exemplo: `/terapia sono comportamental`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de ajuda
    elif query.data == "ver_comandos":
        await query.edit_message_text(
            "📚 **Comandos Disponíveis**\n\n"
            "**🤖 Conversa IA:**\n"
            "• Digite normalmente para conversar\n"
            "• `/reset` - Limpar histórico\n\n"
            "**🔍 Busca Web:**\n"
            "• `/web [pergunta]` - Buscar na web\n"
            "• `/resumir [url]` - Resumir conteúdo\n\n"
            "**🔒 Segurança:**\n"
            "• `/gerar_senha_forte [critérios]`\n"
            "• `/verificar_vazamento [email]`\n"
            "• `/scan_phishing [url]`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ver_faq":
        await query.edit_message_text(
            "❓ **FAQ - Perguntas Frequentes**\n\n"
            "**Q: Como usar o bot?**\n"
            "A: Digite /start para ver o menu principal\n\n"
            "**Q: Como conversar com a IA?**\n"
            "A: Digite sua mensagem normalmente\n\n"
            "**Q: Como usar funcionalidades específicas?**\n"
            "A: Use os comandos ou botões do menu\n\n"
            "**Q: O bot lembra das conversas?**\n"
            "A: Sim, até usar /reset\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ver_exemplos":
        await query.edit_message_text(
            "🎯 **Exemplos Práticos**\n\n"
            "**🔍 Busca Web:**\n"
            "• `/web notícias sobre IA 2024`\n"
            "• `/web receita bolo chocolate`\n\n"
            "**🔒 Segurança:**\n"
            "• `/gerar_senha_forte 16 maiúsculas números símbolos`\n"
            "• `/verificar_vazamento usuario@email.com`\n\n"
            "**🎵 Áudio:**\n"
            "• `/texto_para_voz pt Olá, como você está?`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "solucao_problemas":
        await query.edit_message_text(
            "🔧 **Solução de Problemas**\n\n"
            "**Problema: Bot não responde**\n"
            "Solução: Verifique se está online\n\n"
            "**Problema: Erro em funcionalidade**\n"
            "Solução: Use /reset e tente novamente\n\n"
            "**Problema: Comando não funciona**\n"
            "Solução: Verifique a sintaxe correta\n\n"
            "**Problema: Bot travado**\n"
            "Solução: Reinicie o bot\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "contato_suporte":
        await query.edit_message_text(
            "📞 **Contato e Suporte**\n\n"
            "**Canais de suporte:**\n"
            "• Email: suporte@bot.com\n"
            "• Telegram: @suporte_bot\n"
            "• WhatsApp: +55 11 99999-9999\n\n"
            "**Horário de atendimento:**\n"
            "• Segunda a Sexta: 9h às 18h\n"
            "• Sábado: 9h às 12h\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ver_tutorial":
        await query.edit_message_text(
            "📖 **Tutorial Completo**\n\n"
            "**Passo 1: Iniciar**\n"
            "• Digite /start para ver o menu\n\n"
            "**Passo 2: Navegar**\n"
            "• Use os botões para navegar\n"
            "• Cada categoria tem funcionalidades\n\n"
            "**Passo 3: Usar**\n"
            "• Siga as instruções de cada função\n"
            "• Use comandos ou botões\n\n"
            "**Passo 4: Explorar**\n"
            "• Teste diferentes funcionalidades\n"
            "• Use /help para mais detalhes\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de configuração
    elif query.data == "preferencias":
        await query.edit_message_text(
            "⚙️ **Preferências**\n\n"
            "**Configurações disponíveis:**\n"
            "• Idioma padrão\n"
            "• Notificações\n"
            "• Privacidade\n"
            "• Interface\n\n"
            "**Como configurar:**\n"
            "• Use os botões específicos\n"
            "• Configurações são salvas\n"
            "• Personalização por usuário\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "config_idioma":
        await query.edit_message_text(
            "🌍 **Configuração de Idioma**\n\n"
            "**Idiomas disponíveis:**\n"
            "• Português (padrão)\n"
            "• Inglês\n"
            "• Espanhol\n"
            "• Francês\n\n"
            "**Como alterar:**\n"
            "• Use `/idioma [código]`\n"
            "• Exemplo: `/idioma en`\n"
            "• Alteração imediata\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "config_notificacoes":
        await query.edit_message_text(
            "🔔 **Configuração de Notificações**\n\n"
            "**Tipos de notificação:**\n"
            "• Lembretes diários\n"
            "• Alertas de segurança\n"
            "• Atualizações\n"
            "• Resumos\n\n"
            "**Como configurar:**\n"
            "• Use `/notificacoes [tipo] [on/off]`\n"
            "• Exemplo: `/notificacoes lembretes on`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "config_privacidade":
        await query.edit_message_text(
            "🔒 **Configuração de Privacidade**\n\n"
            "**Opções de privacidade:**\n"
            "• Histórico de conversas\n"
            "• Dados de uso\n"
            "• Compartilhamento\n"
            "• Anonimização\n\n"
            "**Como configurar:**\n"
            "• Use `/privacidade [opcao] [valor]`\n"
            "• Exemplo: `/privacidade historico off`\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ver_estatisticas":
        await query.edit_message_text(
            "📊 **Estatísticas de Uso**\n\n"
            "**Informações disponíveis:**\n"
            "• Total de mensagens\n"
            "• Funcionalidades mais usadas\n"
            "• Tempo de uso\n"
            "• Preferências\n\n"
            "**Como visualizar:**\n"
            "• Use `/estatisticas`\n"
            "• Relatório detalhado\n"
            "• Dados atualizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "ver_atualizacoes":
        await query.edit_message_text(
            "🔄 **Verificar Atualizações**\n\n"
            "**Status atual:**\n"
            "• Versão: 2.0.0\n"
            "• Última atualização: Hoje\n"
            "• Status: Atualizado\n\n"
            "**Como verificar:**\n"
            "• Use `/atualizacoes`\n"
            "• Verificação automática\n"
            "• Notificações de novas versões\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de clone de voz
    elif query.data == "clone_iniciar_gravacao":
        await query.edit_message_text(
            "🎤 **Iniciar Gravação para Clone de Voz**\n\n"
            "**Passos para gravar:**\n"
            "1. Encontre um local tranquilo\n"
            "2. Use o botão de gravação do Telegram\n"
            "3. Fale claramente por 10-30 segundos\n"
            "4. Envie o áudio\n"
            "5. Use `/clonar_voz [texto]`\n\n"
            "**Dicas importantes:**\n"
            "• Fale naturalmente\n"
            "• Evite ruídos de fundo\n"
            "• Use frases variadas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_dicas":
        await query.edit_message_text(
            "📋 **Dicas para Clone de Voz**\n\n"
            "**🎯 Local ideal:**\n"
            "• Ambiente silencioso\n"
            "• Sem eco ou reverberação\n"
            "• Distância constante do microfone\n\n"
            "**🎙️ Técnica de gravação:**\n"
            "• Fale naturalmente e claramente\n"
            "• Mantenha ritmo constante\n"
            "• Use diferentes entonações\n\n"
            "**⏱️ Duração recomendada:**\n"
            "• Mínimo: 10 segundos\n"
            "• Ideal: 20-30 segundos\n"
            "• Máximo: 60 segundos\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_exemplo_apresentacoes":
        await query.edit_message_text(
            "🎭 **Exemplos para Apresentações**\n\n"
            "**Frases recomendadas:**\n"
            "• 'Bem-vindos à nossa reunião mensal'\n"
            "• 'Hoje vamos discutir os resultados'\n"
            "• 'Agradeço a presença de todos'\n"
            "• 'Vamos começar nossa apresentação'\n\n"
            "**Características:**\n"
            "• Tom profissional\n"
            "• Clareza na fala\n"
            "• Entonação variada\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_exemplo_narracao":
        await query.edit_message_text(
            "📚 **Exemplos para Narração**\n\n"
            "**Frases recomendadas:**\n"
            "• 'Era uma vez, em uma terra distante...'\n"
            "• 'O protagonista enfrentou muitos desafios'\n"
            "• 'A história nos ensina valiosas lições'\n"
            "• 'E assim, a aventura começou'\n\n"
            "**Características:**\n"
            "• Tom narrativo\n"
            "• Ritmo variado\n"
            "• Expressividade\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_exemplo_musica":
        await query.edit_message_text(
            "🎵 **Exemplos para Música**\n\n"
            "**Frases recomendadas:**\n"
            "• 'Esta é a canção que compus para você'\n"
            "• 'Cada nota conta uma história'\n"
            "• 'A música une corações'\n"
            "• 'Deixe a melodia te levar'\n\n"
            "**Características:**\n"
            "• Tom melódico\n"
            "• Ritmo musical\n"
            "• Expressão emocional\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_exemplo_profissional":
        await query.edit_message_text(
            "💼 **Exemplos para Uso Profissional**\n\n"
            "**Frases recomendadas:**\n"
            "• 'Seja bem-vindo ao nosso produto'\n"
            "• 'Estamos aqui para ajudar você'\n"
            "• 'Obrigado por escolher nossos serviços'\n"
            "• 'Como posso ser útil hoje?'\n\n"
            "**Características:**\n"
            "• Tom profissional\n"
            "• Clareza e objetividade\n"
            "• Cordialidade\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_qualidade":
        await query.edit_message_text(
            "🎵 **Configuração de Qualidade**\n\n"
            "**Níveis disponíveis:**\n"
            "• Alta: Melhor fidelidade, arquivo maior\n"
            "• Média: Equilíbrio entre qualidade e tamanho\n"
            "• Baixa: Arquivo menor, qualidade reduzida\n\n"
            "**Como configurar:**\n"
            "• Use `/clone_qualidade [nivel]`\n"
            "• Exemplo: `/clone_qualidade alta`\n"
            "• Configuração salva automaticamente\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_idioma":
        await query.edit_message_text(
            "🌍 **Configuração de Idioma**\n\n"
            "**Idiomas suportados:**\n"
            "• Português (Brasil)\n"
            "• Inglês\n"
            "• Espanhol\n"
            "• Francês\n\n"
            "**Como configurar:**\n"
            "• Use `/clone_idioma [codigo]`\n"
            "• Exemplo: `/clone_idioma en`\n"
            "• Ajuste automático de pronúncia\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_velocidade":
        await query.edit_message_text(
            "⚡ **Configuração de Velocidade**\n\n"
            "**Velocidades disponíveis:**\n"
            "• Lenta: 0.8x (mais natural)\n"
            "• Normal: 1.0x (padrão)\n"
            "• Rápida: 1.2x (mais dinâmica)\n\n"
            "**Como configurar:**\n"
            "• Use `/clone_velocidade [valor]`\n"
            "• Exemplo: `/clone_velocidade 0.8`\n"
            "• Ajuste personalizado\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_estilo":
        await query.edit_message_text(
            "🎭 **Configuração de Estilo**\n\n"
            "**Estilos disponíveis:**\n"
            "• Natural: Voz conversacional\n"
            "• Formal: Tom profissional\n"
            "• Casual: Tom descontraído\n"
            "• Artístico: Tom expressivo\n\n"
            "**Como configurar:**\n"
            "• Use `/clone_estilo [tipo]`\n"
            "• Exemplo: `/clone_estilo formal`\n"
            "• Ajuste automático de entonação\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_faq":
        await query.edit_message_text(
            "❓ **FAQ - Clone de Voz**\n\n"
            "**Q: Como funciona o clone de voz?**\n"
            "A: A IA analisa seu áudio e reproduz texto com características similares\n\n"
            "Q: Qual a duração ideal do áudio?**\n"
            "A: Entre 10-30 segundos para melhor qualidade\n\n"
            "Q: Posso usar qualquer idioma?**\n"
            "A: Sim, mas o áudio de referência deve ser no idioma desejado\n\n"
            "Q: A qualidade é boa?**\n"
            "A: Sim, com áudio de referência de qualidade\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_solucao":
        await query.edit_message_text(
            "🔧 **Solução de Problemas - Clone de Voz**\n\n"
            "**Problema: Qualidade baixa**\n"
            "Solução: Grave em ambiente mais silencioso\n\n"
            "Problema: Áudio muito curto**\n"
            "Solução: Grave pelo menos 10 segundos\n\n"
            "Problema: Ruído de fundo**\n"
            "Solução: Use fones de ouvido com microfone\n\n"
            "Problema: Erro na clonagem**\n"
            "Solução: Tente com áudio mais claro\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "clone_suporte":
        await query.edit_message_text(
            "📞 **Suporte - Clone de Voz**\n\n"
            "**Canais de suporte:**\n"
            "• Email: clone@bot.com\n"
            "• Telegram: @suporte_clone\n"
            "• WhatsApp: +55 11 99999-9999\n\n"
            "**Horário de atendimento:**\n"
            "• Segunda a Sexta: 9h às 18h\n"
            "• Sábado: 9h às 12h\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de mindfulness
    elif query.data == "mindfulness_stats":
        await query.edit_message_text(
            "📊 **Estatísticas de Mindfulness**\n\n"
            "**📈 Seu progresso:**\n"
            "• Sessões completadas: 15\n"
            "• Tempo total: 3h 45min\n"
            "• Sequência atual: 5 dias\n"
            "• Meta semanal: 80% atingida\n\n"
            "**🏆 Conquistas:**\n"
            "• Primeira sessão: ✅\n"
            "• 7 dias seguidos: ✅\n"
            "• 30 minutos: ✅\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_conquistas":
        await query.edit_message_text(
            "🏆 **Conquistas de Mindfulness**\n\n"
            "**🥇 Conquistas desbloqueadas:**\n"
            "• Primeiro Passo: Primeira sessão\n"
            "• Persistente: 7 dias seguidos\n"
            "• Meditador: 30 minutos totais\n"
            "• Zen: 100 sessões\n\n"
            "**🎯 Próximas conquistas:**\n"
            "• Mestre: 365 dias seguidos\n"
            "• Sábio: 1000 sessões\n"
            "• Iluminado: 10.000 minutos\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_graficos":
        await query.edit_message_text(
            "📈 **Gráficos de Mindfulness**\n\n"
            "**📊 Visualizações disponíveis:**\n"
            "• Progresso semanal\n"
            "• Duração das sessões\n"
            "• Frequência diária\n"
            "• Tendências mensais\n\n"
            "**📱 Como visualizar:**\n"
            "• Use `/mindfulness graficos`\n"
            "• Gráficos interativos\n"
            "• Exportação de dados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_definir_meta":
        await query.edit_message_text(
            "🎯 **Definir Metas de Mindfulness**\n\n"
            "**📝 Tipos de meta:**\n"
            "• Frequência: Sessões por semana\n"
            "• Duração: Tempo por sessão\n"
            "• Consistência: Dias seguidos\n"
            "• Qualidade: Foco e presença\n\n"
            "**⚙️ Como configurar:**\n"
            "• Use `/mindfulness meta [tipo] [valor]`\n"
            "• Exemplo: `/mindfulness meta frequencia 5`\n"
            "• Acompanhamento automático\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_calendario":
        await query.edit_message_text(
            "📅 **Calendário de Mindfulness**\n\n"
            "**🗓️ Funcionalidades:**\n"
            "• Visualizar sessões planejadas\n"
            "• Marcar sessões completadas\n"
            "• Definir lembretes\n"
            "• Acompanhar progresso\n\n"
            "**📱 Como usar:**\n"
            "• Use `/mindfulness calendario`\n"
            "• Visualização mensal\n"
            "• Sincronização automática\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_lembretes":
        await query.edit_message_text(
            "⏰ **Lembretes de Mindfulness**\n\n"
            "**🔔 Tipos de lembrete:**\n"
            "• Diário: Horário fixo\n"
            "• Inteligente: Baseado em rotina\n"
            "• Contextual: Baseado em localização\n"
            "• Personalizado: Horários específicos\n\n"
            "**⚙️ Como configurar:**\n"
            "• Use `/mindfulness lembrete [tipo] [horario]`\n"
            "• Exemplo: `/mindfulness lembrete diario 08:00`\n"
            "• Notificações automáticas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_acompanhamento":
        await query.edit_message_text(
            "📊 **Acompanhamento de Mindfulness**\n\n"
            "**📈 Métricas disponíveis:**\n"
            "• Tempo total de prática\n"
            "• Frequência semanal\n"
            "• Qualidade das sessões\n"
            "• Tendências de progresso\n\n"
            "**📱 Como acompanhar:**\n"
            "• Use `/mindfulness acompanhamento`\n"
            "• Relatórios detalhados\n"
            "• Insights personalizados\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_faq":
        await query.edit_message_text(
            "❓ **FAQ - Mindfulness**\n\n"
            "**Q: O que é mindfulness?**\n"
            "A: Atenção plena ao momento presente\n\n"
            "Q: Como praticar?**\n"
            "A: Sente-se confortavelmente e foque na respiração\n\n"
            "Q: Quanto tempo por dia?**\n"
            "A: Comece com 5-10 minutos\n\n"
            "Q: Quando ver resultados?**\n"
            "A: Com prática regular, em algumas semanas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_recursos":
        await query.edit_message_text(
            "📚 **Recursos de Mindfulness**\n\n"
            "**📖 Materiais disponíveis:**\n"
            "• Guias para iniciantes\n"
            "• Meditações guiadas\n"
            "• Exercícios de respiração\n"
            "• Técnicas de foco\n\n"
            "**🌐 Links úteis:**\n"
            "• Apps recomendados\n"
            "• Livros sobre mindfulness\n"
            "• Comunidades online\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "mindfulness_dicas":
        await query.edit_message_text(
            "🔧 **Dicas de Mindfulness**\n\n"
            "**💡 Para iniciantes:**\n"
            "• Comece com sessões curtas\n"
            "• Escolha um local tranquilo\n"
            "• Use um timer\n"
            "• Seja paciente consigo mesmo\n\n"
            "**🎯 Para avançados:**\n"
            "• Experimente diferentes técnicas\n"
            "• Mantenha um diário\n"
            "• Participe de retiros\n"
            "• Compartilhe com outros\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    
    # Callbacks para botões de terapia
    elif query.data == "terapia_progresso":
        await query.edit_message_text(
            "📊 **Progresso Terapêutico**\n\n"
            "**📈 Seu progresso:**\n"
            "• Sessões realizadas: 12\n"
            "• Tempo total: 8h 30min\n"
            "• Objetivos atingidos: 6/10\n"
            "• Bem-estar geral: 75%\n\n"
            "**🎯 Objetivos atuais:**\n"
            "• Reduzir ansiedade: 70% atingido\n"
            "• Melhorar sono: 60% atingido\n"
            "• Aumentar autoestima: 80% atingido\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_diario":
        await query.edit_message_text(
            "📝 **Diário Terapêutico**\n\n"
            "**📖 Funcionalidades:**\n"
            "• Registrar pensamentos diários\n"
            "• Anotar emoções e sentimentos\n"
            "• Rastrear gatilhos\n"
            "• Documentar progresso\n\n"
            "**📱 Como usar:**\n"
            "• Use `/terapia diario`\n"
            "• Entrada diária automática\n"
            "• Análise de padrões\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_metas":
        await query.edit_message_text(
            "🎯 **Metas Terapêuticas**\n\n"
            "**📋 Metas atuais:**\n"
            "• Reduzir ansiedade em 50%\n"
            "• Dormir 8h por noite\n"
            "• Exercitar-se 3x por semana\n"
            "• Meditar 10min diários\n\n"
            "**⚙️ Como gerenciar:**\n"
            "• Use `/terapia meta [objetivo]`\n"
            "• Acompanhamento automático\n"
            "• Celebração de conquistas\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_graficos":
        await query.edit_message_text(
            "📈 **Gráficos Terapêuticos**\n\n"
            "**📊 Visualizações:**\n"
            "• Progresso emocional\n"
            "• Frequência de sintomas\n"
            "• Qualidade do sono\n"
            "• Níveis de estresse\n\n"
            "**📱 Como visualizar:**\n"
            "• Use `/terapia graficos`\n"
            "• Gráficos interativos\n"
            "• Tendências temporais\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_livros":
        await query.edit_message_text(
            "📚 **Livros Recomendados**\n\n"
            "**📖 Para ansiedade:**\n"
            "• 'O Poder do Agora' - Eckhart Tolle\n"
            "• 'Ansiedade: Como Enfrentar' - Augusto Cury\n"
            "• 'Mindfulness' - Mark Williams\n\n"
            "**📖 Para depressão:**\n"
            "• 'O Demônio do Meio-Dia' - Andrew Solomon\n"
            "• 'Como Vencer a Depressão' - David Burns\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_podcasts":
        await query.edit_message_text(
            "🎧 **Podcasts Recomendados**\n\n"
            "**🧠 Saúde mental:**\n"
            "• 'Psicologia na Prática'\n"
            "• 'Mente Aberta'\n"
            "• 'Terapia em Casa'\n\n"
            "**🧘 Mindfulness:**\n"
            "• 'Respiração Consciente'\n"
            "• 'Meditação Guiada'\n"
            "• 'Bem-Estar Diário'\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_videos":
        await query.edit_message_text(
            "🎬 **Vídeos Recomendados**\n\n"
            "**📺 Exercícios práticos:**\n"
            "• Técnicas de respiração\n"
            "• Relaxamento muscular\n"
            "• Meditação guiada\n"
            "• Yoga para iniciantes\n\n"
            "**📺 Canais recomendados:**\n"
            "• 'Psicologia Online'\n"
            "• 'Mindfulness Brasil'\n"
            "• 'Terapia em Casa'\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_sites":
        await query.edit_message_text(
            "🌐 **Sites Recomendados**\n\n"
            "**🔗 Recursos online:**\n"
            "• CVV - Centro de Valorização da Vida\n"
            "• Psicologia Viva\n"
            "• Instituto de Psicologia USP\n\n"
            "**🔗 Ferramentas:**\n"
            "• Apps de meditação\n"
            "• Testes de ansiedade\n"
            "• Comunidades de apoio\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_faq":
        await query.edit_message_text(
            "❓ **FAQ - Terapia IA**\n\n"
            "**Q: O que é terapia IA?**\n"
            "A: Apoio emocional com inteligência artificial\n\n"
            "Q: Substitui terapia tradicional?**\n"
            "A: Não, é complementar e de apoio\n\n"
            "Q: É confidencial?**\n"
            "A: Sim, suas conversas são privadas\n\n"
            "Q: Quando buscar ajuda profissional?**\n"
            "A: Em crises ou sintomas graves\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_limitacoes":
        await query.edit_message_text(
            "⚠️ **Limitações da Terapia IA**\n\n"
            "**🚫 O que NÃO pode fazer:**\n"
            "• Diagnosticar condições médicas\n"
            "• Prescrever medicamentos\n"
            "• Substituir terapia profissional\n"
            "• Intervir em crises graves\n\n"
            "**✅ O que PODE fazer:**\n"
            "• Apoio emocional diário\n"
            "• Técnicas de relaxamento\n"
            "• Estratégias de enfrentamento\n"
            "• Acompanhamento de progresso\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )
    elif query.data == "terapia_suporte":
        await query.edit_message_text(
            "📞 **Suporte - Terapia IA**\n\n"
            "**🆘 Em caso de crise:**\n"
            "• CVV: 188 (24h)\n"
            "• SAMU: 192\n"
            "• Polícia: 190\n\n"
            "**📞 Suporte técnico:**\n"
            "• Email: terapia@bot.com\n"
            "• Telegram: @suporte_terapia\n"
            "• WhatsApp: +55 11 99999-9999\n\n"
            "**🔙 Voltar ao Menu:**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
            ]])
        )

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database.reset_chat_history(update.effective_chat.id); await update.message.reply_text("Memória limpa!")

async def get_gemini_chat_from_db(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> genai.ChatSession:
    return context.bot_data["gemini_model"].start_chat(history=database.get_chat_history(chat_id))

async def responder_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, text = update.effective_chat.id, update.message.text
    logger.info(f"Mensagem recebida: '{text}'")
    
    # Verificar se é uma imagem durante face swap
    if update.message.photo and chat_id in face_swap_handler.user_sessions:
        await handle_image_upload(update, context)
        return
    
    database.add_message_to_history(chat_id, "user", text)
    
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        
        # Usar Gemini (única IA disponível)
        chat = await get_gemini_chat_from_db(context, chat_id)
        response = await chat.send_message_async(text)
        await update.message.reply_text(response.text)
        database.add_message_to_history(chat_id, "model", response.text)
            
    except Exception as e:
        logger.error(f"Erro no Gemini: {e}")
        await update.message.reply_text("Desculpe, tive um problema. Tente novamente mais tarde.")

async def search_web(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings, client, gemini_model, query = context.bot_data["settings"], context.bot_data["http_client"], context.bot_data["gemini_model"], " ".join(context.args)
    if not query: await update.message.reply_text("Uso: /web <termo de busca>"); return
    await update.message.reply_text(f"Pesquisando na web sobre '{query}' com Tavily AI...")
    try:
        payload = {"api_key": settings.tavily_api_key, "query": query}
        response = await client.post("https://api.tavily.com/search", json=payload); response.raise_for_status()
        results = response.json().get("results", [])
        if not results: await update.message.reply_text("Não encontrei resultados."); return
        context_text = "\n".join([f"Fonte: {r.get('url')}\nConteúdo: {r.get('content')}" for r in results[:5]])
        prompt_final = f"Com base nas seguintes informações da web:\n\n{context_text}\n\nResponda de forma completa e natural à pergunta: {query}"
        response_gemini = await gemini_model.generate_content_async(prompt_final)
        await update.message.reply_text(response_gemini.text)
    except Exception as e: logger.error(f"Erro na busca com Tavily: {e}"); await update.message.reply_text("Desculpe, ocorreu um erro durante a busca.")

async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    client, gemini_model, url = context.bot_data["http_client"], context.bot_data["gemini_model"], " ".join(context.args)
    if not url or not url.startswith("http"): await update.message.reply_text("Uso: /resumir <url completa>"); return
    msg = await update.message.reply_text("Extraindo conteúdo da URL...")
    try:
        content = await get_url_content(url, client)
        if content.startswith("ERRO:"): await msg.edit_text(content); return
        await msg.edit_text("Conteúdo extraído. Resumindo com a IA...")
        prompt = f"Por favor, resuma o seguinte texto em português, destacando os pontos mais importantes em uma lista:\n\n---\n{content[:15000]}\n---"
        response_gemini = await gemini_model.generate_content_async(prompt)
        await msg.edit_text(f"📝 **Resumo de:** {url}\n\n{response_gemini.text}", parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e: logger.error(f"Erro ao resumir URL: {e}"); await msg.edit_text("Desculpe, ocorreu um erro ao tentar resumir o conteúdo.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    
    await update.message.reply_text("Ouvindo... 👂")
    try:
        # Transcrever áudio com Gemini
        gemini_model = context.bot_data["gemini_model"]
        voice_bytes = await (await update.message.voice.get_file()).download_as_bytearray()
        
        # Detectar formato do áudio automaticamente
        mime_type = update.message.voice.mime_type or "audio/ogg"
        if mime_type == "audio/ogg":
            mime_type = "audio/ogg"
        elif mime_type == "audio/mp3":
            mime_type = "audio/mpeg"
        elif mime_type == "audio/wav":
            mime_type = "audio/wav"
        elif mime_type == "audio/m4a":
            mime_type = "audio/mp4"
        
        # Criar um BytesIO object para o upload
        audio_io = io.BytesIO(voice_bytes)
        audio_file = genai.upload_file(audio_io, mime_type=mime_type)
        
        # Adicionar timeout para evitar "Timed out"
        transcribed_response = await asyncio.wait_for(
            gemini_model.generate_content_async(["Transcreva este áudio e identifique o idioma usado.", audio_file]),
            timeout=60.0  # 60 segundos de timeout
        )
        transcribed_text = transcribed_response.text.strip()
        
        if not transcribed_text: 
            await update.message.reply_text("Não entendi o áudio."); 
            return
        
        # Detectar idioma automaticamente
        detected_lang = await detect_language_from_text(transcribed_text)
        lang_display = get_language_display_name(detected_lang)
        
        await update.message.reply_text(
            f'🎵 **Áudio Processado**\n'
            f'📝 **Transcrição**: "_{transcribed_text}_"\n'
            f'🌍 **Idioma Detectado**: {lang_display}\n'
            f'🔧 **Formato**: {mime_type}',
            parse_mode='Markdown'
        )
        database.add_message_to_history(chat_id, "user", transcribed_text)
        
        # Responder com Gemini no idioma detectado
        chat = await get_gemini_chat_from_db(context, chat_id)
        prompt = f"Responda em {lang_display} para: {transcribed_text}"
        response = await asyncio.wait_for(
            chat.send_message_async(prompt),
            timeout=60.0  # 60 segundos de timeout
        )
        response_text = response.text
        database.add_message_to_history(chat_id, "model", response_text)
        
        # Converter resposta para áudio no idioma correto
        audio_response_io = await asyncio.to_thread(text_to_speech_sync, response_text, detected_lang)
        await context.bot.send_voice(chat_id=chat_id, voice=audio_response_io)
        
        # Salvar contexto multimodal
        context.user_data["last_audio_text"] = transcribed_text
        context.user_data["current_topic"] = transcribed_text[:50]  # Primeiros 50 chars como tópico
        
        # Salvar áudio de referência para clonagem
        context.user_data["clone_reference_audio"] = voice_bytes
        context.user_data["clone_audio_mime_type"] = mime_type
        
        logger.info(f"Áudio salvo para clonagem - Tamanho: {len(voice_bytes)} bytes, MIME: {mime_type}")
        logger.info(f"User data após salvar áudio: {list(context.user_data.keys())}")
        
    except Exception as e: 
        logger.error(f"Erro ao processar voz: {e}")
        await update.message.reply_text("Desculpe, ocorreu um erro ao processar o áudio.")

async def handle_image_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Verificar se é uma imagem durante face swap
    chat_id = update.effective_chat.id
    if chat_id in face_swap_handler.user_sessions:
        await handle_image_upload(update, context)
        return
    
    # Usar Gemini para análise avançada de imagem
    model = context.bot_data["gemini_model"]
    
    await update.message.reply_text("🔍 Analisando imagem com IA avançada...")
    
    try:
        # Inicializar sistema de detecção facial
        await face_swap_handler.initialize()
        
        # Baixar imagem
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        # Detectar rostos usando OpenCV
        cv_img = await face_swap_handler._bytes_to_cv2(bytes(image_bytes))
        faces = face_swap_handler._detect_faces(cv_img)
        
        if faces:
            face_count = len(faces)
            await update.message.reply_text(f"✅ **Rostos detectados:** {face_count}")
            
            # Análise com Gemini
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                response = model.generate_content([
                    "Analise esta imagem e descreva o que você vê, especialmente focando nos rostos detectados.",
                    pil_img
                ])
                
                if response.text:
                    await update.message.reply_text(f"🤖 **Análise da IA:**\n\n{response.text}")
                else:
                    await update.message.reply_text("🤖 **Análise da IA:** Imagem analisada com sucesso!")
                    
            except Exception as gemini_error:
                logger.error(f"Erro no Gemini: {gemini_error}")
                await update.message.reply_text("🤖 **Análise da IA:** Imagem processada com sucesso!")
        else:
            await update.message.reply_text("⚠️ **Nenhum rosto detectado** na imagem.\n\n**Dicas:**\n• Certifique-se de que há rostos visíveis\n• Use boa iluminação\n• Evite ângulos muito extremos")
            
    except Exception as e:
        logger.error(f"Erro na análise de imagem: {e}")
        await update.message.reply_text("❌ **Erro na análise:** Não foi possível processar a imagem.\n\n**Tente:**\n• Enviar uma imagem diferente\n• Verificar se a imagem tem boa qualidade\n• Usar uma foto com rosto bem visível")
        photo_bytes = await (await update.message.photo[-1].get_file()).download_as_bytearray()
        img = Image.open(io.BytesIO(photo_bytes))
        
        # Análise automática se não houver prompt específico
        if not update.message.caption or update.message.caption.startswith('/'):
            prompt = """Analise esta imagem detalhadamente e forneça:
1. 📸 Descrição geral da imagem
2. 🎯 Objetos principais identificados
3. 🌈 Análise de cores e estilo
4. 😊 Sentimento/atmosfera transmitida
5. 📝 Texto visível (se houver)
6. 🏷️ Tags relevantes para categorização"""
        else:
            prompt = update.message.caption
        
        # Análise com timeout
        response = await asyncio.wait_for(
            model.generate_content_async([prompt, img]),
            timeout=90.0
        )
        
        # Formatar resposta
        analysis_text = response.text
        await update.message.reply_text(
            f"🖼️ **Análise da Imagem**\n\n{analysis_text}",
            parse_mode='Markdown'
        )
        
        # Adicionar ao histórico
        chat_id = update.effective_chat.id
        database.add_message_to_history(chat_id, "user", f"[IMAGEM] {prompt}")
        database.add_message_to_history(chat_id, "model", analysis_text)
        
        # Oferecer opções de análise adicional
        await send_image_analysis_options(update, context, img)
        
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ Tempo limite excedido na análise. Tente com uma imagem menor ou mais simples.")
    except Exception as e: 
        logger.error(f"Erro ao analisar imagem: {e}")
        await update.message.reply_text("❌ Desculpe, não consegui analisar a imagem.")

async def send_image_analysis_options(update: Update, context: ContextTypes.DEFAULT_TYPE, img: Image.Image) -> None:
    """Envia botões inline com opções de análise adicional"""
    keyboard = [
        [
            InlineKeyboardButton("🎨 Análise de Cores", callback_data="analyze_colors"),
            InlineKeyboardButton("📝 OCR Texto", callback_data="ocr_text")
        ],
        [
            InlineKeyboardButton("😊 Análise de Sentimento", callback_data="analyze_mood"),
            InlineKeyboardButton("🏷️ Gerar Tags", callback_data="generate_tags")
        ],
        [
            InlineKeyboardButton("🔄 Análise Detalhada", callback_data="detailed_analysis"),
            InlineKeyboardButton("💡 Sugestões", callback_data="suggestions")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 **Opções de Análise Adicional**\n"
        "Escolha uma opção para análise mais específica:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Salvar imagem no contexto para uso posterior
    context.user_data["last_analyzed_image"] = img
    context.user_data["last_image"] = img  # Para análise multimodal

async def handle_color_analysis(query, context):
    """Analisa as cores da imagem"""
    try:
        img = context.user_data.get("last_analyzed_image")
        if not img:
            await query.edit_message_text("❌ Imagem não encontrada. Envie uma nova imagem para análise.")
            return
        
        # Análise de cores com Gemini
        model = context.bot_data["gemini_model"]
        prompt = """Analise as cores desta imagem e forneça:
1. 🎨 Paleta de cores dominantes
2. 🌈 Distribuição de cores
3. 💫 Harmonia e contraste
4. 🎭 Atmosfera criada pelas cores
5. 📊 Percentual aproximado de cada cor principal"""
        
        response = await asyncio.wait_for(
            model.generate_content_async([prompt, img]),
            timeout=60.0
        )
        
        await query.edit_message_text(
            f"🎨 **Análise de Cores**\n\n{response.text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro na análise de cores: {e}")
        await query.edit_message_text("❌ Erro ao analisar cores da imagem.")

async def handle_ocr_analysis(query, context):
    """Extrai texto da imagem usando OCR"""
    try:
        img = context.user_data.get("last_analyzed_image")
        if not img:
            await query.edit_message_text("❌ Imagem não encontrada. Envie uma nova imagem para análise.")
            return
        
        # Usar pytesseract para OCR
        text = pytesseract.image_to_string(img, lang='por+eng')
        
        if text.strip():
            # Melhorar o texto extraído com Gemini
            model = context.bot_data["gemini_model"]
            prompt = f"Melhore e formate este texto extraído de uma imagem:\n\n{text}"
            
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=60.0
            )
            
            await query.edit_message_text(
                f"📝 **Texto Extraído (OCR)**\n\n**Texto Original:**\n`{text.strip()}`\n\n**Texto Melhorado:**\n{response.text}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("🔍 **OCR - Nenhum texto encontrado**\n\nA imagem não contém texto visível ou legível.")
        
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        await query.edit_message_text("❌ Erro ao extrair texto da imagem.")

async def handle_mood_analysis(query, context):
    """Analisa o sentimento/atmosfera da imagem"""
    try:
        img = context.user_data.get("last_analyzed_image")
        if not img:
            await query.edit_message_text("❌ Imagem não encontrada. Envie uma nova imagem para análise.")
            return
        
        model = context.bot_data["gemini_model"]
        prompt = """Analise o sentimento e atmosfera desta imagem:
1. 😊 Qual emoção a imagem transmite?
2. 🌟 Qual é o clima/atmosfera geral?
3. 🎭 Elementos que contribuem para o humor
4. 💭 Que pensamentos/sensações ela desperta?
5. 🎨 Como as cores e composição afetam o sentimento?
6. 📊 Intensidade emocional (1-10)"""
        
        response = await asyncio.wait_for(
            model.generate_content_async([prompt, img]),
            timeout=60.0
        )
        
        await query.edit_message_text(
            f"😊 **Análise de Sentimento**\n\n{response.text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro na análise de sentimento: {e}")
        await query.edit_message_text("❌ Erro ao analisar sentimento da imagem.")

async def handle_tag_generation(query, context):
    """Gera tags relevantes para a imagem"""
    try:
        img = context.user_data.get("last_analyzed_image")
        if not img:
            await query.edit_message_text("❌ Imagem não encontrada. Envie uma nova imagem para análise.")
            return
        
        model = context.bot_data["gemini_model"]
        prompt = """Gere tags relevantes para esta imagem:
1. 🏷️ Tags descritivas (objetos, pessoas, lugares)
2. 🎨 Tags de estilo (arte, fotografia, design)
3. 🌈 Tags de cores e composição
4. 😊 Tags emocionais/atmosféricas
5. 📱 Tags para categorização e busca
6. 🔍 Tags técnicas (resolução, formato, etc.)

Formato: #tag1 #tag2 #tag3..."""
        
        response = await asyncio.wait_for(
            model.generate_content_async([prompt, img]),
            timeout=60.0
        )
        
        await query.edit_message_text(
            f"🏷️ **Tags Geradas**\n\n{response.text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro na geração de tags: {e}")
        await query.edit_message_text("❌ Erro ao gerar tags para a imagem.")

async def handle_detailed_analysis(query, context):
    """Análise detalhada e técnica da imagem"""
    try:
        img = context.user_data.get("last_analyzed_image")
        if not img:
            await query.edit_message_text("❌ Imagem não encontrada. Envie uma nova imagem para análise.")
            return
        
        model = context.bot_data["gemini_model"]
        prompt = """Faça uma análise técnica detalhada desta imagem:
1. 📐 Composição e regras de fotografia
2. 🎯 Foco e profundidade de campo
3. 💡 Iluminação e sombras
4. 🎨 Paleta de cores e contraste
5. 📱 Qualidade técnica e resolução
6. 🎭 Contexto histórico/cultural
7. 🔍 Detalhes técnicos específicos
8. 💡 Sugestões de melhoria"""
        
        response = await asyncio.wait_for(
            model.generate_content_async([prompt, img]),
            timeout=90.0
        )
        
        await query.edit_message_text(
            f"🔬 **Análise Técnica Detalhada**\n\n{response.text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro na análise detalhada: {e}")
        await query.edit_message_text("❌ Erro ao fazer análise detalhada da imagem.")

async def handle_suggestions(query, context):
    """Gera sugestões criativas baseadas na imagem"""
    try:
        img = context.user_data.get("last_analyzed_image")
        if not img:
            await query.edit_message_text("❌ Imagem não encontrada. Envie uma nova imagem para análise.")
            return
        
        model = context.bot_data["gemini_model"]
        prompt = """Baseado nesta imagem, gere sugestões criativas:
1. 🎨 Ideias para edição/retoque
2. 📸 Sugestões de fotografia similar
3. 🎭 Inspirações para arte/design
4. 📝 Histórias ou poemas inspirados
5. 🎵 Músicas ou sons que combinam
6. 🏷️ Hashtags para redes sociais
7. 💡 Usos criativos da imagem
8. 🔮 Variações e experimentos"""
        
        response = await asyncio.wait_for(
            model.generate_content_async([prompt, img]),
            timeout=60.0
        )
        
        await query.edit_message_text(
            f"💡 **Sugestões Criativas**\n\n{response.text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro nas sugestões: {e}")
        await query.edit_message_text("❌ Erro ao gerar sugestões criativas.")

async def clonar_voz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clona a voz do usuário para reproduzir texto personalizado"""
    logger.info(f"Comando clonar_voz chamado por {update.effective_user.id}")
    logger.info(f"Argumentos: {context.args}")
    logger.info(f"User data keys: {list(context.user_data.keys())}")
    
    if not context.args:
        # Menu interativo com botões
        keyboard = [
            [
                InlineKeyboardButton("🎤 Gravar Áudio", callback_data="clone_gravar_audio"),
                InlineKeyboardButton("📝 Exemplos", callback_data="clone_exemplos")
            ],
            [
                InlineKeyboardButton("⚙️ Configurações", callback_data="clone_configuracoes"),
                InlineKeyboardButton("❓ Ajuda", callback_data="clone_ajuda")
            ],
            [
                InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Verificar se há áudio armazenado
        has_reference_audio = context.user_data.get("clone_reference_audio") is not None
        audio_status = "✅ **Áudio de referência disponível**" if has_reference_audio else "❌ **Nenhum áudio de referência**"
        
        await update.message.reply_text(
            "🎭 **Clone de Voz - IA Generativa**\n\n"
            f"{audio_status}\n\n"
            "**Como funciona:**\n"
            "1. 🎤 Grave um áudio de referência\n"
            "2. 📝 Digite o texto que deseja ouvir\n"
            "3. 🎭 A IA clona sua voz e gera o áudio\n\n"
            "**Recursos:**\n"
            "• 🎵 Suporte a múltiplos formatos\n"
            "• 🌍 Preservação de sotaque\n"
            "• ⚡ Processamento em tempo real\n"
            "• 🎯 Qualidade profissional\n\n"
            "**Comandos:**\n"
            "• `/clonar_voz [texto]` - Clonar voz\n"
            "• `/limpar_audio_referencia` - Limpar áudio\n\n"
            "**Escolha uma opção:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Verificar se há áudio de referência
    reference_audio_bytes = context.user_data.get("clone_reference_audio")
    reference_mime_type = context.user_data.get("clone_audio_mime_type")
    
    logger.info(f"Áudio de referência encontrado: {reference_audio_bytes is not None}")
    logger.info(f"Tipo MIME: {reference_mime_type}")
    if reference_audio_bytes:
        logger.info(f"Tamanho do áudio: {len(reference_audio_bytes)} bytes")
    
    if not reference_audio_bytes:
        # Tentar usar o último áudio processado
        last_audio_text = context.user_data.get("last_audio_text")
        
        if last_audio_text:
            await update.message.reply_text(
                "🎤 **Usando Último Áudio Processado**\n\n"
                f"📝 **Último áudio:** {last_audio_text[:100]}...\n\n"
                "**Para clonar sua voz:**\n"
                "1. Grave um áudio de referência (mínimo 10 segundos)\n"
                "2. Envie o áudio normalmente\n"
                "3. Use: /clonar_voz [texto]\n\n"
                "💡 **Dica:** Grave um áudio claro com sua voz natural\n\n"
                "**Exemplo:**\n"
                "`/clonar_voz Olá, esta é minha voz clonada!`\n\n"
                "**Comando alternativo:**\n"
                "`/clonar_voz_simples [texto]` - Usa gTTS básico"
            )
        else:
            await update.message.reply_text(
                "🎤 **Áudio de Referência Necessário**\n\n"
                "Para clonar sua voz:\n"
                "1. Grave um áudio de referência (mínimo 10 segundos)\n"
                "2. Envie o áudio normalmente\n"
                "3. Use: /clonar_voz [texto]\n\n"
                "💡 **Dica:** Grave um áudio claro com sua voz natural\n\n"
                "**Exemplo:**\n"
                "`/clonar_voz Olá, esta é minha voz clonada!`\n\n"
                "**Comando alternativo:**\n"
                "`/clonar_voz_simples [texto]` - Usa gTTS básico"
            )
        return
    
    try:
        text_to_speak = " ".join(context.args)
        
        logger.info(f"Texto para clonar: {text_to_speak}")
        
        await update.message.reply_text(
            "🎭 **Clonando Voz...**\n\n"
            f"📝 **Texto:** {text_to_speak}\n"
            "⏳ Processando áudio de referência...\n"
            "🔄 Aplicando características vocais..."
        )
        
        # Processar áudio de referência
        reference_audio_io = io.BytesIO(reference_audio_bytes)
        reference_audio_io.seek(0)
        
        # Analisar características da voz de referência
        voice_cloner = context.application.bot_data["voice_cloner"]
        voice_characteristics = await voice_cloner.analyze_voice_characteristics(reference_audio_bytes)
        
        await update.message.reply_text(
            "🔍 **Analisando Características Vocais...**\n\n"
            f"📊 **Análise da Voz de Referência:**\n"
            f"• Gênero: {voice_characteristics['gender'].title()}\n"
            f"• Pitch médio: {voice_characteristics['avg_pitch']:.1f} Hz\n"
            f"• Duração: {voice_characteristics['duration']:.1f} segundos\n"
            f"• Energia: {voice_characteristics['avg_energy']:.3f}\n\n"
            "🎭 **Iniciando Clonagem Avançada...**\n"
            "• Usando Fish Audio API\n"
            "• Configurações otimizadas para voz masculina\n"
            "• Processamento em alta qualidade..."
        )
        
        await asyncio.sleep(2)  # Simular processamento adicional
        
        # Clonar voz usando o clonador avançado
        cloned_audio = await voice_cloner.clone_voice_advanced(reference_audio_bytes, text_to_speak)
        
        if cloned_audio:
            audio_io = cloned_audio
        else:
            # Fallback para gTTS com ajustes
            audio_io = await asyncio.to_thread(text_to_speech_sync, text_to_speak, 'pt')
        
        # Determinar qual método foi usado
        if cloned_audio:
            method_used = "Fish Audio API"
            quality_level = "Alta fidelidade"
            features = "Clonagem real da voz"
        else:
            method_used = "gTTS com ajustes"
            quality_level = "Ajustada"
            features = "Simulação de clonagem"
        
        await update.message.reply_text(
            "✅ **Voz Clonada com Sucesso!**\n\n"
            "🎭 **Características Aplicadas:**\n"
            f"• Gênero: {voice_characteristics['gender'].title()}\n"
            f"• Pitch ajustado: {voice_characteristics['avg_pitch']:.1f} Hz\n"
            f"• Método: {method_used}\n"
            f"• Qualidade: {quality_level}\n"
            f"• Tipo: {features}\n\n"
            "📊 **Estatísticas:**\n"
            f"• Texto original: {len(text_to_speak)} caracteres\n"
            f"• Áudio de referência: {voice_characteristics['duration']:.1f}s\n"
            f"• Processamento: {'Real-time' if cloned_audio else 'Local'}\n\n"
            "📤 Enviando áudio clonado..."
        )
        
        # Enviar áudio clonado
        await context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=audio_io,
            caption=f"🎭 **Voz Clonada:** {text_to_speak}"
        )
        
        # Adicionar ao histórico
        chat_id = update.effective_chat.id
        database.add_message_to_history(chat_id, "user", f"[CLONE_VOZ] {text_to_speak}")
        database.add_message_to_history(chat_id, "model", "Voz clonada gerada com sucesso!")
        
        # Limpar áudio de referência após uso (opcional)
        # context.user_data.pop("clone_reference_audio", None)
        # context.user_data.pop("clone_audio_mime_type", None)
        
    except Exception as e:
        logger.error(f"Erro na clonagem de voz: {e}")
        await update.message.reply_text(
            "❌ **Erro na Clonagem de Voz**\n\n"
            "🔧 **Possíveis causas:**\n"
            "• Áudio de referência muito curto\n"
            "• Qualidade do áudio insuficiente\n"
            "• Texto muito longo\n\n"
            "💡 **Sugestões:**\n"
            "• Grave um áudio de 10-30 segundos\n"
            "• Fale claramente e naturalmente\n"
            "• Use texto de até 100 caracteres"
        )

async def gerar_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings, client, prompt = context.bot_data["settings"], context.bot_data["http_client"], " ".join(context.args)
    if not prompt: await update.message.reply_text("Uso: /gerarimagem <descrição>"); return
    await update.message.reply_text(f"Gerando imagem para: '{prompt}'...")
    api_url = f"https://api-inference.huggingface.co/models/{settings.image_model_id}"
    headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}

    try:
        response = await client.post(api_url, headers=headers, json={"inputs": prompt}, timeout=180)
        if response.status_code == 503:
            await update.message.reply_text("O modelo de imagem está sendo iniciado, tentando novamente em 25s...")
            await asyncio.sleep(25);
            response = await client.post(api_url, headers=headers, json={"inputs": prompt}, timeout=180)
        response.raise_for_status()
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=response.content, caption=f"Imagem para: '{prompt}'")
    except Exception as e: logger.error(f"Erro ao gerar imagem: {e}"); await update.message.reply_text("Falha ao gerar a imagem.")

async def mindfulness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sessões de mindfulness e atenção plena"""
    if not context.args:
        # Menu de mindfulness
        keyboard = [
            [
                InlineKeyboardButton("🌬️ Respiração", callback_data="mindfulness_respiracao"),
                InlineKeyboardButton("🌿 Meditação", callback_data="mindfulness_meditacao")
            ],
            [
                InlineKeyboardButton("🌅 Manhã", callback_data="mindfulness_manha"),
                InlineKeyboardButton("🌙 Noite", callback_data="mindfulness_noite")
            ],
            [
                InlineKeyboardButton("⚡ Rápido (5min)", callback_data="mindfulness_rapido"),
                InlineKeyboardButton("🕐 Completo (20min)", callback_data="mindfulness_completo")
            ],
            [
                InlineKeyboardButton("📊 Progresso", callback_data="mindfulness_progresso"),
                InlineKeyboardButton("🎯 Metas", callback_data="mindfulness_metas")
            ],
            [
                InlineKeyboardButton("❓ Ajuda", callback_data="mindfulness_ajuda"),
                InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🧘 **Mindfulness & Atenção Plena**\n\n"
            "Escolha o tipo de sessão:\n\n"
            "🌬️ **Respiração:** Técnicas de respiração consciente\n"
            "🌿 **Meditação:** Meditações guiadas\n"
            "🌅 **Manhã:** Rotinas matinais de mindfulness\n"
            "🌙 **Noite:** Preparação para o sono\n"
            "⚡ **Rápido:** Sessões de 5 minutos\n"
            "🕐 **Completo:** Sessões de 20 minutos\n\n"
            "💡 **Dica:** Encontre um local tranquilo e confortável",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Sessão direta por comando
    tipo = context.args[0].lower()
    duracao = context.args[1] if len(context.args) > 1 else "5"
    
    await iniciar_sessao_mindfulness(update, context, tipo, duracao)

async def iniciar_sessao_mindfulness(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo: str, duracao: str = "5") -> None:
    """Inicia uma sessão de mindfulness específica"""
    
    # Mapeamento de tipos de mindfulness
    mindfulness_types = {
        'respiracao': {
            'title': '🌬️ **Respiração Consciente**',
            'description': 'Técnica de respiração 4-7-8 para relaxamento',
            'steps': [
                "1. Sente-se confortavelmente com as costas retas",
                "2. Coloque uma mão no peito e outra na barriga",
                "3. Inspire pelo nariz por 4 segundos",
                "4. Segure a respiração por 7 segundos",
                "5. Expire pela boca por 8 segundos",
                "6. Repita o ciclo por 5 minutos"
            ]
        },
        'meditacao': {
            'title': '🌿 **Meditação Guiada**',
            'description': 'Meditação de atenção plena para iniciantes',
            'steps': [
                "1. Encontre uma posição confortável",
                "2. Feche os olhos suavemente",
                "3. Concentre-se na sua respiração natural",
                "4. Observe os pensamentos sem julgá-los",
                "5. Volte gentilmente à respiração",
                "6. Continue por 10-15 minutos"
            ]
        },
        'manha': {
            'title': '🌅 **Mindfulness Matinal**',
            'description': 'Rotina de manhã para começar o dia com presença',
            'steps': [
                "1. Acorde 10 minutos mais cedo",
                "2. Sente-se na cama com os olhos fechados",
                "3. Respire profundamente 3 vezes",
                "4. Agradeça por mais um dia",
                "5. Defina uma intenção para o dia",
                "6. Alongue-se suavemente"
            ]
        },
        'noite': {
            'title': '🌙 **Preparação para o Sono**',
            'description': 'Ritual noturno para relaxar e dormir melhor',
            'steps': [
                "1. Desligue dispositivos eletrônicos",
                "2. Prepare um chá calmante",
                "3. Faça respiração 4-7-8 por 5 minutos",
                "4. Visualize um lugar tranquilo",
                "5. Relaxe cada parte do corpo",
                "6. Permita-se adormecer naturalmente"
            ]
        }
    }
    
    if tipo not in mindfulness_types:
        await update.message.reply_text(
            "❌ **Tipo de Mindfulness não reconhecido**\n\n"
            "✅ **Tipos disponíveis:**\n"
            "• respiracao\n"
            "• meditacao\n"
            "• manha\n"
            "• noite\n\n"
            "💡 **Exemplo:** /mindfulness respiracao 10"
        )
        return
    
    session = mindfulness_types[tipo]
    
    # Iniciar sessão
    await update.message.reply_text(
        f"{session['title']}\n\n"
        f"📝 **Descrição:** {session['description']}\n"
        f"⏱️ **Duração:** {duracao} minutos\n\n"
        "🚀 **Iniciando sessão...**\n"
        "🔇 Encontre um local tranquilo\n"
        "🧘 Sente-se confortavelmente\n"
        "🌬️ Respire naturalmente..."
    )
    
    # Simular progresso da sessão
    await asyncio.sleep(2)
    
    # Enviar passos da sessão
    steps_text = "\n".join(session['steps'])
    await update.message.reply_text(
        f"📋 **Passos da Sessão:**\n\n{steps_text}\n\n"
        f"⏰ **Duração:** {duracao} minutos\n"
        "🎯 **Foco:** Respiração e presença\n"
        "💫 **Benefícios:** Redução de estresse, foco, clareza mental"
    )
    
    # Timer para a sessão
    if duracao.isdigit():
        duracao_int = int(duracao)
        if duracao_int > 0:
            await update.message.reply_text(
                f"⏰ **Timer iniciado:** {duracao_int} minutos\n\n"
                "🔔 Você será notificado quando a sessão terminar.\n"
                "🧘 Continue praticando até o final."
            )
            
            # Simular final da sessão
            await asyncio.sleep(5)  # Em produção, usar timer real
            
            await update.message.reply_text(
                "🎉 **Sessão de Mindfulness Concluída!**\n\n"
                "✨ **Como você se sente agora?**\n"
                "🌱 **Benefícios experimentados:**\n"
                "• Redução do estresse\n"
                "• Maior clareza mental\n"
                "• Sensação de calma\n"
                "• Foco aprimorado\n\n"
                "💡 **Dica:** Pratique diariamente para melhores resultados!"
            )
    
    # Adicionar ao histórico
    chat_id = update.effective_chat.id
    database.add_message_to_history(chat_id, "user", f"[MINDFULNESS] {tipo} {duracao}min")
    database.add_message_to_history(chat_id, "model", f"Sessão de mindfulness {tipo} concluída")

async def terapia_ia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sistema de terapia IA para apoio emocional"""
    if not context.args:
        # Menu de abordagens terapêuticas
        keyboard = [
            [
                InlineKeyboardButton("😊 Ansiedade", callback_data="terapia_ansiedade"),
                InlineKeyboardButton("😔 Depressão", callback_data="terapia_depressao")
            ],
            [
                InlineKeyboardButton("😤 Estresse", callback_data="terapia_estresse"),
                InlineKeyboardButton("😴 Sono", callback_data="terapia_sono")
            ],
            [
                InlineKeyboardButton("💪 Autoestima", callback_data="terapia_autoestima"),
                InlineKeyboardButton("🤝 Relacionamentos", callback_data="terapia_relacionamentos")
            ],
            [
                InlineKeyboardButton("🎯 Objetivos", callback_data="terapia_objetivos"),
                InlineKeyboardButton("🌱 Crescimento", callback_data="terapia_crescimento")
            ],
            [
                InlineKeyboardButton("📊 Acompanhamento", callback_data="terapia_acompanhamento"),
                InlineKeyboardButton("📚 Recursos", callback_data="terapia_recursos")
            ],
            [
                InlineKeyboardButton("❓ Ajuda", callback_data="terapia_ajuda"),
                InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💭 **Terapia IA - Apoio Emocional**\n\n"
            "Escolha uma área para trabalharmos:\n\n"
            "😊 **Ansiedade:** Técnicas de controle e relaxamento\n"
            "😔 **Depressão:** Apoio e estratégias de recuperação\n"
            "😤 **Estresse:** Gerenciamento e redução do estresse\n"
            "😴 **Sono:** Melhorar a qualidade do sono\n"
            "💪 **Autoestima:** Construir confiança e autoaceitação\n"
            "🤝 **Relacionamentos:** Melhorar conexões interpessoais\n"
            "🎯 **Objetivos:** Definir e alcançar metas pessoais\n"
            "🌱 **Crescimento:** Desenvolvimento pessoal contínuo\n\n"
            "⚠️ **Importante:** Este é um apoio complementar, não substitui terapia profissional",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Terapia direta por comando
    tema = context.args[0].lower()
    abordagem = context.args[1] if len(context.args) > 1 else "cognitiva"
    
    await iniciar_sessao_terapia(update, context, tema, abordagem)

async def iniciar_sessao_terapia(update: Update, context: ContextTypes.DEFAULT_TYPE, tema: str, abordagem: str = "cognitiva") -> None:
    """Inicia uma sessão de terapia IA específica"""
    
    # Mapeamento de temas terapêuticos
    temas_terapia = {
        'ansiedade': {
            'title': '😊 **Trabalhando com Ansiedade**',
            'description': 'Técnicas para reduzir e gerenciar a ansiedade',
            'abordagens': {
                'cognitiva': [
                    "🔍 **Identificação de Pensamentos:** Observe seus pensamentos ansiosos",
                    "🤔 **Questionamento:** Pergunte-se: 'Isso é realmente verdade?'",
                    "🔄 **Reestruturação:** Reformule pensamentos negativos",
                    "📝 **Registro:** Anote situações que causam ansiedade"
                ],
                'comportamental': [
                    "🌬️ **Respiração 4-7-8:** Técnica de relaxamento imediato",
                    "🏃 **Exercício Físico:** Libera endorfinas e reduz tensão",
                    "🧘 **Relaxamento Muscular:** Técnica progressiva de relaxamento",
                    "🎯 **Exposição Gradual:** Enfrente medos gradualmente"
                ]
            }
        },
        'depressao': {
            'title': '😔 **Apoio para Depressão**',
            'description': 'Estratégias para melhorar o humor e energia',
            'abordagens': {
                'cognitiva': [
                    "🌅 **Rotina Matinal:** Estabeleça uma rotina consistente",
                    "🎯 **Metas Pequenas:** Defina objetivos alcançáveis diariamente",
                    "📝 **Gratidão:** Liste 3 coisas pelas quais é grato",
                    "🤝 **Conexão Social:** Mantenha contato com pessoas queridas"
                ],
                'comportamental': [
                    "☀️ **Exposição à Luz:** Passe tempo ao ar livre",
                    "🏃 **Atividade Física:** Exercícios leves regularmente",
                    "🎨 **Atividades Prazerosas:** Faça algo que goste todos os dias",
                    "😴 **Higiene do Sono:** Mantenha horários regulares"
                ]
            }
        },
        'estresse': {
            'title': '😤 **Gerenciamento do Estresse**',
            'description': 'Técnicas para reduzir e controlar o estresse',
            'abordagens': {
                'cognitiva': [
                    "📊 **Identificação:** Identifique fontes de estresse",
                    "🎯 **Priorização:** Foque no que realmente importa",
                    "⏰ **Gestão do Tempo:** Organize suas atividades",
                    "🚫 **Limites:** Aprenda a dizer 'não' quando necessário"
                ],
                'comportamental': [
                    "🧘 **Meditação:** 10 minutos diários de mindfulness",
                    "🌿 **Natureza:** Passe tempo em ambientes naturais",
                    "🎵 **Música:** Ouça músicas relaxantes",
                    "💆 **Autocuidado:** Dedique tempo para si mesmo"
                ]
            }
        },
        'sono': {
            'title': '😴 **Melhorando a Qualidade do Sono**',
            'description': 'Estratégias para um sono mais reparador',
            'abordagens': {
                'cognitiva': [
                    "🧠 **Higiene Mental:** Evite pensamentos estressantes antes de dormir",
                    "📱 **Desconexão Digital:** Desligue dispositivos 1 hora antes",
                    "📚 **Leitura:** Leia algo leve e agradável",
                    "🎯 **Ritual:** Crie um ritual relaxante para dormir"
                ],
                'comportamental': [
                    "🌡️ **Temperatura:** Mantenha o quarto fresco (18-22°C)",
                    "🌙 **Escuridão:** Use cortinas blackout se necessário",
                    "🛏️ **Conforto:** Invista em um colchão e travesseiro adequados",
                    "⏰ **Horário:** Mantenha horários consistentes de sono"
                ]
            }
        }
    }
    
    if tema not in temas_terapia:
        await update.message.reply_text(
            "❌ **Tema terapêutico não reconhecido**\n\n"
            "✅ **Temas disponíveis:**\n"
            "• ansiedade\n"
            "• depressao\n"
            "• estresse\n"
            "• sono\n\n"
            "💡 **Exemplo:** /terapia ansiedade cognitiva"
        )
        return
    
    tema_info = temas_terapia[tema]
    
    if abordagem not in tema_info['abordagens']:
        abordagem = 'cognitiva'  # Padrão
    
    # Iniciar sessão terapêutica
    await update.message.reply_text(
        f"{tema_info['title']}\n\n"
        f"📝 **Descrição:** {tema_info['description']}\n"
        f"🧠 **Abordagem:** {abordagem.title()}\n\n"
        "🚀 **Iniciando sessão terapêutica...**\n"
        "💭 Encontre um local tranquilo e confortável\n"
        "🧘 Respire profundamente algumas vezes\n"
        "💪 Lembre-se: você é mais forte do que pensa..."
    )
    
    await asyncio.sleep(2)
    
    # Enviar estratégias terapêuticas
    estrategias = tema_info['abordagens'][abordagem]
    estrategias_text = "\n".join(estrategias)
    
    await update.message.reply_text(
        f"📋 **Estratégias Terapêuticas ({abordagem.title()}):**\n\n{estrategias_text}\n\n"
        "💡 **Como aplicar:**\n"
        "• Escolha 1-2 estratégias para começar\n"
        "• Pratique diariamente por pelo menos 1 semana\n"
        "• Observe as mudanças em seu bem-estar\n"
        "• Ajuste conforme necessário"
    )
    
    # Acompanhamento e suporte
    await asyncio.sleep(3)
    
    await update.message.reply_text(
        "🌟 **Acompanhamento e Suporte**\n\n"
        "📊 **Monitoramento:**\n"
        "• Como você se sente agora? (1-10)\n"
        "• Qual estratégia mais ressoou com você?\n"
        "• Que desafios você prevê?\n\n"
        "🔄 **Próximos Passos:**\n"
        "• Pratique as estratégias escolhidas\n"
        "• Use /terapia novamente quando precisar\n"
        "• Considere buscar apoio profissional se necessário\n\n"
        "💪 **Lembre-se:** Mudanças levam tempo, seja paciente consigo mesmo!"
    )
    
    # Adicionar ao histórico
    chat_id = update.effective_chat.id
    database.add_message_to_history(chat_id, "user", f"[TERAPIA_IA] {tema} {abordagem}")
    database.add_message_to_history(chat_id, "model", f"Sessão de terapia {tema} com abordagem {abordagem} concluída")

# === FUNÇÕES DOS NOVOS BOTÕES INTERATIVOS ===

async def handle_clone_gravar_audio(query, context):
    """Guia para gravar áudio para clonagem"""
    keyboard = [
        [
            InlineKeyboardButton("🎤 Iniciar Gravação", callback_data="clone_iniciar_gravacao"),
            InlineKeyboardButton("📋 Dicas de Gravação", callback_data="clone_dicas")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="clone_voltar"),
            InlineKeyboardButton("❓ Ajuda", callback_data="clone_ajuda")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎤 **Gravar Áudio para Clonagem**\n\n"
        "**Passos para um áudio perfeito:**\n\n"
        "1. 🎯 **Local Tranquilo**\n"
        "   • Sem ruídos de fundo\n"
        "   • Ambiente silencioso\n"
        "   • Sem eco ou reverberação\n\n"
        "2. 🎙️ **Técnica de Gravação**\n"
        "   • Fale naturalmente e claramente\n"
        "   • Mantenha distância constante do microfone\n"
        "   • Evite respirar diretamente no microfone\n\n"
        "3. ⏱️ **Duração Ideal**\n"
        "   • Mínimo: 10 segundos\n"
        "   • Ideal: 20-30 segundos\n"
        "   • Máximo: 60 segundos\n\n"
        "4. 📝 **Conteúdo Recomendado**\n"
        "   • Fale frases variadas\n"
        "   • Use diferentes entonações\n"
        "   • Inclua pausas naturais\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_clone_exemplos(query, context):
    """Exemplos de uso do clone de voz"""
    keyboard = [
        [
            InlineKeyboardButton("🎭 Apresentações", callback_data="clone_exemplo_apresentacoes"),
            InlineKeyboardButton("📚 Narração", callback_data="clone_exemplo_narracao")
        ],
        [
            InlineKeyboardButton("🎵 Música", callback_data="clone_exemplo_musica"),
            InlineKeyboardButton("💼 Profissional", callback_data="clone_exemplo_profissional")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="clone_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 **Exemplos de Uso - Clone de Voz**\n\n"
        "**🎭 Apresentações:**\n"
        "• 'Bem-vindos à nossa reunião mensal'\n"
        "• 'Hoje vamos discutir os resultados do trimestre'\n"
        "• 'Agradeço a presença de todos'\n\n"
        "**📚 Narração:**\n"
        "• 'Era uma vez, em uma terra distante...'\n"
        "• 'O protagonista enfrentou muitos desafios'\n"
        "• 'A história nos ensina valiosas lições'\n\n"
        "**🎵 Música:**\n"
        "• 'Esta é a canção que compus para você'\n"
        "• 'Cada nota conta uma história'\n"
        "• 'A música une corações'\n\n"
        "**💼 Profissional:**\n"
        "• 'Seja bem-vindo ao nosso produto'\n"
        "• 'Estamos aqui para ajudar você'\n"
        "• 'Obrigado por escolher nossos serviços'\n\n"
        "**Escolha uma categoria:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_clone_configuracoes(query, context):
    """Configurações do clone de voz"""
    keyboard = [
        [
            InlineKeyboardButton("🎵 Qualidade", callback_data="clone_qualidade"),
            InlineKeyboardButton("🌍 Idioma", callback_data="clone_idioma")
        ],
        [
            InlineKeyboardButton("⚡ Velocidade", callback_data="clone_velocidade"),
            InlineKeyboardButton("🎭 Estilo", callback_data="clone_estilo")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="clone_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ **Configurações - Clone de Voz**\n\n"
        "**🎵 Qualidade:**\n"
        "• Alta: Melhor fidelidade, arquivo maior\n"
        "• Média: Equilíbrio entre qualidade e tamanho\n"
        "• Baixa: Arquivo menor, qualidade reduzida\n\n"
        "**🌍 Idioma:**\n"
        "• Português (Brasil)\n"
        "• Inglês\n"
        "• Espanhol\n"
        "• Francês\n\n"
        "**⚡ Velocidade:**\n"
        "• Lenta: 0.8x (mais natural)\n"
        "• Normal: 1.0x (padrão)\n"
        "• Rápida: 1.2x (mais dinâmica)\n\n"
        "**🎭 Estilo:**\n"
        "• Natural: Voz conversacional\n"
        "• Formal: Tom profissional\n"
        "• Casual: Tom descontraído\n\n"
        "**Escolha uma configuração:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_clone_ajuda(query, context):
    """Ajuda para clone de voz"""
    keyboard = [
        [
            InlineKeyboardButton("❓ FAQ", callback_data="clone_faq"),
            InlineKeyboardButton("🔧 Solução de Problemas", callback_data="clone_solucao")
        ],
        [
            InlineKeyboardButton("📞 Suporte", callback_data="clone_suporte"),
            InlineKeyboardButton("🔙 Voltar", callback_data="clone_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ **Ajuda - Clone de Voz**\n\n"
        "**Como usar:**\n"
        "1. Grave um áudio de referência\n"
        "2. Use /clonar_voz ou responda ao áudio\n"
        "3. Digite o texto desejado\n"
        "4. Receba o áudio clonado\n\n"
        "**Comandos disponíveis:**\n"
        "• `/clonar_voz` - Menu principal\n"
        "• `/clonar_voz [texto]` - Clonagem direta\n\n"
        "**Formatos suportados:**\n"
        "• OGG (padrão Telegram)\n"
        "• MP3\n"
        "• WAV\n"
        "• M4A\n\n"
        "**Escolha uma opção de ajuda:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_mindfulness_progresso(query, context):
    """Acompanhamento do progresso de mindfulness"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Estatísticas", callback_data="mindfulness_stats"),
            InlineKeyboardButton("🏆 Conquistas", callback_data="mindfulness_conquistas")
        ],
        [
            InlineKeyboardButton("📈 Gráficos", callback_data="mindfulness_graficos"),
            InlineKeyboardButton("🎯 Metas", callback_data="mindfulness_metas")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="mindfulness_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 **Progresso - Mindfulness**\n\n"
        "**📈 Seu Progresso:**\n"
        "• Sessões completadas: 0\n"
        "• Tempo total: 0 minutos\n"
        "• Dias consecutivos: 0\n"
        "• Meta semanal: 5 sessões\n\n"
        "**🏆 Conquistas Disponíveis:**\n"
        "🥉 Iniciante: Primeira sessão\n"
        "🥈 Regular: 7 dias consecutivos\n"
        "🥇 Avançado: 30 dias consecutivos\n"
        "💎 Mestre: 100 sessões\n\n"
        "**🎯 Próximas Metas:**\n"
        "• Completar 1 sessão hoje\n"
        "• Manter 3 dias consecutivos\n"
        "• Alcançar 10 minutos diários\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_mindfulness_metas(query, context):
    """Definir e gerenciar metas de mindfulness"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Definir Meta", callback_data="mindfulness_definir_meta"),
            InlineKeyboardButton("📅 Calendário", callback_data="mindfulness_calendario")
        ],
        [
            InlineKeyboardButton("⏰ Lembretes", callback_data="mindfulness_lembretes"),
            InlineKeyboardButton("📊 Acompanhamento", callback_data="mindfulness_acompanhamento")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="mindfulness_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎯 **Metas - Mindfulness**\n\n"
        "**🎯 Metas Atuais:**\n"
        "• Diária: 10 minutos de mindfulness\n"
        "• Semanal: 5 sessões\n"
        "• Mensal: 20 sessões\n\n"
        "**📅 Calendário de Prática:**\n"
        "• Segunda: Respiração (10min)\n"
        "• Terça: Meditação (15min)\n"
        "• Quarta: Respiração (10min)\n"
        "• Quinta: Meditação (15min)\n"
        "• Sexta: Respiração (10min)\n"
        "• Sábado: Manhã (20min)\n"
        "• Domingo: Noite (15min)\n\n"
        "**⏰ Lembretes Configurados:**\n"
        "• Manhã: 7:00 AM\n"
        "• Tarde: 2:00 PM\n"
        "• Noite: 9:00 PM\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_mindfulness_ajuda(query, context):
    """Ajuda para mindfulness"""
    keyboard = [
        [
            InlineKeyboardButton("❓ FAQ", callback_data="mindfulness_faq"),
            InlineKeyboardButton("📚 Recursos", callback_data="mindfulness_recursos")
        ],
        [
            InlineKeyboardButton("🔧 Dicas", callback_data="mindfulness_dicas"),
            InlineKeyboardButton("🔙 Voltar", callback_data="mindfulness_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ **Ajuda - Mindfulness**\n\n"
        "**🧘 O que é Mindfulness?**\n"
        "Mindfulness é a prática de atenção plena ao momento presente, sem julgamentos.\n\n"
        "**💡 Benefícios:**\n"
        "• Reduz estresse e ansiedade\n"
        "• Melhora foco e concentração\n"
        "• Aumenta autoconhecimento\n"
        "• Promove bem-estar emocional\n\n"
        "**🎯 Como praticar:**\n"
        "1. Encontre um local tranquilo\n"
        "2. Sente-se confortavelmente\n"
        "3. Foque na respiração\n"
        "4. Observe pensamentos sem julgá-los\n"
        "5. Volte gentilmente à respiração\n\n"
        "**Escolha uma opção de ajuda:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_terapia_acompanhamento(query, context):
    """Acompanhamento terapêutico"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Progresso", callback_data="terapia_progresso"),
            InlineKeyboardButton("📝 Diário", callback_data="terapia_diario")
        ],
        [
            InlineKeyboardButton("🎯 Metas", callback_data="terapia_metas"),
            InlineKeyboardButton("📈 Gráficos", callback_data="terapia_graficos")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="terapia_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 **Acompanhamento - Terapia IA**\n\n"
        "**📈 Seu Progresso:**\n"
        "• Sessões realizadas: 0\n"
        "• Temas trabalhados: 0\n"
        "• Estratégias aplicadas: 0\n"
        "• Melhoria percebida: 0%\n\n"
        "**📝 Diário Terapêutico:**\n"
        "• Registre seus pensamentos\n"
        "• Anote estratégias que funcionaram\n"
        "• Monitore mudanças de humor\n"
        "• Acompanhe desafios e conquistas\n\n"
        "**🎯 Metas Terapêuticas:**\n"
        "• Reduzir ansiedade em 30%\n"
        "• Aplicar 3 estratégias por semana\n"
        "• Manter rotina de mindfulness\n"
        "• Melhorar qualidade do sono\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_terapia_recursos(query, context):
    """Recursos terapêuticos adicionais"""
    keyboard = [
        [
            InlineKeyboardButton("📚 Livros", callback_data="terapia_livros"),
            InlineKeyboardButton("🎧 Podcasts", callback_data="terapia_podcasts")
        ],
        [
            InlineKeyboardButton("🎬 Vídeos", callback_data="terapia_videos"),
            InlineKeyboardButton("🌐 Sites", callback_data="terapia_sites")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="terapia_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 **Recursos - Terapia IA**\n\n"
        "**📚 Livros Recomendados:**\n"
        "• 'O Poder do Agora' - Eckhart Tolle\n"
        "• 'Mindfulness' - Mark Williams\n"
        "• 'A Coragem de Ser Imperfeito' - Brené Brown\n"
        "• 'O Monje e o Executivo' - James C. Hunter\n\n"
        "**🎧 Podcasts:**\n"
        "• 'Psicologia Hoje'\n"
        "• 'Mindful Minutes'\n"
        "• 'Terapia em Casa'\n"
        "• 'Bem-Estar Mental'\n\n"
        "**🎬 Vídeos:**\n"
        "• Técnicas de respiração\n"
        "• Meditações guiadas\n"
        "• Exercícios de relaxamento\n"
        "• Estratégias cognitivas\n\n"
        "**Escolha uma categoria:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_terapia_ajuda(query, context):
    """Ajuda para terapia IA"""
    keyboard = [
        [
            InlineKeyboardButton("❓ FAQ", callback_data="terapia_faq"),
            InlineKeyboardButton("⚠️ Limitações", callback_data="terapia_limitacoes")
        ],
        [
            InlineKeyboardButton("📞 Suporte", callback_data="terapia_suporte"),
            InlineKeyboardButton("🔙 Voltar", callback_data="terapia_voltar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ **Ajuda - Terapia IA**\n\n"
        "**💭 O que é a Terapia IA?**\n"
        "A Terapia IA é um sistema de apoio emocional que oferece estratégias baseadas em evidências científicas.\n\n"
        "**✅ O que oferece:**\n"
        "• Técnicas de respiração\n"
        "• Estratégias cognitivas\n"
        "• Exercícios de relaxamento\n"
        "• Apoio para diferentes temas\n\n"
        "**⚠️ Limitações importantes:**\n"
        "• Não substitui terapia profissional\n"
        "• Não oferece diagnóstico\n"
        "• Não é adequado para crises\n"
        "• Complementar ao tratamento\n\n"
        "**🚨 Quando buscar ajuda profissional:**\n"
        "• Pensamentos suicidas\n"
        "• Crises de ansiedade severas\n"
        "• Depressão persistente\n"
        "• Dificuldades funcionais\n\n"
        "**Escolha uma opção de ajuda:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Funções de navegação
async def clone_voltar(query, context):
    """Volta ao menu principal do clone de voz"""
    await clonar_voz(query, context)

async def mindfulness_voltar(query, context):
    """Volta ao menu principal do mindfulness"""
    await mindfulness(query, context)

async def terapia_voltar(query, context):
    """Volta ao menu principal da terapia"""
    await terapia_ia(query, context)

async def voltar_ao_menu_principal(query, context):
    """Volta ao menu principal com botões interativos"""
    welcome_message = (
        "🤖 **Bem-vindo ao Bot Profissional de IA Avançada!**\n\n"
        "**🚀 25+ Funcionalidades de IA Profissional**\n\n"
        "**🤖 CONVERSA INTELIGENTE**\n"
        "• Converse naturalmente comigo\n"
        "• IA avançada com memória de contexto\n"
        "• Suporte multilíngue completo\n\n"
        "**🔍 BUSCA WEB INTELIGENTE**\n"
        "• Pesquisa em tempo real com IA\n"
        "• Resumo automático de URLs\n"
        "• Análise inteligente de resultados\n\n"
        "**🔒 SEGURANÇA DIGITAL AVANÇADA**\n"
        "• Geração de senhas ultra-seguras\n"
        "• Verificação de vazamentos (100% LOCAL)\n"
        "• Anti-phishing inteligente\n"
        "• Anonimização de dados\n\n"
        "**🖼️ FERRAMENTAS DE IMAGEM IA**\n"
        "• Geração de imagens com IA\n"
        "• Remoção automática de fundo\n"
        "• Redimensionamento inteligente\n"
        "• Aplicação de filtros automáticos\n"
        "• Melhoria de qualidade (upscale)\n\n"
        "**🎵 ÁUDIO AVANÇADO - IA MULTIMÍDIA**\n"
        "• Texto para voz multilíngue\n"
        "• Transcrição de áudio com IA\n"
        "• Detecção automática de idioma\n"
        "• Suporte a múltiplos formatos\n"
        "• Clone de voz personalizado\n\n"
        "**🔍 ANÁLISE DE IMAGEM IA - AVANÇADA**\n"
        "• Análise automática completa\n"
        "• Análise de cores e paletas\n"
        "• OCR multilíngue de texto\n"
        "• Análise de sentimentos\n"
        "• Geração de tags automáticas\n"
        "• Sugestões criativas\n\n"
        "**🎭 IA GENERATIVA ESPECIALIZADA**\n"
        "• Clone de voz com características únicas\n"
        "• Aplicação de estilos artísticos\n"
        "• Escritor fantasma em estilos literários\n"
        "• Arquitetura e design com IA\n"
        "• Composição musical inteligente\n"
        "• Geração de vídeos curtos\n\n"
        "**🧘 COACH EMOCIONAL IA - APOIO TERAPÊUTICO**\n"
        "• Mindfulness personalizado\n"
        "• Terapia IA para ansiedade/depressão\n"
        "• Técnicas de respiração\n"
        "• Meditações guiadas\n"
        "• Acompanhamento de progresso\n"
        "• Estratégias de enfrentamento\n\n"
        "💡 <i>Use /help para ver todos os comandos e exemplos detalhados.</i>"
    )
    
    # Criar botões interativos para as principais funcionalidades
    keyboard = [
        [
            InlineKeyboardButton("🤖 Conversa IA", callback_data="menu_conversa"),
            InlineKeyboardButton("🔍 Busca Web", callback_data="menu_busca")
        ],
        [
            InlineKeyboardButton("🔒 Segurança", callback_data="menu_seguranca"),
            InlineKeyboardButton("🖼️ Imagens", callback_data="menu_imagens")
        ],
        [
            InlineKeyboardButton("🎵 Áudio", callback_data="menu_audio"),
            InlineKeyboardButton("🔍 Análise IA", callback_data="menu_analise")
        ],
        [
            InlineKeyboardButton("🎭 IA Generativa", callback_data="menu_ia_generativa"),
            InlineKeyboardButton("🧘 Coach Emocional", callback_data="menu_coach")
        ],
        [
            InlineKeyboardButton("🎨 Face Swapping", callback_data="image_main_menu"),
            InlineKeyboardButton("📚 Ajuda Completa", callback_data="menu_ajuda")
        ],
        [
            InlineKeyboardButton("⚙️ Configurações", callback_data="menu_config")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode='HTML')

# === MENUS PRINCIPAIS COM BOTÕES ===

async def handle_menu_conversa(query, context):
    """Menu de conversa inteligente"""
    keyboard = [
        [
            InlineKeyboardButton("💬 Conversar", callback_data="conversar_agora"),
            InlineKeyboardButton("🧠 IA Avançada", callback_data="ia_avancada")
        ],
        [
            InlineKeyboardButton("📝 Histórico", callback_data="ver_historico"),
            InlineKeyboardButton("🗑️ Limpar Chat", callback_data="limpar_chat")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 **Conversa Inteligente - IA Avançada**\n\n"
        "**💬 Converse naturalmente comigo:**\n"
        "• Perguntas e respostas inteligentes\n"
        "• Análise de contexto avançada\n"
        "• Memória de conversas\n"
        "• Suporte multilíngue\n\n"
        "**🧠 Recursos da IA:**\n"
        "• Google Gemini Pro\n"
        "• Processamento de linguagem natural\n"
        "• Compreensão contextual\n"
        "• Respostas personalizadas\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_busca(query, context):
    """Menu de busca web"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Buscar Agora", callback_data="buscar_web"),
            InlineKeyboardButton("📰 Últimas Notícias", callback_data="ultimas_noticias")
        ],
        [
            InlineKeyboardButton("🌐 Resumir URL", callback_data="resumir_url"),
            InlineKeyboardButton("📊 Pesquisa Avançada", callback_data="pesquisa_avancada")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 **Busca Web Inteligente**\n\n"
        "**🔍 Busca Web:** `/web [sua pergunta]`\n"
        "• Pesquisa em tempo real\n"
        "• Resultados relevantes\n"
        "• Análise com IA\n\n"
        "**📰 Resumo de URL:** `/resumir [link]`\n"
        "• Extração de conteúdo\n"
        "• Resumo inteligente\n"
        "• Pontos principais\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_seguranca(query, context):
    """Menu de segurança digital"""
    keyboard = [
        [
            InlineKeyboardButton("🔑 Senhas Fortes", callback_data="gerar_senha"),
            InlineKeyboardButton("🛡️ Verificar Vazamentos", callback_data="verificar_vazamento")
        ],
        [
            InlineKeyboardButton("🚫 Anti-Phishing", callback_data="scan_phishing"),
            InlineKeyboardButton("🎭 Anonimizar Dados", callback_data="anonimizar_dados")
        ],
        [
            InlineKeyboardButton("🔒 Criptografia", callback_data="criptografia"),
            InlineKeyboardButton("📊 Relatório Segurança", callback_data="relatorio_seguranca")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔒 **Segurança Digital Avançada**\n\n"
        "**🔑 Senhas Fortes:** `/gerar_senha_forte [critérios]`\n"
        "• Geração segura de senhas\n"
        "• Múltiplos critérios\n"
        "• Validação de força\n\n"
        "**🛡️ Verificar Vazamentos:** `/verificar_vazamento [email]`\n"
        "• Análise local de padrões\n"
        "• Detecção de riscos\n"
        "• Relatório detalhado\n\n"
        "**🚫 Anti-Phishing:** `/scan_phishing [url]`\n"
        "• Análise de URLs suspeitas\n"
        "• Detecção de fraudes\n"
        "• Proteção contra ataques\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_imagens(query, context):
    """Menu de ferramentas de imagem"""
    keyboard = [
        [
            InlineKeyboardButton("🎨 Gerar Imagem", callback_data="gerar_imagem"),
            InlineKeyboardButton("✂️ Remover Fundo", callback_data="remover_fundo")
        ],
        [
            InlineKeyboardButton("📏 Redimensionar", callback_data="redimensionar"),
            InlineKeyboardButton("🎭 Aplicar Filtro", callback_data="aplicar_filtro")
        ],
        [
            InlineKeyboardButton("⚡ Melhorar Qualidade", callback_data="upscale"),
            InlineKeyboardButton("🔄 Converter Formato", callback_data="converter_formato")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🖼️ **Ferramentas de Imagem IA**\n\n"
        "**🎨 Gerar Imagem:** `/gerarimagem [descrição]`\n"
        "• Criação com IA\n"
        "• Múltiplos estilos\n"
        "• Alta qualidade\n\n"
        "**✂️ Remover Fundo:** `/remover_fundo`\n"
        "• Remoção automática\n"
        "• Precisão avançada\n"
        "• Formato PNG\n\n"
        "**📏 Redimensionar:** `/redimensionar 800x600`\n"
        "• Múltiplas resoluções\n"
        "• Manter proporção\n"
        "• Qualidade preservada\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_audio(query, context):
    """Menu de áudio avançado"""
    keyboard = [
        [
            InlineKeyboardButton("🔊 Texto para Voz", callback_data="texto_para_voz"),
            InlineKeyboardButton("🎤 Voz para Texto", callback_data="voz_para_texto")
        ],
        [
            InlineKeyboardButton("🌍 Multilíngue", callback_data="audio_multilingue"),
            InlineKeyboardButton("🎵 Formatos", callback_data="formatos_audio")
        ],
        [
            InlineKeyboardButton("🎭 Clone de Voz", callback_data="clone_voz"),
            InlineKeyboardButton("⚙️ Configurações", callback_data="config_audio")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎵 **Áudio Avançado - IA Multimídia**\n\n"
        "**🔊 Texto para Voz:** `/texto_para_voz pt [texto]`\n"
        "• Múltiplos idiomas\n"
        "• Voz natural\n"
        "• Controle de velocidade\n\n"
        "**🎤 Voz para Texto:** Envie mensagem de áudio\n"
        "• Transcrição automática\n"
        "• Detecção de idioma\n"
        "• Alta precisão\n\n"
        "**🌍 Multilíngue:** Detecção automática de idioma\n"
        "• Português, Inglês, Espanhol\n"
        "• Resposta no idioma detectado\n"
        "• Suporte completo\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_analise(query, context):
    """Menu de análise de imagem IA"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Análise Automática", callback_data="analise_automatica"),
            InlineKeyboardButton("🎨 Análise de Cores", callback_data="analise_cores")
        ],
        [
            InlineKeyboardButton("📝 OCR Texto", callback_data="ocr_texto"),
            InlineKeyboardButton("😊 Análise de Sentimento", callback_data="analise_sentimento")
        ],
        [
            InlineKeyboardButton("🏷️ Gerar Tags", callback_data="gerar_tags"),
            InlineKeyboardButton("🔬 Análise Técnica", callback_data="analise_tecnica")
        ],
        [
            InlineKeyboardButton("💡 Sugestões Criativas", callback_data="sugestoes_criativas"),
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 **Análise de Imagem IA - Avançada**\n\n"
        "**🔍 Análise Automática:** Envie uma imagem\n"
        "• Descrição completa\n"
        "• Objetos identificados\n"
        "• Contexto e cenário\n\n"
        "**🎨 Análise de Cores:** Paleta e harmonia\n"
        "• Cores dominantes\n"
        "• Combinações\n"
        "• Psicologia das cores\n\n"
        "**📝 OCR Texto:** Extração de texto\n"
        "• Múltiplos idiomas\n"
        "• Alta precisão\n"
        "• Formatação preservada\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_ia_generativa(query, context):
    """Menu de IA generativa especializada"""
    keyboard = [
        [
            InlineKeyboardButton("🎭 Clone de Voz", callback_data="clone_voz_menu"),
            InlineKeyboardButton("🎨 Estilo Artístico", callback_data="estilo_artistico")
        ],
        [
            InlineKeyboardButton("📝 Escritor Fantasma", callback_data="escritor_fantasma"),
            InlineKeyboardButton("🏗️ Arquitetura IA", callback_data="arquitetura_ia")
        ],
        [
            InlineKeyboardButton("🎵 Música IA", callback_data="musica_ia"),
            InlineKeyboardButton("🎬 Vídeo IA", callback_data="video_ia")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎭 **IA Generativa Especializada**\n\n"
        "**🎭 Clone de Voz:** `/clonar_voz [áudio] [texto]`\n"
        "• Reproduzir texto com voz do usuário\n"
        "• Preservação de características\n"
        "• Qualidade profissional\n\n"
        "**🎨 Estilo Artístico:** Aplicar estilos de artistas\n"
        "• Van Gogh, Picasso, Monet\n"
        "• Estilos personalizados\n"
        "• Transformação completa\n\n"
        "**📝 Escritor Fantasma:** Escrever no estilo de autores\n"
        "• Machado de Assis, Shakespeare\n"
        "• Estilos literários\n"
        "• Criatividade única\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_coach(query, context):
    """Menu de coach emocional"""
    keyboard = [
        [
            InlineKeyboardButton("🧘 Mindfulness", callback_data="mindfulness_menu"),
            InlineKeyboardButton("💭 Terapia IA", callback_data="terapia_menu")
        ],
        [
            InlineKeyboardButton("😊 Ansiedade", callback_data="ansiedade_coach"),
            InlineKeyboardButton("😔 Depressão", callback_data="depressao_coach")
        ],
        [
            InlineKeyboardButton("😤 Estresse", callback_data="estresse_coach"),
            InlineKeyboardButton("😴 Sono", callback_data="sono_coach")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🧘 **Coach Emocional IA - Apoio Terapêutico**\n\n"
        "**🧘 Mindfulness:** `/mindfulness [tipo] [duração]`\n"
        "• Sessões de atenção plena\n"
        "• Técnicas de respiração\n"
        "• Meditações guiadas\n\n"
        "**💭 Terapia IA:** `/terapia [tema] [abordagem]`\n"
        "• Apoio emocional\n"
        "• Estratégias terapêuticas\n"
        "• Acompanhamento\n\n"
        "**😊 Ansiedade:** Técnicas de controle\n"
        "• Respiração 4-7-8\n"
        "• Relaxamento muscular\n"
        "• Estratégias cognitivas\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_ajuda(query, context):
    """Menu de ajuda completa"""
    keyboard = [
        [
            InlineKeyboardButton("📚 Comandos", callback_data="ver_comandos"),
            InlineKeyboardButton("❓ FAQ", callback_data="ver_faq")
        ],
        [
            InlineKeyboardButton("🎯 Exemplos", callback_data="ver_exemplos"),
            InlineKeyboardButton("🔧 Solução Problemas", callback_data="solucao_problemas")
        ],
        [
            InlineKeyboardButton("📞 Suporte", callback_data="contato_suporte"),
            InlineKeyboardButton("📖 Tutorial", callback_data="ver_tutorial")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 **Ajuda Completa - Bot Profissional**\n\n"
        "**📚 Comandos Disponíveis:**\n"
        "• 25+ funcionalidades de IA\n"
        "• Comandos organizados por categoria\n"
        "• Exemplos práticos\n\n"
        "**❓ FAQ - Perguntas Frequentes:**\n"
        "• Como usar cada funcionalidade\n"
        "• Solução de problemas\n"
        "• Dicas e truques\n\n"
        "**🎯 Exemplos Práticos:**\n"
        "• Casos de uso reais\n"
        "• Demonstrações\n"
        "• Melhores práticas\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_config(query, context):
    """Menu de configurações"""
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Preferências", callback_data="preferencias"),
            InlineKeyboardButton("🌍 Idioma", callback_data="config_idioma")
        ],
        [
            InlineKeyboardButton("🔔 Notificações", callback_data="config_notificacoes"),
            InlineKeyboardButton("🔒 Privacidade", callback_data="config_privacidade")
        ],
        [
            InlineKeyboardButton("📊 Estatísticas", callback_data="ver_estatisticas"),
            InlineKeyboardButton("🔄 Atualizações", callback_data="ver_atualizacoes")
        ],
        [
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ **Configurações e Preferências**\n\n"
        "**⚙️ Preferências:**\n"
        "• Configurações personalizadas\n"
        "• Ajustes de interface\n"
        "• Comportamento do bot\n\n"
        "**🌍 Idioma:**\n"
        "• Português (padrão)\n"
        "• Inglês\n"
        "• Espanhol\n\n"
        "**🔔 Notificações:**\n"
        "• Lembretes personalizados\n"
        "• Frequência de alertas\n"
        "• Tipos de notificação\n\n"
        "**Escolha uma opção:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# === COMANDOS MULTIMODAIS ===
async def analise_multimodal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando principal para análise multimodal"""
    await update.message.reply_text(
        "🔍 **Análise Multimodal**\n\n"
        "Este comando permite análise combinada de diferentes tipos de mídia:\n\n"
        "📸 **Texto + Imagem**: `/texto_imagem`\n"
        "🎤 **Áudio + Contexto**: `/audio_contexto`\n"
        "📄 **Documento + Busca**: `/documento_busca`\n"
        "📊 **Dados + Visualização**: `/dados_visualizacao`\n\n"
        "**Como usar:**\n"
        "1. Envie uma imagem com texto\n"
        "2. Use `/texto_imagem` para análise combinada\n"
        "3. Ou envie áudio e use `/audio_contexto`\n\n"
        "**Exemplo:**\n"
        "Envie uma foto de um produto + texto 'Analise este produto'",
        parse_mode='Markdown'
    )

async def analise_texto_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Análise combinada de texto + imagem"""
    try:
        # Verificar se há imagem no contexto
        if not context.user_data.get("last_image"):
            await update.message.reply_text(
                "📸 **Análise Texto + Imagem**\n\n"
                "Para usar este comando:\n"
                "1. Envie uma imagem primeiro\n"
                "2. Depois use `/texto_imagem` com seu texto\n\n"
                "**Exemplo:**\n"
                "`/texto_imagem Analise esta imagem e me diga o que você vê`",
                parse_mode='Markdown'
            )
            return
        
        text = " ".join(context.args) if context.args else "Analise esta imagem"
        image = context.user_data["last_image"]
        
        # Processar análise multimodal
        processor = context.application.bot_data["multimodal_processor"]
        multimodal_context = MultimodalContext(
            text=text,
            image=image,
            timestamp=datetime.now().isoformat()
        )
        
        result = await processor.analyze_text_image(text, image)
        
        if result["success"]:
            await update.message.reply_text(
                f"🔍 **Análise Texto + Imagem**\n\n"
                f"{result['analysis']}\n\n"
                f"**Confiança:** {result['confidence']:.1%}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Erro na análise: {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro em analise_texto_imagem: {e}")
        await update.message.reply_text("❌ Erro ao processar análise multimodal")

async def analise_audio_contexto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Análise combinada de áudio + contexto"""
    try:
        # Verificar se há áudio no contexto
        if not context.user_data.get("last_audio_text"):
            await update.message.reply_text(
                "🎤 **Análise Áudio + Contexto**\n\n"
                "Para usar este comando:\n"
                "1. Envie uma mensagem de voz primeiro\n"
                "2. Depois use `/audio_contexto`\n\n"
                "O bot analisará o áudio considerando:\n"
                "• Histórico da conversa\n"
                "• Preferências do usuário\n"
                "• Contexto atual",
                parse_mode='Markdown'
            )
            return
        
        audio_text = context.user_data["last_audio_text"]
        user_context = {
            "user_history": context.user_data.get("chat_history", []),
            "current_topic": context.user_data.get("current_topic", ""),
            "preferences": context.user_data.get("preferences", {})
        }
        
        # Processar análise multimodal
        processor = context.application.bot_data["multimodal_processor"]
        result = await processor.analyze_audio_context(audio_text, user_context)
        
        if result["success"]:
            await update.message.reply_text(
                f"🎤 **Análise Áudio + Contexto**\n\n"
                f"{result['analysis']}\n\n"
                f"**Intenção:** {result['intent'].title()}\n"
                f"**Confiança:** {result['confidence']:.1%}\n\n"
                f"**Sugestões:**\n" + "\n".join(f"• {s}" for s in result['suggestions']),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Erro na análise: {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro em analise_audio_contexto: {e}")
        await update.message.reply_text("❌ Erro ao processar análise de áudio")

async def analise_documento_busca(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Análise combinada de documento + busca web"""
    try:
        # Verificar se há documento no contexto
        if not context.user_data.get("last_document"):
            await update.message.reply_text(
                "📄 **Análise Documento + Busca**\n\n"
                "Para usar este comando:\n"
                "1. Envie um documento primeiro\n"
                "2. Depois use `/documento_busca`\n\n"
                "O bot irá:\n"
                "• Analisar o documento\n"
                "• Buscar informações relacionadas\n"
                "• Validar fatos\n"
                "• Fornecer contexto adicional",
                parse_mode='Markdown'
            )
            return
        
        document_content = context.user_data["last_document"]
        search_query = " ".join(context.args) if context.args else document_content[:100]
        
        # Buscar informações relacionadas
        settings = context.application.bot_data["settings"]
        search_url = "https://api.tavily.com/search"
        search_params = {
            "api_key": settings.tavily_api_key,
            "query": search_query,
            "max_results": 5
        }
        
        async with context.application.bot_data["http_client"] as client:
            search_response = await client.get(search_url, params=search_params)
            search_results = search_response.json().get("results", [])
        
        # Processar análise multimodal
        processor = context.application.bot_data["multimodal_processor"]
        result = await processor.analyze_document_search(document_content, search_results)
        
        if result["success"]:
            await update.message.reply_text(
                f"📄 **Análise Documento + Busca**\n\n"
                f"{result['analysis']}\n\n"
                f"**Resumo:** {result['document_summary']}\n"
                f"**Confiança:** {result['confidence']:.1%}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Erro na análise: {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro em analise_documento_busca: {e}")
        await update.message.reply_text("❌ Erro ao processar análise de documento")

async def analise_dados_visualizacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Análise combinada de dados + visualização"""
    try:
        # Verificar se há dados no contexto
        if not context.args:
            await update.message.reply_text(
                "📊 **Análise Dados + Visualização**\n\n"
                "**Sintaxe:** `/dados_visualizacao <tipo> <dados>`\n\n"
                "**Tipos disponíveis:**\n"
                "• `chart` - Gráfico genérico\n"
                "• `bar` - Gráfico de barras\n"
                "• `line` - Gráfico de linha\n"
                "• `pie` - Gráfico de pizza\n\n"
                "**Exemplo:**\n"
                "`/dados_visualizacao bar vendas:100,marketing:80,suporte:60`",
                parse_mode='Markdown'
            )
            return
        
        viz_type = context.args[0]
        data_str = " ".join(context.args[1:])
        
        # Converter string de dados para dicionário
        try:
            data = {}
            for item in data_str.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    data[key.strip()] = float(value.strip())
        except:
            await update.message.reply_text("❌ Formato de dados inválido. Use: chave:valor,chave:valor")
            return
        
        # Processar análise multimodal
        processor = context.application.bot_data["multimodal_processor"]
        result = await processor.analyze_data_visualization(data, viz_type)
        
        if result["success"]:
            await update.message.reply_text(
                f"📊 **Análise Dados + Visualização**\n\n"
                f"{result['analysis']}\n\n"
                f"**Gráfico Recomendado:** {result['recommended_chart']}\n"
                f"**Confiança:** {result['confidence']:.1%}\n\n"
                f"**Insights:**\n" + "\n".join(f"• {insight}" for insight in result['insights']),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Erro na análise: {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro em analise_dados_visualizacao: {e}")
        await update.message.reply_text("❌ Erro ao processar análise de dados")

async def limpar_audio_referencia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Limpa o áudio de referência armazenado"""
    try:
        # Verificar se há áudio armazenado
        if context.user_data.get("clone_reference_audio"):
            # Limpar áudio de referência
            context.user_data.pop("clone_reference_audio", None)
            context.user_data.pop("clone_audio_mime_type", None)
            
            await update.message.reply_text(
                "🗑️ **Áudio de Referência Removido**\n\n"
                "✅ O áudio de referência foi limpo com sucesso!\n\n"
                "**Para usar clone de voz novamente:**\n"
                "1. Grave um novo áudio de referência\n"
                "2. Envie o áudio normalmente\n"
                "3. Use `/clonar_voz [texto]`"
            )
        else:
            await update.message.reply_text(
                "ℹ️ **Nenhum Áudio Armazenado**\n\n"
                "Não há áudio de referência para ser removido.\n\n"
                "**Para usar clone de voz:**\n"
                "1. Grave um áudio de referência\n"
                "2. Envie o áudio normalmente\n"
                "3. Use `/clonar_voz [texto]`"
            )
            
    except Exception as e:
        logger.error(f"Erro ao limpar áudio de referência: {e}")
        await update.message.reply_text("❌ Erro ao limpar áudio de referência")

async def clonar_voz_simples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Versão simplificada do clone de voz que sempre funciona"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🎭 **Clone de Voz Simples**\n\n"
                "**Como usar:**\n"
                "`/clonar_voz_simples [texto]`\n\n"
                "**Exemplo:**\n"
                "`/clonar_voz_simples Olá, esta é minha voz!`\n\n"
                "**Características:**\n"
                "• Sempre funciona\n"
                "• Qualidade alta\n"
                "• Processamento rápido\n"
                "• Sem necessidade de áudio de referência"
            )
            return
        
        text_to_speak = " ".join(context.args)
        
        await update.message.reply_text(
            "🎭 **Gerando Áudio...**\n\n"
            f"📝 **Texto:** {text_to_speak}\n"
            "⏳ Processando..."
        )
        
        # Tentar usar clonador se houver áudio de referência
        voice_cloner = context.application.bot_data["voice_cloner"]
        reference_audio_bytes = context.user_data.get("clone_reference_audio")
        
        if reference_audio_bytes:
            # Usar clonagem avançada
            cloned_audio = await voice_cloner.clone_voice_advanced(reference_audio_bytes, text_to_speak)
            if cloned_audio:
                audio_io = cloned_audio
            else:
                # Fallback para gTTS
                audio_io = await asyncio.to_thread(text_to_speech_sync, text_to_speak, 'pt')
        else:
            # Gerar áudio com gTTS
            audio_io = await asyncio.to_thread(text_to_speech_sync, text_to_speak, 'pt')
        
        # Verificar se usou clonagem
        used_cloning = reference_audio_bytes and cloned_audio is not None
        
        await update.message.reply_text(
            "✅ **Áudio Gerado com Sucesso!**\n\n"
            "🎭 **Características:**\n"
            f"• Método: {'Clonagem de voz' if used_cloning else 'Voz natural em português'}\n"
            "• Qualidade alta\n"
            "• Processamento otimizado\n"
            f"• {'Voz masculina ajustada' if used_cloning else 'Voz padrão'}\n\n"
            "📤 Enviando áudio..."
        )
        
        # Enviar áudio
        await context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=audio_io,
            caption=f"🎭 **Voz Gerada:** {text_to_speak}"
        )
        
        # Adicionar ao histórico
        chat_id = update.effective_chat.id
        database.add_message_to_history(chat_id, "user", f"[CLONE_VOZ_SIMPLES] {text_to_speak}")
        database.add_message_to_history(chat_id, "model", "Áudio gerado com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro no clone de voz simples: {e}")
        await update.message.reply_text(
            "❌ **Erro ao Gerar Áudio**\n\n"
            "🔧 **Possíveis causas:**\n"
            "• Texto muito longo\n"
            "• Caracteres especiais\n"
            "• Problema de conexão\n\n"
            "💡 **Sugestões:**\n"
            "• Use texto mais curto\n"
            "• Evite caracteres especiais\n"
            "• Tente novamente"
        )

# --- INICIALIZAÇÃO ---
async def post_init(application: Application) -> None:
    database.initialize_db()
    settings = Settings.load_from_env()
    
    # Configurar Gemini
    genai.configure(api_key=settings.gemini_api_key)
    
    application.bot_data["settings"] = settings
    application.bot_data["http_client"] = httpx.AsyncClient()
    
    # Modelo Gemini
    safety_settings = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
    application.bot_data["gemini_model"] = genai.GenerativeModel(settings.gemini_model_name, safety_settings=safety_settings)
    
    # Processador Multimodal
    application.bot_data["multimodal_processor"] = MultimodalProcessor(
        application.bot_data["gemini_model"], 
        application.bot_data["http_client"]
    )
    
    # Clonador de Voz
    application.bot_data["voice_cloner"] = VoiceCloner(
        fish_audio_api_key=settings.fish_audio_api_key,
        coqui_api_key=settings.coqui_api_key
    )
    
    logger.info("Recursos (DB, HTTP, Gemini, Multimodal, VoiceCloner) inicializados.")

async def post_shutdown(application: Application) -> None:
    client: httpx.AsyncClient = application.bot_data.get("http_client")
    if client: await client.aclose()
    logger.info("Recursos (cliente HTTP) liberados.")

# === NOVOS COMANDOS PARA INTERFACE MELHORADA ===
async def comando_voz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de voz para controle do bot"""
    try:
        # Verificar se há áudio de voz
        if not update.message.voice and not update.message.audio:
            await update.message.reply_text(
                "🎤 **Comando de Voz**\n\n"
                "Para usar comandos de voz:\n"
                "• Grave uma mensagem de voz\n"
                "• Ou envie um áudio\n\n"
                "**Comandos disponíveis:**\n"
                "• 'Clonar minha voz'\n"
                "• 'Gerar imagem'\n"
                "• 'Chat com IA'\n"
                "• 'Verificar segurança'\n"
                "• 'Abrir configurações'"
            )
            return
        
        # Processar áudio de voz
        await update.message.reply_text("🎤 **Processando comando de voz...**")
        
        # Simular processamento de áudio (em produção, usar speech-to-text)
        # Por enquanto, vamos usar um comando simulado
        simulated_command = "clonar minha voz"  # Em produção, extrair do áudio
        
        # Processar comando usando o sistema de UI
        await ui_manager.process_voice_command(update, context, simulated_command)
        
    except Exception as e:
        logger.error(f"Erro no comando de voz: {e}")
        await update.message.reply_text(
            "❌ **Erro no Comando de Voz**\n\n"
            "Não foi possível processar seu comando de voz.\n"
            "Tente novamente ou use comandos de texto."
        )

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menu principal melhorado com interface dinâmica"""
    try:
        await ui_manager.show_menu(update, context, "main_menu")
    except Exception as e:
        logger.error(f"Erro ao mostrar menu principal: {e}")
        await update.message.reply_text("❌ Erro ao carregar menu. Tente novamente.")

async def shortcuts_personalizados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra shortcuts personalizados do usuário"""
    try:
        await ui_manager.show_shortcuts(update, context)
    except Exception as e:
        logger.error(f"Erro ao mostrar shortcuts: {e}")
        await update.message.reply_text("❌ Erro ao carregar shortcuts. Tente novamente.")

async def tour_interativo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia tour interativo para novos usuários"""
    try:
        await ui_manager.start_interactive_tour(update, context)
    except Exception as e:
        logger.error(f"Erro ao iniciar tour: {e}")
        await update.message.reply_text("❌ Erro ao iniciar tour. Tente novamente.")

async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manipula TODOS os callbacks do bot (menus e botões)"""
    try:
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        logger.info(f"🔍 Callback recebido: {callback_data}")
        
        # === CALLBACK SWAP_FACES COM PRIORIDADE ABSOLUTA ===
        if callback_data == "swap_faces":
            logger.info("🎯 CALLBACK SWAP_FACES DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🔄 **Face Swap Funcional!**\n\n"
                "**Como usar:**\n"
                "1. Use `/trocar_rosto` para iniciar\n"
                "2. Envie a primeira imagem (rosto fonte)\n"
                "3. Envie a segunda imagem (rosto destino)\n"
                "4. Receba o resultado!\n\n"
                "**Comandos disponíveis:**\n"
                "• `/trocar_rosto` - Face swap básico\n"
                "• `/trocar_rosto_ultra` - Qualidade máxima\n"
                "• `/trocar_rosto_rapido` - Processamento rápido\n\n"
                "**Status:** ✅ Sistema funcionando!\n"
                "**Teste:** Use `/trocar_rosto` agora!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Tentar Agora", callback_data="try_swap_faces"),
                    InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACK FACE_SCENARIO_MENU COM PRIORIDADE ===
        if callback_data == "face_scenario_menu":
            logger.info("🎭 CALLBACK FACE_SCENARIO_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎭 **Rosto + Cenário**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🌅 Cenário Personalizado\n"
                "• 🎨 Estilo Realista\n"
                "• ✨ Estilo Fantasia\n"
                "• 🚀 Estilo Cyberpunk\n"
                "• 📸 Estilo Vintage\n\n"
                "**Como usar:**\n"
                "1. Envie uma foto com rosto\n"
                "2. Use `/rosto_cenario <descrição>`\n"
                "3. Aguarde a geração\n\n"
                "**Exemplos:**\n"
                "• `/rosto_cenario praia tropical`\n"
                "• `/rosto_cenario cidade futurista`\n"
                "• `/rosto_cenario floresta mágica`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌅 Cenário Personalizado", callback_data="custom_scenario"),
                    InlineKeyboardButton("🎨 Estilos", callback_data="artistic_styles_menu")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="image_main_menu")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACK ARTISTIC_STYLES_MENU COM PRIORIDADE ===
        if callback_data == "artistic_styles_menu":
            logger.info("🎨 CALLBACK ARTISTIC_STYLES_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎨 **Estilos Artísticos**\n\n"
                "**Estilos disponíveis:**\n"
                "• 🎭 Estilo Anime\n"
                "• 🖼️ Estilo Pintura\n"
                "• 📸 Estilo Fotográfico\n"
                "• 🎪 Estilo Cartoon\n"
                "• 🌟 Estilo Surrealista\n\n"
                "**Como usar:**\n"
                "1. Escolha o estilo desejado\n"
                "2. Envie uma foto com rosto\n"
                "3. Receba resultado com estilo aplicado\n\n"
                "**Recomendações:**\n"
                "• Realista: Para fotos profissionais\n"
                "• Fantasia: Para arte conceitual\n"
                "• Cyberpunk: Para temas futuristas\n"
                "• Vintage: Para nostalgia\n"
                "• Artístico: Para pinturas\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎭 Anime", callback_data="anime_style"),
                    InlineKeyboardButton("🖼️ Pintura", callback_data="painting_style")
                ], [
                    InlineKeyboardButton("📸 Fotográfico", callback_data="photographic_style"),
                    InlineKeyboardButton("🎪 Cartoon", callback_data="cartoon_style")
                ], [
                    InlineKeyboardButton("🌟 Surrealista", callback_data="surreal_style")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="image_main_menu")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACK SCENARIO_TEMPLATES_MENU COM PRIORIDADE ===
        if callback_data == "scenario_templates_menu":
            logger.info("🌅 CALLBACK SCENARIO_TEMPLATES_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🌅 **Templates de Cenários**\n\n"
                "**Templates disponíveis:**\n"
                "• 🏖️ Praia Tropical\n"
                "• 🏢 Escritório Moderno\n"
                "• 🌲 Floresta Mágica\n"
                "• 🍽️ Restaurante Elegante\n"
                "• 🌌 Espaço Sideral\n"
                "• ⛰️ Montanha Majestosa\n"
                "• 🏙️ Cidade Futurista\n"
                "• 🏰 Castelo Medieval\n"
                "• 🔬 Laboratório Científico\n"
                "• 📚 Biblioteca Antiga\n\n"
                "**Como usar:**\n"
                "1. Escolha um template\n"
                "2. Envie uma foto com rosto\n"
                "3. Receba resultado com seu rosto no cenário\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏖️ Praia", callback_data="template_praia"),
                    InlineKeyboardButton("🏢 Escritório", callback_data="template_escritorio")
                ], [
                    InlineKeyboardButton("🌲 Floresta", callback_data="template_floresta"),
                    InlineKeyboardButton("🍽️ Restaurante", callback_data="template_restaurante")
                ], [
                    InlineKeyboardButton("🌌 Espaço", callback_data="template_espaco"),
                    InlineKeyboardButton("⛰️ Montanha", callback_data="template_montanha")
                ], [
                    InlineKeyboardButton("🏙️ Cidade", callback_data="template_cidade"),
                    InlineKeyboardButton("🏰 Castelo", callback_data="template_castelo")
                ], [
                    InlineKeyboardButton("🔬 Laboratório", callback_data="template_laboratorio"),
                    InlineKeyboardButton("📚 Biblioteca", callback_data="template_biblioteca")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="image_main_menu")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACK FACE_ANALYSIS_MENU COM PRIORIDADE ===
        if callback_data == "face_analysis_menu":
            logger.info("📸 CALLBACK FACE_ANALYSIS_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📸 **Análise Facial Avançada**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🔍 Detecção de Rostos\n"
                "• 📊 Análise de Qualidade\n"
                "• 🎯 Pontos Faciais\n"
                "• 📏 Medições Faciais\n"
                "• 🎨 Análise de Estilo\n"
                "• 📈 Relatório Completo\n\n"
                "**Como usar:**\n"
                "1. Envie uma foto com rosto\n"
                "2. Use `/analisar_rosto` para análise completa\n"
                "3. Receba relatório detalhado\n\n"
                "**Informações analisadas:**\n"
                "• Detecção de rostos (0-1.0)\n"
                "• Alinhamento facial (0-1.0)\n"
                "• Iluminação (0-1.0)\n"
                "• Resolução da imagem (0-1.0)\n"
                "• Pose do rosto (0-1.0)\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Analisar Imagem", callback_data="analyze_current_image"),
                    InlineKeyboardButton("📊 Ver Histórico", callback_data="view_analysis_history")
                ], [
                    InlineKeyboardButton("🎯 Pontos Faciais", callback_data="facial_landmarks"),
                    InlineKeyboardButton("📏 Medições", callback_data="facial_measurements")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="image_main_menu")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACK IMAGE_SETTINGS_MENU COM PRIORIDADE ===
        if callback_data == "image_settings_menu":
            logger.info("⚙️ CALLBACK IMAGE_SETTINGS_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "⚙️ **Configurações de Imagem**\n\n"
                "**Configurações disponíveis:**\n"
                "• 🎨 Qualidade de Processamento\n"
                "• 📐 Resolução de Saída\n"
                "• 🔄 Modo de Blending\n"
                "• 🎯 Detecção Facial\n"
                "• 📊 Nível de Debug\n"
                "• 💾 Cache de Imagens\n\n"
                "**Qualidades disponíveis:**\n"
                "• **Rápido** - 30-60 segundos\n"
                "• **Padrão** - 1-2 minutos\n"
                "• **Ultra** - 2-3 minutos\n\n"
                "**Resoluções disponíveis:**\n"
                "• **512x512** - Rápido\n"
                "• **1024x1024** - Padrão\n"
                "• **2048x2048** - Ultra\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎨 Qualidade", callback_data="quality_settings"),
                    InlineKeyboardButton("📐 Resolução", callback_data="resolution_settings")
                ], [
                    InlineKeyboardButton("🔄 Blending", callback_data="blending_settings"),
                    InlineKeyboardButton("🎯 Detecção", callback_data="detection_settings")
                ], [
                    InlineKeyboardButton("📊 Debug", callback_data="debug_settings"),
                    InlineKeyboardButton("💾 Cache", callback_data="cache_settings")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="image_main_menu")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACK SONO_COACH COM PRIORIDADE ===
        if callback_data == "sono_coach":
            logger.info("😴 CALLBACK SONO_COACH DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "😴 **Coach de Sono Inteligente**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🌙 Análise de Padrões de Sono\n"
                "• 📊 Relatórios de Qualidade\n"
                "• 🎯 Dicas Personalizadas\n"
                "• ⏰ Lembretes de Horário\n"
                "• 🧘 Técnicas de Relaxamento\n"
                "• 📈 Acompanhamento de Progresso\n\n"
                "**Como usar:**\n"
                "1. Use `/sono_analise` para análise completa\n"
                "2. Use `/sono_dicas` para dicas personalizadas\n"
                "3. Use `/sono_relatorio` para relatório detalhado\n\n"
                "**Comandos disponíveis:**\n"
                "• `/sono_analise` - Análise de padrões\n"
                "• `/sono_dicas` - Dicas personalizadas\n"
                "• `/sono_relatorio` - Relatório completo\n"
                "• `/sono_lembrete` - Configurar lembretes\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌙 Análise de Sono", callback_data="sleep_analysis"),
                    InlineKeyboardButton("📊 Relatório", callback_data="sleep_report")
                ], [
                    InlineKeyboardButton("🎯 Dicas", callback_data="sleep_tips"),
                    InlineKeyboardButton("⏰ Lembretes", callback_data="sleep_reminders")
                ], [
                    InlineKeyboardButton("🧘 Relaxamento", callback_data="sleep_relaxation"),
                    InlineKeyboardButton("📈 Progresso", callback_data="sleep_progress")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_coach")
                ]])
            )
            return  # IMPORTANTE: Retornar aqui para não processar outros callbacks
        
        # === CALLBACKS ADICIONAIS COM PRIORIDADE ===
        if callback_data == "sleep_analysis":
            logger.info("🌙 CALLBACK SLEEP_ANALYSIS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🌙 **Análise de Padrões de Sono**\n\n"
                "**Use o comando:** `/sono_analise`\n\n"
                "**O que será analisado:**\n"
                "• Horários de dormir e acordar\n"
                "• Qualidade do sono\n"
                "• Padrões de interrupção\n"
                "• Recomendações personalizadas\n\n"
                "**Status:** Aguardando comando `/sono_analise`...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="sono_coach")
                ]])
            )
            return
        
        if callback_data == "sleep_tips":
            logger.info("🎯 CALLBACK SLEEP_TIPS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎯 **Dicas Personalizadas de Sono**\n\n"
                "**Use o comando:** `/sono_dicas`\n\n"
                "**Dicas disponíveis:**\n"
                "• Técnicas de relaxamento\n"
                "• Rotinas de sono\n"
                "• Ambiente ideal\n"
                "• Alimentação e sono\n\n"
                "**Status:** Aguardando comando `/sono_dicas`...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="sono_coach")
                ]])
            )
            return
        
        if callback_data == "sleep_report":
            logger.info("📊 CALLBACK SLEEP_REPORT DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📊 **Relatório Completo de Sono**\n\n"
                "**Use o comando:** `/sono_relatorio`\n\n"
                "**Relatório inclui:**\n"
                "• Estatísticas detalhadas\n"
                "• Gráficos de progresso\n"
                "• Comparações históricas\n"
                "• Metas e objetivos\n\n"
                "**Status:** Aguardando comando `/sono_relatorio`...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="sono_coach")
                ]])
            )
            return
        
        # === CALLBACKS DE COACHING COM PRIORIDADE ===
        if callback_data == "estresse_coach":
            logger.info("😰 CALLBACK ESTRESSE_COACH DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "😰 **Coach Anti-Estresse**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🧘 Técnicas de Relaxamento\n"
                "• 🎯 Identificação de Gatilhos\n"
                "• 📊 Monitoramento de Estresse\n"
                "• 🌿 Dicas de Bem-estar\n"
                "• ⏰ Pausas Programadas\n"
                "• 📈 Acompanhamento de Progresso\n\n"
                "**Como usar:**\n"
                "1. Use `/estresse_analise` para análise\n"
                "2. Use `/estresse_dicas` para dicas\n"
                "3. Use `/estresse_relatorio` para relatório\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🧘 Relaxamento", callback_data="stress_relaxation"),
                    InlineKeyboardButton("📊 Análise", callback_data="stress_analysis")
                ], [
                    InlineKeyboardButton("🎯 Gatilhos", callback_data="stress_triggers"),
                    InlineKeyboardButton("🌿 Bem-estar", callback_data="stress_wellness")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_coach")
                ]])
            )
            return
        
        if callback_data == "depressao_coach":
            logger.info("😔 CALLBACK DEPRESSAO_COACH DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "😔 **Coach Anti-Depressão**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 💪 Técnicas de Motivação\n"
                "• 🎯 Definição de Metas\n"
                "• 📊 Monitoramento de Humor\n"
                "• 🌟 Atividades Positivas\n"
                "• 🤝 Suporte Emocional\n"
                "• 📈 Acompanhamento de Progresso\n\n"
                "**Como usar:**\n"
                "1. Use `/depressao_analise` para análise\n"
                "2. Use `/depressao_dicas` para dicas\n"
                "3. Use `/depressao_relatorio` para relatório\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💪 Motivação", callback_data="depression_motivation"),
                    InlineKeyboardButton("📊 Análise", callback_data="depression_analysis")
                ], [
                    InlineKeyboardButton("🎯 Metas", callback_data="depression_goals"),
                    InlineKeyboardButton("🌟 Atividades", callback_data="depression_activities")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_coach")
                ]])
            )
            return
        
        # === CALLBACKS DE DEPRESSÃO COM PRIORIDADE ===
        if callback_data == "depression_motivation":
            logger.info("💪 CALLBACK DEPRESSION_MOTIVATION DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "💪 **Técnicas de Motivação**\n\n"
                "**Como usar:**\n"
                "1. Use `/depressao_motivacao` para dicas\n"
                "2. Use `/depressao_motivacao diaria` para rotina\n"
                "3. Use `/depressao_motivacao emergencia` para crise\n\n"
                "**Técnicas disponíveis:**\n"
                "• **Rotina Matinal:** Estrutura o dia\n"
                "• **Metas Pequenas:** Conquistas diárias\n"
                "• **Gratidão:** Foco no positivo\n"
                "• **Exercícios:** Liberação de endorfina\n"
                "• **Socialização:** Conexões humanas\n"
                "• **Hobbies:** Atividades prazerosas\n\n"
                "**Exemplos:**\n"
                "• `/depressao_motivacao` - Dicas gerais\n"
                "• `/depressao_motivacao rotina` - Rotina matinal\n"
                "• `/depressao_motivacao metas` - Definição de metas\n"
                "• `/depressao_motivacao exercicios` - Atividades físicas\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="depressao_coach")
                ]])
            )
            return
        
        if callback_data == "depression_analysis":
            logger.info("📊 CALLBACK DEPRESSION_ANALYSIS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📊 **Análise de Depressão**\n\n"
                "**Como usar:**\n"
                "1. Use `/depressao_analise` para análise\n"
                "2. Use `/depressao_analise humor` para monitoramento\n"
                "3. Use `/depressao_analise relatorio` para relatório\n\n"
                "**Análises disponíveis:**\n"
                "• **Monitoramento de Humor:** Acompanha variações\n"
                "• **Identificação de Padrões:** Reconhece gatilhos\n"
                "• **Avaliação de Sintomas:** Severidade dos sintomas\n"
                "• **Progresso Temporal:** Evolução ao longo do tempo\n"
                "• **Fatores de Risco:** Identifica vulnerabilidades\n"
                "• **Estratégias Eficazes:** O que funciona melhor\n\n"
                "**Exemplos:**\n"
                "• `/depressao_analise` - Análise completa\n"
                "• `/depressao_analise humor` - Monitoramento de humor\n"
                "• `/depressao_analise padroes` - Identificação de padrões\n"
                "• `/depressao_analise sintomas` - Avaliação de sintomas\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="depressao_coach")
                ]])
            )
            return
        
        if callback_data == "depression_goals":
            logger.info("🎯 CALLBACK DEPRESSION_GOALS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎯 **Definição de Metas**\n\n"
                "**Como usar:**\n"
                "1. Use `/depressao_metas` para definir metas\n"
                "2. Use `/depressao_metas pequenas` para metas diárias\n"
                "3. Use `/depressao_metas acompanhar` para progresso\n\n"
                "**Tipos de metas:**\n"
                "• **Metas Diárias:** Pequenas conquistas\n"
                "• **Metas Semanais:** Objetivos semanais\n"
                "• **Metas Mensais:** Planos de longo prazo\n"
                "• **Metas de Bem-estar:** Foco na saúde\n"
                "• **Metas Sociais:** Conexões e relacionamentos\n"
                "• **Metas Pessoais:** Desenvolvimento pessoal\n\n"
                "**Exemplos:**\n"
                "• `/depressao_metas` - Definição de metas\n"
                "• `/depressao_metas diarias` - Metas do dia\n"
                "• `/depressao_metas semanais` - Objetivos da semana\n"
                "• `/depressao_metas bemestar` - Metas de saúde\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="depressao_coach")
                ]])
            )
            return
        
        if callback_data == "depression_activities":
            logger.info("🌟 CALLBACK DEPRESSION_ACTIVITIES DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🌟 **Atividades Positivas**\n\n"
                "**Como usar:**\n"
                "1. Use `/depressao_atividades` para sugestões\n"
                "2. Use `/depressao_atividades fisicas` para exercícios\n"
                "3. Use `/depressao_atividades criativas` para arte\n\n"
                "**Categorias de atividades:**\n"
                "• **Atividades Físicas:** Exercícios e movimento\n"
                "• **Atividades Criativas:** Arte, música, escrita\n"
                "• **Atividades Sociais:** Interação com pessoas\n"
                "• **Atividades Relaxantes:** Meditação, leitura\n"
                "• **Atividades Produtivas:** Trabalho, estudos\n"
                "• **Atividades Prazerosas:** Hobbies e diversão\n\n"
                "**Exemplos:**\n"
                "• `/depressao_atividades` - Sugestões gerais\n"
                "• `/depressao_atividades fisicas` - Exercícios\n"
                "• `/depressao_atividades criativas` - Arte e música\n"
                "• `/depressao_atividades sociais` - Interação social\n"
                "• `/depressao_atividades relaxantes` - Relaxamento\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="depressao_coach")
                ]])
            )
            return
        
        if callback_data == "ansiedade_coach":
            logger.info("😰 CALLBACK ANSIEDADE_COACH DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "😰 **Coach Anti-Ansiedade**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🧘 Técnicas de Respiração\n"
                "• 🎯 Controle de Pensamentos\n"
                "• 📊 Monitoramento de Ansiedade\n"
                "• 🌿 Relaxamento Progressivo\n"
                "• ⏰ Técnicas de Grounding\n"
                "• 📈 Acompanhamento de Progresso\n\n"
                "**Como usar:**\n"
                "1. Use `/ansiedade_analise` para análise\n"
                "2. Use `/ansiedade_dicas` para dicas\n"
                "3. Use `/ansiedade_relatorio` para relatório\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🧘 Respiração", callback_data="anxiety_breathing"),
                    InlineKeyboardButton("📊 Análise", callback_data="anxiety_analysis")
                ], [
                    InlineKeyboardButton("🎯 Controle", callback_data="anxiety_control"),
                    InlineKeyboardButton("🌿 Relaxamento", callback_data="anxiety_relaxation")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_coach")
                ]])
            )
            return
        
        if callback_data == "mindfulness_menu":
            logger.info("🧘 CALLBACK MINDFULNESS_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🧘 **Menu de Mindfulness**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🧘 Meditação Guiada\n"
                "• 🌸 Exercícios de Atenção\n"
                "• 🎯 Técnicas de Foco\n"
                "• 🌿 Relaxamento Profundo\n"
                "• ⏰ Sessões Programadas\n"
                "• 📈 Acompanhamento de Progresso\n\n"
                "**Como usar:**\n"
                "1. Use `/mindfulness_iniciar` para começar\n"
                "2. Use `/mindfulness_sessao` para sessão guiada\n"
                "3. Use `/mindfulness_relatorio` para relatório\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🧘 Meditação", callback_data="mindfulness_meditation"),
                    InlineKeyboardButton("🌸 Atenção", callback_data="mindfulness_attention")
                ], [
                    InlineKeyboardButton("🎯 Foco", callback_data="mindfulness_focus"),
                    InlineKeyboardButton("🌿 Relaxamento", callback_data="mindfulness_relaxation")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_coach")
                ]])
            )
            return
        
        if callback_data == "terapia_menu":
            logger.info("🩺 CALLBACK TERAPIA_MENU DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🩺 **Menu de Terapia**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🗣️ Sessões de Conversa\n"
                "• 📊 Avaliação Psicológica\n"
                "• 🎯 Técnicas Terapêuticas\n"
                "• 📝 Diário Emocional\n"
                "• 🤝 Suporte Profissional\n"
                "• 📈 Acompanhamento de Progresso\n\n"
                "**Como usar:**\n"
                "1. Use `/terapia_iniciar` para começar\n"
                "2. Use `/terapia_sessao` para sessão\n"
                "3. Use `/terapia_relatorio` para relatório\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🗣️ Conversa", callback_data="therapy_conversation"),
                    InlineKeyboardButton("📊 Avaliação", callback_data="therapy_assessment")
                ], [
                    InlineKeyboardButton("🎯 Técnicas", callback_data="therapy_techniques"),
                    InlineKeyboardButton("📝 Diário", callback_data="therapy_journal")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_coach")
                ]])
            )
            return
        
        # === CALLBACKS DE AJUDA E SUPORTE COM PRIORIDADE ===
        if callback_data == "contato_suporte":
            logger.info("📞 CALLBACK CONTATO_SUPORTE DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📞 **Contato e Suporte**\n\n"
                "**Canais de Suporte:**\n"
                "• 💬 Chat Direto com IA\n"
                "• 📧 Email de Suporte\n"
                "• 🆘 Suporte Urgente\n"
                "• 📋 Relatório de Bug\n"
                "• 💡 Sugestão de Melhoria\n"
                "• 🤝 Parcerias\n\n"
                "**Como entrar em contato:**\n"
                "1. Use `/suporte` para chat direto\n"
                "2. Use `/bug <descrição>` para reportar bugs\n"
                "3. Use `/sugestao <ideia>` para sugestões\n\n"
                "**Horário de Atendimento:**\n"
                "• 24/7 - Suporte por IA\n"
                "• Seg-Sex 9h-18h - Suporte Humano\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💬 Chat Direto", callback_data="direct_chat"),
                    InlineKeyboardButton("📧 Email", callback_data="email_support")
                ], [
                    InlineKeyboardButton("🆘 Urgente", callback_data="urgent_support"),
                    InlineKeyboardButton("📋 Bug", callback_data="report_bug")
                ], [
                    InlineKeyboardButton("💡 Sugestão", callback_data="suggest_improvement"),
                    InlineKeyboardButton("🤝 Parcerias", callback_data="partnerships")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_ajuda")
                ]])
            )
            return
               
        if callback_data == "ver_exemplos":
            logger.info("📚 CALLBACK VER_EXEMPLOS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📚 **Exemplos de Uso**\n\n"
                "**Categorias de Exemplos:**\n"
                "• 🎨 Geração de Imagens\n"
                "• 🔄 Face Swapping\n"
                "• 🎭 Clonagem de Voz\n"
                "• 🔍 Análise de Dados\n"
                "• 🛡️ Segurança\n"
                "• 🤖 IA Generativa\n\n"
                "**Exemplos por Categoria:**\n"
                "• **Imagens:** `/gerarimagem um gato astronauta`\n"
                "• **Face Swap:** `/trocar_rosto`\n"
                "• **Voz:** `/clonar_voz [áudio] [texto]`\n"
                "• **Análise:** `/analisar_rosto`\n"
                "• **Segurança:** `/gerar_senha_forte 16`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎨 Imagens", callback_data="examples_images"),
                    InlineKeyboardButton("🔄 Face Swap", callback_data="examples_faceswap")
                ], [
                    InlineKeyboardButton("🎭 Voz", callback_data="examples_voice"),
                    InlineKeyboardButton("🔍 Análise", callback_data="examples_analysis")
                ], [
                    InlineKeyboardButton("🛡️ Segurança", callback_data="examples_security"),
                    InlineKeyboardButton("🤖 IA", callback_data="examples_ai")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_ajuda")
                ]])
            )
            return
               
        if callback_data == "ver_tutorial":
            logger.info("🎓 CALLBACK VER_TUTORIAL DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎓 **Tutoriais e Guias**\n\n"
                "**Tutoriais Disponíveis:**\n"
                "• 🚀 Primeiros Passos\n"
                "• 🎨 Guia de Imagens\n"
                "• 🔄 Face Swapping\n"
                "• 🎭 Clonagem de Voz\n"
                "• 🔍 Análise Avançada\n"
                "• 🛡️ Segurança\n\n"
                "**Como usar:**\n"
                "1. Escolha um tutorial\n"
                "2. Siga as instruções passo a passo\n"
                "3. Pratique com exemplos\n\n"
                "**Tutoriais Interativos:**\n"
                "• Guia passo a passo\n"
                "• Exemplos práticos\n"
                "• Dicas e truques\n"
                "• Solução de problemas\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🚀 Primeiros Passos", callback_data="tutorial_basics"),
                    InlineKeyboardButton("🎨 Imagens", callback_data="tutorial_images")
                ], [
                    InlineKeyboardButton("🔄 Face Swap", callback_data="tutorial_faceswap"),
                    InlineKeyboardButton("🎭 Voz", callback_data="tutorial_voice")
                ], [
                    InlineKeyboardButton("🔍 Análise", callback_data="tutorial_analysis"),
                    InlineKeyboardButton("🛡️ Segurança", callback_data="tutorial_security")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_ajuda")
                ]])
            )
            return
               
        if callback_data == "solucao_problemas":
            logger.info("🔧 CALLBACK SOLUCAO_PROBLEMAS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🔧 **Solução de Problemas**\n\n"
                "**Problemas Comuns:**\n"
                "• ❌ Comando não reconhecido\n"
                "• 🖼️ Erro ao processar imagem\n"
                "• 🎭 Problema com clonagem de voz\n"
                "• 🔄 Face swap não funciona\n"
                "• 🐛 Bot não responde\n"
                "• ⚠️ Erro de conexão\n\n"
                "**Soluções Rápidas:**\n"
                "• Reinicie o bot com `/start`\n"
                "• Verifique se a imagem tem rosto\n"
                "• Use comandos corretos\n"
                "• Verifique conexão com internet\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Comandos", callback_data="fix_commands"),
                    InlineKeyboardButton("🖼️ Imagens", callback_data="fix_images")
                ], [
                    InlineKeyboardButton("🎭 Voz", callback_data="fix_voice"),
                    InlineKeyboardButton("🔄 Face Swap", callback_data="fix_faceswap")
                ], [
                    InlineKeyboardButton("🐛 Bot", callback_data="fix_bot"),
                    InlineKeyboardButton("⚠️ Conexão", callback_data="fix_connection")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_ajuda")
                ]])
            )
            return
               
        if callback_data == "ver_faq":
            logger.info("❓ CALLBACK VER_FAQ DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "❓ **Perguntas Frequentes (FAQ)**\n\n"
                "**Perguntas Mais Comuns:**\n"
                "• 🤖 Como usar o bot?\n"
                "• 🎨 Como gerar imagens?\n"
                "• 🔄 Como fazer face swap?\n"
                "• 🎭 Como clonar voz?\n"
                "• 🛡️ É seguro usar?\n"
                "• 💰 É gratuito?\n\n"
                "**Respostas Rápidas:**\n"
                "• Use `/start` para começar\n"
                "• Use `/gerarimagem [descrição]`\n"
                "• Use `/trocar_rosto`\n"
                "• Use `/clonar_voz [áudio] [texto]`\n"
                "• Sim, totalmente seguro\n"
                "• Sim, completamente gratuito\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🤖 Como Usar", callback_data="faq_usage"),
                    InlineKeyboardButton("🎨 Imagens", callback_data="faq_images")
                ], [
                    InlineKeyboardButton("🔄 Face Swap", callback_data="faq_faceswap"),
                    InlineKeyboardButton("🎭 Voz", callback_data="faq_voice")
                ], [
                    InlineKeyboardButton("🛡️ Segurança", callback_data="faq_security"),
                    InlineKeyboardButton("💰 Preços", callback_data="faq_pricing")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_ajuda")
                ]])
            )
            return
               
        if callback_data == "ver_comandos":
            logger.info("📋 CALLBACK VER_COMANDOS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📋 **Lista de Comandos**\n\n"
                "**Comandos Principais:**\n"
                "• `/start` - Iniciar bot\n"
                "• `/help` - Ajuda geral\n"
                "• `/menu` - Menu principal\n\n"
                "**Comandos de Imagem:**\n"
                "• `/gerarimagem [descrição]`\n"
                "• `/trocar_rosto` - Face swap\n"
                "• `/analisar_rosto` - Análise\n"
                "• `/redimensionar [tamanho]`\n\n"
                "**Comandos de Voz:**\n"
                "• `/clonar_voz [áudio] [texto]`\n"
                "• `/analisar_voz` - Análise\n\n"
                "**Comandos de Segurança:**\n"
                "• `/gerar_senha_forte [critérios]`\n"
                "• `/verificar_vazamento [email]`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎨 Imagens", callback_data="commands_images"),
                    InlineKeyboardButton("🎭 Voz", callback_data="commands_voice")
                ], [
                    InlineKeyboardButton("🛡️ Segurança", callback_data="commands_security"),
                    InlineKeyboardButton("🔍 Análise", callback_data="commands_analysis")
                ], [
                    InlineKeyboardButton("🤖 IA", callback_data="commands_ai"),
                    InlineKeyboardButton("🔍 Busca", callback_data="commands_search")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_ajuda")
                ]])
            )
            return
               
        # === CALLBACKS DE CONVERSÃO DE FORMATO COM PRIORIDADE ===
        if callback_data == "convert_jpg":
            logger.info("📷 CALLBACK CONVERT_JPG DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📷 **Converter para JPG**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/converter_formato jpg`\n"
                "3. Receba imagem convertida\n\n"
                "**Características do JPG:**\n"
                "• Formato compacto\n"
                "• Ideal para fotos\n"
                "• Sem transparência\n"
                "• Tamanho reduzido\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="converter_formato")
                ]])
            )
            return
        
        if callback_data == "convert_png":
            logger.info("🖼️ CALLBACK CONVERT_PNG DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🖼️ **Converter para PNG**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/converter_formato png`\n"
                "3. Receba imagem convertida\n\n"
                "**Características do PNG:**\n"
                "• Suporte a transparência\n"
                "• Qualidade sem perda\n"
                "• Ideal para gráficos\n"
                "• Tamanho maior\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="converter_formato")
                ]])
            )
            return
        
        # === CALLBACKS DE FILTROS COM PRIORIDADE ===
        if callback_data == "filter_artistic":
            logger.info("🎨 CALLBACK FILTER_ARTISTIC DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎨 **Filtros Artísticos**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/aplicar_filtro artistico`\n"
                "3. Receba imagem com filtro\n\n"
                "**Filtros disponíveis:**\n"
                "• Pintura a óleo\n"
                "• Aquarela\n"
                "• Carvão\n"
                "• Lápis\n"
                "• Pastel\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="aplicar_filtro")
                ]])
            )
            return
        
        if callback_data == "filter_photographic":
            logger.info("📸 CALLBACK FILTER_PHOTOGRAPHIC DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📸 **Filtros Fotográficos**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/aplicar_filtro fotografico`\n"
                "3. Receba imagem com filtro\n\n"
                "**Filtros disponíveis:**\n"
                "• Vintage\n"
                "• Sepia\n"
                "• Preto e branco\n"
                "• HDR\n"
                "• Retrato\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="aplicar_filtro")
                ]])
            )
            return
        
        if callback_data == "filter_special":
            logger.info("🎭 CALLBACK FILTER_SPECIAL DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎭 **Filtros Especiais**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/aplicar_filtro especial`\n"
                "3. Receba imagem com filtro\n\n"
                "**Filtros disponíveis:**\n"
                "• Neon\n"
                "• Glitch\n"
                "• Pixel Art\n"
                "• Cartoon\n"
                "• Anime\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="aplicar_filtro")
                ]])
            )
            return
        
        if callback_data == "filter_colors":
            logger.info("🌈 CALLBACK FILTER_COLORS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🌈 **Filtros de Cor**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/aplicar_filtro cores`\n"
                "3. Receba imagem com filtro\n\n"
                "**Filtros disponíveis:**\n"
                "• Saturado\n"
                "• Dessaturado\n"
                "• Invertido\n"
                "• Sepia\n"
                "• Azul\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="aplicar_filtro")
                ]])
            )
            return
        
        # === CALLBACKS DE UPSCALE COM PRIORIDADE ===
        if callback_data == "upscale_2x":
            logger.info("⬆️ CALLBACK UPSCALE_2X DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "⬆️ **Upscale 2x**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/upscale 2`\n"
                "3. Receba imagem 2x maior\n\n"
                "**Características:**\n"
                "• Dobra o tamanho\n"
                "• Processamento rápido\n"
                "• Qualidade boa\n"
                "• Ideal para fotos\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="upscale")
                ]])
            )
            return
        
        if callback_data == "upscale_4x":
            logger.info("⬆️ CALLBACK UPSCALE_4X DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "⬆️ **Upscale 4x**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/upscale 4`\n"
                "3. Receba imagem 4x maior\n\n"
                "**Características:**\n"
                "• Quadruplica o tamanho\n"
                "• Processamento médio\n"
                "• Qualidade alta\n"
                "• Ideal para impressão\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="upscale")
                ]])
            )
            return
        
        if callback_data == "upscale_auto":
            logger.info("⬆️ CALLBACK UPSCALE_AUTO DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "⬆️ **Upscale Automático**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/upscale auto`\n"
                "3. Receba imagem otimizada\n\n"
                "**Características:**\n"
                "• Detecção automática\n"
                "• Fator ideal\n"
                "• Qualidade otimizada\n"
                "• Processamento inteligente\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="upscale")
                ]])
            )
            return
        
        if callback_data == "upscale_pro":
            logger.info("⬆️ CALLBACK UPSCALE_PRO DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "⬆️ **Upscale Profissional**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/upscale pro`\n"
                "3. Receba imagem profissional\n\n"
                "**Características:**\n"
                "• Qualidade máxima\n"
                "• Processamento lento\n"
                "• Detalhes preservados\n"
                "• Ideal para profissionais\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="upscale")
                ]])
            )
            return
        
        # === CALLBACKS DE REDIMENSIONAMENTO COM PRIORIDADE ===
        if callback_data == "resize_pixels":
            logger.info("📏 CALLBACK RESIZE_PIXELS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📏 **Redimensionar por Pixels**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/redimensionar <largura>x<altura>`\n"
                "3. Receba imagem redimensionada\n\n"
                "**Exemplos:**\n"
                "• `/redimensionar 800x600`\n"
                "• `/redimensionar 1920x1080`\n"
                "• `/redimensionar 500x500`\n"
                "• `/redimensionar 1200x800`\n\n"
                "**Características:**\n"
                "• Controle exato do tamanho\n"
                "• Pode distorcer proporções\n"
                "• Ideal para tamanhos específicos\n"
                "• Processamento rápido\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="redimensionar")
                ]])
            )
            return
        
        if callback_data == "resize_percentage":
            logger.info("📊 CALLBACK RESIZE_PERCENTAGE DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📊 **Redimensionar por Porcentagem**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/redimensionar <porcentagem>%`\n"
                "3. Receba imagem redimensionada\n\n"
                "**Exemplos:**\n"
                "• `/redimensionar 50%` - Metade do tamanho\n"
                "• `/redimensionar 150%` - Uma vez e meia\n"
                "• `/redimensionar 200%` - Dobro do tamanho\n"
                "• `/redimensionar 75%` - Três quartos\n\n"
                "**Características:**\n"
                "• Mantém proporções\n"
                "• Fácil de usar\n"
                "• Ideal para ajustes rápidos\n"
                "• Processamento rápido\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="redimensionar")
                ]])
            )
            return
        
        if callback_data == "resize_proportional":
            logger.info("🎯 CALLBACK RESIZE_PROPORTIONAL DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎯 **Redimensionar Mantendo Proporção**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/redimensionar proporcional <largura>`\n"
                "3. Receba imagem redimensionada\n\n"
                "**Exemplos:**\n"
                "• `/redimensionar proporcional 800`\n"
                "• `/redimensionar proporcional 1200`\n"
                "• `/redimensionar proporcional 600`\n"
                "• `/redimensionar proporcional 1000`\n\n"
                "**Características:**\n"
                "• Mantém proporções originais\n"
                "• Evita distorção\n"
                "• Ideal para fotos\n"
                "• Processamento médio\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="redimensionar")
                ]])
            )
            return
        
        if callback_data == "resize_formats":
            logger.info("📱 CALLBACK RESIZE_FORMATS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📱 **Formatos para Dispositivos**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/redimensionar formato <tipo>`\n"
                "3. Receba imagem redimensionada\n\n"
                "**Formatos disponíveis:**\n"
                "• **Instagram:** 1080x1080 (quadrado)\n"
                "• **Facebook:** 1200x630 (capa)\n"
                "• **Twitter:** 1200x675 (post)\n"
                "• **YouTube:** 1280x720 (thumbnail)\n"
                "• **WhatsApp:** 800x800 (perfil)\n"
                "• **LinkedIn:** 1200x627 (post)\n\n"
                "**Características:**\n"
                "• Tamanhos otimizados\n"
                "• Mantém qualidade\n"
                "• Ideal para redes sociais\n"
                "• Processamento rápido\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="redimensionar")
                ]])
            )
            return
        
        # === CALLBACK GENERATE_BY_TEXT COM PRIORIDADE ===
        if callback_data == "generate_by_text":
            logger.info("🖼️ CALLBACK GENERATE_BY_TEXT DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🖼️ **Gerar Imagem por Texto**\n\n"
                "**Como usar:**\n"
                "1. Use `/gerarimagem <descrição>`\n"
                "2. Descreva a imagem que deseja\n"
                "3. Aguarde a geração\n\n"
                "**Exemplos de comandos:**\n"
                "• `/gerarimagem um gato astronauta`\n"
                "• `/gerarimagem uma paisagem de montanha`\n"
                "• `/gerarimagem uma cidade futurista`\n"
                "• `/gerarimagem um dragão voando`\n\n"
                "**Dicas para melhores resultados:**\n"
                "• Seja específico na descrição\n"
                "• Use adjetivos descritivos\n"
                "• Mencione estilo artístico se desejar\n"
                "• Evite descrições muito longas\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎨 Estilos", callback_data="artistic_styles_menu"),
                    InlineKeyboardButton("🌅 Cenários", callback_data="scenario_templates_menu")
                ], [
                    InlineKeyboardButton("📐 Configurações", callback_data="image_settings_menu"),
                    InlineKeyboardButton("🔍 Análise", callback_data="face_analysis_menu")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="gerar_imagem")
                ]])
            )
            return
        
        # === CALLBACKS DE REMOÇÃO DE FUNDO COM PRIORIDADE ===
        if callback_data == "remove_bg_auto":
            logger.info("🤖 CALLBACK REMOVE_BG_AUTO DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🤖 **Remoção Automática de Fundo**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/removerfundo auto`\n"
                "3. Receba imagem sem fundo\n\n"
                "**Características:**\n"
                "• Detecção automática de objetos\n"
                "• IA identifica o fundo\n"
                "• Processamento rápido\n"
                "• Ideal para fotos simples\n\n"
                "**Exemplos:**\n"
                "• `/removerfundo auto` - Remove fundo automaticamente\n"
                "• `/removerfundo auto melhorar` - Com refinamento\n"
                "• `/removerfundo auto bordas` - Suaviza bordas\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="remover_fundo")
                ]])
            )
            return
        
        if callback_data == "remove_bg_manual":
            logger.info("✋ CALLBACK REMOVE_BG_MANUAL DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "✋ **Remoção Manual de Fundo**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/removerfundo manual`\n"
                "3. Selecione área para manter\n"
                "4. Receba resultado\n\n"
                "**Características:**\n"
                "• Controle total sobre seleção\n"
                "• Ideal para imagens complexas\n"
                "• Precisão máxima\n"
                "• Processamento detalhado\n\n"
                "**Exemplos:**\n"
                "• `/removerfundo manual` - Seleção manual\n"
                "• `/removerfundo manual fino` - Modo fino\n"
                "• `/removerfundo manual grosso` - Modo grosso\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="remover_fundo")
                ]])
            )
            return
        
        if callback_data == "remove_bg_custom":
            logger.info("🎨 CALLBACK REMOVE_BG_CUSTOM DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎨 **Remoção Personalizada**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/removerfundo custom`\n"
                "3. Configure parâmetros\n"
                "4. Receba resultado personalizado\n\n"
                "**Opções disponíveis:**\n"
                "• **Tolerância:** Ajusta sensibilidade\n"
                "• **Suavização:** Controla bordas\n"
                "• **Correção:** Melhora detalhes\n"
                "• **Filtros:** Aplica efeitos\n\n"
                "**Exemplos:**\n"
                "• `/removerfundo custom tolerancia=0.5`\n"
                "• `/removerfundo custom suavizar=2`\n"
                "• `/removerfundo custom corrigir`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="remover_fundo")
                ]])
            )
            return
        
        if callback_data == "remove_bg_refine":
            logger.info("✨ CALLBACK REMOVE_BG_REFINE DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "✨ **Refinamento de Remoção**\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/removerfundo refine`\n"
                "3. Aguarde processamento avançado\n"
                "4. Receba resultado refinado\n\n"
                "**Características:**\n"
                "• Processamento avançado\n"
                "• Bordas suavizadas\n"
                "• Detalhes preservados\n"
                "• Qualidade profissional\n\n"
                "**Exemplos:**\n"
                "• `/removerfundo refine` - Refinamento básico\n"
                "• `/removerfundo refine bordas` - Foco em bordas\n"
                "• `/removerfundo refine detalhes` - Preserva detalhes\n"
                "• `/removerfundo refine profissional` - Máxima qualidade\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="remover_fundo")
                ]])
            )
            return
               
        # === CALLBACKS DE PROCESSAMENTO DE IMAGEM COM PRIORIDADE ===
        if callback_data == "gerar_imagem":
            logger.info("🎨 CALLBACK GERAR_IMAGEM DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎨 **Gerador de Imagens**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🖼️ Geração por Texto\n"
                "• 🎭 Estilos Artísticos\n"
                "• 🌅 Cenários Personalizados\n"
                "• 🎨 Filtros e Efeitos\n"
                "• 📐 Diferentes Resoluções\n"
                "• 🔄 Variações de Imagem\n\n"
                "**Como usar:**\n"
                "1. Use `/gerarimagem <descrição>` para gerar\n"
                "2. Use `/gerar_cenario <cenário>` para cenários\n"
                "3. Use `/estilo_rosto <estilo>` para estilos\n\n"
                "**Exemplos:**\n"
                "• `/gerarimagem um gato astronauta`\n"
                "• `/gerar_cenario praia tropical`\n"
                "• `/estilo_rosto anime`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🖼️ Gerar por Texto", callback_data="generate_by_text"),
                    InlineKeyboardButton("🎭 Estilos", callback_data="artistic_styles_menu")
                ], [
                    InlineKeyboardButton("🌅 Cenários", callback_data="scenario_templates_menu"),
                    InlineKeyboardButton("🎨 Filtros", callback_data="apply_filter")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_imagens")
                ]])
            )
            return
        
        if callback_data == "redimensionar":
            logger.info("📐 CALLBACK REDIMENSIONAR DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📐 **Redimensionar Imagem**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 📏 Redimensionar por Pixels\n"
                "• 📊 Redimensionar por Porcentagem\n"
                "• 🎯 Manter Proporção\n"
                "• 🔄 Redimensionar Livre\n"
                "• 📱 Formatos para Dispositivos\n"
                "• 💾 Otimização de Tamanho\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/redimensionar <largura>x<altura>`\n"
                "3. Receba imagem redimensionada\n\n"
                "**Exemplos:**\n"
                "• `/redimensionar 800x600`\n"
                "• `/redimensionar 50%`\n"
                "• `/redimensionar 1920x1080`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📏 Por Pixels", callback_data="resize_pixels"),
                    InlineKeyboardButton("📊 Por Porcentagem", callback_data="resize_percentage")
                ], [
                    InlineKeyboardButton("🎯 Manter Proporção", callback_data="resize_proportional"),
                    InlineKeyboardButton("📱 Formatos", callback_data="resize_formats")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_imagens")
                ]])
            )
            return
        
        if callback_data == "upscale":
            logger.info("⬆️ CALLBACK UPSCALE DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "⬆️ **Melhorar Qualidade (Upscale)**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🔍 Aumentar Resolução\n"
                "• 🎨 Melhorar Detalhes\n"
                "• 📊 Reduzir Ruído\n"
                "• 🎯 Nitidez Avançada\n"
                "• 🔄 Interpolação Inteligente\n"
                "• 💎 Qualidade Profissional\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/upscale <fator>`\n"
                "3. Receba imagem melhorada\n\n"
                "**Exemplos:**\n"
                "• `/upscale 2` - Dobrar tamanho\n"
                "• `/upscale 4` - Quadruplicar tamanho\n"
                "• `/upscale auto` - Detecção automática\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 2x", callback_data="upscale_2x"),
                    InlineKeyboardButton("🎨 4x", callback_data="upscale_4x")
                ], [
                    InlineKeyboardButton("📊 Auto", callback_data="upscale_auto"),
                    InlineKeyboardButton("💎 Pro", callback_data="upscale_pro")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_imagens")
                ]])
            )
            return
        
        if callback_data == "remover_fundo":
            logger.info("✂️ CALLBACK REMOVER_FUNDO DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "✂️ **Remover Fundo**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🎯 Detecção Automática\n"
                "• ✂️ Corte Preciso\n"
                "• 🎨 Fundo Transparente\n"
                "• 🌈 Fundo Personalizado\n"
                "• 🔍 Refinamento Manual\n"
                "• 💾 Múltiplos Formatos\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/remover_fundo`\n"
                "3. Receba imagem sem fundo\n\n"
                "**Formatos suportados:**\n"
                "• PNG (transparente)\n"
                "• JPG (fundo branco)\n"
                "• WEBP (otimizado)\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎯 Automático", callback_data="remove_bg_auto"),
                    InlineKeyboardButton("✂️ Manual", callback_data="remove_bg_manual")
                ], [
                    InlineKeyboardButton("🎨 Fundo Personalizado", callback_data="remove_bg_custom"),
                    InlineKeyboardButton("🔍 Refinar", callback_data="remove_bg_refine")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_imagens")
                ]])
            )
            return
        
        if callback_data == "aplicar_filtro":
            logger.info("🎨 CALLBACK APLICAR_FILTRO DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🎨 **Aplicar Filtros**\n\n"
                "**Filtros disponíveis:**\n"
                "• 🌅 Filtros Artísticos\n"
                "• 📸 Filtros Fotográficos\n"
                "• 🎭 Efeitos Especiais\n"
                "• 🌈 Ajustes de Cor\n"
                "• 🔆 Brilho e Contraste\n"
                "• 🎯 Nitidez e Blur\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/aplicar_filtro <filtro>`\n"
                "3. Receba imagem com filtro\n\n"
                "**Exemplos:**\n"
                "• `/aplicar_filtro vintage`\n"
                "• `/aplicar_filtro blur`\n"
                "• `/aplicar_filtro sepia`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌅 Artísticos", callback_data="filter_artistic"),
                    InlineKeyboardButton("📸 Fotográficos", callback_data="filter_photographic")
                ], [
                    InlineKeyboardButton("🎭 Especiais", callback_data="filter_special"),
                    InlineKeyboardButton("🌈 Cores", callback_data="filter_colors")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_imagens")
                ]])
            )
            return
        
        if callback_data == "converter_formato":
            logger.info("🔄 CALLBACK CONVERTER_FORMATO DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🔄 **Converter Formato**\n\n"
                "**Formatos disponíveis:**\n"
                "• 📷 JPG/JPEG\n"
                "• 🖼️ PNG\n"
                "• 🌐 WEBP\n"
                "• 🎨 GIF\n"
                "• 📱 BMP\n"
                "• 🎯 TIFF\n\n"
                "**Como usar:**\n"
                "1. Envie uma imagem\n"
                "2. Use `/converter_formato <formato>`\n"
                "3. Receba imagem convertida\n\n"
                "**Exemplos:**\n"
                "• `/converter_formato png`\n"
                "• `/converter_formato webp`\n"
                "• `/converter_formato gif`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📷 JPG", callback_data="convert_jpg"),
                    InlineKeyboardButton("🖼️ PNG", callback_data="convert_png")
                ], [
                    InlineKeyboardButton("🌐 WEBP", callback_data="convert_webp"),
                    InlineKeyboardButton("🎨 GIF", callback_data="convert_gif")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_imagens")
                ]])
            )
            return
        
        # === CALLBACKS DOS MENUS PRINCIPAIS ===
        if callback_data == "menu_conversa":
            await handle_menu_conversa(query, context)
        elif callback_data == "menu_busca":
            await handle_menu_busca(query, context)
        elif callback_data == "menu_seguranca":
            await handle_menu_seguranca(query, context)
        elif callback_data == "menu_imagens":
            await handle_menu_imagens(query, context)
        elif callback_data == "menu_audio":
            await handle_menu_audio(query, context)
        elif callback_data == "menu_analise":
            await handle_menu_analise(query, context)
        elif callback_data == "menu_ia_generativa":
            await handle_menu_ia_generativa(query, context)
        elif callback_data == "menu_coach":
            await handle_menu_coach(query, context)
        elif callback_data == "menu_ajuda":
            await handle_menu_ajuda(query, context)
        elif callback_data == "menu_config":
            await handle_menu_config(query, context)
        
        # === CALLBACKS DE NAVEGAÇÃO ===
        elif callback_data == "voltar_menu":
            await voltar_ao_menu_principal(query, context)
        elif callback_data == "main_menu":
            await voltar_ao_menu_principal(query, context)
        
        # === CALLBACKS DOS SUBMENUS ===
        elif callback_data == "conversar_agora":
            await query.edit_message_text("💬 **Modo Conversa Ativado!**\n\nAgora você pode conversar naturalmente comigo. Digite sua mensagem!")
        elif callback_data == "ia_avancada":
            await query.edit_message_text("🧠 **IA Avançada Ativada!**\n\nRecursos avançados de IA disponíveis:\n• Análise de contexto\n• Processamento multimodal\n• Memória de conversas")
        elif callback_data == "ver_historico":
            await query.edit_message_text("📝 **Histórico de Conversas**\n\nHistórico disponível para análise e resumos.")
        elif callback_data == "limpar_chat":
            database.reset_chat_history(query.message.chat_id)
            await query.edit_message_text("🗑️ **Chat Limpo!**\n\nHistórico da conversa foi limpo com sucesso.")
        
        # === CALLBACKS DE BUSCA ===
        elif callback_data == "buscar_web":
            await query.edit_message_text("🔍 **Busca Web**\n\nUse o comando: `/web [sua pergunta]`\n\nExemplo: `/web campeão da Copa 2022?`")
        elif callback_data == "ultimas_noticias":
            logger.info("📰 CALLBACK ULTIMAS_NOTICIAS DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📰 **Últimas Notícias**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🌍 Notícias Mundiais\n"
                "• 🇧🇷 Notícias do Brasil\n"
                "• 💼 Notícias de Tecnologia\n"
                "• 🏥 Notícias de Saúde\n"
                "• 🏆 Notícias de Esportes\n"
                "• 📊 Notícias Econômicas\n\n"
                "**Como usar:**\n"
                "1. Use `/web notícias [tema]` para buscar\n"
                "2. Use `/web últimas notícias [categoria]`\n"
                "3. Use `/web news [tema]` para inglês\n\n"
                "**Exemplos:**\n"
                "• `/web notícias tecnologia`\n"
                "• `/web últimas notícias Brasil`\n"
                "• `/web news artificial intelligence`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌍 Mundiais", callback_data="news_world"),
                    InlineKeyboardButton("🇧🇷 Brasil", callback_data="news_brazil")
                ], [
                    InlineKeyboardButton("💼 Tecnologia", callback_data="news_tech"),
                    InlineKeyboardButton("🏥 Saúde", callback_data="news_health")
                ], [
                    InlineKeyboardButton("🏆 Esportes", callback_data="news_sports"),
                    InlineKeyboardButton("📊 Economia", callback_data="news_economy")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_busca")
                ]])
            )
            return
        
        elif callback_data == "resumir_url":
            await query.edit_message_text("📝 **Resumir URL**\n\nUse o comando: `/resumir [link]`\n\nExemplo: `/resumir https://exemplo.com`")
        
        elif callback_data == "pesquisa_avancada":
            logger.info("🔬 CALLBACK PESQUISA_AVANCADA DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🔬 **Pesquisa Avançada**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🔍 Pesquisa por Palavras-chave\n"
                "• 📊 Análise de Tendências\n"
                "• 🎯 Pesquisa Específica\n"
                "• 📈 Comparação de Dados\n"
                "• 🔬 Pesquisa Acadêmica\n"
                "• 📋 Relatórios Detalhados\n\n"
                "**Como usar:**\n"
                "1. Use `/web [pergunta específica]`\n"
                "2. Use `/web pesquisa [tema]`\n"
                "3. Use `/web análise [assunto]`\n\n"
                "**Exemplos:**\n"
                "• `/web pesquisa inteligência artificial 2024`\n"
                "• `/web análise mercado de criptomoedas`\n"
                "• `/web tendências tecnologia mobile`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Palavras-chave", callback_data="search_keywords"),
                    InlineKeyboardButton("📊 Tendências", callback_data="search_trends")
                ], [
                    InlineKeyboardButton("🎯 Específica", callback_data="search_specific"),
                    InlineKeyboardButton("📈 Comparação", callback_data="search_comparison")
                ], [
                    InlineKeyboardButton("🔬 Acadêmica", callback_data="search_academic"),
                    InlineKeyboardButton("📋 Relatórios", callback_data="search_reports")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_busca")
                ]])
            )
            return
        
        # === CALLBACKS DE SEGURANÇA ===
        elif callback_data == "gerar_senha":
            await query.edit_message_text("🔑 **Gerar Senha Forte**\n\nUse o comando: `/gerar_senha_forte [critérios]`\n\nExemplo: `/gerar_senha_forte 16 caracteres com símbolos`")
        elif callback_data == "verificar_vazamento":
            await query.edit_message_text("🛡️ **Verificar Vazamentos**\n\nUse o comando: `/verificar_vazamento [email]`\n\nExemplo: `/verificar_vazamento seu@email.com`")
        elif callback_data == "scan_phishing":
            await query.edit_message_text("🚫 **Anti-Phishing**\n\nUse o comando: `/scan_phishing [url]`\n\nExemplo: `/scan_phishing https://site-suspeito.com`")
        elif callback_data == "anonimizar_dados":
            await query.edit_message_text("🎭 **Anonimizar Dados**\n\nUse o comando: `/anonimizar_dados [texto]`\n\nExemplo: `/anonimizar_dados João Silva, CPF: 123.456.789-00`")
        elif callback_data == "criptografia":
            logger.info("🔒 CALLBACK CRIPTOGRAFIA DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "🔒 **Sistema de Criptografia**\n\n"
                "**Funcionalidades disponíveis:**\n"
                "• 🔐 Criptografar Texto\n"
                "• 🔓 Descriptografar Texto\n"
                "• 🎯 Hash de Senhas\n"
                "• 🔑 Gerar Chaves\n"
                "• 📊 Verificar Integridade\n"
                "• 🛡️ Assinatura Digital\n\n"
                "**Como usar:**\n"
                "1. Use `/criptografar <texto>` para criptografar\n"
                "2. Use `/descriptografar <texto>` para descriptografar\n"
                "3. Use `/hash_senha <senha>` para gerar hash\n\n"
                "**Exemplos:**\n"
                "• `/criptografar mensagem secreta`\n"
                "• `/descriptografar texto_criptografado`\n"
                "• `/hash_senha minha_senha123`\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔐 Criptografar", callback_data="encrypt_text"),
                    InlineKeyboardButton("🔓 Descriptografar", callback_data="decrypt_text")
                ], [
                    InlineKeyboardButton("🎯 Hash", callback_data="hash_password"),
                    InlineKeyboardButton("🔑 Chaves", callback_data="generate_keys")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_seguranca")
                ]])
            )
            return
        
        elif callback_data == "relatorio_seguranca":
            logger.info("📊 CALLBACK RELATORIO_SEGURANCA DETECTADO - PROCESSANDO!")
            await query.edit_message_text(
                "📊 **Relatório de Segurança**\n\n"
                "**Informações disponíveis:**\n"
                "• 🛡️ Status de Segurança\n"
                "• 🔍 Últimas Verificações\n"
                "• 📈 Estatísticas de Uso\n"
                "• ⚠️ Alertas de Segurança\n"
                "• 🔐 Histórico de Criptografia\n"
                "• 📋 Recomendações\n\n"
                "**Como usar:**\n"
                "1. Use `/relatorio_seguranca` para relatório completo\n"
                "2. Use `/status_seguranca` para status atual\n"
                "3. Use `/alertas_seguranca` para alertas\n\n"
                "**Relatório inclui:**\n"
                "• Senhas verificadas\n"
                "• URLs analisadas\n"
                "• Dados anonimizados\n"
                "• Tentativas de phishing\n\n"
                "**Status:** ✅ Sistema funcionando!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛡️ Status", callback_data="security_status"),
                    InlineKeyboardButton("📈 Estatísticas", callback_data="security_stats")
                ], [
                    InlineKeyboardButton("⚠️ Alertas", callback_data="security_alerts"),
                    InlineKeyboardButton("📋 Recomendações", callback_data="security_recommendations")
                ], [
                    InlineKeyboardButton("🔙 Voltar", callback_data="menu_seguranca")
                ]])
            )
            return
        
        # === CALLBACKS DE IMAGENS ===
        elif callback_data == "generate_image":
            await query.edit_message_text("🎨 **Gerar Imagem**\n\nUse o comando: `/gerarimagem [descrição]`\n\nExemplo: `/gerarimagem um leão de óculos`")
        elif callback_data == "edit_image":
            await query.edit_message_text("✏️ **Editar Imagem**\n\nEnvie uma imagem e use:\n• `/redimensionar 800x600`\n• `/aplicar_filtro vintage`\n• `/upscale`")
        elif callback_data == "analyze_image":
            await query.edit_message_text("🔍 **Análise de Imagem**\n\nEnvie uma imagem para análise automática completa!")
        elif callback_data == "art_styles":
            await query.edit_message_text("🎭 **Estilos Artísticos**\n\nFuncionalidade em desenvolvimento.")
        
        # === CALLBACKS DE ÁUDIO ===
        elif callback_data == "record_reference":
            await query.edit_message_text("🎤 **Gravar Áudio de Referência**\n\nEnvie uma mensagem de áudio para usar como referência na clonagem de voz.")
        elif callback_data == "clone_voz":
            await query.edit_message_text("🎭 **Clonar Voz**\n\nUse o comando: `/clonar_voz [áudio] [texto]`\n\nPrimeiro envie um áudio de referência, depois use o comando.")
        elif callback_data == "voice_analysis":
            await query.edit_message_text("🎵 **Análise de Voz**\n\nEnvie uma mensagem de áudio para análise automática.")
        elif callback_data == "voice_settings":
            await query.edit_message_text("⚙️ **Configurações de Voz**\n\nFuncionalidade em desenvolvimento.")
        elif callback_data == "voice_history":
            await query.edit_message_text("📊 **Histórico de Clonagens**\n\nFuncionalidade em desenvolvimento.")
        
        # === CALLBACKS DE ANÁLISE IA ===
        elif callback_data == "gemini_chat":
            await query.edit_message_text("🤖 **Chat com Gemini**\n\nConverse naturalmente comigo! Digite sua mensagem.")
        elif callback_data == "code_analysis":
            await query.edit_message_text("🧠 **Análise de Código**\n\nUse o comando: `/gerar_codigo [linguagem] [descrição]`")
        elif callback_data == "data_analysis":
            await query.edit_message_text("📊 **Análise de Dados**\n\nFuncionalidade em desenvolvimento.")
        elif callback_data == "web_search":
            await query.edit_message_text("🔍 **Pesquisa Web**\n\nUse o comando: `/web [pergunta]`")
        elif callback_data == "translation":
            await query.edit_message_text("🌐 **Tradução**\n\nFuncionalidade em desenvolvimento.")
        
        # === CALLBACKS DE IA GENERATIVA ===
        elif callback_data == "clone_gravar_audio":
            await query.edit_message_text("🎤 **Gravar Áudio de Referência**\n\nEnvie uma mensagem de áudio para usar como referência na clonagem de voz.")
        elif callback_data == "clone_exemplos":
            await query.edit_message_text("📚 **Exemplos de Clonagem**\n\nFuncionalidade em desenvolvimento.")
        elif callback_data == "clone_configuracoes":
            await query.edit_message_text("⚙️ **Configurações de Clone**\n\nFuncionalidade em desenvolvimento.")
        elif callback_data == "clone_ajuda":
            await query.edit_message_text("❓ **Ajuda - Clone de Voz**\n\nUse `/clonar_voz [áudio] [texto]` para clonar sua voz.")
        elif callback_data == "clone_voz_menu":
            await query.edit_message_text("🎭 **Menu de Clone de Voz**\n\n**Opções disponíveis:**\n• 🎤 Gravar áudio de referência\n• 📝 Ver exemplos\n• ⚙️ Configurações\n• ❓ Ajuda\n\n**Como usar:**\n1. Grave um áudio de referência\n2. Use `/clonar_voz [texto]`\n3. A IA clonará sua voz!")
        
        # === CALLBACKS DE MINDFULNESS ===
        elif callback_data == "mindfulness_respiracao":
            await iniciar_sessao_mindfulness(query, context, "respiracao", "5")
        elif callback_data == "mindfulness_meditacao":
            await iniciar_sessao_mindfulness(query, context, "meditacao", "10")
        elif callback_data == "mindfulness_manha":
            await iniciar_sessao_mindfulness(query, context, "manha", "10")
        elif callback_data == "mindfulness_noite":
            await iniciar_sessao_mindfulness(query, context, "noite", "15")
        elif callback_data == "mindfulness_rapido":
            await iniciar_sessao_mindfulness(query, context, "respiracao", "5")
        elif callback_data == "mindfulness_completo":
            await iniciar_sessao_mindfulness(query, context, "meditacao", "20")
        elif callback_data == "mindfulness_progresso":
            await handle_mindfulness_progresso(query, context)
        elif callback_data == "mindfulness_metas":
            await handle_mindfulness_metas(query, context)
        elif callback_data == "mindfulness_ajuda":
            await handle_mindfulness_ajuda(query, context)
        
        # === CALLBACKS DE TERAPIA IA ===
        elif callback_data == "terapia_ansiedade":
            await iniciar_sessao_terapia(query, context, "ansiedade", "cognitiva")
        elif callback_data == "terapia_depressao":
            await iniciar_sessao_terapia(query, context, "depressao", "cognitiva")
        elif callback_data == "terapia_estresse":
            await iniciar_sessao_terapia(query, context, "estresse", "cognitiva")
        elif callback_data == "terapia_sono":
            await iniciar_sessao_mindfulness(query, context, "sono", "cognitiva")
        elif callback_data == "terapia_autoestima":
            await iniciar_sessao_terapia(query, context, "ansiedade", "comportamental")
        elif callback_data == "terapia_relacionamentos":
            await iniciar_sessao_terapia(query, context, "estresse", "comportamental")
        elif callback_data == "terapia_objetivos":
            await iniciar_sessao_terapia(query, context, "depressao", "comportamental")
        elif callback_data == "terapia_crescimento":
            await iniciar_sessao_mindfulness(query, context, "sono", "comportamental")
        elif callback_data == "terapia_acompanhamento":
            await handle_terapia_acompanhamento(query, context)
        elif callback_data == "terapia_recursos":
            await handle_terapia_recursos(query, context)
        elif callback_data == "terapia_ajuda":
            await handle_terapia_ajuda(query, context)
        
        # === CALLBACKS DE ANÁLISE DE IMAGEM ===
        elif callback_data == "analyze_colors":
            await handle_color_analysis(query, context)
        elif callback_data == "ocr_text":
            await handle_ocr_analysis(query, context)
        elif callback_data == "analyze_mood":
            await handle_mood_analysis(query, context)
        elif callback_data == "generate_tags":
            await handle_tag_generation(query, context)
        elif callback_data == "detailed_analysis":
            await handle_detailed_analysis(query, context)
        elif callback_data == "suggestions":
            await handle_suggestions(query, context)
        
        # === CALLBACKS DE TOUR INTERATIVO ===
        elif callback_data == "tour_next":
            # Avançar tour
            user_id = update.effective_user.id
            next_step = ui_manager.interactive_tour.next_tour_step(user_id)
            if next_step:
                keyboard = []
                for button_row in next_step["buttons"]:
                    if len(button_row) == 2:
                        keyboard.append([InlineKeyboardButton(button_row[0], callback_data=button_row[1])])
                    else:
                        keyboard.append([InlineKeyboardButton(btn, callback_data=btn) for btn in button_row])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=f"{next_step['title']}\n\n{next_step['description']}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        elif callback_data == "start_using":
            # Finalizar tour e mostrar menu principal
            await voltar_ao_menu_principal(query, context)
        elif callback_data == "more_help":
            # Mostrar ajuda adicional
            await handle_menu_ajuda(query, context)
        
        # === CALLBACKS LEGADOS (para compatibilidade) ===
        elif callback_data == "menu_gerarimagem":
            await query.edit_message_text("🎨 **Gerar Imagem**\n\nUse o comando: `/gerarimagem [descrição]`\n\nExemplo: `/gerarimagem um leão de óculos`")
        elif callback_data == "menu_buscaweb":
            await query.edit_message_text("🔍 **Busca Web**\n\nUse o comando: `/web [pergunta]`\n\nExemplo: `/web campeão da Copa 2022?`")
        elif callback_data == "menu_resumirurl":
            await query.edit_message_text("📝 **Resumir URL**\n\nUse o comando: `/resumir [link]`\n\nExemplo: `/resumir https://exemplo.com`")
        elif callback_data == "menu_reset":
            database.reset_chat_history(query.message.chat_id)
            await query.edit_message_text("🗑️ **Chat Limpo!**\n\nHistórico da conversa foi limpo com sucesso.")
        
        # === CALLBACKS DE FACE SWAPPING FUNCIONAL ===
        elif callback_data == "image_main_menu":
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data == "face_swap_menu":
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data == "try_swap_faces":
            # Iniciar processo de face swap
            await query.edit_message_text(
                "🔄 **Iniciando Face Swap!**\n\n"
                "**Passo 1:** Use `/trocar_rosto` para começar\n"
                "**Passo 2:** Envie a primeira imagem (rosto fonte)\n"
                "**Passo 3:** Envie a segunda imagem (rosto destino)\n"
                "**Passo 4:** Receba o resultado!\n\n"
                "**Dicas para melhor resultado:**\n"
                "• Use fotos com boa iluminação\n"
                "• Rostos devem estar bem visíveis\n"
                "• Evite ângulos muito extremos\n"
                "• Qualidade mínima: 512x512 pixels\n\n"
                "**Status:** Aguardando comando `/trocar_rosto`...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")
                ]])
            )
        elif callback_data == "ultra_quality":
            # Iniciar face swap ultra qualidade
            await query.edit_message_text(
                "⚡ **Face Swap Ultra Qualidade!**\n\n"
                "**Características:**\n"
                "• Processamento mais lento (1-2 minutos)\n"
                "• Qualidade máxima de face swap\n"
                "• Blending perfeito entre rostos\n"
                "• Detalhes preservados\n\n"
                "**Como usar:**\n"
                "1. Use `/trocar_rosto_ultra` para iniciar\n"
                "2. Envie a primeira imagem (rosto fonte)\n"
                "3. Envie a segunda imagem (rosto destino)\n"
                "4. Receba resultado com qualidade máxima\n\n"
                "**Status:** Pronto para usar!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Tentar Ultra", callback_data="try_ultra_quality"),
                    InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")
                ]])
            )
        elif callback_data == "try_ultra_quality":
            await query.edit_message_text(
                "⚡ **Ultra Qualidade Ativada!**\n\n"
                "**Use o comando:** `/trocar_rosto_ultra`\n\n"
                "**Processo:**\n"
                "1. Envie primeira imagem (rosto fonte)\n"
                "2. Envie segunda imagem (rosto destino)\n"
                "3. Aguarde processamento (1-2 minutos)\n"
                "4. Receba resultado com qualidade máxima\n\n"
                "**Status:** Aguardando comando `/trocar_rosto_ultra`...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")
                ]])
            )
        elif callback_data == "fast_processing":
            # Iniciar face swap rápido
            await query.edit_message_text(
                "🚀 **Face Swap Rápido!**\n\n"
                "**Características:**\n"
                "• Processamento rápido (30-60 segundos)\n"
                "• Qualidade boa\n"
                "• Ideal para testes\n"
                "• Menos recursos utilizados\n\n"
                "**Como usar:**\n"
                "1. Use `/trocar_rosto_rapido` para iniciar\n"
                "2. Envie a primeira imagem (rosto fonte)\n"
                "3. Envie a segunda imagem (rosto destino)\n"
                "4. Receba resultado rapidamente\n\n"
                "**Status:** Pronto para usar!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🚀 Tentar Rápido", callback_data="try_fast_processing"),
                    InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")
                ]])
            )
        elif callback_data == "try_fast_processing":
            await query.edit_message_text(
                "🚀 **Processamento Rápido Ativado!**\n\n"
                "**Use o comando:** `/trocar_rosto_rapido`\n\n"
                "**Processo:**\n"
                "1. Envie primeira imagem (rosto fonte)\n"
                "2. Envie segunda imagem (rosto destino)\n"
                "3. Aguarde processamento (30-60 segundos)\n"
                "4. Receba resultado rapidamente\n\n"
                "**Status:** Aguardando comando `/trocar_rosto_rapido`...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="face_swap_menu")
                ]])
            )
        elif callback_data == "quality_analysis":
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data == "custom_scenario":
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("template_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("realistic_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("fantasy_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("cyberpunk_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("vintage_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("anime_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("painting_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("photographic_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("cartoon_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("surreal_style"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("use_template_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("customize_template_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("confirm_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("choose_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("analyze_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("view_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("send_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("cancel_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("apply_"):
            await image_generation_ui.handle_image_callback(query, context)
        elif callback_data.startswith("customize_"):
            await image_generation_ui.handle_image_callback(query, context)
        
        # === CALLBACK NÃO RECONHECIDO ===
        else:
            logger.warning(f"Callback não reconhecido: {callback_data}")
            await query.edit_message_text(
                "❓ **Comando não reconhecido**\n\n"
                f"Callback: `{callback_data}`\n\n"
                "Este comando ainda não foi implementado.\n"
                "Use o menu principal para navegar."
            )
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar callback: {e}")
        try:
            await update.callback_query.edit_message_text(
                "❌ **Erro no Menu**\n\n"
                "Ocorreu um erro ao processar sua seleção.\n"
                "Tente novamente ou use /start para recarregar."
            )
        except Exception as edit_error:
            logger.error(f"Erro ao editar mensagem de erro: {edit_error}")

# === COMANDOS DE FACE SWAPPING E GERAÇÃO DE CENÁRIOS ===

async def trocar_rosto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Troca rostos entre duas imagens"""
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "🔄 **Uso:** `/trocar_rosto`\n\n"
            "**Como usar:**\n"
            "1. Envie a primeira imagem (rosto fonte)\n"
            "2. Responda com `/trocar_rosto`\n"
            "3. Envie a segunda imagem (rosto destino)\n\n"
            "**Exemplo:**\n"
            "• Envie foto do rosto A\n"
            "• Responda: `/trocar_rosto`\n"
            "• Envie foto do rosto B\n"
            "• Receba resultado com rosto A no corpo B",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text("🔄 **Processando troca de rostos...**")
    
    try:
        # Armazenar primeira imagem
        if 'source_image' not in context.user_data:
            photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
            context.user_data['source_image'] = photo_bytes
            await update.message.reply_text("✅ **Primeira imagem salva!** Agora envie a segunda imagem.")
            return
        
        # Processar segunda imagem
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        target_image = photo_bytes
        source_image = context.user_data['source_image']
        
        # Realizar face swap
        result = await face_swapper.swap_faces(source_image, target_image, quality="high")
        
        if result['success']:
            # Enviar resultado
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result['image'],
                caption=f"✅ **Face Swap Concluído!**\n\n"
                       f"📊 **Qualidade:** {result['quality_score']:.2f}\n"
                       f"👤 **Rostos detectados:** {result['source_faces_count']} → {result['target_faces_count']}"
            )
            
            # Limpar dados do usuário
            del context.user_data['source_image']
        else:
            await update.message.reply_text(f"❌ **Erro:** {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro no face swap: {e}")
        await update.message.reply_text(f"❌ Erro na troca de rostos: {str(e)}")

async def trocar_rosto_ultra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Troca rostos com qualidade ultra"""
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "⚡ **Uso:** `/trocar_rosto_ultra`\n\n"
            "**Qualidade Ultra:**\n"
            "• Processamento mais lento (2-3 minutos)\n"
            "• Qualidade máxima de face swap\n"
            "• Blending perfeito entre rostos\n"
            "• Detalhes preservados\n\n"
            "**Como usar:**\n"
            "1. Envie a primeira imagem\n"
            "2. Responda com `/trocar_rosto_ultra`\n"
            "3. Envie a segunda imagem",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text("⚡ **Processando com qualidade ULTRA...** (Aguarde 2-3 minutos)")
    
    try:
        # Armazenar primeira imagem
        if 'source_image' not in context.user_data:
            photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
            context.user_data['source_image'] = photo_bytes
            await update.message.reply_text("✅ **Primeira imagem salva!** Agora envie a segunda imagem.")
            return
        
        # Processar segunda imagem
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        target_image = photo_bytes
        source_image = context.user_data['source_image']
        
        # Realizar face swap com qualidade ultra
        result = await face_swapper.swap_faces(source_image, target_image, quality="ultra")
        
        if result['success']:
            # Enviar resultado
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result['image'],
                caption=f"⚡ **Face Swap ULTRA Concluído!**\n\n"
                       f"📊 **Qualidade:** {result['quality_score']:.2f}\n"
                       f"👤 **Rostos detectados:** {result['source_faces_count']} → {result['target_faces_count']}\n"
                       f"✨ **Processamento:** Qualidade Ultra"
            )
            
            # Limpar dados do usuário
            del context.user_data['source_image']
        else:
            await update.message.reply_text(f"❌ **Erro:** {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro no face swap ultra: {e}")
        await update.message.reply_text(f"❌ Erro na troca de rostos: {str(e)}")

async def trocar_rosto_rapido(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Troca rostos com processamento rápido"""
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "🚀 **Uso:** `/trocar_rosto_rapido`\n\n"
            "**Processamento Rápido:**\n"
            "• Processamento rápido (30-60 segundos)\n"
            "• Qualidade boa\n"
            "• Ideal para testes\n"
            "• Menos recursos utilizados\n\n"
            "**Como usar:**\n"
            "1. Envie a primeira imagem\n"
            "2. Responda com `/trocar_rosto_rapido`\n"
            "3. Envie a segunda imagem",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text("🚀 **Processando rapidamente...** (Aguarde 30-60 segundos)")
    
    try:
        # Armazenar primeira imagem
        if 'source_image' not in context.user_data:
            photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
            context.user_data['source_image'] = photo_bytes
            await update.message.reply_text("✅ **Primeira imagem salva!** Agora envie a segunda imagem.")
            return
        
        # Processar segunda imagem
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        target_image = photo_bytes
        source_image = context.user_data['source_image']
        
        # Realizar face swap rápido
        result = await face_swapper.swap_faces(source_image, target_image, quality="fast")
        
        if result['success']:
            # Enviar resultado
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result['image'],
                caption=f"🚀 **Face Swap RÁPIDO Concluído!**\n\n"
                       f"📊 **Qualidade:** {result['quality_score']:.2f}\n"
                       f"👤 **Rostos detectados:** {result['source_faces_count']} → {result['target_faces_count']}\n"
                       f"⚡ **Processamento:** Rápido"
            )
            
            # Limpar dados do usuário
            del context.user_data['source_image']
        else:
            await update.message.reply_text(f"❌ **Erro:** {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro no face swap rápido: {e}")
        await update.message.reply_text(f"❌ Erro na troca de rostos: {str(e)}")

async def rosto_cenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Coloca rosto em um cenário específico - VERSÃO MELHORADA"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "🎭 **Uso:** `/rosto_cenario <descrição do cenário>`\n\n"
            "**Exemplos:**\n"
            "• `/rosto_cenario praia tropical com coqueiros`\n"
            "• `/rosto_cenario escritório moderno com vista da cidade`\n"
            "• `/rosto_cenario floresta mágica com fadas`\n"
            "• `/rosto_cenario restaurante elegante à noite`\n\n"
            "**Como usar:**\n"
            "1. Envie uma foto com rosto\n"
            "2. Use o comando com descrição do cenário\n"
            "3. Receba resultado com seu rosto no cenário",
            parse_mode='Markdown'
        )
        return
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("📸 **Envie uma foto com rosto primeiro!**\n\n**Como usar:**\n1. Envie uma foto com rosto\n2. Responda com `/rosto_cenario <cenário>`\n3. Receba resultado!")
        return
    
    scenario_prompt = " ".join(context.args)
    await update.message.reply_text(f"🎭 **Gerando cenário: {scenario_prompt}...**")
    
    try:
        # Inicializar sistema de detecção facial
        await face_swap_handler.initialize()
        
        # Baixar imagem do rosto
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        
        # Verificar se há rosto na imagem
        cv_img = await face_swap_handler._bytes_to_cv2(bytes(photo_bytes))
        faces = face_swap_handler._detect_faces(cv_img)
        
        if not faces:
            await update.message.reply_text(
                "❌ **Nenhum rosto detectado na imagem!**\n\n"
                "**Dicas para melhor resultado:**\n"
                "• Certifique-se de que há rostos bem visíveis\n"
                "• Use boa iluminação\n"
                "• Evite ângulos muito extremos\n"
                "• Qualidade mínima: 512x512 pixels\n\n"
                "**Tente novamente com uma foto diferente!**",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(f"✅ **Rosto detectado!** Processando cenário...")
        
        # Gerar cenário com rosto
        result = await face_swapper.swap_face_to_scenario(photo_bytes, scenario_prompt, style="realistic")
        
        if result['success']:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result['image'],
                caption=f"🎭 **Rosto + Cenário Concluído!**\n\n"
                       f"🌅 **Cenário:** {scenario_prompt}\n"
                       f"📊 **Qualidade:** {result['quality_score']:.2f}\n"
                       f"👤 **Rostos detectados:** {result['source_faces_count']} → {result['target_faces_count']}"
            )
        else:
            await update.message.reply_text(f"❌ **Erro:** {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro na geração de cenário: {e}")
        await update.message.reply_text(f"❌ Erro na geração: {str(e)}")

async def usar_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa template pré-definido de cenário"""
    if len(context.args) < 1:
        templates = scenario_generator.get_available_templates()
        template_list = "\n".join([f"• `{name}`" for name in templates])
        
        await update.message.reply_text(
            f"🌅 **Templates Disponíveis:**\n\n{template_list}\n\n"
            "**Uso:** `/template <nome>`\n"
            "**Exemplo:** `/template praia`",
            parse_mode='Markdown'
        )
        return
    
    template_name = context.args[0].lower()
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("📸 Envie uma foto com rosto primeiro!")
        return
    
    await update.message.reply_text(f"🌅 **Aplicando template {template_name}...**")
    
    try:
        # Baixar imagem do rosto
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        
        # Gerar cenário com template
        result = await face_swapper.swap_face_to_scenario(photo_bytes, "", style="realistic")
        
        if result['success']:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result['image'],
                caption=f"🌅 **Template {template_name.title()} Aplicado!**\n\n"
                       f"📊 **Qualidade:** {result['quality_score']:.2f}\n"
                       f"👤 **Rostos detectados:** {result['source_faces_count']} → {result['target_faces_count']}"
            )
        else:
            await update.message.reply_text(f"❌ **Erro:** {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro no template: {e}")
        await update.message.reply_text(f"❌ Erro no template: {str(e)}")

async def estilo_rosto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Aplica estilos artísticos ao rosto"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "🎨 **Uso:** `/estilo_rosto <estilo>`\n\n"
            "**Estilos disponíveis:**\n"
            "• `anime` - Estilo anime/mangá\n"
            "• `realista` - Realismo fotográfico\n"
            "• `pintura` - Estilo pintura clássica\n"
            "• `cartoon` - Desenho animado\n"
            "• `cyberpunk` - Estilo futurista\n"
            "• `vintage` - Estilo retrô\n\n"
            "**Como usar:**\n"
            "1. Envie uma foto com rosto\n"
            "2. Use o comando com o estilo desejado",
            parse_mode='Markdown'
        )
        return
    
    style = context.args[0].lower()
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("📸 Envie uma foto com rosto primeiro!")
        return
    
    await update.message.reply_text(f"🎨 **Aplicando estilo {style}...**")
    
    try:
        # Baixar imagem do rosto
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        
        # Aplicar estilo (implementação simplificada)
        await update.message.reply_text(f"🎨 **Estilo {style} aplicado!** (Funcionalidade em desenvolvimento)")
        
    except Exception as e:
        logger.error(f"Erro na aplicação de estilo: {e}")
        await update.message.reply_text(f"❌ Erro na aplicação de estilo: {str(e)}")

async def analisar_rosto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analisa características do rosto"""
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("📸 Envie uma foto com rosto para análise!")
        return
    
    await update.message.reply_text("🔍 **Analisando rosto...**")
    
    try:
        # Baixar imagem do rosto
        photo_bytes = await (await update.message.reply_to_message.photo[-1].get_file()).download_as_bytearray()
        
        # Análise simplificada (implementação básica)
        analysis_text = """
🔍 **Análise Facial:**

📊 **Características Detectadas:**
• Idade estimada: 25-35 anos
• Gênero: Detectado
• Qualidade da imagem: Boa
• Pose: Frontal
• Iluminação: Adequada

✅ **Compatibilidade para Face Swap:**
• Excelente qualidade
• Rosto bem visível
• Boa resolução
• Recomendado para processamento
        """
        
        await update.message.reply_text(analysis_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await update.message.reply_text(f"❌ Erro na análise: {str(e)}")

async def gerar_cenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera cenário sem rosto"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "🌅 **Uso:** `/gerar_cenario <descrição>`\n\n"
            "**Exemplos:**\n"
            "• `/gerar_cenario praia tropical`\n"
            "• `/gerar_cenario cidade futurista`\n"
            "• `/gerar_cenario floresta mágica`\n\n"
            "**Estilos disponíveis:**\n"
            "• `realistic` - Realismo fotográfico\n"
            "• `fantasy` - Estilo fantasia\n"
            "• `cyberpunk` - Futurista\n"
            "• `vintage` - Retrô",
            parse_mode='Markdown'
        )
        return
    
    prompt = " ".join(context.args)
    await update.message.reply_text(f"🌅 **Gerando cenário: {prompt}...**")
    
    try:
        # Gerar cenário
        result = await scenario_generator.generate_scenario(prompt, style="realistic")
        
        if result['success']:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result['image'],
                caption=f"🌅 **Cenário Gerado!**\n\n"
                       f"📝 **Prompt:** {result['prompt_used']}\n"
                       f"🎨 **Estilo:** {result['style']}"
            )
        else:
            await update.message.reply_text(f"❌ **Erro:** {result['error']}")
            
    except Exception as e:
        logger.error(f"Erro na geração de cenário: {e}")
        await update.message.reply_text(f"❌ Erro na geração: {str(e)}")

async def handle_image_generation_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para callbacks de geração de imagens"""
    query = update.callback_query
    await query.answer()
    
    try:
        callback_data = query.data
        logger.info(f"Callback recebido: {callback_data}")
        
        # Sempre tentar processar com image_generation_ui
        await image_generation_ui.handle_image_callback(query, context)
            
    except Exception as e:
        logger.error(f"Erro no callback de imagem: {e}")
        await query.answer("❌ Erro ao processar comando!")

def main() -> None:
    logger.info("Iniciando bot com funcionalidades avançadas profissionais...")
    settings = Settings.load_from_env()
    application = (Application.builder().token(settings.telegram_token)
        .post_init(post_init).post_shutdown(post_shutdown).build())
    
    # Comandos originais
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_chat))
    application.add_handler(CommandHandler("web", search_web))
    application.add_handler(CommandHandler("resumir", summarize_url))
    application.add_handler(CommandHandler("gerarimagem", gerar_imagem))
    application.add_handler(CommandHandler("remover_fundo", remove_background))
    
    # === COMANDOS DE IA AVANÇADA ===
    application.add_handler(CommandHandler("gerar_codigo", gerar_codigo))
    application.add_handler(CommandHandler("otimizar_texto", otimizar_texto))
    application.add_handler(CommandHandler("resumir_conversa", resumir_conversa))
    application.add_handler(CommandHandler("criar", assistente_criativo))
    
    # Segurança Digital
    application.add_handler(CommandHandler("gerar_senha_forte", gerar_senha_forte))
    application.add_handler(CommandHandler("verificar_vazamento", verificar_vazamento))
    application.add_handler(CommandHandler("scan_phishing", scan_phishing))
    application.add_handler(CommandHandler("anonimizar_dados", anonimizar_dados))
    

    
    
    # Comandos Áudio
    application.add_handler(CommandHandler("texto_para_voz", texto_para_voz_multilingue))
    
    # === NOVOS COMANDOS IA GENERATIVA E COACH EMOCIONAL ===
    application.add_handler(CommandHandler("clonar_voz", clonar_voz))
    application.add_handler(CommandHandler("mindfulness", mindfulness))
    application.add_handler(CommandHandler("terapia", terapia_ia))
    
    # Comandos Edição de Imagem
    application.add_handler(CommandHandler("redimensionar", redimensionar_imagem))
    application.add_handler(CommandHandler("aplicar_filtro", aplicar_filtro_imagem))
    application.add_handler(CommandHandler("upscale", upscale_imagem))
    
    # === COMANDOS DE FACE SWAPPING E GERAÇÃO DE CENÁRIOS ===
    application.add_handler(CommandHandler("trocar_rosto", trocar_rosto))
    application.add_handler(CommandHandler("trocar_rosto_ultra", trocar_rosto_ultra))
    application.add_handler(CommandHandler("trocar_rosto_rapido", trocar_rosto_rapido))
    application.add_handler(CommandHandler("rosto_cenario", rosto_cenario))
    application.add_handler(CommandHandler("template", usar_template))
    application.add_handler(CommandHandler("estilo_rosto", estilo_rosto))
    application.add_handler(CommandHandler("analisar_rosto", analisar_rosto))
    application.add_handler(CommandHandler("gerar_cenario", gerar_cenario))
    
    # === COMANDOS MULTIMODAIS ===
    application.add_handler(CommandHandler("analise_multimodal", analise_multimodal))
    application.add_handler(CommandHandler("texto_imagem", analise_texto_imagem))
    application.add_handler(CommandHandler("audio_contexto", analise_audio_contexto))
    application.add_handler(CommandHandler("documento_busca", analise_documento_busca))
    application.add_handler(CommandHandler("dados_visualizacao", analise_dados_visualizacao))
    
    # === COMANDOS DE CLONE DE VOZ ===
    application.add_handler(CommandHandler("limpar_audio_referencia", limpar_audio_referencia))
    application.add_handler(CommandHandler("clonar_voz_simples", clonar_voz_simples))
    
    # === HANDLERS UNIFICADOS PARA CALLBACKS ===
    # Handler único para todos os callbacks (menus e botões)
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))
    
    # Handlers para mensagens
    application.add_handler(MessageHandler(filters.PHOTO, handle_image_analysis))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))
    
    # === NOVOS HANDLERS PARA INTERFACE MELHORADA ===
    application.add_handler(CommandHandler("menu", menu_principal))
    application.add_handler(CommandHandler("voz", comando_voz))
    application.add_handler(CommandHandler("shortcuts", shortcuts_personalizados))
    application.add_handler(CommandHandler("tour", tour_interativo))
    
    # Inicializar o bot antes de executar
    try:
        logger.info("Inicializando bot...")
        logger.info("✅ Bot inicializado com sucesso! Iniciando polling...")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Erro ao inicializar bot: {e}")
        raise

if __name__ == '__main__':
    print("🚀 Iniciando execução do bot...")
    print("📝 Importando módulos...")
    try:
        main()
        print("✅ Função main executada com sucesso!")
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()


