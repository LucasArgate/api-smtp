"""
MCP Server - Model Context Protocol
Interface normalizada para LLMs (Claude, GPT, Gemini, etc.)
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

from email_receiver import EmailReceiver
from main import get_api_key

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router para endpoints MCP
mcp_router = APIRouter(prefix="/mcp", tags=["MCP - Model Context Protocol"])

# Modelos Pydantic para normalização de dados
class MCPEmailSummary(BaseModel):
    """Resumo normalizado de email para LLMs"""
    id: str = Field(..., description="ID único do email")
    subject: str = Field(..., description="Assunto do email")
    from_address: str = Field(..., description="Endereço do remetente")
    from_name: Optional[str] = Field(None, description="Nome do remetente")
    to_addresses: List[str] = Field(..., description="Lista de endereços de destino")
    received_at: str = Field(..., description="Data/hora de recebimento")
    has_attachments: bool = Field(..., description="Se o email possui anexos")
    content_preview: str = Field(..., description="Preview do conteúdo (primeiros 200 chars)")
    priority: str = Field(default="normal", description="Prioridade estimada (high/medium/low/normal)")
    category: str = Field(default="general", description="Categoria estimada (work/personal/spam/notification)")

class MCPEmailDetail(BaseModel):
    """Detalhes completos de email para LLMs"""
    id: str = Field(..., description="ID único do email")
    subject: str = Field(..., description="Assunto do email")
    from_address: str = Field(..., description="Endereço do remetente")
    from_name: Optional[str] = Field(None, description="Nome do remetente")
    to_addresses: List[str] = Field(..., description="Lista de endereços de destino")
    received_at: str = Field(..., description="Data/hora de recebimento")
    text_content: Optional[str] = Field(None, description="Conteúdo em texto plano")
    html_content: Optional[str] = Field(None, description="Conteúdo HTML")
    attachments: List[Dict] = Field(..., description="Lista de anexos")
    metadata: Dict[str, Any] = Field(..., description="Metadados adicionais")

class MCPContext(BaseModel):
    """Contexto de conversa para LLMs"""
    conversation_id: str = Field(..., description="ID da conversa")
    email_thread: List[str] = Field(..., description="IDs dos emails na thread")
    participants: List[str] = Field(..., description="Participantes da conversa")
    topic: str = Field(..., description="Tópico principal da conversa")
    sentiment: str = Field(default="neutral", description="Sentimento estimado (positive/negative/neutral)")
    urgency: str = Field(default="normal", description="Urgência estimada (high/medium/low/normal)")
    last_activity: str = Field(..., description="Última atividade na conversa")

class MCPResponse(BaseModel):
    """Resposta normalizada para LLMs"""
    email_id: str = Field(..., description="ID do email respondido")
    response_type: str = Field(..., description="Tipo de resposta (auto_reply/forward/archive/flag)")
    content: str = Field(..., description="Conteúdo da resposta")
    actions: List[str] = Field(..., description="Ações executadas")
    confidence: float = Field(..., description="Confiança da resposta (0.0 a 1.0)")
    reasoning: str = Field(..., description="Raciocínio para a resposta")

class MCPWorkflow(BaseModel):
    """Workflow automatizado para LLMs"""
    workflow_id: str = Field(..., description="ID do workflow")
    trigger_email_id: str = Field(..., description="Email que disparou o workflow")
    workflow_type: str = Field(..., description="Tipo de workflow (auto_reply/forward/archive/notification)")
    conditions: List[Dict] = Field(..., description="Condições para execução")
    actions: List[Dict] = Field(..., description="Ações a serem executadas")
    status: str = Field(default="pending", description="Status do workflow")
    created_at: str = Field(..., description="Data/hora de criação")

class MCPEmailSystem:
    """Sistema de emails normalizado para LLMs"""
    
    def __init__(self, email_receiver: EmailReceiver):
        self.email_receiver = email_receiver
        self.conversation_contexts: Dict[str, MCPContext] = {}
    
    def normalize_email_for_llm(self, email_data: Dict) -> MCPEmailSummary:
        """Normaliza email para formato LLM-friendly"""
        try:
            # Extrair endereços de email
            from_info = email_data.get('from', {})
            to_info = email_data.get('to', [])
            
            from_address = from_info.get('address', 'unknown@example.com')
            from_name = from_info.get('name')
            
            to_addresses = []
            if isinstance(to_info, list):
                for recipient in to_info:
                    if isinstance(recipient, dict):
                        to_addresses.append(recipient.get('address', ''))
                    else:
                        to_addresses.append(str(recipient))
            
            # Criar preview do conteúdo
            text_content = email_data.get('text', '')
            html_content = email_data.get('html', '')
            content_preview = text_content[:200] if text_content else html_content[:200] if html_content else "Sem conteúdo"
            
            # Determinar prioridade baseada em palavras-chave
            priority = self._estimate_priority(email_data)
            
            # Determinar categoria
            category = self._estimate_category(email_data)
            
            return MCPEmailSummary(
                id=email_data.get('id', ''),
                subject=email_data.get('subject', 'Sem assunto'),
                from_address=from_address,
                from_name=from_name,
                to_addresses=to_addresses,
                received_at=email_data.get('received_at', ''),
                has_attachments=len(email_data.get('attachments', [])) > 0,
                content_preview=content_preview,
                priority=priority,
                category=category
            )
        except Exception as e:
            logger.error(f"Erro ao normalizar email: {e}")
            raise
    
    def _estimate_priority(self, email_data: Dict) -> str:
        """Estima a prioridade do email baseada em palavras-chave"""
        subject = email_data.get('subject', '').lower()
        text = email_data.get('text', '').lower()
        
        high_priority_keywords = ['urgente', 'urgent', 'crítico', 'critical', 'emergência', 'emergency', 'imediato', 'immediate']
        medium_priority_keywords = ['importante', 'important', 'atenção', 'attention', 'revisar', 'review']
        
        for keyword in high_priority_keywords:
            if keyword in subject or keyword in text:
                return "high"
        
        for keyword in medium_priority_keywords:
            if keyword in subject or keyword in text:
                return "medium"
        
        return "normal"
    
    def _estimate_category(self, email_data: Dict) -> str:
        """Estima a categoria do email"""
        subject = email_data.get('subject', '').lower()
        from_address = str(email_data.get('from', {})).lower()
        
        # Categorias baseadas em padrões
        if any(word in subject for word in ['pedido', 'order', 'compra', 'purchase']):
            return "purchase"
        elif any(word in subject for word in ['suporte', 'support', 'ajuda', 'help']):
            return "support"
        elif any(word in subject for word in ['notificação', 'notification', 'alerta', 'alert']):
            return "notification"
        elif any(word in from_address for word in ['noreply', 'no-reply', 'donotreply']):
            return "notification"
        elif any(word in subject for word in ['spam', 'promoção', 'promotion', 'marketing']):
            return "marketing"
        
        return "general"
    
    async def get_email_context(self, email_id: str) -> Optional[MCPContext]:
        """Obtém contexto de conversa para um email"""
        try:
            # Buscar email
            all_emails = await self.email_receiver.get_received_emails(limit=1000, offset=0)
            target_email = None
            
            for email in all_emails:
                if email.get('id') == email_id:
                    target_email = email
                    break
            
            if not target_email:
                return None
            
            # Buscar emails relacionados (mesmo remetente, assunto similar)
            from_address = target_email.get('from', {}).get('address', '')
            subject = target_email.get('subject', '')
            
            related_emails = []
            participants = set()
            
            for email in all_emails:
                if email.get('from', {}).get('address') == from_address:
                    related_emails.append(email.get('id'))
                    participants.add(from_address)
                
                # Adicionar destinatários
                to_info = email.get('to', [])
                if isinstance(to_info, list):
                    for recipient in to_info:
                        if isinstance(recipient, dict):
                            participants.add(recipient.get('address', ''))
                        else:
                            participants.add(str(recipient))
            
            # Determinar tópico principal
            topic = self._extract_main_topic(subject)
            
            # Estimar sentimento e urgência
            sentiment = self._estimate_sentiment(target_email)
            urgency = self._estimate_urgency(target_email)
            
            return MCPContext(
                conversation_id=f"conv_{email_id}",
                email_thread=related_emails,
                participants=list(participants),
                topic=topic,
                sentiment=sentiment,
                urgency=urgency,
                last_activity=target_email.get('received_at', '')
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto: {e}")
            return None
    
    def _extract_main_topic(self, subject: str) -> str:
        """Extrai o tópico principal do assunto"""
        # Implementação simples - pode ser melhorada com NLP
        subject_lower = subject.lower()
        
        if any(word in subject_lower for word in ['pedido', 'order']):
            return "Pedidos e Compras"
        elif any(word in subject_lower for word in ['suporte', 'support']):
            return "Suporte Técnico"
        elif any(word in subject_lower for word in ['reunião', 'meeting']):
            return "Agendamento"
        elif any(word in subject_lower for word in ['relatório', 'report']):
            return "Relatórios"
        
        return "Geral"
    
    def _estimate_sentiment(self, email_data: Dict) -> str:
        """Estima o sentimento do email"""
        text = email_data.get('text', '').lower()
        subject = email_data.get('subject', '').lower()
        
        positive_words = ['obrigado', 'thanks', 'excelente', 'excellent', 'ótimo', 'great', 'bom', 'good']
        negative_words = ['problema', 'problem', 'erro', 'error', 'ruim', 'bad', 'péssimo', 'terrible']
        
        positive_count = sum(1 for word in positive_words if word in text or word in subject)
        negative_count = sum(1 for word in negative_words if word in text or word in subject)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _estimate_urgency(self, email_data: Dict) -> str:
        """Estima a urgência do email"""
        priority = self._estimate_priority(email_data)
        
        if priority == "high":
            return "high"
        elif priority == "medium":
            return "medium"
        else:
            return "low"

# Instância global do sistema MCP
mcp_system: Optional[MCPEmailSystem] = None

def init_mcp_system(email_receiver: EmailReceiver):
    """Inicializa o sistema MCP"""
    global mcp_system
    mcp_system = MCPEmailSystem(email_receiver)
    logger.info("Sistema MCP inicializado com sucesso")

# Endpoints MCP
@mcp_router.get("/emails", response_model=List[MCPEmailSummary])
async def mcp_get_emails(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Lista emails normalizados para LLMs
    Interface otimizada para modelos de linguagem
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        # Buscar emails
        emails = await mcp_system.email_receiver.get_received_emails(limit=limit, offset=offset)
        
        # Normalizar para formato LLM
        normalized_emails = []
        for email in emails:
            try:
                normalized = mcp_system.normalize_email_for_llm(email)
                
                # Filtrar por categoria se especificado
                if category and normalized.category != category:
                    continue
                
                # Filtrar por prioridade se especificado
                if priority and normalized.priority != priority:
                    continue
                
                normalized_emails.append(normalized)
            except Exception as e:
                logger.error(f"Erro ao normalizar email {email.get('id')}: {e}")
                continue
        
        return normalized_emails
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar emails: {str(e)}")

@mcp_router.get("/emails/{email_id}", response_model=MCPEmailDetail)
async def mcp_get_email_detail(
    email_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Obtém detalhes completos de um email para LLMs
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        # Buscar email específico
        all_emails = await mcp_system.email_receiver.get_received_emails(limit=1000, offset=0)
        
        for email in all_emails:
            if email.get('id') == email_id:
                # Normalizar para formato detalhado
                from_info = email.get('from', {})
                to_info = email.get('to', [])
                
                to_addresses = []
                if isinstance(to_info, list):
                    for recipient in to_info:
                        if isinstance(recipient, dict):
                            to_addresses.append(recipient.get('address', ''))
                        else:
                            to_addresses.append(str(recipient))
                
                return MCPEmailDetail(
                    id=email.get('id', ''),
                    subject=email.get('subject', 'Sem assunto'),
                    from_address=from_info.get('address', ''),
                    from_name=from_info.get('name'),
                    to_addresses=to_addresses,
                    received_at=email.get('received_at', ''),
                    text_content=email.get('text'),
                    html_content=email.get('html'),
                    attachments=email.get('attachments', []),
                    metadata={
                        "processed_at": email.get('processed_at'),
                        "has_attachments": len(email.get('attachments', [])) > 0,
                        "content_length": len(email.get('text', '') + email.get('html', ''))
                    }
                )
        
        raise HTTPException(status_code=404, detail="Email não encontrado")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar email: {str(e)}")

@mcp_router.get("/emails/{email_id}/context", response_model=MCPContext)
async def mcp_get_email_context(
    email_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Obtém contexto de conversa para um email
    Útil para LLMs entenderem o histórico da conversa
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        context = await mcp_system.get_email_context(email_id)
        if not context:
            raise HTTPException(status_code=404, detail="Contexto não encontrado")
        
        return context
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter contexto: {str(e)}")

@mcp_router.post("/emails/{email_id}/respond", response_model=MCPResponse)
async def mcp_respond_to_email(
    email_id: str,
    response_data: Dict[str, Any],
    api_key: str = Depends(get_api_key)
):
    """
    Gera resposta automática para um email
    Interface para LLMs responderem automaticamente
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        # Validar dados da resposta
        response_type = response_data.get('response_type', 'auto_reply')
        content = response_data.get('content', '')
        confidence = response_data.get('confidence', 0.8)
        reasoning = response_data.get('reasoning', 'Resposta gerada automaticamente')
        
        if not content:
            raise HTTPException(status_code=400, detail="Conteúdo da resposta é obrigatório")
        
        # Aqui você implementaria a lógica de resposta automática
        # Por enquanto, retornamos uma resposta simulada
        
        actions = []
        if response_type == 'auto_reply':
            actions.append("Resposta automática gerada")
        elif response_type == 'forward':
            actions.append("Email encaminhado")
        elif response_type == 'archive':
            actions.append("Email arquivado")
        elif response_type == 'flag':
            actions.append("Email marcado como importante")
        
        return MCPResponse(
            email_id=email_id,
            response_type=response_type,
            content=content,
            actions=actions,
            confidence=confidence,
            reasoning=reasoning
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resposta: {str(e)}")

@mcp_router.post("/workflow", response_model=MCPWorkflow)
async def mcp_create_workflow(
    workflow_data: Dict[str, Any],
    api_key: str = Depends(get_api_key)
):
    """
    Cria um workflow automatizado baseado em regras
    Interface para LLMs criarem automações
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        # Validar dados do workflow
        trigger_email_id = workflow_data.get('trigger_email_id')
        workflow_type = workflow_data.get('workflow_type', 'auto_reply')
        conditions = workflow_data.get('conditions', [])
        actions = workflow_data.get('actions', [])
        
        if not trigger_email_id:
            raise HTTPException(status_code=400, detail="ID do email disparador é obrigatório")
        
        # Criar workflow
        workflow = MCPWorkflow(
            workflow_id=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            trigger_email_id=trigger_email_id,
            workflow_type=workflow_type,
            conditions=conditions,
            actions=actions,
            status="pending",
            created_at=datetime.now().isoformat()
        )
        
        # Aqui você implementaria a lógica de execução do workflow
        # Por enquanto, retornamos o workflow criado
        
        return workflow
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar workflow: {str(e)}")

@mcp_router.get("/search", response_model=List[MCPEmailSummary])
async def mcp_search_emails(
    query: str,
    limit: int = 50,
    api_key: str = Depends(get_api_key)
):
    """
    Busca emails com interface otimizada para LLMs
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        # Buscar emails
        emails = await mcp_system.email_receiver.search_received_emails(query)
        
        # Normalizar e limitar resultados
        normalized_emails = []
        for email in emails[:limit]:
            try:
                normalized = mcp_system.normalize_email_for_llm(email)
                normalized_emails.append(normalized)
            except Exception as e:
                logger.error(f"Erro ao normalizar email {email.get('id')}: {e}")
                continue
        
        return normalized_emails
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")

@mcp_router.get("/statistics")
async def mcp_get_statistics(
    api_key: str = Depends(get_api_key)
):
    """
    Estatísticas do sistema para LLMs
    """
    if not mcp_system:
        raise HTTPException(status_code=503, detail="Sistema MCP não está disponível")
    
    try:
        stats = mcp_system.email_receiver.get_statistics()
        
        # Adicionar estatísticas específicas para MCP
        mcp_stats = {
            **stats,
            "mcp_endpoints_available": [
                "/mcp/emails",
                "/mcp/emails/{id}",
                "/mcp/emails/{id}/context",
                "/mcp/emails/{id}/respond",
                "/mcp/workflow",
                "/mcp/search"
            ],
            "llm_optimized": True,
            "normalized_data": True,
            "context_aware": True
        }
        
        return mcp_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")
