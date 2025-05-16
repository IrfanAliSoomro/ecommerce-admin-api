from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-commerce Admin API"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str

    # For PyMySQL, the URL should be in the format:
    # mysql+pymysql://user:password@host:port/dbname

    # If using python-dotenv, settings can be loaded from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

# The lru_cache decorator means the Settings object is created only once.
# The first time it's called, it loads the settings. Subsequent calls return the cached instance.
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 