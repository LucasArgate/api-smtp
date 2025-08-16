import json
import asyncio
import aiohttp
import smtplib
from datetime import datetime
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
import mimetypes
import os
from minio import Minio
from minio.error import S3Error
import uuid
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailReceiver:
    """
    Classe para receber e processar emails do MailDev
    """
    
    def __init__(self, smtp_config: dict):
        self.smtp_config = smtp_config
        self.maildev_web_port = 1080
        self.maildev_smtp_port = 1025
        
        # Inicializar cliente MinIO
        self.minio_client = Minio(
            smtp_config.get('minio_server', "localhost:9000"),
            access_key=smtp_config.get('minio_access_key', "minioadmin"),
            secret_key=smtp_config.get('minio_secret_key', "minioadmin"),
            secure=smtp_config.get('minio_secure', False),
        )
        
        # Criar bucket para emails recebidos se não existir
        self._ensure_bucket_exists("received_emails")
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """Garante que o bucket MinIO existe"""
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar bucket '{bucket_name}': {e}")
    
    async def listen_for_emails(self, callback=None):
        """
        Escuta por novos emails no MailDev via polling
        """
        logger.info("Iniciando listener de emails do MailDev...")
        
        while True:
            try:
                # Buscar emails não lidos
                unread_emails = await self.get_unread_emails()
                
                for email in unread_emails:
                    logger.info(f"Processando email: {email.get('id', 'unknown')}")
                    
                    # Processar email
                    processed_email = await self.process_received_email(email)
                    
                    # Chamar callback se fornecido
                    if callback and callable(callback):
                        await callback(processed_email)
                    
                    # Marcar como lido
                    await self.mark_email_as_read(email['id'])
                
                # Aguardar antes da próxima verificação
                await asyncio.sleep(30)  # Verificar a cada 30 segundos
                
            except Exception as e:
                logger.error(f"Erro no listener de emails: {e}")
                await asyncio.sleep(60)  # Aguardar mais tempo em caso de erro
    
    async def get_unread_emails(self) -> List[Dict]:
        """Busca emails não lidos do MailDev"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:{self.maildev_web_port}/api/mails"
                async with session.get(url) as response:
                    if response.status == 200:
                        emails = await response.json()
                        # Filtrar apenas emails não lidos
                        unread_emails = [email for email in emails if not email.get('read', False)]
                        return unread_emails
                    else:
                        logger.error(f"Erro ao buscar emails: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Erro ao buscar emails não lidos: {e}")
            return []
    
    async def get_email_content(self, email_id: str) -> Optional[Dict]:
        """Busca o conteúdo completo de um email específico"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:{self.maildev_web_port}/api/mail/{email_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Erro ao buscar email {email_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo do email {email_id}: {e}")
            return None
    
    async def mark_email_as_read(self, email_id: str):
        """Marca um email como lido no MailDev"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:{self.maildev_web_port}/api/mail/{email_id}/read"
                async with session.post(url) as response:
                    if response.status == 200:
                        logger.info(f"Email {email_id} marcado como lido")
                    else:
                        logger.error(f"Erro ao marcar email {email_id} como lido: {response.status}")
        except Exception as e:
            logger.error(f"Erro ao marcar email {email_id} como lido: {e}")
    
    async def process_received_email(self, email_data: Dict) -> Dict:
        """Processa um email recebido"""
        try:
            # Buscar conteúdo completo do email
            full_email = await self.get_email_content(email_data['id'])
            if not full_email:
                return {"error": "Não foi possível obter conteúdo do email"}
            
            # Extrair informações do email
            processed_email = {
                "id": email_data['id'],
                "from": full_email.get('from', {}),
                "to": full_email.get('to', []),
                "subject": full_email.get('subject', ''),
                "text": full_email.get('text', ''),
                "html": full_email.get('html', ''),
                "attachments": full_email.get('attachments', []),
                "received_at": full_email.get('time', datetime.now().isoformat()),
                "processed_at": datetime.now().isoformat()
            }
            
            # Salvar email processado
            await self.save_received_email(processed_email)
            
            # Processar anexos se houver
            if processed_email['attachments']:
                await self.process_attachments(processed_email['id'], processed_email['attachments'])
            
            logger.info(f"Email {email_data['id']} processado com sucesso")
            return processed_email
            
        except Exception as e:
            logger.error(f"Erro ao processar email {email_data.get('id', 'unknown')}: {e}")
            return {"error": str(e)}
    
    async def save_received_email(self, email_data: Dict):
        """Salva email recebido no MinIO"""
        try:
            email_id = email_data['id']
            bucket_name = "received_emails"
            
            # Criar nome único para o arquivo
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            object_name = f"{timestamp}_{email_id}_email.json"
            
            # Converter para JSON
            email_json = json.dumps(email_data, indent=2, ensure_ascii=False)
            
            # Salvar no MinIO
            self.minio_client.put_object(
                bucket_name,
                object_name,
                email_json.encode('utf-8'),
                length=len(email_json.encode('utf-8')),
                content_type="application/json"
            )
            
            logger.info(f"Email salvo no MinIO: {object_name}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar email no MinIO: {e}")
    
    async def process_attachments(self, email_id: str, attachments: List[Dict]):
        """Processa anexos do email recebido"""
        try:
            bucket_name = "received_emails"
            
            for attachment in attachments:
                try:
                    # Buscar conteúdo do anexo
                    attachment_content = await self.download_attachment(email_id, attachment['id'])
                    if attachment_content:
                        # Salvar anexo no MinIO
                        object_name = f"{email_id}_{attachment['id']}_{attachment['filename']}"
                        
                        self.minio_client.put_object(
                            bucket_name,
                            object_name,
                            attachment_content,
                            length=len(attachment_content),
                            content_type=attachment.get('contentType', 'application/octet-stream')
                        )
                        
                        logger.info(f"Anexo salvo: {object_name}")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar anexo {attachment.get('filename', 'unknown')}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao processar anexos do email {email_id}: {e}")
    
    async def download_attachment(self, email_id: str, attachment_id: str) -> Optional[bytes]:
        """Download de um anexo específico"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:{self.maildev_web_port}/api/mail/{email_id}/attachment/{attachment_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Erro ao baixar anexo {attachment_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Erro ao baixar anexo {attachment_id}: {e}")
            return None
    
    async def get_received_emails(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Lista emails recebidos armazenados"""
        try:
            bucket_name = "received_emails"
            objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
            
            emails = []
            for obj in objects[offset:offset + limit]:
                try:
                    response = self.minio_client.get_object(bucket_name, obj.object_name)
                    email_data = json.loads(response.read().decode('utf-8'))
                    emails.append(email_data)
                except Exception as e:
                    logger.error(f"Erro ao ler email {obj.object_name}: {e}")
            
            return emails
            
        except Exception as e:
            logger.error(f"Erro ao listar emails recebidos: {e}")
            return []
    
    async def search_received_emails(self, query: str) -> List[Dict]:
        """Busca emails recebidos por texto"""
        try:
            all_emails = await self.get_received_emails(limit=1000, offset=0)
            
            matching_emails = []
            query_lower = query.lower()
            
            for email in all_emails:
                # Buscar no assunto, remetente, destinatário e corpo
                if (query_lower in email.get('subject', '').lower() or
                    query_lower in str(email.get('from', {})).lower() or
                    query_lower in str(email.get('to', [])).lower() or
                    query_lower in email.get('text', '').lower() or
                    query_lower in email.get('html', '').lower()):
                    matching_emails.append(email)
            
            return matching_emails
            
        except Exception as e:
            logger.error(f"Erro na busca de emails: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas dos emails recebidos"""
        try:
            bucket_name = "received_emails"
            objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
            
            total_emails = len([obj for obj in objects if obj.object_name.endswith('_email.json')])
            total_attachments = len([obj for obj in objects if not obj.object_name.endswith('_email.json')])
            
            return {
                "total_emails_received": total_emails,
                "total_attachments": total_attachments,
                "bucket_size_bytes": sum(obj.size for obj in objects),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}

# Função para iniciar o receiver como tarefa em background
async def start_email_receiver(smtp_config: dict, callback=None):
    """Inicia o email receiver em background"""
    receiver = EmailReceiver(smtp_config)
    
    # Iniciar listener em background
    asyncio.create_task(receiver.listen_for_emails(callback))
    
    logger.info("Email receiver iniciado com sucesso")
    return receiver
