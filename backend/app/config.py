from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://smartcampus:smartcampus@db:5432/smartcampus"
    jwt_secret: str = "change-me-in-prod"
    jwt_alg: str = "HS256"
    access_ttl_min: int = 15
    refresh_ttl_days: int = 7
    cors_origins: list[str] = ["http://localhost:3000"]
    first_admin_email: str = "admin@smartcampus.local"
    first_admin_password: str = "ChangeMe123!"


settings = Settings()
