#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para baixar checkpoints do OpenVoice
"""

import urllib.request
import os
import zipfile

def download_checkpoints():
    """Baixa os checkpoints do OpenVoice"""
    print("📥 Baixando checkpoints do OpenVoice...")
    
    # URLs dos checkpoints
    urls = {
        'v1': 'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip',
        'v2': 'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip'
    }
    
    try:
        # Remover arquivo corrompido se existir
        if os.path.exists('checkpoints_1226.zip'):
            print("🗑️  Removendo arquivo corrompido...")
            os.remove('checkpoints_1226.zip')
        
        # Baixar V1 (mais estável)
        print("📦 Baixando OpenVoice V1...")
        print(f"🔗 URL: {urls['v1']}")
        
        # Baixar com barra de progresso
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = (downloaded * 100) / total_size
                print(f"\r📥 Progresso: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        urllib.request.urlretrieve(
            urls['v1'], 
            'checkpoints_1226.zip',
            show_progress
        )
        
        print("\n✅ Download concluído!")
        
        # Verificar se é um arquivo ZIP válido
        print("🔍 Verificando arquivo...")
        try:
            with zipfile.ZipFile('checkpoints_1226.zip', 'r') as zip_ref:
                file_list = zip_ref.namelist()
                print(f"📋 Arquivos no ZIP: {len(file_list)}")
                print("📁 Primeiros arquivos:")
                for file in file_list[:5]:
                    print(f"   - {file}")
                
                if len(file_list) > 5:
                    print(f"   ... e mais {len(file_list) - 5} arquivos")
                
                print("\n✅ Arquivo ZIP válido!")
                return True
                
        except zipfile.BadZipFile:
            print("❌ Arquivo não é um ZIP válido!")
            return False
            
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        return False

def main():
    """Função principal"""
    print("🎭 Download de Checkpoints - OpenVoice MIT/MyShell")
    print("=" * 60)
    
    if download_checkpoints():
        print("\n🎉 **Download concluído com sucesso!** 🎉")
        print("\n🔧 Agora execute:")
        print("   python extract_checkpoints.py")
        print("\n🧪 Depois teste com:")
        print("   python teste_openvoice_final.py")
    else:
        print("\n❌ **Download falhou!** ❌")
        print("\n💡 Tente novamente ou use o link manual:")
        print("   https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip")

if __name__ == "__main__":
    main()
