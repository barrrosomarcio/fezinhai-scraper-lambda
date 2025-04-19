import os
from dotenv import load_dotenv
from handler import handler
from aws_lambda_powertools.utilities.typing import LambdaContext
from dataclasses import dataclass

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Mock do LambdaContext
@dataclass
class MockContext:
    function_name: str = "fezinhai-scraper-local"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "local"
    aws_request_id: str = "local"

def test_scraper():
    # Verifica se as variáveis de ambiente necessárias estão configuradas
    required_vars = ['API_URL', 'LOTOFACIL_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Erro: Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("Por favor, configure as variáveis no arquivo .env")
        return
    
    print("🔍 Iniciando teste do scraper...")
    
    try:
        # Simula o evento da API Gateway
        event = {
            "requestContext": {
                "requestId": "test-request-id"
            }
        }
        
        # Executa o handler
        result = handler(event, MockContext())
        
        # Verifica o resultado
        if result['statusCode'] == 200:
            data = eval(result['body'])  # Converte a string JSON para dict
            print(f"\n✅ Sucesso! Processados {data['recordsProcessed']} registros")
        else:
            print(f"\n❌ Erro: {result['body']}")
            
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    test_scraper() 