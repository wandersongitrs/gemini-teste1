# Bot Telegram com Sistema de Contexto Avançado

Bot Telegram revolucionário que utiliza a API do Google Gemini com um **Sistema de Contexto Avançado** que permite ao bot "lembrar" de interações multimodais anteriores e usar esse contexto para enriquecer respostas futuras.

## 🧠 Sistema de Contexto Avançado

### ✨ Funcionalidades Revolucionárias
- **🧠 Memória Contextual Multimodal**: O bot lembra de imagens, áudios e vídeos analisados anteriormente
- **🎛️ Estados de Conversa Inteligentes**: Sistema de modos que adapta comportamento baseado no contexto
- **🎭 Personalização de Personalidade**: Usuários podem configurar diferentes personalidades (cientista, pirata, artista, etc.)
- **💾 Persistência Entre Sessões**: Contexto mantido mesmo após reinicializações
- **🔄 Integração Transparente**: Funciona automaticamente com todos os handlers existentes

### 🎯 Exemplo Prático
```
Usuário: [Envia imagem de uma floresta]
Bot: 🖼️ Imagem analisada! Descrição: Uma floresta densa com árvores altas...

Usuário: Crie uma história sobre isso
Bot: [Usando contexto da imagem] Era uma vez uma floresta mágica onde...
```

## ✨ Funcionalidades Principais

- 🤖 **Chat Inteligente** - Conversas avançadas com Gemini AI
- 🖼️ **Análise de Imagens** - Processamento multimodal com IA
- 🎵 **Clonagem de Voz** - Clone vozes usando OpenVoice
- 🔄 **Face Swapping** - Troca de rostos em imagens
- 🎨 **Geração de Imagens** - Criação de imagens com IA
- 📊 **Processamento Multimodal** - Análise completa de conteúdo
- 🛡️ **Segurança Avançada** - Rate limiting e validação robusta
- 📝 **Logging Completo** - Monitoramento e debugging

## 🚀 Configuração Inicial

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/gemini-teste1.git
cd gemini-teste1
```

### 2. Configure as variáveis de ambiente

1. Copie o arquivo de exemplo:
```bash
cp env.example .env
```

2. Edite o arquivo `.env` com suas chaves de API:
```bash
# Configurações do Bot Telegram
TELEGRAM_TOKEN=seu_token_telegram_aqui

# Chaves de API
GEMINI_API_KEY=sua_chave_gemini_aqui
HUGGINGFACE_API_KEY=sua_chave_huggingface_aqui
TAVILY_API_KEY=sua_chave_tavily_aqui
REMOVEBG_API_KEY=sua_chave_removebg_aqui
FISH_AUDIO_API_KEY=sua_chave_fish_audio_aqui

# Configurações do Modelo
GEMINI_MODEL_NAME=gemini-1.5-flash
```

### 3. Obtenha suas chaves de API

- **Telegram Token**: Crie um bot em [@BotFather](https://t.me/BotFather)
- **Gemini API**: Obtenha em [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Hugging Face**: Crie um token em [Hugging Face Settings](https://huggingface.co/settings/tokens)
- **Tavily**: Registre-se em [Tavily](https://tavily.com/)
- **Remove.bg**: Obtenha API key em [Remove.bg API](https://www.remove.bg/api)
- **Fish Audio**: Registre-se em [Fish Audio](https://fish.audio/)

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Execute o bot

**Sistema de Contexto Avançado (NOVO - Recomendado):**
```bash
python context_aware_bot.py
```

**Versão Melhorada:**
```bash
python bot_improved.py
```

**Versão Original:**
```bash
python bot.py
```

> 💡 **Recomendação:** Use `context_aware_bot.py` para o sistema de contexto avançado com memória multimodal e personalidades!

### 6. Teste o sistema
```bash
python test_context_system.py
```

## 🐳 Execução com Docker

### Construir e executar
```bash
# Construir a imagem
docker build -t geminiteste .

# Executar o container
docker run -d --name geminiteste --env-file .env geminiteste
```

### Comandos úteis
- **Parar**: `docker stop geminiteste`
- **Iniciar**: `docker start geminiteste`
- **Ver logs**: `docker logs geminiteste`
- **Remover**: `docker rm geminiteste`

## 🔒 Segurança e Tratamento de Erros

### Proteção de Tokens
⚠️ **IMPORTANTE**: Nunca compartilhe seu arquivo `.env` ou commite-o no Git. Ele contém informações sensíveis como tokens de API.

O arquivo `.env` está incluído no `.gitignore` para proteger suas credenciais.

### Melhorias de Segurança Implementadas

- ✅ **Configuração Segura**: Chaves de API carregadas de variáveis de ambiente
- ✅ **Validação de Entrada**: Sanitização e validação de todos os inputs
- ✅ **Rate Limiting**: Limite de 10 requisições por minuto por usuário
- ✅ **Tratamento de Erros**: Sistema robusto com retry automático
- ✅ **Logging Seguro**: Logs detalhados sem exposição de dados sensíveis
- ✅ **Validação de Arquivos**: Verificação de segurança para imagens e áudios

### Sistema de Tratamento de Erros

O bot implementa tratamento robusto de erros com:
- Retry automático com backoff exponencial
- Mensagens amigáveis ao usuário
- Logging detalhado para debugging
- Fallbacks para funcionalidades opcionais

## 📁 Estrutura do Projeto

```
gemini-teste1/
├── context_aware_bot.py           # Bot com sistema de contexto avançado (NOVO)
├── advanced_context_system.py    # Sistema de contexto multimodal (NOVO)
├── demo_context_system.py         # Demonstração do sistema (NOVO)
├── test_context_system.py         # Testes do sistema (NOVO)
├── DOCUMENTACAO_CONTEXTO_AVANCADO.md # Documentação completa (NOVO)
├── bot.py                         # Versão original do bot
├── bot_improved.py               # Versão melhorada
├── config_manager.py             # Gerenciamento seguro de configurações
├── error_handler.py              # Tratamento robusto de erros
├── conversation_persistence.py   # Sistema de persistência
├── database.py                   # Banco de dados expandido
├── .env                          # Variáveis de ambiente (NÃO COMMITAR)
├── env.example                   # Template de configuração
├── requirements.txt              # Dependências Python
├── Dockerfile                    # Configuração Docker
├── DOCUMENTACAO_TECNICA.md       # Documentação técnica completa
├── bot.log                       # Logs do sistema
├── bot_data.db                   # Banco de dados SQLite
├── checkpoints/                  # Modelos de IA
├── voice_cache/                  # Cache de vozes
└── OpenVoice/                    # Biblioteca de clonagem de voz
```

## 🛠️ Funcionalidades Detalhadas

### Comandos Básicos
- `/start` - Iniciar o bot e ver menu principal
- `/help` - Ver todos os comandos disponíveis
- `/status` - Verificar status do sistema

### Comandos de Contexto Avançado (NOVO)
- `/contexto` - Mostrar contexto multimodal atual
- `/limpar_contexto` - Limpar todo o contexto multimodal
- `/personalidade` - Configurar personalidade do bot
- `/personalidade [tipo]` - Definir personalidade específica (cientista, pirata, artista, etc.)
- `/clonarvoz` - Entrar em modo de clonagem de voz
- `/sair_modo` - Sair do modo atual

### Personalidades Disponíveis
- **assistente** - Assistente útil e prestativo (padrão)
- **cientista** - Cientista cético e analítico
- **pirata** - Pirata aventureiro e carismático
- **professor** - Professor paciente e didático
- **artista** - Artista criativo e inspirador
- **filósofo** - Filósofo profundo e reflexivo
- **médico** - Médico cuidadoso e preciso
- **engenheiro** - Engenheiro prático e lógico
- **historiador** - Historiador erudito e detalhista
- **escritor** - Escritor criativo e expressivo

### Funcionalidades de IA
- **Chat Inteligente**: Conversas naturais com Gemini AI
- **Análise de Imagens**: Processamento multimodal de imagens
- **Geração de Conteúdo**: Criação de texto, código e análises
- **Tradução**: Tradução automática entre idiomas
- **OCR**: Extração de texto de imagens

### Funcionalidades Avançadas
- **Clonagem de Voz**: Clone vozes usando OpenVoice
- **Face Swapping**: Troca de rostos em imagens
- **Geração de Imagens**: Criação de imagens com IA
- **Processamento Multimodal**: Análise completa de conteúdo
- **Sistema de Plugins**: Extensibilidade modular

### Recursos de Segurança
- **Rate Limiting**: Controle de requisições por usuário
- **Validação de Entrada**: Sanitização de dados
- **Logging Seguro**: Monitoramento sem exposição de dados
- **Tratamento de Erros**: Sistema robusto com retry automático

## 📊 Monitoramento e Debugging

### Logs do Sistema
O bot gera logs detalhados em `bot.log`:

```bash
# Ver logs em tempo real
tail -f bot.log

# Filtrar erros
grep "ERROR" bot.log

# Filtrar por usuário específico
grep "usuário 123456" bot.log
```

### Métricas Importantes
- ✅ Taxa de sucesso das requisições
- ✅ Tempo de resposta da IA
- ✅ Uso de rate limiting
- ✅ Erros por tipo e usuário

### Debugging Comum

1. **Erro de Configuração:**
   - Verificar arquivo `.env`
   - Validar chaves de API

2. **Rate Limiting:**
   - Verificar logs de rate limiting
   - Ajustar limites se necessário

3. **Erro de IA:**
   - Verificar conectividade
   - Validar chave do Gemini

## 📚 Documentação Adicional

- **[Sistema de Contexto Avançado](DOCUMENTACAO_CONTEXTO_AVANCADO.md)** - Documentação completa do sistema de contexto (NOVO)
- **[Documentação Técnica](DOCUMENTACAO_TECNICA.md)** - Guia técnico completo
- **[Configuração de APIs](CONFIGURACAO_API.md)** - Como obter chaves de API
- **[Instruções Docker](INSTRUCOES_DOCKER.md)** - Execução com Docker

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Se você encontrar algum problema ou tiver dúvidas, abra uma issue no GitHub.

## 🏗️ Arquitetura (Visão Geral)

```
[Usuário]
   │ Telegram
   ▼
[Bot (python-telegram-bot)]  ── usa →  [AdvancedContextSystem]
   │                                 │
   │                                 ├─ Contexto Multimodal (SQLite)
   │                                 └─ Estados/Personalidade (SQLite)
   │
   ├─► Geração/Análise (Gemini)
   ├─► Pesquisa (Tavily)  ←→  [Cache API (SQLite)]
   └─► Tarefas Pesadas → [Celery Worker] ← Broker [Redis]
                                       │
                                       └─ Notifica resultado → Telegram
```

## ⚙️ Ambientes e Configuração (APP_ENV)

- Defina `APP_ENV=dev` (padrão) ou `APP_ENV=prod` no ambiente.
- Arquivos de configuração:
  - `config.dev.json`: desenvolvimento
  - `config.prod.json`: produção
- Carregamento automático via `config_loader.py`.

Variáveis úteis no `.env` (exemplos):

```
TELEGRAM_TOKEN=seu_token
GEMINI_API_KEY=sua_chave
ADMIN_USER_IDS=123456789
REDIS_URL=redis://localhost:6379/0
BOT_LOG_FILE=bot.log
APP_ENV=dev
```

## 🚦 Execução com Filas (Celery + Redis)

1) Inicie o Redis (local ou serviço).
2) Inicie o worker Celery:

```bash
celery -A tasks.celery_app.celery_app worker -l info
```

3) Execute o bot normalmente:

```bash
python context_aware_bot.py
```

O comando `/clonarvoz` irá enfileirar a clonagem de voz (não bloqueia o bot). Você receberá as mensagens de progresso e conclusão automaticamente.

## 🧾 Logging e Alertas

- Logging configurado em `logging_setup.py` (console + arquivo rotativo).
- Em nível `ERROR`, o bot envia um alerta para os `ADMIN_USER_IDS` via Telegram (se configurados).
- Arquivo padrão: `BOT_LOG_FILE=bot.log`.

## 🧪 Testes e Analytics

- Testes (pytest):
  - `tests/test_cache.py` – testa cache API em SQLite
- Analytics:
  - `analytics.py` – gera relatório rápido: papéis, top comandos, uso por hora

Execução:

```bash
pytest -q
python analytics.py
```

## 💡 Exemplos de Uso

- Personalidade:
  - `/personalidade cientista` – respostas mais analíticas
- Contexto:
  - Envie uma imagem → peça: “Crie uma história sobre isso”
- Filas:
  - `/clonarvoz` → envie um áudio de 5–10s → processamento em segundo plano

## 🛟 Troubleshooting Rápido

- “Fila indisponível”: confirme `REDIS_URL` e o worker Celery ativo.
- “Sem respostas do bot”: confirme `TELEGRAM_TOKEN` e conectividade.
- “Cache não retorna”: verifique TTL e chave de cache (parâmetros normalizados).
