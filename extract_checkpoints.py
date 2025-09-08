#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extrair checkpoints do OpenVoice
"""

import zipfile
import os
import shutil

def extract_checkpoints():
    """Extrai os checkpoints do OpenVoice"""
    print("🔧 Extraindo checkpoints do OpenVoice...")
    
    try:
        # Verificar se o arquivo existe
        if not os.path.exists('checkpoints_1226.zip'):
            print("❌ Arquivo checkpoints_1226.zip não encontrado!")
            return False
        
        # Remover diretório checkpoints se existir
        if os.path.exists('checkpoints'):
            print("🗑️  Removendo diretório checkpoints existente...")
            shutil.rmtree('checkpoints')
        
        # Extrair arquivo
        print("📦 Extraindo checkpoints...")
        with zipfile.ZipFile('checkpoints_1226.zip', 'r') as zip_ref:
            zip_ref.extractall('.')
        
        print("✅ Checkpoints extraídos com sucesso!")
        
        # Verificar estrutura
        if os.path.exists('checkpoints'):
            print("📁 Diretório checkpoints criado!")
            
            # Listar conteúdo
            print("\n📋 Conteúdo do diretório checkpoints:")
            for root, dirs, files in os.walk('checkpoints'):
                level = root.replace('checkpoints', '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # Mostrar apenas os primeiros 5 arquivos
                    print(f"{subindent}{file}")
                if len(files) > 5:
                    print(f"{subindent}... e mais {len(files) - 5} arquivos")
            
            return True
        else:
            print("❌ Diretório checkpoints não foi criado!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao extrair checkpoints: {e}")
        return False

if __name__ == "__main__":
    if extract_checkpoints():
        print("\n🎉 Checkpoints extraídos com sucesso!")
        print("📖 Agora você pode usar o OpenVoice no seu bot!")
    else:
        print("\n❌ Falha ao extrair checkpoints!")
