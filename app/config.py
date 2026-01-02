from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"
    claude_timeout: int = 60
    claude_max_tokens: int = 4096

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
