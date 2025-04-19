from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths

logger = Logger(service="fezinhai-scraper", correlation_id_path=correlation_paths.API_GATEWAY_REST) 