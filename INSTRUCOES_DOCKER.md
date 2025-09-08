# 🐳 Executando o Bot Gemini no Docker

## ✅ Status Atual
- ✅ Dockerfile configurado
- ✅ Imagem construída com sucesso
- ✅ Container executando
- ❌ Token do Telegram não configurado

## 🔧 Configuração Necessária

### 1. Obter Token do Telegram
1. Fale com @BotFather no Telegram
2. Use o comando `/newbot`
3. Siga as instruções para criar o bot
4. Copie o token fornecido

### 2. Configurar arquivo .env
```bash
TELEGRAM_TOKEN=SEU_TOKEN_REAL_AQUI
GEMINI_API_KEY=sua_chave_gemini_aqui
HUGGINGFACE_API_KEY=sua_chave_huggingface_aqui
TAVILY_API_KEY=sua_chave_tavily_aqui
REMOVEBG_API_KEY=sua_chave_removebg_aqui
GEMINI_MODEL_NAME=gemini-1.5-flash
```

## 🚀 Comandos Docker

### Construir imagem
```bash
docker build -t gemini-teste1 .
```

### Executar container
```bash
docker run -d --name gemini-teste1 gemini-teste1
```

### Ver logs
```bash
docker logs gemini-teste1
```

### Parar container
```bash
docker stop gemini-teste1
```

### Remover container
```bash
docker rm gemini-teste1
```

## 📝 Próximos Passos
1. Configure o arquivo .env com tokens reais
2. Reconstrua a imagem Docker
3. Execute o container novamente
4. Teste o bot no Telegram

## 🎯 Funcionalidades Disponíveis
- Chat com IA Gemini
- Processamento de imagens
- Verificação de vazamentos
- Tradução de idiomas
- Análise de documentos
- Geração de áudio
