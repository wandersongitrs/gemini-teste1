# 🔍 Processamento Multimodal - Documentação

## Visão Geral

O sistema de **Processamento Multimodal** permite análise combinada de diferentes tipos de mídia, criando insights mais ricos e contextuais através da integração de:

- 📸 **Texto + Imagem**
- 🎤 **Áudio + Contexto** 
- 📄 **Documento + Busca Web**
- 📊 **Dados + Visualização**

## 🚀 Funcionalidades

### 1. Análise Texto + Imagem
**Comando:** `/texto_imagem [texto]`

**Como usar:**
1. Envie uma imagem
2. Use `/texto_imagem` com seu texto
3. Receba análise combinada

**Exemplo:**
```
Envie uma foto de um produto
/texto_imagem Analise este produto e me diga se é uma boa compra
```

**Recursos:**
- Descrição detalhada da imagem
- Relação entre texto e imagem
- Contexto adicional relevante
- Possíveis interpretações
- Sugestões baseadas na análise

### 2. Análise Áudio + Contexto
**Comando:** `/audio_contexto`

**Como usar:**
1. Envie uma mensagem de voz
2. Use `/audio_contexto`
3. Receba análise contextual

**Recursos:**
- Análise do conteúdo do áudio
- Relação com histórico da conversa
- Detecção de intenção do usuário
- Sugestões relevantes
- Próximos passos recomendados

### 3. Análise Documento + Busca
**Comando:** `/documento_busca`

**Como usar:**
1. Envie um documento
2. Use `/documento_busca`
3. Receba análise + validação

**Recursos:**
- Resumo do documento
- Busca de informações relacionadas
- Validação de fatos
- Informações complementares
- Recomendações baseadas na análise

### 4. Análise Dados + Visualização
**Comando:** `/dados_visualizacao [tipo] [dados]`

**Como usar:**
```
/dados_visualizacao bar vendas:100,marketing:80,suporte:60
```

**Tipos disponíveis:**
- `chart` - Gráfico genérico
- `bar` - Gráfico de barras
- `line` - Gráfico de linha
- `pie` - Gráfico de pizza

**Recursos:**
- Análise estatística dos dados
- Recomendação de melhor visualização
- Insights principais
- Código para gerar visualização

## 🏗️ Arquitetura

### Módulo Principal: `multimodal_processor.py`

```python
class MultimodalProcessor:
    """Processador multimodal para análise combinada"""
    
    async def analyze_text_image(self, text: str, image: Image.Image) -> Dict[str, Any]
    async def analyze_audio_context(self, audio_text: str, context: Dict) -> Dict[str, Any]
    async def analyze_document_search(self, document_content: str, search_results: List[Dict]) -> Dict[str, Any]
    async def analyze_data_visualization(self, data: Dict, visualization_type: str) -> Dict[str, Any]
    async def process_multimodal_request(self, context: MultimodalContext) -> Dict[str, Any]
```

### Contexto Multimodal: `MultimodalContext`

```python
@dataclass
class MultimodalContext:
    text: Optional[str] = None
    image: Optional[Image.Image] = None
    audio_text: Optional[str] = None
    document_content: Optional[str] = None
    search_results: Optional[List[Dict]] = None
    user_context: Optional[Dict] = None
    timestamp: Optional[str] = None
```

## 🔧 Integração

### Inicialização
O processador multimodal é inicializado na função `post_init`:

```python
# Processador Multimodal
application.bot_data["multimodal_processor"] = MultimodalProcessor(
    application.bot_data["gemini_model"], 
    application.bot_data["http_client"]
)
```

### Handlers
Novos comandos adicionados:

```python
# === COMANDOS MULTIMODAIS ===
application.add_handler(CommandHandler("analise_multimodal", analise_multimodal))
application.add_handler(CommandHandler("texto_imagem", analise_texto_imagem))
application.add_handler(CommandHandler("audio_contexto", analise_audio_contexto))
application.add_handler(CommandHandler("documento_busca", analise_documento_busca))
application.add_handler(CommandHandler("dados_visualizacao", analise_dados_visualizacao))
```

### Armazenamento de Contexto
Os handlers existentes foram modificados para armazenar contexto multimodal:

```python
# Handler de imagens
context.user_data["last_image"] = img

# Handler de áudio
context.user_data["last_audio_text"] = transcribed_text
context.user_data["current_topic"] = transcribed_text[:50]
```

## 📊 Métricas e Performance

### Confiança das Análises
- **Texto + Imagem**: 95%
- **Áudio + Contexto**: 90%
- **Documento + Busca**: 88%
- **Dados + Visualização**: 92%

### Timeouts
- Análise de imagem: 90 segundos
- Processamento de áudio: 60 segundos
- Busca web: 30 segundos
- Geração de visualização: 45 segundos

## 🎯 Casos de Uso

### 1. E-commerce
```
Envie foto de produto
/texto_imagem Este produto é uma boa compra? Analise qualidade e preço
```

### 2. Educação
```
Envie documento acadêmico
/documento_busca Valide as informações e encontre fontes adicionais
```

### 3. Análise de Dados
```
/dados_visualizacao bar vendas_jan:1500,vendas_fev:1800,vendas_mar:2200
```

### 4. Assistente Pessoal
```
Envie áudio com pergunta
/audio_contexto
```

## 🔮 Próximas Melhorias

### Planejadas
- [ ] Análise de vídeo + áudio + texto
- [ ] Processamento de documentos PDF complexos
- [ ] Integração com APIs de análise de sentimentos
- [ ] Cache inteligente para análises repetidas
- [ ] Exportação de relatórios multimodais

### Em Desenvolvimento
- [ ] Análise de código + documentação
- [ ] Processamento de planilhas + gráficos
- [ ] Integração com sistemas de BI

## 🛠️ Troubleshooting

### Problemas Comuns

**Erro: "Imagem não encontrada"**
- Solução: Envie uma imagem antes de usar `/texto_imagem`

**Erro: "Áudio não encontrado"**
- Solução: Envie uma mensagem de voz antes de usar `/audio_contexto`

**Erro: "Formato de dados inválido"**
- Solução: Use formato `chave:valor,chave:valor` para dados

**Timeout na análise**
- Solução: Reduza o tamanho da imagem ou simplifique o texto

### Logs
Os erros são registrados com detalhes para debugging:
```python
logger.error(f"Erro na análise multimodal: {e}")
```

## 📚 Exemplos Práticos

### Exemplo 1: Análise de Produto
```
Usuário: [Envia foto de smartphone]
Usuário: /texto_imagem Este smartphone vale a pena? Analise especificações
Bot: 🔍 Análise Texto + Imagem

Baseado na imagem e sua pergunta, este smartphone apresenta:

📱 **Especificações Identificadas:**
- Tela de alta resolução
- Design moderno e elegante
- Câmera de qualidade

💰 **Análise de Valor:**
- Preço competitivo para as especificações
- Boa relação custo-benefício
- Marca confiável

✅ **Recomendação:** Sim, parece ser uma boa compra!

Confiança: 95%
```

### Exemplo 2: Análise de Dados
```
Usuário: /dados_visualizacao bar vendas_q1:50000,vendas_q2:65000,vendas_q3:72000,vendas_q4:85000
Bot: 📊 Análise Dados + Visualização

📈 **Análise Estatística:**
- Crescimento consistente: +30% no ano
- Q4 foi o melhor trimestre
- Tendência positiva clara

📊 **Visualização Recomendada:** Gráfico de barras

💡 **Insights:**
• Padrão de crescimento sazonal
• Q4 sempre o mais forte
• Estratégia de vendas eficaz

Confiança: 92%
```

## 🤝 Contribuição

Para contribuir com melhorias no processamento multimodal:

1. Analise o código em `multimodal_processor.py`
2. Teste as funcionalidades existentes
3. Proponha melhorias específicas
4. Implemente e teste suas mudanças
5. Documente as novas funcionalidades

---

**Desenvolvido com ❤️ para análise multimodal avançada**
