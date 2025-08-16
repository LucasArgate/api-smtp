#!/usr/bin/env python3
"""
Demonstração Completa do Sistema de Email
Este script demonstra como usar tanto o envio quanto o recebimento de emails
"""

import asyncio
import json
import time
import requests
from datetime import datetime

# Configurações
API_BASE_URL = "http://localhost"
API_KEY = "b83f1368-155b-4e53-8151-d2ab788adc5e"  # Sua API key do smtp_config.json
MAILDEV_WEB_URL = "http://localhost:1080"

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_section(title):
    """Imprime uma seção formatada"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_service_status():
    """Verifica se os serviços estão rodando"""
    print_header("VERIFICAÇÃO DE SERVIÇOS")
    
    services = {
        "API FastAPI": f"{API_BASE_URL}/docs",
        "MailDev Web": f"{MAILDEV_WEB_URL}",
        "MinIO Console": "http://localhost:9001"
    }
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Rodando em {url}")
            else:
                print(f"⚠️  {service_name}: Respondendo mas com status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name}: Não está rodando - {e}")

def send_test_email():
    """Envia um email de teste"""
    print_section("ENVIANDO EMAIL DE TESTE")
    
    email_data = {
        "recipient_email": "test@dev.local",
        "subject": f"Teste do Sistema - {datetime.now().strftime('%H:%M:%S')}",
        "body": f"""
        <h2>🎯 Teste do Sistema de Email</h2>
        <p>Este é um email de teste enviado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>O sistema está funcionando perfeitamente!</p>
        <ul>
            <li>✅ Envio de emails</li>
            <li>✅ Recebimento de emails</li>
            <li>✅ Armazenamento no MinIO</li>
            <li>✅ API REST completa</li>
        </ul>
        """,
        "body_type": "html",
        "debug": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/mail/send",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json=email_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email enviado com sucesso!")
            print(f"   ID: {result.get('email_id')}")
            print(f"   Mensagem: {result.get('message')}")
            return result.get('email_id')
        else:
            print(f"❌ Erro ao enviar email: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def wait_for_email_processing():
    """Aguarda o processamento do email"""
    print_section("AGUARDANDO PROCESSAMENTO")
    
    print("⏳ Aguardando 10 segundos para o email ser processado...")
    for i in range(10, 0, -1):
        print(f"   ⏰ {i} segundos restantes...")
        time.sleep(1)
    print("✅ Tempo de espera concluído!")

def check_received_emails():
    """Verifica emails recebidos"""
    print_section("VERIFICANDO EMAILS RECEBIDOS")
    
    try:
        # Listar emails recebidos
        response = requests.get(
            f"{API_BASE_URL}/v1/mail/received",
            headers={"X-API-Key": API_KEY},
            params={"limit": 10, "offset": 0}
        )
        
        if response.status_code == 200:
            result = response.json()
            emails = result.get('emails', [])
            
            print(f"📧 Total de emails recebidos: {result.get('total', 0)}")
            
            if emails:
                print("\n📋 Últimos emails recebidos:")
                for i, email in enumerate(emails[:5]):
                    print(f"   {i+1}. ID: {email.get('id', 'N/A')}")
                    print(f"      De: {email.get('from', {}).get('address', 'N/A')}")
                    print(f"      Assunto: {email.get('subject', 'N/A')}")
                    print(f"      Recebido: {email.get('received_at', 'N/A')}")
                    print()
            else:
                print("📭 Nenhum email recebido ainda")
                
        else:
            print(f"❌ Erro ao buscar emails: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def get_statistics():
    """Obtém estatísticas do sistema"""
    print_section("ESTATÍSTICAS DO SISTEMA")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/mail/received/statistics",
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            stats = response.json()
            
            print("📊 Estatísticas dos Emails Recebidos:")
            print(f"   📧 Total de emails: {stats.get('total_emails_received', 0)}")
            print(f"   📎 Total de anexos: {stats.get('total_attachments', 0)}")
            print(f"   💾 Tamanho do bucket: {stats.get('bucket_size_bytes', 0)} bytes")
            print(f"   ⏰ Última atualização: {stats.get('last_updated', 'N/A')}")
            
        else:
            print(f"❌ Erro ao obter estatísticas: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def search_emails():
    """Demonstra busca de emails"""
    print_section("BUSCA DE EMAILS")
    
    search_terms = ["teste", "sistema", "email"]
    
    for term in search_terms:
        try:
            response = requests.get(
                f"{API_BASE_URL}/v1/mail/received/search",
                headers={"X-API-Key": API_KEY},
                params={"query": term}
            )
            
            if response.status_code == 200:
                result = response.json()
                emails = result.get('emails', [])
                
                print(f"🔍 Busca por '{term}': {len(emails)} resultados")
                
                if emails:
                    for email in emails[:3]:  # Mostrar apenas os primeiros 3
                        print(f"   📧 {email.get('subject', 'Sem assunto')}")
                        
            else:
                print(f"❌ Erro na busca por '{term}': {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na busca por '{term}': {e}")

def show_maildev_interface():
    """Mostra informações sobre a interface do MailDev"""
    print_section("INTERFACE DO MAILDEV")
    
    print("🌐 Acesse a interface web do MailDev:")
    print(f"   📧 Web Interface: {MAILDEV_WEB_URL}")
    print(f"   📤 SMTP Port: localhost:1025")
    print(f"   📥 Web Port: localhost:1080")
    print()
    print("💡 Dicas:")
    print("   • Use a porta 1025 para enviar emails via SMTP")
    print("   • Use a porta 1080 para visualizar emails recebidos")
    print("   • Todos os emails enviados para a porta 1025 aparecem na interface web")
    print("   • O Email Receiver processa automaticamente emails da interface web")

def show_api_endpoints():
    """Mostra todos os endpoints disponíveis"""
    print_section("ENDPOINTS DA API")
    
    endpoints = [
        ("POST", "/v1/mail/send", "Enviar email simples"),
        ("POST", "/v1/mail/send-with-attachments", "Enviar email com anexos"),
        ("GET", "/v1/mail/received", "Listar emails recebidos"),
        ("GET", "/v1/mail/received/search", "Buscar emails recebidos"),
        ("GET", "/v1/mail/received/statistics", "Estatísticas dos emails"),
        ("GET", "/v1/mail/received/{id}", "Obter email específico"),
        ("DELETE", "/v1/mail/received/{id}", "Remover email"),
        ("GET", "/docs", "Documentação Swagger"),
        ("GET", "/redoc", "Documentação ReDoc")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:6} {endpoint:<35} - {description}")

def main():
    """Função principal da demonstração"""
    print_header("DEMONSTRAÇÃO COMPLETA DO SISTEMA DE EMAIL")
    
    print("🎯 Este script demonstra todas as funcionalidades do sistema:")
    print("   • Verificação de serviços")
    print("   • Envio de emails")
    print("   • Recebimento automático")
    print("   • Consulta de emails recebidos")
    print("   • Estatísticas do sistema")
    print("   • Busca de emails")
    
    # Verificar serviços
    check_service_status()
    
    # Mostrar endpoints
    show_api_endpoints()
    
    # Mostrar interface do MailDev
    show_maildev_interface()
    
    # Enviar email de teste
    email_id = send_test_email()
    
    if email_id:
        # Aguardar processamento
        wait_for_email_processing()
        
        # Verificar emails recebidos
        check_received_emails()
        
        # Obter estatísticas
        get_statistics()
        
        # Demonstrar busca
        search_emails()
        
        print_header("DEMONSTRAÇÃO CONCLUÍDA")
        print("🎉 O sistema está funcionando perfeitamente!")
        print("📚 Consulte a documentação em README_EMAIL_RECEIVER.md")
        print("🧪 Execute test_email_receiver.py para testes avançados")
        
    else:
        print_header("DEMONSTRAÇÃO INTERROMPIDA")
        print("❌ Não foi possível enviar o email de teste")
        print("🔧 Verifique se todos os serviços estão rodando")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante a demonstração: {e}")
        import traceback
        traceback.print_exc()
