from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEMO_MODE: bool = True
    ENVIRONMENT: str = "development"
    LLM_BACKEND: str = "framework"  # "framework" (universal adapter) or "direct" (OpenAI / Sarvam)
    FRAMEWORK_BASE_URL: str = "http://localhost:11434/v1"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = ""
    SARVAM_API_KEY: str = ""
    TOMTOM_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    DATABASE_URL: str = "sqlite:///./data/namma_twin.db"

    # Vulnerability & priority weights
    WEIGHT_SEVERITY: float = 0.35
    WEIGHT_VELOCITY: float = 0.25
    WEIGHT_VULNERABILITY: float = 0.25
    WEIGHT_CONFIDENCE: float = 0.15


settings = Settings()
