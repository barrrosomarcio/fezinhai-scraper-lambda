# fezinhai-scraper-lambda

AWS Lambda function to scrape Lotofácil results from the Caixa website and process them.

## Features

- Scrapes Lotofácil results from the official Caixa website
- Downloads and processes the Excel file with results
- Converts data to JSON format
- Sends processed data to an API endpoint

## Setup

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up environment variables:
- `API_URL`: The URL of your API endpoint
- `API_KEY`: (Optional) API key for authentication

## Deployment

1. Create a ZIP file with the code and dependencies
2. Create a new Lambda function in AWS
3. Upload the ZIP file
4. Set the handler to `handler.handler`
5. Configure environment variables in the Lambda console
6. Set appropriate timeout (recommended: 2-3 minutes)
7. Configure necessary IAM permissions

## Local Testing

To test locally, you can create a `test.py` file:

```python
from handler import handler
result = handler({}, {})
print(result)
```

## Notes

- The function expects the Excel file to be available via a download button on the Lotofácil page
- Make sure the Lambda function has sufficient memory and timeout settings
- The function will automatically handle temporary file cleanup