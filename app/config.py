import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    POLICY_STORE_ID: str = os.getenv("POLICY_STORE_ID", "")
    OPENSEARCH_ENDPOINT: str = os.getenv("OPENSEARCH_ENDPOINT", "")
    OPENSEARCH_INDEX: str = "enterprise-knowledge-base"
    BEDROCK_PRIMARY_MODEL: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    BEDROCK_FALLBACK_MODEL: str = "anthropic.claude-3-haiku-20240307-v1:0"
    BEDROCK_EMBEDDING_MODEL: str = "amazon.titan-embed-text-v2:0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")



settings = Settings()
