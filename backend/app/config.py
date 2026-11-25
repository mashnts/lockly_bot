from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    BOT_TOKEN: str
    CRYPTOBOT_TOKEN: str
    SECRET_KEY: str
    INTERNAL_API_TOKEN: str
    SQL_ECHO: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
