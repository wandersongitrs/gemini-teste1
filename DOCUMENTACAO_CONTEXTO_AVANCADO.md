# Sistema de Contexto Avançado - Documentação Completa

## 📋 Visão Geral

O **Sistema de Contexto Avançado** é uma implementação revolucionária que transforma o bot Telegram em uma inteligência artificial verdadeiramente contextual. O sistema permite que o bot "lembre" de interações multimodais anteriores e use esse contexto para enriquecer respostas futuras.

### 🎯 Principais Funcionalidades

- **🧠 Contexto Multimodal Persistente**: O bot lembra de imagens, áudios e vídeos analisados anteriormente
- **🎛️ Estados de Conversa Inteligentes**: Sistema de modos que adapta o comportamento baseado no contexto
- **🎭 Personalização de Personalidade**: Usuários podem configurar diferentes personalidades para o bot
- **💾 Persistência Entre Sessões**: Contexto mantido mesmo após reinicializações
- **🔄 Integração Transparente**: Funciona automaticamente com todos os handlers existentes

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE CONTEXTO AVANÇADO             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Context Manager │  │ State Manager   │  │ Personality  │ │
│  │                 │  │                 │  │ Manager      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Advanced Context System                  │
├─────────────────────────────────────────────────────────────┤
│                    Conversation Manager                     │
├─────────────────────────────────────────────────────────────┤
│                    SQLite Database                         │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

1. **Entrada Multimodal** → Context Manager salva contexto
2. **Mensagem do Usuário** → Sistema enriquece com contexto
3. **Personalidade** → Sistema aplica instruções personalizadas
4. **Estado Atual** → Sistema adapta comportamento
5. **Resposta** → Sistema gera resposta contextualizada

---

## 🧠 Contexto Multimodal

### Como Funciona

O sistema salva automaticamente o contexto de cada interação multimodal:

```python
# Exemplo: Usuário envia imagem
image_description = "Uma paisagem montanhosa com lago cristalino"
context_system.handle_multimodal_interaction(
    user_id, "image", image_description, conversation_id
)

# Próxima mensagem: "Crie uma história sobre isso"
enriched_message = context_system.enrich_message_with_context(user_id, "Crie uma história sobre isso")
# Resultado: "Contexto recente: Uma paisagem montanhosa com lago cristalino\n\nMensagem do usuário: Crie uma história sobre isso"
```

### Tipos de Contexto Suportados

- **🖼️ Imagens**: Descrições de imagens analisadas
- **🎤 Áudio**: Transcrições de arquivos de áudio
- **🎬 Vídeos**: Análises de conteúdo de vídeo
- **🔍 Pesquisas**: Tópicos de pesquisas realizadas
- **🎨 Geração de Imagens**: Prompts usados para gerar imagens

### Persistência Temporal

- **⏰ Duração**: Contexto válido por 10 minutos
- **🔄 Renovação**: Atualizado a cada nova interação multimodal
- **🧹 Limpeza**: Automática após expiração

---

## 🎛️ Estados de Conversa

### Estados Disponíveis

```python
class ConversationState(Enum):
    CHAT_GERAL = "chat_geral"                    # Modo normal de conversa
    AGUARDANDO_AUDIO_CLONE = "aguardando_audio_clone"  # Aguardando áudio para clonagem
    AGUARDANDO_IMAGEM_ANALISE = "aguardando_imagem_analise"  # Aguardando imagem
    AGUARDANDO_VIDEO_ANALISE = "aguardando_video_analise"    # Aguardando vídeo
    PESQUISANDO = "pesquisando"                  # Modo de pesquisa ativa
    GERANDO_IMAGEM = "gerando_imagem"            # Gerando imagem
    CONFIGURANDO = "configurando"                # Configurando bot
    AGUARDANDO_PERSONALIDADE = "aguardando_personalidade"  # Aguardando personalidade
```

### Exemplo de Uso

```python
# Usuário executa /clonarvoz
context_system.set_conversation_state(user_id, ConversationState.AGUARDANDO_AUDIO_CLONE)

# Bot responde adequadamente ao estado
if context_system.is_in_state(user_id, ConversationState.AGUARDANDO_AUDIO_CLONE):
    # Bot aguarda áudio, não responde a texto normal
    await send_message("Aguardando arquivo de áudio...")
```

### Transições de Estado

- **Entrada**: Comandos específicos (`/clonarvoz`, `/pesquisar`)
- **Processamento**: Estados automáticos durante processamento
- **Saída**: Comandos de reset (`/sair_modo`) ou conclusão automática

---

## 🎭 Sistema de Personalidades

### Personalidades Pré-definidas

| Personalidade | Descrição | Uso Recomendado |
|---------------|-----------|-----------------|
| **assistente** | Assistente útil e prestativo | Uso geral |
| **cientista** | Cientista cético e analítico | Análises técnicas |
| **pirata** | Pirata aventureiro e carismático | Histórias e aventuras |
| **professor** | Professor paciente e didático | Explicações educativas |
| **artista** | Artista criativo e inspirador | Criação artística |
| **filósofo** | Filósofo profundo e reflexivo | Discussões profundas |
| **médico** | Médico cuidadoso e preciso | Conselhos de saúde |
| **engenheiro** | Engenheiro prático e lógico | Soluções técnicas |
| **historiador** | Historiador erudito e detalhista | Contexto histórico |
| **escritor** | Escritor criativo e expressivo | Narrativas |

### Configuração de Personalidade

```python
# Definir personalidade pré-definida
context_system.set_user_personality(user_id, "cientista")

# Definir personalidade customizada
custom_description = "Você é um especialista em IA com foco em ética tecnológica"
context_system.set_user_personality(user_id, "custom", custom_description)

# Obter instrução do sistema
system_instruction = context_system.get_system_instruction(user_id)
```

### Comandos de Personalidade

- **`/personalidade`**: Mostra personalidade atual e opções
- **`/personalidade cientista`**: Define personalidade específica
- **`/personalidade custom "descrição"`**: Define personalidade customizada

---

## 💾 Persistência e Banco de Dados

### Estrutura do Banco de Dados

#### Tabela: `multimodal_context`
```sql
CREATE TABLE multimodal_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    conversation_id INTEGER NOT NULL,
    last_image_description TEXT,
    last_audio_transcription TEXT,
    last_video_analysis TEXT,
    last_research_topic TEXT,
    last_generated_image_prompt TEXT,
    context_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    context_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabela: `conversation_states`
```sql
CREATE TABLE conversation_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    conversation_id INTEGER NOT NULL,
    current_state TEXT NOT NULL DEFAULT 'chat_geral',
    state_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, conversation_id)
);
```

#### Tabela: `user_personalities`
```sql
CREATE TABLE user_personalities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    personality_type TEXT NOT NULL DEFAULT 'assistente',
    personality_description TEXT NOT NULL,
    custom_instructions TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Operações de Persistência

```python
# Salvar contexto multimodal
database.save_multimodal_context(user_id, conversation_id, context_data)

# Obter contexto multimodal
context = database.get_multimodal_context(user_id, conversation_id)

# Salvar estado da conversa
database.save_conversation_state(user_id, conversation_id, "pesquisando")

# Obter estado da conversa
state = database.get_conversation_state(user_id, conversation_id)

# Salvar personalidade
database.save_user_personality(user_id, "cientista", description)

# Obter personalidade
personality = database.get_user_personality(user_id)
```

---

## 🚀 Implementação e Uso

### Instalação

1. **Instalar dependências**:
```bash
pip install -r requirements.txt
```

2. **Configurar banco de dados**:
```python
from database import initialize_db
initialize_db()  # Cria tabelas automaticamente
```

3. **Executar bot**:
```bash
python context_aware_bot.py
```

### Integração com Bot Existente

```python
from advanced_context_system import get_advanced_context_system
from conversation_persistence import get_conversation_manager

# Inicializar sistema
conversation_manager = get_conversation_manager()
context_system = get_advanced_context_system(conversation_manager)

# Em handler de imagem
async def handle_image(update, context):
    # Processar imagem
    description = process_image(image_file)
    
    # Salvar contexto
    context_system.handle_multimodal_interaction(
        user_id, "image", description, conversation_id
    )

# Em handler de mensagem
async def handle_message(update, context):
    # Enriquecer mensagem
    enriched_message = context_system.enrich_message_with_context(user_id, message)
    
    # Obter instrução do sistema
    system_instruction = context_system.get_system_instruction(user_id)
    
    # Gerar resposta contextualizada
    response = generate_response(enriched_message, system_instruction)
```

### Comandos Disponíveis

#### Comandos Básicos
- **`/start`**: Inicia bot e mostra menu principal
- **`/help`**: Mostra ajuda e comandos disponíveis

#### Comandos de Contexto
- **`/contexto`**: Mostra contexto multimodal atual
- **`/limpar_contexto`**: Limpa todo o contexto multimodal
- **`/personalidade`**: Configura personalidade do bot
- **`/personalidade [tipo]`**: Define personalidade específica

#### Comandos de Modo
- **`/clonarvoz`**: Entra em modo de clonagem de voz
- **`/sair_modo`**: Sai do modo atual

#### Comandos de Configuração
- **`/config`**: Menu de configurações
- **`/stats`**: Estatísticas do usuário
- **`/backup`**: Criar backup dos dados

---

## 🎯 Exemplos Práticos

### Exemplo 1: Análise de Imagem + História

```
Usuário: [Envia imagem de uma floresta]
Bot: 🖼️ Imagem analisada! Descrição: Uma floresta densa com árvores altas...

Usuário: Crie uma história sobre isso
Bot: [Usando contexto da imagem] Era uma vez uma floresta mágica onde...
```

### Exemplo 2: Clonagem de Voz

```
Usuário: /clonarvoz
Bot: 🎤 Modo de clonagem ativado. Envie um áudio de 5-10 segundos.

Usuário: [Envia áudio]
Bot: ✅ Voz clonada! Agora você pode usar /falar para gerar áudio.

Usuário: /falar Olá, como você está?
Bot: [Gera áudio com voz clonada]
```

### Exemplo 3: Mudança de Personalidade

```
Usuário: /personalidade cientista
Bot: 🎭 Personalidade alterada para Cientista!

Usuário: Explique inteligência artificial
Bot: [Como cientista] Baseado em evidências empíricas, a IA pode ser definida como...
```

### Exemplo 4: Contexto Persistente

```
Usuário: [Envia vídeo de gato]
Bot: 🎬 Vídeo analisado: Gato brincando com bola...

[Usuário sai e volta depois]

Usuário: Me conte mais sobre isso
Bot: [Lembra do vídeo] Sobre o gato brincando com a bola, posso explicar...
```

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```bash
# Configurações do bot
TELEGRAM_TOKEN=seu_token_telegram
GEMINI_API_KEY=sua_chave_gemini

# Configurações de contexto
CONTEXT_TIMEOUT_MINUTES=10
MAX_CONTEXT_HISTORY=50
CLEANUP_DAYS=30

# Configurações de personalidade
DEFAULT_PERSONALITY=assistente
CUSTOM_PERSONALITIES_ENABLED=true

# Configurações de admin
ADMIN_USER_IDS=123456789,987654321
```

### Personalização de Personalidades

```python
# Adicionar nova personalidade
custom_personalities = {
    "detetive": "Você é um detetive investigativo, sempre buscando pistas e conexões.",
    "chef": "Você é um chef experiente, sempre dando dicas culinárias práticas.",
    "músico": "Você é um músico talentoso, sempre relacionando tudo com música."
}

# Integrar no sistema
personality_manager.predefined_personalities.update(custom_personalities)
```

### Configuração de Estados

```python
# Adicionar novo estado
class ConversationState(Enum):
    # ... estados existentes ...
    AGUARDANDO_TRADUCAO = "aguardando_traducao"
    GERANDO_MUSICA = "gerando_musica"

# Implementar handler para novo estado
async def handle_translation_mode(update, context):
    if context_system.is_in_state(user_id, ConversationState.AGUARDANDO_TRADUCAO):
        # Processar tradução
        pass
```

---

## 📊 Monitoramento e Debugging

### Logs do Sistema

```python
# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Logs específicos do contexto
logger = logging.getLogger('context_system')
logger.info(f"Contexto salvo para usuário {user_id}")
logger.debug(f"Estado alterado: {old_state} -> {new_state}")
```

### Métricas de Performance

```python
# Estatísticas de contexto
context_stats = {
    'total_contexts_saved': 1250,
    'active_contexts': 45,
    'context_hit_rate': 0.78,
    'average_context_age': '5.2 minutes'
}

# Estatísticas de personalidade
personality_stats = {
    'most_used_personality': 'assistente',
    'custom_personalities': 12,
    'personality_changes_today': 8
}
```

### Debugging de Contexto

```python
# Verificar contexto atual
def debug_context(user_id):
    context = context_system.context_manager.get_context_for_response(user_id)
    state = context_system.get_conversation_state(user_id)
    personality = context_system.get_user_personality(user_id)
    
    print(f"Contexto: {context}")
    print(f"Estado: {state.value}")
    print(f"Personalidade: {personality.personality_type}")
```

---

## 🚨 Tratamento de Erros

### Erros Comuns e Soluções

#### Erro: Contexto não persistido
```python
# Verificar inicialização do banco
try:
    initialize_db()
except Exception as e:
    logger.error(f"Erro na inicialização do banco: {e}")
```

#### Erro: Estado não alterado
```python
# Verificar se estado é válido
if state in ConversationState:
    context_system.set_conversation_state(user_id, state)
else:
    logger.error(f"Estado inválido: {state}")
```

#### Erro: Personalidade não aplicada
```python
# Verificar se personalidade existe
if personality_type in available_personalities:
    context_system.set_user_personality(user_id, personality_type)
else:
    logger.warning(f"Personalidade não encontrada: {personality_type}")
```

### Recuperação de Erros

```python
# Sistema de fallback
def safe_context_operation(user_id, operation):
    try:
        return operation(user_id)
    except Exception as e:
        logger.error(f"Erro na operação de contexto: {e}")
        # Fallback para estado padrão
        context_system.set_conversation_state(user_id, ConversationState.CHAT_GERAL)
        return None
```

---

## 🔮 Funcionalidades Futuras

### Roadmap de Desenvolvimento

#### Versão 2.0
- **🤖 Contexto de IA**: Integração com modelos de linguagem para contexto mais rico
- **🌐 Contexto Web**: Busca automática de informações relacionadas
- **🎨 Contexto Criativo**: Análise de estilo artístico para geração consistente

#### Versão 3.0
- **👥 Contexto Colaborativo**: Compartilhamento de contexto entre usuários
- **🧠 Contexto Emocional**: Análise de sentimento e adaptação de personalidade
- **📱 Contexto Multiplataforma**: Sincronização entre diferentes plataformas

### Contribuições

Para contribuir com o desenvolvimento:

1. **Fork** do repositório
2. **Criar branch** para nova funcionalidade
3. **Implementar** com testes
4. **Documentar** mudanças
5. **Submeter** pull request

---

## 📚 Referências e Recursos

### Documentação Técnica
- [Google Gemini API](https://ai.google.dev/docs)
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### Tutoriais Relacionados
- [Sistema de Persistência](GUIA_PERSISTENCIA.md)
- [Bot Multimodal](DOCUMENTACAO_MULTIMODAL.md)
- [Configuração Avançada](CONFIGURACAO_API.md)

### Comunidade
- [GitHub Issues](https://github.com/seu-repo/issues)
- [Discord Community](https://discord.gg/seu-servidor)
- [Telegram Group](https://t.me/seu-grupo)

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

## 👥 Créditos

**Desenvolvido por**: [Seu Nome]
**Contribuidores**: [Lista de contribuidores]
**Inspiração**: Sistema de contexto multimodal para bots inteligentes

---

*Última atualização: Janeiro 2025*
*Versão: 1.0.0*
