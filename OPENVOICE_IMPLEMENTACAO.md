# 🎭 OpenVoice - Clonagem de Voz Instantânea MIT/MyShell

## 📋 **Visão Geral**

O **OpenVoice** é uma solução de clonagem de voz de código aberto desenvolvida pelo **MIT** e **MyShell**, oferecendo clonagem instantânea com controle granular de estilo.

### ✨ **Características Principais**

- **🎯 Clonagem de Tom de Cor Preciso** - Clone exato da voz de referência
- **🎨 Controle Flexível de Estilo** - Emoção, sotaque, ritmo, pausas e entonação
- **🌍 Zero-shot Cross-lingual** - Funciona em qualquer idioma sem treinamento
- **📜 Licença MIT** - Gratuito para uso comercial e pesquisa

## 🚀 **Instalação**

### **1. Dependências Python**

```bash
pip install torch torchaudio transformers accelerate
```

### **2. Script de Instalação Automática**

```bash
python install_openvoice_real.py
```

### **3. Download Manual dos Modelos**

```bash
# Usar o script automático (recomendado)
python install_openvoice_real.py

# Ou manualmente:
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice
python -m openvoice.download_models
cp -r checkpoints/* ../checkpoints/
```

## 🔧 **Configuração**

### **Estrutura de Diretórios**

```
checkpoints/
├── base_speakers/
│   ├── ses_zh-csmsc.pth
│   └── config.json
└── tone_color_converter/
    ├── model.pth
    └── config.json
```

### **Variáveis de Ambiente**

```env
# OpenVoice (opcional - usa modelos locais)
OPENVOICE_MODEL_PATH=checkpoints
```

## 📚 **Uso Básico**

### **1. Importar o Módulo**

```python
from openvoice_cloner import OpenVoiceCloner

# Criar instância
cloner = OpenVoiceCloner()
```

### **2. Clonagem Simples**

```python
# Clonar voz
audio_result = await cloner.clone_voice_instant(
    reference_audio_bytes=audio_bytes,
    text="Olá, como você está?",
    language="pt"
)
```

### **3. Clonagem com Estilo Personalizado**

```python
# Configurações de estilo
style_settings = {
    "language": "pt",
    "speed": 1.2,           # 20% mais rápido
    "emotion": "happy",      # Emoção feliz
    "accent": "brazilian",   # Sotaque brasileiro
    "pitch": 1.1,           # Pitch ligeiramente mais alto
    "energy": 1.3           # Mais energia na voz
}

# Clonar com estilo
audio_result = await cloner.clone_voice_instant(
    reference_audio_bytes=audio_bytes,
    text="Que dia maravilhoso!",
    style_settings=style_settings
)
```

## 🎯 **Integração com Sistema Principal**

### **Hierarquia de Prioridades**

1. **🥇 OpenVoice** - Clonagem instantânea local
2. **🥈 Fish Audio** - Clonagem real com API
3. **🥉 Coqui TTS** - Fallback otimizado
4. **🔄 gTTS** - Fallback de emergência

### **Uso no VoiceCloner**

```python
from voice_cloner import VoiceCloner

# O OpenVoice é automaticamente detectado e usado
voice_cloner = VoiceCloner(
    fish_audio_api_key="sua_chave_fish_audio"
)

# Clonagem automática com OpenVoice prioritário
result = await voice_cloner.clone_voice_advanced(
    reference_audio_bytes=audio_bytes,
    text="Texto para clonar"
)
```

## 🌍 **Idiomas Suportados**

- **🇧🇷 Português (pt)** - Nativo
- **🇺🇸 Inglês (en)** - Nativo
- **🇪🇸 Espanhol (es)** - Nativo
- **🇫🇷 Francês (fr)** - Nativo
- **🇨🇳 Chinês (zh)** - Nativo
- **🇯🇵 Japonês (ja)** - Nativo
- **🇰🇷 Coreano (ko)** - Nativo

## 🎨 **Controles de Estilo**

### **Parâmetros Disponíveis**

| Parâmetro | Descrição | Valores | Padrão |
|-----------|-----------|---------|---------|
| `speed` | Velocidade de fala | 0.5 - 2.0 | 1.0 |
| `emotion` | Emoção da voz | neutral, happy, sad, angry, excited, calm | neutral |
| `accent` | Sotaque | neutral, brazilian, american, british | neutral |
| `pitch` | Altura da voz | 0.5 - 2.0 | 1.0 |
| `energy` | Energia/entusiasmo | 0.5 - 2.0 | 1.0 |
| `pause_duration` | Duração das pausas | 0.0 - 1.0 | 0.1 |
| `intonation` | Entonação | 0.5 - 2.0 | 1.0 |

### **Exemplos de Configuração**

```python
# Voz feliz e energética
happy_style = {
    "emotion": "happy",
    "energy": 1.5,
    "speed": 1.2
}

# Voz calma e lenta
calm_style = {
    "emotion": "calm",
    "speed": 0.8,
    "energy": 0.7
}

# Voz masculina brasileira
brazilian_style = {
    "accent": "brazilian",
    "pitch": 0.8,
    "emotion": "neutral"
}
```

## 🔍 **Análise de Voz**

### **Características Extraídas**

```python
# Analisar características da voz
analysis = await cloner.analyze_voice_characteristics(audio_bytes)

# Resultado inclui:
{
    "tone_color_features": "shape_info",
    "voice_quality": "high",
    "cloning_compatibility": "excellent",
    "recommended_settings": {
        "speed": 1.0,
        "emotion": "neutral",
        "accent": "preserve_original"
    }
}
```

## 🚨 **Solução de Problemas**

### **Erro: "OpenVoice não disponível"**

```bash
# Solução 1: Instalar OpenVoice real
python install_openvoice_real.py

# Solução 2: Verificar modelos
ls checkpoints/base_speakers/
ls checkpoints/tone_color_converter/
```

### **Erro: "Modelos não encontrados"**

```bash
# Solução automática (recomendada)
python install_openvoice_real.py

# Ou baixar modelos manualmente
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice
python -m openvoice.download_models
cp -r checkpoints/* ../checkpoints/
```

### **Erro: "CUDA não disponível"**

```python
# OpenVoice funciona em CPU, mas é mais lento
# Verificar se torch está instalado corretamente
import torch
print(f"CUDA disponível: {torch.cuda.is_available()}")
```

## 📊 **Performance**

### **Tempos de Processamento**

| Hardware | Tempo de Clonagem | Qualidade |
|----------|-------------------|-----------|
| **GPU (CUDA)** | 2-5 segundos | ⭐⭐⭐⭐⭐ |
| **CPU (Intel i7)** | 10-20 segundos | ⭐⭐⭐⭐ |
| **CPU (Intel i5)** | 20-40 segundos | ⭐⭐⭐ |

### **Otimizações**

```python
# Usar cache para vozes frequentes
cached_result = await voice_cloner._clone_with_cached_model(
    cached_model, text
)

# Processamento em background
result = await asyncio.create_task(
    cloner.clone_voice_instant(audio_bytes, text)
)
```

## 🔒 **Segurança e Privacidade**

- **✅ Processamento Local** - Áudio não é enviado para servidores externos
- **✅ Modelos Locais** - Todos os modelos ficam na sua máquina
- **✅ Licença MIT** - Código aberto e auditável
- **✅ Sem Coleta de Dados** - Não há telemetria ou tracking

## 📈 **Roadmap**

### **Versão Atual (v1.0)**
- ✅ Clonagem básica de voz
- ✅ Controle de estilo
- ✅ Suporte multilíngue
- ✅ Integração com sistema principal

### **Próximas Versões**
- 🔄 Clonagem em tempo real
- 🔄 Ajuste automático de qualidade
- 🔄 Suporte a mais idiomas
- 🔄 Interface gráfica

## 🤝 **Contribuições**

### **Como Contribuir**

1. **Fork** o repositório
2. **Clone** localmente
3. **Crie** uma branch para sua feature
4. **Commit** suas mudanças
5. **Push** para a branch
6. **Abra** um Pull Request

### **Áreas de Melhoria**

- 📱 Interface mobile
- 🎵 Suporte a mais formatos de áudio
- 🌐 API REST para integração
- 📊 Métricas de qualidade
- 🔧 Configuração avançada

## 📞 **Suporte**

### **Canais de Ajuda**

- **📖 Documentação**: Este arquivo
- **🐛 Issues**: GitHub Issues
- **💬 Discussões**: GitHub Discussions
- **📧 Email**: [seu-email@exemplo.com]

### **Recursos Adicionais**

- **🔗 Repositório Original**: [OpenVoice GitHub](https://github.com/myshell-ai/OpenVoice)
- **📄 Paper**: [arXiv:2312.01479](https://arxiv.org/abs/2312.01479)
- **🌐 Website**: [research.myshell.ai/open-voice](https://research.myshell.ai/open-voice)
- **📦 Instalação Automática**: `python install_openvoice_real.py`

---

**🎭 OpenVoice - Clonagem de Voz Instantânea MIT/MyShell**

*Desenvolvido com ❤️ pelo MIT e MyShell*
