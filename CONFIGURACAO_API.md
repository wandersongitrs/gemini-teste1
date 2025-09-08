# Configuração de APIs

## APIs Necessárias

### 1. Telegram Bot API
- **Token**: Obtido através do [@BotFather](https://t.me/botfather)
- **Variável**: `TELEGRAM_TOKEN`

### 2. Google Gemini API
- **Chave**: Obtida através do [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Variável**: `GEMINI_API_KEY`

### 3. Fish Audio API
- **Chave**: Obtida através do [Fish Audio](https://fish.audio/pt/app/api-keys/)
- **Variável**: `FISH_AUDIO_API_KEY`
- **Chave atual**: `97a90fde992b4c54b2b5961556afd1dc`

### 4. Hugging Face API
- **Token**: Obtido através do [Hugging Face](https://huggingface.co/settings/tokens)
- **Variável**: `HUGGINGFACE_API_KEY`

### 5. Tavily API
- **Chave**: Obtida através do [Tavily](https://tavily.com/)
- **Variável**: `TAVILY_API_KEY`

### 6. RemoveBG API
- **Chave**: Obtida através do [RemoveBG](https://www.remove.bg/api)
- **Variável**: `REMOVEBG_API_KEY`

## Configuração do Arquivo .env

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
# Configurações do Bot Telegram
TELEGRAM_TOKEN=seu_token_aqui

# Chaves de API
GEMINI_API_KEY=sua_chave_gemini_aqui
HUGGINGFACE_API_KEY=sua_chave_huggingface_aqui
TAVILY_API_KEY=sua_chave_tavily_aqui
REMOVEBG_API_KEY=sua_chave_removebg_aqui
FISH_AUDIO_API_KEY=97a90fde992b4c54b2b5961556afd1dc

# Configurações do Modelo
GEMINI_MODEL_NAME=gemini-1.5-flash
```

## Configuração do Fish Audio

### Vantagens da API Fish Audio:
- ✅ **Clonagem de voz de alta qualidade**
- ✅ **Sem limitações de plano gratuito**
- ✅ **Processamento rápido**
- ✅ **Suporte a múltiplos idiomas**
- ✅ **API estável e confiável**

### Endpoints utilizados:
- **TTS**: `https://api.fish.audio/v1/tts/{voice_id}`
- **Autenticação**: Bearer Token
- **Formato**: JSON

## Teste das APIs

Para testar se todas as APIs estão funcionando:

1. **Verifique o arquivo .env** com todas as chaves
2. **Execute o bot** e teste a funcionalidade de clonagem de voz
3. **Verifique os logs** para confirmar que todas as APIs estão respondendo

## Suporte

Em caso de problemas com as APIs:
- **Fish Audio**: [Documentação oficial](https://fish.audio/pt/app/api-keys/)
- **Google Gemini**: [Documentação oficial](https://ai.google.dev/)
- **Telegram**: [Documentação oficial](https://core.telegram.org/bots/api)
