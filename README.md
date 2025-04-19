# FezinhAI Scraper Lambda

AWS Lambda function para raspar resultados da Lotofácil do site da Caixa, processá-los e enviar para a API do FezinhAI.

## Funcionalidades

- Coleta resultados da Lotofácil do site oficial da Caixa Econômica Federal
- Baixa e processa o arquivo Excel com todos os resultados
- Converte os dados para o formato JSON compatível com a API
- Verifica quais concursos são novos consultando a API
- Envia apenas os resultados novos para a API em lotes
- Autenticação automática na API para obtenção de token

## Configuração

### Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure as seguintes variáveis:

```bash
# API Configuration
API_URL=https://api.seu-dominio.com
API_EMAIL=seu-email@exemplo.com
API_PASSWORD=sua-senha

# Scraping Configuration
LOTOFACIL_URL=https://url-do-site-da-lotofacil.com
```

### Instalação de Dependências

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Requisitos

- Python 3.9 ou superior
- Google Chrome instalado (necessário para o Selenium)
- Conexão com a internet para acessar o site da Lotofácil e a API

## Fluxo de Execução

1. **Autenticação**: Faz login na API para obter o token de acesso
2. **Consulta de Concursos**: Verifica qual é o último concurso salvo na API
3. **Coleta de Dados**: Baixa o arquivo Excel com todos os resultados da Lotofácil
4. **Filtragem**: Filtra apenas os concursos mais recentes que não existem na API
5. **Processamento**: Converte os dados do Excel para o formato JSON
6. **Envio**: Envia os resultados para a API em lotes de 100 concursos

## Implantação na AWS Lambda

1. Instale as dependências no diretório raiz:
   ```bash
   pip install -r requirements.txt -t .
   ```

2. Crie um arquivo ZIP com todo o conteúdo do diretório:
   ```bash
   zip -r lambda_function.zip .
   ```

3. Faça upload do arquivo ZIP para o AWS Lambda

4. Configure as variáveis de ambiente no console do Lambda

5. Defina o handler como `handler.handler`

6. Configure um timeout adequado (recomendado: 3-5 minutos)

7. Configure a memória (recomendado: 1024MB ou mais)

8. Configure um evento de gatilho (CloudWatch Events, EventBridge, etc.)

## Testes Locais

Para testar localmente, você pode criar um arquivo `test.py`:

```python
from handler import handler
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

# Simula um evento do API Gateway
event = APIGatewayProxyEvent({
    "httpMethod": "GET",
    "path": "/scrape",
    "headers": {},
    "queryStringParameters": {}
})

# Simula o contexto do Lambda
context = LambdaContext()

# Executa a função handler
result = handler(event, context)
print(result)
```

## Solução de Problemas

- **Erro ao baixar o arquivo**: Verifique se o LOTOFACIL_URL está correto e se o botão de download no site tem o ID "btnResultados"
- **Erro na autenticação**: Verifique se as credenciais de API_EMAIL e API_PASSWORD estão corretas
- **Erro ao processar o Excel**: Verifique se o formato do Excel mudou, os nomes das colunas podem variar
- **Erro 413 ao enviar os dados**: A função já divide os dados em lotes para evitar este erro

## Manutenção

- **Alterações no formato do Excel**: Se a Caixa alterar o formato do arquivo Excel, será necessário atualizar o código em `mapper.py`
- **Alterações na API**: Se os endpoints da API mudarem, atualize as URLs em `handler.py`