from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    environment: str = "development"
    port: int = 8000
    frontend_url: str
    gee_service_account: str
    gee_credentials_json: str
    gee_project_id: str = "irrigation-advisor-493714"
    vapid_private_key: str
    vapid_public_key: str
    vapid_subject: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()