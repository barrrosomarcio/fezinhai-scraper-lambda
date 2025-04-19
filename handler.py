import json
import os
import tempfile
import time
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dataclasses import asdict
from dto import SaveResultsDto
from logger import logger, LambdaContext
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

tracer = Tracer(service="fezinhai-scraper")

def setup_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa em modo headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Configura o diretório de download
    download_dir = tempfile.mkdtemp()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    return chrome_options, download_dir

@tracer.capture_method
def fetch_excel_file() -> str:
    logger.info("Starting Excel file fetch from Lotofácil website")
    
    url = os.environ.get('LOTOFACIL_URL')
    if not url:
        logger.error("LOTOFACIL_URL environment variable not set")
        raise Exception("LOTOFACIL_URL environment variable not set")

    chrome_options, download_dir = setup_chrome_options()
    
    try:
        # Configura o serviço do Chrome com log de erro detalhado
        service = Service()
        service.creation_flags = 0x08000000  # No Window Flag
        
        logger.info("Initializing Chrome with webdriver_manager")
        driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        
        logger.info("Chrome initialized successfully")
        
        # Acessa a página
        driver.get(url)
        logger.info("Page loaded successfully")
        
        # Espera o botão ficar disponível e clica nele
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnResultados"))
        )
        button.click()
        logger.info("Download button clicked")
        
        # Espera o download completar (máximo 30 segundos)
        max_wait = 30
        while max_wait > 0:
            downloaded_files = os.listdir(download_dir)
            excel_files = [f for f in downloaded_files if f.endswith('.xlsx')]
            if excel_files:
                excel_path = os.path.join(download_dir, excel_files[0])
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                
                # Move o arquivo para o local temporário
                with open(excel_path, 'rb') as src, open(temp_file.name, 'wb') as dst:
                    dst.write(src.read())
                
                logger.info("Excel file downloaded successfully", temp_file=temp_file.name)
                return temp_file.name
            
            time.sleep(1)
            max_wait -= 1
        
        raise Exception("Download timeout exceeded")
        
    except Exception as e:
        logger.error("Error during file download", error=str(e))
        raise
    
    finally:
        try:
            driver.quit()
            # Limpa o diretório de download
            for file in os.listdir(download_dir):
                os.remove(os.path.join(download_dir, file))
            os.rmdir(download_dir)
        except Exception as cleanup_error:
            logger.warning("Error during cleanup", error=str(cleanup_error))

@tracer.capture_method
def get_last_contest() -> int:
    """
    Consulta a API para obter o número do último concurso salvo.
    Retorna 0 se não houver resultados (404) para importar todos os concursos.
    """
    logger.info("Getting last contest number from API")
    
    api_url = os.environ.get('API_URL')
    if not api_url:
        logger.error("API_URL environment variable not set")
        raise Exception("API_URL environment variable not set")

    # Obtém o token de acesso
    access_token = login_api()
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(f"{api_url}/lotofacil/last", headers=headers)
        
        # Se retornar 404, significa que não há resultados ainda
        if response.status_code == 404:
            logger.info("No results found in API (404), will import all contests")
            return 0
            
        response.raise_for_status()
        
        data = response.json()
        last_contest = data.get('concurso', 0)
        
        logger.info("Last contest number retrieved", last_contest=last_contest)
        return last_contest
        
    except requests.exceptions.RequestException as e:
        # Se não for 404, é um erro que precisa ser tratado
        logger.error("Failed to get last contest", error=str(e))
        raise Exception(f"Failed to get last contest: {str(e)}")

@tracer.capture_method
def map_excel_data(file_path: str) -> SaveResultsDto:
    logger.info("Starting Excel data mapping", file_path=file_path)
    
    # Obtém o último concurso da API
    last_contest = get_last_contest()
    logger.info("Filtering contests newer than", last_contest=last_contest)
    
    from mapper import map_excel_to_dto
    df = pd.read_excel(file_path)
    logger.info("Excel file loaded successfully", rows_count=len(df))
    
    # Filtra apenas os concursos mais recentes que o último
    df_filtered = df[df['Concurso'] > last_contest]
    new_contests_count = len(df_filtered)
    
    if new_contests_count == 0:
        logger.info("No new contests to process")
        return SaveResultsDto(results=[])
    
    logger.info("Found new contests to process", count=new_contests_count)
    results = map_excel_to_dto(df_filtered)
    logger.info("Data mapped to DTO successfully", results_count=len(results.results))
    
    os.unlink(file_path)
    logger.info("Temporary file deleted")
    
    return results

@tracer.capture_method
def login_api() -> str:
    """
    Faz login na API e retorna o token de acesso
    """
    logger.info("Starting API login")
    
    api_url = os.environ.get('API_URL')
    if not api_url:
        logger.error("API_URL environment variable not set")
        raise Exception("API_URL environment variable not set")

    email = os.environ.get('API_EMAIL')
    password = os.environ.get('API_PASSWORD')
    
    if not email or not password:
        logger.error("API credentials not set")
        raise Exception("API_EMAIL and API_PASSWORD environment variables must be set")

    login_url = f"{api_url}/auth/login"  # Ajuste o endpoint conforme necessário
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('accessToken')
        
        if not access_token:
            raise Exception("No access token in response")
            
        logger.info("Login successful")
        return access_token
        
    except requests.exceptions.RequestException as e:
        logger.error("Login failed", error=str(e))
        raise Exception(f"Failed to login: {str(e)}")

@tracer.capture_method
def send_to_api(data: SaveResultsDto) -> None:
    if not data.results:
        logger.info("No data to send to API")
        return
        
    logger.info("Starting API data submission", records_count=len(data.results))
    
    api_url = os.environ.get('API_URL')
    if not api_url:
        logger.error("API_URL environment variable not set")
        raise Exception("API_URL environment variable not set")

    # Obtém o token de acesso
    access_token = login_api()
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    # Divide os resultados em lotes de 100
    batch_size = 100
    total_results = len(data.results)
    
    for i in range(0, total_results, batch_size):
        batch = data.results[i:i + batch_size]
        batch_data = SaveResultsDto(results=batch)
        
        logger.info(f"Sending batch {i//batch_size + 1}/{(total_results + batch_size - 1)//batch_size}", 
                   batch_start=i, 
                   batch_size=len(batch))
        
        serialized_data = json.loads(
            json.dumps(
                asdict(batch_data),
                default=lambda obj: obj.isoformat() if isinstance(obj, datetime) else str(obj)
            )
        )
        
        response = requests.post(f"{api_url}/lotofacil/save-results", json=serialized_data, headers=headers)
        
        if not response.ok:
            logger.error("API request failed", 
                        status_code=response.status_code,
                        response_text=response.text,
                        batch_number=i//batch_size + 1)
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        
        logger.info("Batch sent successfully", 
                   batch_number=i//batch_size + 1, 
                   status_code=response.status_code)
    
    logger.info("All batches sent successfully", total_batches=(total_results + batch_size - 1)//batch_size)

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def handler(event: APIGatewayProxyEvent, context: LambdaContext):
    try:
        logger.info("Lambda handler started")
        
        excel_file_path = fetch_excel_file()
        mapped_data = map_excel_data(excel_file_path)
        send_to_api(mapped_data)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed Lotofácil results',
                'recordsProcessed': len(mapped_data.results)
            })
        }
        
        logger.info("Lambda handler completed successfully")
        return response
        
    except Exception as e:
        logger.exception("Lambda handler failed")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
