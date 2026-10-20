from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ai_insurance"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_TIMEOUT_SECONDS: float = 30.0

    APP_ENV: str = "development"
    APP_DEBUG: bool = False

    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALLOW_REGISTRATION: bool = True

    CORS_ORIGINS: str = "http://localhost:3000,https://ai-insurance-frontend-93n2ybmaz.vercel.app"

    # Run extraction -> risk scoring -> follow-up automatically when a claim is submitted.
    AUTO_PROCESS_CLAIMS: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
