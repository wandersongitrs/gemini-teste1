# 🎭 SISTEMA DE FACE SWAPPING E GERAÇÃO DE CENÁRIOS

## 🚀 **Instalação Rápida**

### **1. Instalar Dependências**
```bash
python install_face_swapping.py
```

### **2. Configurar Variáveis de Ambiente**
```bash
cp .env.example .env
# Edite o .env com suas chaves de API
```

### **3. Executar o Bot**
```bash
python bot.py
```

## 🎯 **Comandos Principais**

### **🔄 Face Swapping**
- `/trocar_rosto` - Troca básica de rostos
- `/trocar_rosto_ultra` - Qualidade máxima
- `/trocar_rosto_rapido` - Processamento rápido

### **🎭 Rosto + Cenário**
- `/rosto_cenario <descrição>` - Cenário personalizado
- `/template <nome>` - Template pré-definido

### **🎨 Estilos**
- `/estilo_rosto <estilo>` - Aplicar estilo artístico
- `/analisar_rosto` - Análise facial

### **🌅 Cenários**
- `/gerar_cenario <descrição>` - Gerar cenário

## 🎨 **Interface de Botões**

Acesse através do botão **🎨 Face Swapping** no menu principal para uma interface completa com:

- **Menus organizados** por funcionalidade
- **Templates visuais** com previews
- **Configurações de qualidade** interativas
- **Instruções passo a passo** para cada função

## 📊 **Templates Disponíveis**

| Template | Descrição | Emoji |
|----------|-----------|-------|
| `praia` | Praia tropical com coqueiros | 🏖️ |
| `escritorio` | Escritório moderno | 🏢 |
| `floresta` | Floresta mágica | 🌲 |
| `restaurante` | Restaurante elegante | 🍽️ |
| `espaço` | Espaço sideral | 🌌 |
| `montanha` | Paisagem de montanha | ⛰️ |
| `cidade` | Vista aérea da cidade | 🏙️ |
| `castelo` | Castelo medieval | 🏰 |
| `laboratorio` | Laboratório científico | 🔬 |
| `biblioteca` | Biblioteca antiga | 📚 |

## 🔧 **Configurações Avançadas**

### **Qualidade de Processamento**

| Qualidade | Tempo | Recursos | Resultado |
|-----------|-------|----------|-----------|
| **Fast** | 30-60s | Baixo | Bom |
| **High** | 60-120s | Médio | Muito bom |
| **Ultra** | 120-300s | Alto | Excelente |

### **Estilos Artísticos**

| Estilo | Características | Uso |
|--------|-----------------|-----|
| `realistic` | Realismo fotográfico | Fotos profissionais |
| `fantasy` | Estilo mágico | Arte conceitual |
| `cyberpunk` | Futurista | Sci-fi |
| `vintage` | Retrô | Nostalgia |
| `artistic` | Pintura | Arte clássica |

## 🚨 **Solução de Problemas**

### **Erro: "Nenhum rosto detectado"**
- Use fotos com boa iluminação
- Certifique-se de que o rosto está bem visível
- Evite ângulos muito extremos
- Use resolução mínima de 512x512 pixels

### **Erro: "Modelo não encontrado"**
```bash
python -c "import insightface; insightface.app.FaceAnalysis(name='buffalo_l')"
```

### **Erro: "Timeout na execução"**
- Use `/trocar_rosto_rapido` para processamento mais rápido
- Reduza o tamanho das imagens
- Verifique a conexão com a internet

## 📈 **Performance**

### **Requisitos Mínimos**
- **RAM**: 4GB
- **CPU**: Intel i5 ou equivalente
- **Espaço**: 2GB para modelos

### **Requisitos Recomendados**
- **RAM**: 8GB+
- **GPU**: NVIDIA GTX 1060 ou superior
- **CPU**: Intel i7 ou equivalente
- **Espaço**: 5GB para modelos

## 🔒 **Segurança**

- **Processamento local**: Face swapping é processado na sua máquina
- **Dados temporários**: Imagens são limpas automaticamente
- **Privacidade**: Nenhum dado pessoal é mantido

## 📞 **Suporte**

Para problemas ou dúvidas:
- **📖 Documentação**: `FACE_SWAPPING_GUIDE.md`
- **🐛 Issues**: GitHub Issues
- **💬 Discussões**: GitHub Discussions

---

**🎭 Sistema de Face Swapping e Geração de Cenários**

*Desenvolvido com ❤️ para manipulação facial avançada*

