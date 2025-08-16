#!/usr/bin/env python3
"""
Script de teste para o Email Receiver
Demonstra como usar a classe EmailReceiver independentemente da API FastAPI
"""

import asyncio
import json
import sys
import os

# Adicionar o diretório atual ao path para importar o módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_receiver import EmailReceiver

async def test_email_receiver():
    """Testa o email receiver"""
    
    # Carregar configuração
    try:
        with open('smtp_config.json', 'r') as f:
            smtp_config = json.load(f)
    except FileNotFoundError:
        print("❌ Arquivo smtp_config.json não encontrado!")
        return
    
    print("🚀 Iniciando teste do Email Receiver...")
    
    # Criar instância do receiver
    receiver = EmailReceiver(smtp_config)
    
    try:
        # Testar conexão com MinIO
        print("📦 Testando conexão com MinIO...")
        buckets = list(receiver.minio_client.list_buckets())
        print(f"✅ Conectado ao MinIO. Buckets disponíveis: {[b.name for b in buckets]}")
        
        # Testar busca de emails
        print("📧 Testando busca de emails...")
        unread_emails = await receiver.get_unread_emails()
        print(f"📊 Emails não lidos encontrados: {len(unread_emails)}")
        
        if unread_emails:
            print("📋 Primeiros emails:")
            for i, email in enumerate(unread_emails[:3]):
                print(f"  {i+1}. ID: {email.get('id')} | Assunto: {email.get('subject', 'Sem assunto')}")
        
        # Testar estatísticas
        print("📊 Testando estatísticas...")
        stats = receiver.get_statistics()
        print(f"📈 Estatísticas: {json.dumps(stats, indent=2)}")
        
        # Testar busca
        print("🔍 Testando busca...")
        search_results = await receiver.search_received_emails("test")
        print(f"🔎 Resultados da busca por 'test': {len(search_results)} emails")
        
        print("\n✅ Todos os testes passaram!")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

async def test_listener():
    """Testa o listener de emails em tempo real"""
    
    print("\n🎧 Testando listener de emails em tempo real...")
    print("⚠️  Pressione Ctrl+C para parar")
    
    try:
        with open('smtp_config.json', 'r') as f:
            smtp_config = json.load(f)
        
        receiver = EmailReceiver(smtp_config)
        
        # Callback simples para mostrar emails recebidos
        async def email_callback(email_data):
            print(f"\n📧 NOVO EMAIL RECEBIDO!")
            print(f"   De: {email_data.get('from', {}).get('address', 'Desconhecido')}")
            print(f"   Assunto: {email_data.get('subject', 'Sem assunto')}")
            print(f"   ID: {email_data.get('id')}")
            print(f"   Timestamp: {email_data.get('received_at')}")
        
        # Iniciar listener
        await receiver.listen_for_emails(email_callback)
        
    except KeyboardInterrupt:
        print("\n🛑 Listener interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro no listener: {e}")

def main():
    """Função principal"""
    print("🧪 TESTE DO EMAIL RECEIVER")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--listen":
        # Modo listener
        asyncio.run(test_listener())
    else:
        # Modo teste básico
        asyncio.run(test_email_receiver())

if __name__ == "__main__":
    main()
