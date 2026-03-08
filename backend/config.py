"""
Application configuration management
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Database - SQLite for local development
    DATABASE_URL: str = "sqlite:///./retail_simulator.db"

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001

    # Performance SLA
    RISK_PROCESSING_SLA_SECONDS: int = 300
    SIMULATION_SLA_SECONDS: int = 30
    UI_RESPONSE_SLA_SECONDS: int = 2

    # ------------------------------------------------------------------ #
    # Google Gemini                                                        #
    # Set GEMINI_API_KEY in your .env file — never hard-code it           #
    # Get your key at: https://aistudio.google.com/apikey                 #
    # ------------------------------------------------------------------ #
    GEMINI_API_KEY: str = ""

    # Change this ONE value in .env to switch Gemini models.
    #
    # Recommended:
    #   gemini-2.0-flash   ← default (fast, cost-efficient)
    #   gemini-1.5-pro     ← deep reasoning, higher cost
    #   gemini-1.5-flash   ← fast, lower cost
    #
    GEMINI_MODEL_ID: str = "gemini-2.0-flash"

    # ------------------------------------------------------------------ #
    # AWS S3                                                               #
    # Set credentials in .env — never hard-code them                     #
    # ------------------------------------------------------------------ #
    AWS_REGION: str = "eu-west-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "spectacular-crew-retail-data"

    # ------------------------------------------------------------------ #
    # AWS Bedrock                                                          #
    # ------------------------------------------------------------------ #
    AWS_BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # ------------------------------------------------------------------ #
    # DynamoDB table names                                                 #
    # ------------------------------------------------------------------ #
    DYNAMO_TABLE_UPLOADS: str = "ai_bharat_uploads"
    DYNAMO_TABLE_SIMULATIONS: str = "ai_bharat_simulations"
    DYNAMO_TABLE_ACTIVITY_LOGS: str = "ai_bharat_activity_logs"

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
