# 🎭 SISTEMA DE FACE SWAPPING E GERAÇÃO DE CENÁRIOS

## 📋 **Visão Geral**

O sistema aprimorado de geração de imagens inclui funcionalidades avançadas de face swapping e geração de cenários usando tecnologias de ponta:

- **🔄 Face Swapping**: Troca de rostos entre imagens usando InsightFace
- **🎭 Rosto + Cenário**: Colocação de rostos em cenários gerados com IA
- **🌅 Templates**: Cenários pré-definidos para uso rápido
- **🎨 Estilos Artísticos**: Aplicação de estilos visuais aos rostos

## 🚀 **Instalação**

### **1. Instalar Dependências**

```bash
pip install -r requirements.txt
```

### **2. Configurar Modelos**

```bash
# Criar diretório para modelos
mkdir -p models/face_swap

# Baixar modelos InsightFace (automático na primeira execução)
python -c "import insightface; insightface.app.FaceAnalysis(name='buffalo_l')"
```

### **3. Configurar Variáveis de Ambiente**

Adicione ao arquivo `.env`:

```env
# APIs existentes
TELEGRAM_TOKEN=seu_token_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
HUGGINGFACE_API_KEY=sua_chave_huggingface_aqui

# Configurações de Face Swapping
FACE_SWAP_MODEL_PATH=models/face_swap
MAX_FACE_SWAP_SIZE=1024
FACE_ANALYSIS_ENABLED=true
```

## 🎯 **Comandos Disponíveis**

### **🔄 Face Swapping**

#### **Troca Básica de Rostos**
```
/trocar_rosto
```
**Como usar:**
1. Envie a primeira imagem (rosto fonte)
2. Responda com `/trocar_rosto`
3. Envie a segunda imagem (rosto destino)
4. Receba o resultado

#### **Qualidade Ultra**
```
/trocar_rosto_ultra
```
**Características:**
- Processamento mais lento (2-3 minutos)
- Qualidade máxima de face swap
- Blending perfeito entre rostos
- Detalhes preservados

#### **Processamento Rápido**
```
/trocar_rosto_rapido
```
**Características:**
- Processamento rápido (30-60 segundos)
- Qualidade boa
- Ideal para testes
- Menos recursos utilizados

### **🎭 Rosto + Cenário**

#### **Cenário Personalizado**
```
/rosto_cenario <descrição do cenário>
```

**Exemplos:**
- `/rosto_cenario praia tropical com coqueiros`
- `/rosto_cenario escritório moderno com vista da cidade`
- `/rosto_cenario floresta mágica com fadas`
- `/rosto_cenario restaurante elegante à noite`

**Como usar:**
1. Envie uma foto com rosto
2. Use o comando com descrição do cenário
3. Receba resultado com seu rosto no cenário

#### **Templates Pré-definidos**
```
/template <nome>
```

**Templates disponíveis:**
- `praia` - Praia tropical com coqueiros
- `escritorio` - Escritório moderno
- `floresta` - Floresta mágica
- `restaurante` - Restaurante elegante
- `espaço` - Espaço sideral
- `montanha` - Paisagem de montanha
- `cidade` - Vista aérea da cidade
- `castelo` - Castelo medieval
- `laboratorio` - Laboratório científico
- `biblioteca` - Biblioteca antiga

### **🎨 Estilos Artísticos**

```
/estilo_rosto <estilo>
```

**Estilos disponíveis:**
- `anime` - Estilo anime/mangá
- `realista` - Realismo fotográfico
- `pintura` - Estilo pintura clássica
- `cartoon` - Desenho animado
- `cyberpunk` - Estilo futurista
- `vintage` - Estilo retrô

### **🔍 Análise Facial**

```
/analisar_rosto
```

**Funcionalidades:**
- Detecção de características faciais
- Análise de qualidade da imagem
- Compatibilidade para face swap
- Estimativa de idade e gênero

### **🌅 Geração de Cenários**

```
/gerar_cenario <descrição>
```

**Exemplos:**
- `/gerar_cenario praia tropical`
- `/gerar_cenario cidade futurista`
- `/gerar_cenario floresta mágica`

## 🎨 **Interface de Botões**

### **Menu Principal**
- **🎨 Face Swapping** - Acesso direto às funcionalidades

### **Menu de Face Swapping**
- **🔄 Trocar Rostos** - Troca básica
- **🎯 Qualidade Ultra** - Processamento de alta qualidade
- **⚡ Processamento Rápido** - Processamento rápido
- **📊 Análise de Qualidade** - Avaliação de resultados

### **Menu de Rosto + Cenário**
- **🌅 Cenário Personalizado** - Descrição livre
- **🎨 Estilo Realista** - Realismo fotográfico
- **✨ Estilo Fantasia** - Estilo mágico
- **🚀 Estilo Cyberpunk** - Futurista
- **📸 Estilo Vintage** - Retrô

### **Menu de Templates**
- **🏖️ Praia** - Cenário tropical
- **🏢 Escritório** - Ambiente corporativo
- **🌲 Floresta** - Natureza mágica
- **🍽️ Restaurante** - Ambiente elegante
- **🌌 Espaço** - Cosmos
- **⛰️ Montanha** - Paisagem natural
- **🏙️ Cidade** - Urbano
- **🏰 Castelo** - Medieval
- **🔬 Laboratório** - Científico
- **📚 Biblioteca** - Acadêmico

## 🔧 **Configurações Avançadas**

### **Qualidade de Processamento**

```python
# Configurações no face_swapper_advanced.py
quality_settings = {
    "fast": {
        "blend_factor": 0.6,
        "enhance": False,
        "timeout": 30
    },
    "high": {
        "blend_factor": 0.8,
        "enhance": True,
        "timeout": 60
    },
    "ultra": {
        "blend_factor": 0.9,
        "enhance": True,
        "timeout": 180
    }
}
```

### **Modelos de IA**

```python
# Modelos disponíveis
models = {
    'realistic': 'stabilityai/stable-diffusion-xl-base-1.0',
    'artistic': 'runwayml/stable-diffusion-v1.5',
    'fantasy': 'stabilityai/stable-diffusion-xl-base-1.0',
    'cyberpunk': 'stabilityai/stable-diffusion-xl-base-1.0',
    'vintage': 'stabilityai/stable-diffusion-xl-base-1.0'
}
```

## 📊 **Métricas de Qualidade**

### **Score de Qualidade**
- **0.9-1.0**: Excelente
- **0.8-0.9**: Muito bom
- **0.7-0.8**: Bom
- **0.6-0.7**: Regular
- **<0.6**: Baixo

### **Fatores de Qualidade**
- Detecção de rostos
- Alinhamento facial
- Iluminação
- Resolução da imagem
- Pose do rosto

## 🚨 **Solução de Problemas**

### **Erro: "Nenhum rosto detectado"**
**Soluções:**
- Use fotos com boa iluminação
- Certifique-se de que o rosto está bem visível
- Evite ângulos muito extremos
- Use resolução mínima de 512x512 pixels

### **Erro: "Modelo não encontrado"**
**Soluções:**
```bash
# Reinstalar modelos
python -c "import insightface; insightface.app.FaceAnalysis(name='buffalo_l')"
```

### **Erro: "Timeout na execução"**
**Soluções:**
- Use `/trocar_rosto_rapido` para processamento mais rápido
- Reduza o tamanho das imagens
- Verifique a conexão com a internet

### **Erro: "API não disponível"**
**Soluções:**
- Verifique se a chave Hugging Face está configurada
- Aguarde alguns minutos e tente novamente
- Use templates locais em vez de geração online

## 🔒 **Segurança e Privacidade**

### **Processamento Local**
- Face swapping é processado localmente
- Imagens não são enviadas para servidores externos
- Modelos ficam na sua máquina

### **Dados Temporários**
- Imagens são armazenadas temporariamente durante processamento
- Dados são limpos automaticamente após uso
- Nenhum dado pessoal é mantido

## 📈 **Performance**

### **Tempos de Processamento**

| Qualidade | CPU | GPU | Qualidade |
|-----------|-----|-----|-----------|
| **Fast** | 30-60s | 10-20s | Boa |
| **High** | 60-120s | 20-40s | Muito boa |
| **Ultra** | 120-300s | 40-80s | Excelente |

### **Requisitos de Sistema**

**Mínimo:**
- RAM: 4GB
- CPU: Intel i5 ou equivalente
- Espaço: 2GB para modelos

**Recomendado:**
- RAM: 8GB+
- GPU: NVIDIA GTX 1060 ou superior
- CPU: Intel i7 ou equivalente
- Espaço: 5GB para modelos

## 🎯 **Exemplos de Uso**

### **Exemplo 1: Troca de Rostos**
```
1. Envie foto do rosto A
2. Responda: /trocar_rosto
3. Envie foto do rosto B
4. Receba resultado com rosto A no corpo B
```

### **Exemplo 2: Rosto em Cenário**
```
1. Envie foto com rosto
2. Use: /rosto_cenario praia tropical com coqueiros
3. Receba resultado com seu rosto na praia
```

### **Exemplo 3: Template Rápido**
```
1. Envie foto com rosto
2. Use: /template escritorio
3. Receba resultado com seu rosto no escritório
```

## 🔮 **Próximas Funcionalidades**

### **Em Desenvolvimento**
- [ ] Face swapping em tempo real
- [ ] Suporte a vídeos
- [ ] Múltiplos rostos simultâneos
- [ ] Estilos artísticos avançados
- [ ] Integração com câmera do Telegram

### **Planejado**
- [ ] API REST para integração
- [ ] Dashboard web
- [ ] Histórico de processamentos
- [ ] Compartilhamento de resultados
- [ ] Colaboração em tempo real

---

## 📞 **Suporte**

Para problemas ou dúvidas:
- **📖 Documentação**: Este arquivo
- **🐛 Issues**: GitHub Issues
- **💬 Discussões**: GitHub Discussions
- **📧 Email**: [seu-email@exemplo.com]

---

**🎭 Sistema de Face Swapping e Geração de Cenários**

*Desenvolvido com ❤️ para manipulação facial avançada*

