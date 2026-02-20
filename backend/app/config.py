import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    db_path: str = "/app/data/trends.db"
    users_csv_path: str = "/app/data/users.csv"
    seed_keywords_path: str = "/app/data/seed_keywords.json"

    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")

    ebay_app_id: str = os.getenv("EBAY_APP_ID", "")
    ebay_cert_id: str = os.getenv("EBAY_CERT_ID", "")

    etsy_api_key: str = os.getenv("ETSY_API_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
