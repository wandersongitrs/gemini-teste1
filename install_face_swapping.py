#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Instalação para Sistema de Face Swapping
Instala dependências e configura modelos automaticamente
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Executa comando e trata erros"""
    try:
        logger.info(f"🔄 {description}...")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} concluído!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro em {description}: {e}")
        logger.error(f"Saída de erro: {e.stderr}")
        return False

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ é necessário!")
        return False
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def install_dependencies():
    """Instala dependências do requirements.txt"""
    if not os.path.exists("requirements.txt"):
        logger.error("❌ Arquivo requirements.txt não encontrado!")
        return False
    
    return run_command("pip install -r requirements.txt", "Instalando dependências")

def create_directories():
    """Cria diretórios necessários"""
    directories = [
        "models",
        "models/face_swap",
        "temp",
        "cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Diretório criado: {directory}")
    
    return True

def download_models():
    """Baixa modelos necessários"""
    try:
        logger.info("🔄 Baixando modelos InsightFace...")
        
        # Importar insightface para baixar modelos
        import insightface
        
        # Inicializar FaceAnalysis para baixar modelo buffalo_l
        app = insightface.app.FaceAnalysis(name='buffalo_l')
        app.prepare(ctx_id=0, det_size=(640, 640))
        
        logger.info("✅ Modelos InsightFace baixados!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao baixar modelos: {e}")
        return False

def check_gpu_support():
    """Verifica suporte a GPU"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"🚀 GPU detectada: {gpu_name} ({gpu_count} dispositivo(s))")
            return True
        else:
            logger.info("💻 Usando CPU (GPU não detectada)")
            return False
    except ImportError:
        logger.info("💻 PyTorch não instalado, usando CPU")
        return False

def test_installation():
    """Testa se a instalação foi bem-sucedida"""
    try:
        logger.info("🧪 Testando instalação...")
        
        # Testar imports principais
        import cv2
        import numpy as np
        import insightface
        import onnxruntime as ort
        from PIL import Image
        
        logger.info("✅ Todos os imports funcionando!")
        
        # Testar inicialização do face swapper
        from face_swapper_advanced import face_swapper
        logger.info("✅ Sistema de face swapping carregado!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False

def create_env_example():
    """Cria arquivo .env.example com configurações"""
    env_content = """# Configurações do Bot Telegram
TELEGRAM_TOKEN=seu_token_telegram_aqui

# APIs de IA
GEMINI_API_KEY=sua_chave_gemini_aqui
HUGGINGFACE_API_KEY=sua_chave_huggingface_aqui

# Configurações de Face Swapping
FACE_SWAP_MODEL_PATH=models/face_swap
MAX_FACE_SWAP_SIZE=1024
FACE_ANALYSIS_ENABLED=true

# Configurações de Performance
USE_GPU=true
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT=300

# Configurações de Cache
CACHE_ENABLED=true
CACHE_SIZE_MB=500
CACHE_TTL_HOURS=24
"""
    
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    logger.info("📝 Arquivo .env.example criado!")

def main():
    """Função principal de instalação"""
    logger.info("🎭 Iniciando instalação do Sistema de Face Swapping...")
    
    # Verificar versão do Python
    if not check_python_version():
        sys.exit(1)
    
    # Criar diretórios
    if not create_directories():
        logger.error("❌ Falha ao criar diretórios")
        sys.exit(1)
    
    # Instalar dependências
    if not install_dependencies():
        logger.error("❌ Falha na instalação de dependências")
        sys.exit(1)
    
    # Verificar suporte a GPU
    check_gpu_support()
    
    # Baixar modelos
    if not download_models():
        logger.warning("⚠️ Falha ao baixar modelos, mas instalação pode continuar")
    
    # Testar instalação
    if not test_installation():
        logger.error("❌ Falha no teste de instalação")
        sys.exit(1)
    
    # Criar arquivo de exemplo
    create_env_example()
    
    logger.info("🎉 Instalação concluída com sucesso!")
    logger.info("📋 Próximos passos:")
    logger.info("1. Copie .env.example para .env")
    logger.info("2. Configure suas chaves de API no .env")
    logger.info("3. Execute: python bot.py")
    logger.info("4. Teste com: /trocar_rosto")

if __name__ == "__main__":
    main()

