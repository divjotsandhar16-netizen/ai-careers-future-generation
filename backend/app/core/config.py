from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ai Careers for Future Generation"
    database_url: str = "sqlite:///./ai_careers.db"
    frontend_origin: str = "http://localhost:5173"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    jwt_secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 1440
    dev_auth_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
