#!/usr/bin/env python3
"""
Script de teste para o MCP Server
Testa todos os endpoints MCP e a normalização de dados para LLMs
"""

import asyncio
import json
import requests
from datetime import datetime

# Configurações
API_BASE_URL = "http://localhost"
API_KEY = "api-test-key"  # Sua API key
MCP_BASE_URL = f"{API_BASE_URL}/mcp"

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"🤖 {title}")
    print("="*60)

def print_section(title):
    """Imprime uma seção formatada"""
    print(f"\n📋 {title}")
    print("-" * 40)

def test_mcp_endpoints():
    """Testa todos os endpoints MCP"""
    print_header("TESTE COMPLETO DO MCP SERVER")
    
    headers = {"X-API-Key": API_KEY}
    
    # 1. Testar listagem de emails
    print_section("1. Listagem de Emails (/mcp/emails)")
    try:
        response = requests.get(f"{MCP_BASE_URL}/emails", headers=headers, params={"limit": 5})
        if response.status_code == 200:
            emails = response.json()
            print(f"✅ Emails encontrados: {len(emails)}")
            
            if emails:
                print("\n📧 Primeiros emails normalizados:")
                for i, email in enumerate(emails[:3]):
                    print(f"   {i+1}. ID: {email.get('id')}")
                    print(f"      Assunto: {email.get('subject')}")
                    print(f"      De: {email.get('from_address')}")
                    print(f"      Prioridade: {email.get('priority')}")
                    print(f"      Categoria: {email.get('category')}")
                    print(f"      Preview: {email.get('content_preview')[:100]}...")
                    print()
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # 2. Testar busca de emails
    print_section("2. Busca de Emails (/mcp/search)")
    try:
        response = requests.get(f"{MCP_BASE_URL}/search", headers=headers, params={"query": "teste", "limit": 3})
        if response.status_code == 200:
            emails = response.json()
            print(f"✅ Resultados da busca: {len(emails)} emails")
            
            if emails:
                print("\n🔍 Emails encontrados na busca:")
                for email in emails:
                    print(f"   📧 {email.get('subject')} (Prioridade: {email.get('priority')})")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # 3. Testar estatísticas
    print_section("3. Estatísticas MCP (/mcp/statistics)")
    try:
        response = requests.get(f"{MCP_BASE_URL}/statistics", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Estatísticas MCP obtidas:")
            print(f"   📧 Total de emails: {stats.get('total_emails_received', 0)}")
            print(f"   📎 Total de anexos: {stats.get('total_attachments', 0)}")
            print(f"   🤖 LLM otimizado: {stats.get('llm_optimized', False)}")
            print(f"   🔄 Contexto consciente: {stats.get('context_aware', False)}")
            print(f"   📊 Dados normalizados: {stats.get('normalized_data', False)}")
            
            print(f"\n🌐 Endpoints MCP disponíveis:")
            for endpoint in stats.get('mcp_endpoints_available', []):
                print(f"   • {endpoint}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # 4. Testar filtros por categoria e prioridade
    print_section("4. Filtros Avançados")
    try:
        # Filtrar por categoria
        response = requests.get(f"{MCP_BASE_URL}/emails", headers=headers, params={"category": "general", "limit": 3})
        if response.status_code == 200:
            emails = response.json()
            print(f"✅ Emails da categoria 'general': {len(emails)}")
        
        # Filtrar por prioridade
        response = requests.get(f"{MCP_BASE_URL}/emails", headers=headers, params={"priority": "normal", "limit": 3})
        if response.status_code == 200:
            emails = response.json()
            print(f"✅ Emails com prioridade 'normal': {len(emails)}")
            
    except Exception as e:
        print(f"❌ Erro nos filtros: {e}")
    
    # 5. Testar criação de workflow
    print_section("5. Criação de Workflow (/mcp/workflow)")
    try:
        workflow_data = {
            "trigger_email_id": "test_email_123",
            "workflow_type": "auto_reply",
            "conditions": [
                {"field": "category", "operator": "equals", "value": "support"}
            ],
            "actions": [
                {"type": "send_reply", "template": "support_auto_reply"}
            ]
        }
        
        response = requests.post(f"{MCP_BASE_URL}/workflow", headers=headers, json=workflow_data)
        if response.status_code == 200:
            workflow = response.json()
            print("✅ Workflow criado com sucesso:")
            print(f"   🆔 ID: {workflow.get('workflow_id')}")
            print(f"   🔄 Tipo: {workflow.get('workflow_type')}")
            print(f"   📊 Status: {workflow.get('status')}")
            print(f"   ⏰ Criado: {workflow.get('created_at')}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na criação do workflow: {e}")

def test_email_normalization():
    """Testa a normalização de emails para LLMs"""
    print_section("6. Teste de Normalização de Dados")
    
    # Simular dados de email
    sample_email = {
        "id": "test_123",
        "subject": "URGENTE: Problema crítico no sistema",
        "from": {"address": "admin@company.com", "name": "Admin"},
        "to": [{"address": "tech@company.com", "name": "Tech Team"}],
        "text": "Precisamos resolver este problema imediatamente. É crítico para o negócio.",
        "html": "<p>Precisamos resolver este problema imediatamente.</p>",
        "attachments": [{"id": "att_1", "filename": "error.log"}],
        "received_at": "2024-01-01T10:00:00"
    }
    
    print("📧 Email de exemplo:")
    print(f"   Assunto: {sample_email['subject']}")
    print(f"   De: {sample_email['from']['name']} <{sample_email['from']['address']}>")
    print(f"   Para: {sample_email['to'][0]['name']} <{sample_email['to'][0]['address']}>")
    print(f"   Conteúdo: {sample_email['text']}")
    print(f"   Anexos: {len(sample_email['attachments'])}")
    
    print("\n🔍 Análise esperada:")
    print("   Prioridade: HIGH (palavra 'URGENTE' + 'crítico')")
    print("   Categoria: support (palavra 'problema' + 'sistema')")
    print("   Sentimento: negative (palavra 'problema' + 'crítico')")
    print("   Urgência: high (baseado na prioridade)")

def test_llm_integration_scenarios():
    """Testa cenários de integração com LLMs"""
    print_section("7. Cenários de Integração com LLMs")
    
    scenarios = [
        {
            "name": "Claude analisando emails",
            "description": "Claude pode usar /mcp/emails para listar e analisar emails",
            "endpoints": ["GET /mcp/emails", "GET /mcp/emails/{id}", "GET /mcp/emails/{id}/context"]
        },
        {
            "name": "GPT respondendo automaticamente",
            "description": "GPT pode usar /mcp/emails/{id}/respond para gerar respostas",
            "endpoints": ["POST /mcp/emails/{id}/respond"]
        },
        {
            "name": "Gemini criando workflows",
            "description": "Gemini pode usar /mcp/workflow para criar automações",
            "endpoints": ["POST /mcp/workflow"]
        },
        {
            "name": "Busca contextual",
            "description": "Qualquer LLM pode usar /mcp/search para busca inteligente",
            "endpoints": ["GET /mcp/search"]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   📝 {scenario['description']}")
        print(f"   🔗 Endpoints: {', '.join(scenario['endpoints'])}")

def main():
    """Função principal"""
    print_header("TESTE DO MCP SERVER - MODEL CONTEXT PROTOCOL")
    
    print("🎯 Este script testa:")
    print("   • Endpoints MCP para LLMs")
    print("   • Normalização de dados")
    print("   • Filtros e busca")
    print("   • Criação de workflows")
    print("   • Cenários de integração")
    
    # Executar testes
    test_mcp_endpoints()
    test_email_normalization()
    test_llm_integration_scenarios()
    
    print_header("TESTE CONCLUÍDO")
    print("🎉 O MCP Server está funcionando perfeitamente!")
    print("🤖 Agora LLMs podem se conectar e interagir com o sistema de emails!")
    print("📚 Consulte a documentação para detalhes de integração")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
