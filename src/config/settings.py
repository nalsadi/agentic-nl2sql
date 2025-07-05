import os
from openai import AzureOpenAI
from typing import Optional

AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT"
)

AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY", 
)

AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

SPIDER_DB_PATH = os.getenv("SPIDER_DB_PATH", "spider_data/database")

MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

def get_openai_client() -> AzureOpenAI:
    """Get configured Azure OpenAI client"""
    return AzureOpenAI(
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
    )

def validate_config() -> bool:
    """Validate that all required configuration is present"""
    required_vars = [
        ("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_API_KEY", AZURE_OPENAI_API_KEY),
        ("AZURE_OPENAI_DEPLOYMENT", AZURE_OPENAI_DEPLOYMENT),
    ]
    
    missing = []
    for name, value in required_vars:
        if not value or value == "your-endpoint-here":
            missing.append(name)
    
    if missing:
        print(f"Missing configuration: {', '.join(missing)}")
        return False
    
    if not os.path.exists(SPIDER_DB_PATH):
        print(f"Spider database path not found: {SPIDER_DB_PATH}")
        return False
    
    return True

if __name__ == "__main__":
    if validate_config():
        print("Configuration is valid")
    else:
        print("Configuration validation failed")
