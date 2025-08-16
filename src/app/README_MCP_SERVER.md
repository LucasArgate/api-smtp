# MCP Server - Model Context Protocol

## 🎯 Visão Geral

O **MCP Server** é uma interface normalizada e otimizada para **Modelos de Linguagem (LLMs)** como Claude, GPT, Gemini e outros. Ele fornece endpoints específicos que permitem que IAs interajam com o sistema de emails de forma inteligente e contextual.

## 🤖 Por que MCP?

### **Problema Resolvido**
- ❌ **Interfaces complexas**: APIs tradicionais são difíceis para LLMs entenderem
- ❌ **Dados não estruturados**: Informações não normalizadas confundem IAs
- ❌ **Falta de contexto**: LLMs não conseguem entender relacionamentos entre emails
- ❌ **Automação limitada**: Difícil criar workflows inteligentes

### **Solução MCP**
- ✅ **Interface normalizada**: Endpoints específicos para LLMs
- ✅ **Dados estruturados**: Emails normalizados com metadados inteligentes
- ✅ **Contexto rico**: Informações sobre conversas e relacionamentos
- ✅ **Automação inteligente**: Workflows baseados em IA

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email API     │    │   MCP Server    │    │   LLM Client    │
│  (FastAPI)      │◄──►│   (Normalizer)  │◄──►│  (Claude/GPT)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MinIO Storage │    │   Context       │    │   AI Processing │
│   (Emails)      │    │   Management    │    │   & Responses   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Modelos de Dados

### **1. MCPEmailSummary**
Resumo normalizado de email para listagens:

```json
{
  "id": "email_123",
  "subject": "URGENTE: Problema crítico",
  "from_address": "admin@company.com",
  "from_name": "Admin",
  "to_addresses": ["tech@company.com"],
  "received_at": "2024-01-01T10:00:00",
  "has_attachments": true,
  "content_preview": "Precisamos resolver este problema...",
  "priority": "high",
  "category": "support"
}
```

### **2. MCPEmailDetail**
Detalhes completos para análise profunda:

```json
{
  "id": "email_123",
  "subject": "URGENTE: Problema crítico",
  "from_address": "admin@company.com",
  "text_content": "Conteúdo completo em texto",
  "html_content": "<p>Conteúdo HTML</p>",
  "attachments": [...],
  "metadata": {
    "processed_at": "2024-01-01T10:00:05",
    "has_attachments": true,
    "content_length": 150
  }
}
```

### **3. MCPContext**
Contexto de conversa para LLMs:

```json
{
  "conversation_id": "conv_email_123",
  "email_thread": ["email_123", "email_124"],
  "participants": ["admin@company.com", "tech@company.com"],
  "topic": "Suporte Técnico",
  "sentiment": "negative",
  "urgency": "high",
  "last_activity": "2024-01-01T10:00:00"
}
```

## 🌐 Endpoints MCP

### **📧 Listagem de Emails**
```http
GET /mcp/emails?limit=50&offset=0&category=support&priority=high
```

**Parâmetros:**
- `limit`: Número máximo de emails (padrão: 50)
- `offset`: Deslocamento para paginação (padrão: 0)
- `category`: Filtrar por categoria (opcional)
- `priority`: Filtrar por prioridade (opcional)

**Resposta:** Lista de `MCPEmailSummary`

### **📧 Detalhes de Email**
```http
GET /mcp/emails/{email_id}
```

**Resposta:** `MCPEmailDetail` completo

### **🔄 Contexto de Conversa**
```http
GET /mcp/emails/{email_id}/context
```

**Resposta:** `MCPContext` com histórico da conversa

### **💬 Resposta Automática**
```http
POST /mcp/emails/{email_id}/respond
```

**Body:**
```json
{
  "response_type": "auto_reply",
  "content": "Resposta gerada pela IA",
  "confidence": 0.95,
  "reasoning": "Email de suporte - resposta automática apropriada"
}
```

**Resposta:** `MCPResponse` com ações executadas

### **⚙️ Criação de Workflow**
```http
POST /mcp/workflow
```

**Body:**
```json
{
  "trigger_email_id": "email_123",
  "workflow_type": "auto_reply",
  "conditions": [
    {"field": "category", "operator": "equals", "value": "support"}
  ],
  "actions": [
    {"type": "send_reply", "template": "support_auto_reply"}
  ]
}
```

**Resposta:** `MCPWorkflow` criado

### **🔍 Busca Inteligente**
```http
GET /mcp/search?query=problema&limit=10
```

**Resposta:** Lista de `MCPEmailSummary` encontrados

### **📊 Estatísticas MCP**
```http
GET /mcp/statistics
```

**Resposta:** Estatísticas do sistema + informações MCP

## 🧠 Inteligência Integrada

### **1. Análise de Prioridade**
O sistema analisa automaticamente:
- **Palavras-chave**: "URGENTE", "crítico", "emergência"
- **Contexto**: Assunto, conteúdo, remetente
- **Classificação**: high, medium, low, normal

### **2. Categorização Automática**
Categorias detectadas:
- **support**: Problemas, ajuda, suporte
- **purchase**: Pedidos, compras, vendas
- **notification**: Alertas, notificações
- **marketing**: Promoções, newsletters
- **general**: Outros tipos

### **3. Análise de Sentimento**
Baseada em:
- **Palavras positivas**: "obrigado", "excelente", "ótimo"
- **Palavras negativas**: "problema", "erro", "ruim"
- **Classificação**: positive, negative, neutral

### **4. Contexto de Conversa**
Identifica:
- **Threads de email**: Conversas relacionadas
- **Participantes**: Remetentes e destinatários
- **Tópicos**: Assuntos principais
- **Histórico**: Atividade recente

## 🚀 Cenários de Uso

### **1. Claude Analisando Emails**
```python
# Claude pode:
# 1. Listar emails por prioridade
emails = await mcp.get_emails(priority="high")

# 2. Analisar contexto de conversa
context = await mcp.get_email_context(email_id)

# 3. Gerar resumo inteligente
summary = f"Email de {context.topic} com urgência {context.urgency}"
```

### **2. GPT Respondendo Automaticamente**
```python
# GPT pode:
# 1. Ler email completo
email = await mcp.get_email_detail(email_id)

# 2. Gerar resposta contextual
response = await mcp.respond_to_email(email_id, {
    "response_type": "auto_reply",
    "content": "Resposta gerada por IA",
    "confidence": 0.9
})
```

### **3. Gemini Criando Workflows**
```python
# Gemini pode:
# 1. Analisar padrões de email
emails = await mcp.get_emails(category="support")

# 2. Criar automação inteligente
workflow = await mcp.create_workflow({
    "trigger_email_id": email_id,
    "workflow_type": "auto_reply",
    "conditions": [{"field": "category", "value": "support"}],
    "actions": [{"type": "send_reply", "template": "support"}]
})
```

## 🔧 Configuração

### **1. Inicialização Automática**
O MCP Server é inicializado automaticamente com a aplicação:

```python
@app.on_event("startup")
async def startup_event():
    # Inicializar email receiver
    email_receiver = await start_email_receiver(smtp_config)
    
    # Inicializar sistema MCP
    init_mcp_system(email_receiver)
```

### **2. Dependências**
```txt
fastapi          # Framework web
pydantic         # Validação de dados
aiohttp          # Requisições HTTP assíncronas
requests         # Requisições HTTP síncronas
```

## 🧪 Testes

### **Teste Completo**
```bash
cd src/app
python test_mcp_server.py
```

### **Teste Individual**
```bash
# Testar endpoints MCP
curl -H "X-API-Key: api-test-key" \
     http://localhost/mcp/emails?limit=5

# Testar busca
curl -H "X-API-Key: api-test-key" \
     "http://localhost/mcp/search?query=teste"

# Testar estatísticas
curl -H "X-API-Key: api-test-key" \
     http://localhost/mcp/statistics
```

## 🔮 Próximos Passos

### **1. Melhorias Imediatas**
- 🔍 **NLP avançado**: Análise semântica mais sofisticada
- 📊 **Machine Learning**: Classificação automática melhorada
- 🔄 **Workflows reais**: Execução de automações
- 📧 **Respostas automáticas**: Envio real de emails

### **2. Funcionalidades Futuras**
- 🤖 **IA integrada**: Modelos locais para análise
- 📱 **Notificações**: Alertas inteligentes
- 🌐 **Webhooks**: Integração com sistemas externos
- 📈 **Analytics**: Métricas avançadas de uso

### **3. Integração com LLMs**
- 🔗 **Claude**: Análise e resposta automática
- 🔗 **GPT**: Geração de conteúdo
- 🔗 **Gemini**: Workflows inteligentes
- 🔗 **Outros**: Qualquer LLM compatível com MCP

## 📚 Recursos Adicionais

### **Documentação**
- [README principal](../readme.md)
- [Email Receiver](README_EMAIL_RECEIVER.md)
- [API FastAPI](../main.py)

### **Exemplos de Código**
- [Teste MCP](test_mcp_server.py)
- [Demo do sistema](demo_email_system.py)
- [Teste Email Receiver](test_email_receiver.py)

---

## 🎉 **Conclusão**

O **MCP Server** transforma seu sistema de emails em uma **plataforma inteligente** onde:

- 🤖 **LLMs podem se conectar** e interagir naturalmente
- 📧 **Emails são analisados** automaticamente com contexto
- 🔄 **Workflows inteligentes** são criados e executados
- 📊 **Dados são normalizados** para fácil compreensão por IAs

**O futuro é agora: emails processados, analisados e respondidos por inteligência artificial!** 🚀
