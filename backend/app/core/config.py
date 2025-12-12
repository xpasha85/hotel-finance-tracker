from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str = "change_me"
    jwt_expires_min: int = 43200  # 30 days

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
