from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    multiportal_service_url: str
    multiportal_service_username: str
    multiportal_service_password: str
    multiportal_service_app_id: str
    multiportal_empresa_target_id: int
    master_pass: str
    jwt_secret: str
    jwt_expiration_secs: int

    environment: str = 'DEV'
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), '..', '..', '.env'), frozen=True, extra='ignore')

@lru_cache
def get_settings():
    return Settings()

if __name__ == '__main__':
    print(get_settings())