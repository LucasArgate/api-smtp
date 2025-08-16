# Email Receiver - Documentação

## Visão Geral

O **Email Receiver** é um módulo Python que se integra com sua API SMTP existente para **receber e processar emails** do MailDev. Ele funciona como um complemento à sua funcionalidade de envio de emails.

## Como Funciona

### 1. **Listener Automático**
- ✅ Escuta automaticamente por novos emails no MailDev
- ✅ Verifica a cada 30 segundos por emails não lidos
- ✅ Processa emails em background sem bloquear a API

### 2. **Integração com MinIO**
- ✅ Armazena emails recebidos no bucket `received_emails`
- ✅ Salva anexos automaticamente
- ✅ Organiza por timestamp e ID único

### 3. **API REST Completa**
- ✅ Endpoints para listar emails recebidos
- ✅ Busca por texto nos emails
- ✅ Estatísticas em tempo real
- ✅ Gerenciamento individual de emails

## Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MailDev       │    │  Email Receiver │    │     MinIO       │
│   (Porta 1080)  │◄──►│   (Python)      │───►│  (Storage)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Web Interface  │    │   FastAPI       │    │  Bucket:        │
│  (Porta 1080)   │    │   (Porta 8000)  │    │  received_emails│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Endpoints da API

### 📥 **Listar Emails Recebidos**
```http
GET /v1/mail/received?limit=50&offset=0
X-API-Key: your_api_key
```

**Resposta:**
```json
{
  "emails": [
    {
      "id": "email_id_123",
      "from": {"address": "sender@example.com", "name": "Sender Name"},
      "to": [{"address": "recipient@example.com", "name": "Recipient"}],
      "subject": "Assunto do Email",
      "text": "Conteúdo em texto plano",
      "html": "<h1>Conteúdo HTML</h1>",
      "attachments": [],
      "received_at": "2024-01-01T10:00:00",
      "processed_at": "2024-01-01T10:00:05"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 🔍 **Buscar Emails**
```http
GET /v1/mail/received/search?query=palavra_chave
X-API-Key: your_api_key
```

### 📊 **Estatísticas**
```http
GET /v1/mail/received/statistics
X-API-Key: your_api_key
```

**Resposta:**
```json
{
  "total_emails_received": 150,
  "total_attachments": 45,
  "bucket_size_bytes": 1048576,
  "last_updated": "2024-01-01T10:00:00"
}
```

### 📧 **Email Específico**
```http
GET /v1/mail/received/{email_id}
X-API-Key: your_api_key
```

### 🗑️ **Remover Email**
```http
DELETE /v1/mail/received/{email_id}
X-API-Key: your_api_key
```

## Configuração

### 1. **Arquivo de Configuração**
```json
{
  "maildev": {
    "web_port": 1080,
    "smtp_port": 1025,
    "polling_interval": 30,
    "error_retry_interval": 60
  },
  "storage": {
    "bucket_name": "received_emails",
    "max_email_size_mb": 10,
    "max_attachment_size_mb": 5
  }
}
```

### 2. **Variáveis de Ambiente**
```bash
# Portas do MailDev
MAILDEV_WEB_PORT=1080
MAILDEV_SMTP_PORT=1025

# Configurações do MinIO
MINIO_SERVER=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## Uso

### 1. **Inicialização Automática**
O Email Receiver é iniciado automaticamente quando sua API FastAPI inicia:

```python
@app.on_event("startup")
async def startup_event():
    global email_receiver
    email_receiver = await start_email_receiver(smtp_config, callback_function)
```

### 2. **Callback Personalizado**
```python
async def my_email_callback(email_data):
    """Função chamada quando um email é recebido"""
    print(f"Novo email: {email_data['subject']}")
    
    # Sua lógica personalizada aqui
    # - Notificações
    # - Processamento específico
    # - Integração com outros sistemas
    # - Logs customizados

# Usar o callback
email_receiver = await start_email_receiver(smtp_config, my_email_callback)
```

### 3. **Uso Independente**
```python
from email_receiver import EmailReceiver

# Criar instância
receiver = EmailReceiver(smtp_config)

# Listar emails
emails = await receiver.get_received_emails(limit=10)

# Buscar emails
results = await receiver.search_received_emails("importante")

# Estatísticas
stats = receiver.get_statistics()
```

## Testes

### 1. **Teste Básico**
```bash
cd src/app
python test_email_receiver.py
```

### 2. **Teste em Tempo Real**
```bash
cd src/app
python test_email_receiver.py --listen
```

### 3. **Teste via API**
```bash
# Listar emails
curl -H "X-API-Key: your_api_key" \
     http://localhost/v1/mail/received

# Buscar emails
curl -H "X-API-Key: your_api_key" \
     "http://localhost/v1/mail/received/search?query=teste"

# Estatísticas
curl -H "X-API-Key: your_api_key" \
     http://localhost/v1/mail/received/statistics
```

## Monitoramento

### 1. **Logs Automáticos**
- ✅ Todos os emails recebidos são logados
- ✅ Erros são capturados e logados
- ✅ Estatísticas em tempo real

### 2. **Métricas Disponíveis**
- 📊 Total de emails recebidos
- 📎 Total de anexos
- 💾 Tamanho total do bucket
- ⏰ Última atualização

### 3. **Alertas e Notificações**
```python
async def alert_callback(email_data):
    """Callback para alertas"""
    if "URGENTE" in email_data['subject'].upper():
        # Enviar notificação
        await send_alert_notification(email_data)
    
    if email_data['from']['address'] in ['admin@company.com']:
        # Processamento especial
        await process_admin_email(email_data)
```

## Troubleshooting

### 1. **Email Receiver não inicia**
- ✅ Verificar se o MailDev está rodando na porta 1080
- ✅ Verificar conexão com MinIO
- ✅ Verificar arquivo de configuração

### 2. **Emails não são processados**
- ✅ Verificar logs da aplicação
- ✅ Verificar se o bucket `received_emails` existe
- ✅ Verificar permissões do MinIO

### 3. **Performance lenta**
- ✅ Ajustar `polling_interval` na configuração
- ✅ Verificar tamanho dos emails e anexos
- ✅ Monitorar uso de memória

## Exemplos de Uso

### 1. **Sistema de Notificações**
```python
async def notification_callback(email_data):
    """Envia notificações para diferentes canais"""
    
    # Notificação por email
    if email_data['from']['address'] == 'support@company.com':
        await send_support_notification(email_data)
    
    # Notificação por Slack
    if "URGENTE" in email_data['subject']:
        await send_slack_alert(email_data)
    
    # Notificação por SMS
    if email_data['from']['address'] == 'ceo@company.com':
        await send_sms_alert(email_data)
```

### 2. **Processamento Automático**
```python
async def processing_callback(email_data):
    """Processa emails automaticamente"""
    
    # Emails de pedidos
    if "pedido" in email_data['subject'].lower():
        await process_order_email(email_data)
    
    # Emails de suporte
    if "suporte" in email_data['subject'].lower():
        await create_support_ticket(email_data)
    
    # Emails de relatórios
    if email_data['attachments']:
        await process_report_attachments(email_data)
```

## Integração com Sistemas Externos

### 1. **Webhooks**
```python
async def webhook_callback(email_data):
    """Envia webhook para sistemas externos"""
    
    webhook_data = {
        "event": "email_received",
        "timestamp": datetime.now().isoformat(),
        "email": email_data
    }
    
    # Enviar para múltiplos sistemas
    await send_webhook("https://api1.com/webhook", webhook_data)
    await send_webhook("https://api2.com/webhook", webhook_data)
```

### 2. **Banco de Dados**
```python
async def database_callback(email_data):
    """Salva emails no banco de dados"""
    
    # Salvar no PostgreSQL
    await save_to_postgres(email_data)
    
    # Salvar no MongoDB
    await save_to_mongodb(email_data)
    
    # Salvar no Redis para cache
    await save_to_redis(email_data)
```

## Segurança

### 1. **Autenticação**
- ✅ API Key obrigatória para todos os endpoints
- ✅ Validação de permissões por endpoint

### 2. **Validação de Dados**
- ✅ Sanitização de entrada
- ✅ Validação de tamanho de arquivos
- ✅ Verificação de tipos MIME

### 3. **Logs de Auditoria**
- ✅ Todos os acessos são logados
- ✅ IP do cliente registrado
- ✅ Timestamp de todas as operações

## Próximos Passos

### 1. **Funcionalidades Futuras**
- 🔄 Webhooks configuráveis
- 📧 Filtros avançados de email
- 🔍 Busca semântica
- 📊 Dashboard de analytics

### 2. **Integrações**
- 🔗 Slack/Teams notifications
- 📱 Push notifications
- 📧 Integração com outros provedores de email
- 🗄️ Mais opções de storage

### 3. **Performance**
- ⚡ Processamento paralelo
- 🚀 Cache inteligente
- 📈 Métricas avançadas
- 🔄 Load balancing

---

**🎯 O Email Receiver transforma sua API SMTP em um sistema completo de gerenciamento de emails, permitindo não apenas enviar, mas também receber, processar e gerenciar emails de forma eficiente e escalável.**
