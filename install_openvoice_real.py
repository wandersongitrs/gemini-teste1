#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Instalação OpenVoice Real
Instala o OpenVoice oficial do repositório MIT/MyShell
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_openvoice_real():
    """Instala o OpenVoice real do repositório oficial"""
    print("🎭 Instalando OpenVoice Real - MIT/MyShell...")
    
    try:
        # 1. Verificar se git está disponível
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git não encontrado. Instale o Git primeiro.")
            return False
        
        # 2. Clonar repositório OpenVoice
        print("📥 Clonando repositório OpenVoice...")
        if Path("OpenVoice").exists():
            print("🗑️  Removendo instalação anterior...")
            shutil.rmtree("OpenVoice")
        
        subprocess.check_call([
            "git", "clone", "https://github.com/myshell-ai/OpenVoice.git"
        ])
        
        # 3. Entrar no diretório e instalar
        os.chdir("OpenVoice")
        print("📦 Instalando OpenVoice...")
        
        # 4. Instalar dependências Python
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "torch", "torchaudio", "transformers", "accelerate"
        ])
        
        # 5. Instalar OpenVoice em modo desenvolvimento
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-e", "."
        ])
        
        # 6. Baixar modelos
        print("📥 Baixando modelos...")
        subprocess.check_call([
            sys.executable, "-m", "openvoice.download_models"
        ])
        
        # 7. Voltar ao diretório original
        os.chdir("..")
        
        # 8. Copiar modelos para o projeto
        print("📁 Copiando modelos para o projeto...")
        checkpoints_dir = Path("checkpoints")
        if checkpoints_dir.exists():
            shutil.rmtree(checkpoints_dir)
        
        shutil.copytree("OpenVoice/checkpoints", "checkpoints")
        
        print("✅ OpenVoice Real instalado com sucesso!")
        print("📁 Diretório de checkpoints: checkpoints/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na instalação: {e}")
        return False

def verify_installation():
    """Verifica se a instalação foi bem-sucedida"""
    try:
        # Verificar se os modelos estão disponíveis
        checkpoints_dir = Path("checkpoints")
        if not checkpoints_dir.exists():
            print("❌ Diretório de checkpoints não encontrado")
            return False
        
        base_speakers_dir = checkpoints_dir / "base_speakers"
        tone_converter_dir = checkpoints_dir / "tone_color_converter"
        
        if not base_speakers_dir.exists() or not tone_converter_dir.exists():
            print("❌ Estrutura de modelos incompleta")
            return False
        
        # Verificar se os arquivos principais existem
        required_files = [
            base_speakers_dir / "ses_zh-csmsc.pth",
            base_speakers_dir / "config.json",
            tone_converter_dir / "model.pth",
            tone_converter_dir / "config.json"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                print(f"❌ Arquivo não encontrado: {file_path}")
                return False
        
        print("✅ Modelos OpenVoice verificados com sucesso!")
        
        # Testar importação
        try:
            from openvoice_cloner import OpenVoiceCloner
            print("✅ Módulo OpenVoice importado com sucesso!")
            
            # Testar criação da instância
            cloner = OpenVoiceCloner()
            print(f"✅ OpenVoice Cloner criado: {cloner.available}")
            
            return True
            
        except ImportError as e:
            print(f"❌ Erro ao importar OpenVoice: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro ao criar OpenVoice Cloner: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def cleanup():
    """Limpa arquivos temporários"""
    try:
        if Path("OpenVoice").exists():
            print("🧹 Limpando arquivos temporários...")
            shutil.rmtree("OpenVoice")
    except Exception as e:
        print(f"⚠️  Erro ao limpar: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando instalação do OpenVoice Real...")
    
    try:
        if install_openvoice_real():
            print("\n🔍 Verificando instalação...")
            if verify_installation():
                print("\n🎉 OpenVoice Real instalado e configurado com sucesso!")
                print("📖 Para usar, importe: from openvoice_cloner import OpenVoiceCloner")
            else:
                print("\n⚠️  Instalação concluída, mas verificação falhou")
        else:
            print("\n❌ Falha na instalação do OpenVoice Real")
            sys.exit(1)
    finally:
        cleanup()
