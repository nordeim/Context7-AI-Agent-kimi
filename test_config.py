# test_config.py
from src.config import config
print("✅ Environment variables loaded successfully!")
print(f"API Key: {config.openai_api_key[:10]}...")
print(f"Model: {config.openai_model}")
print(f"Base URL: {config.openai_base_url}")
