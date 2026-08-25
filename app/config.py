from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ai_insurance"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://user:password@localhost:5432/ai_insurance"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
