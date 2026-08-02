from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==================================================
    # APPLICATION
    # ==================================================
    APP_NAME: str = "VIZU Academy API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # ==================================================
    # Storage
    # ==================================================
    STORAGE_PROVIDER: str = "local"
    UPLOAD_PATH: str = "uploads"

    # ==================================================
    # Cloudflare R2 (video storage)
    # ==================================================
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_ENDPOINT: str = ""
    R2_REGION: str = "auto"

    # Presigned streaming URL lifetime, in seconds. 5 minutes per the
    # video-security spec — never issue longer-lived or permanent links.
    R2_SIGNED_URL_EXPIRE_SECONDS: int = 300

    # Video upload constraints, enforced in VideoService before any bytes
    # are written to storage.
    VIDEO_MAX_UPLOAD_SIZE_MB: int = 2048
    VIDEO_ALLOWED_CONTENT_TYPES: str = "video/mp4,video/webm,video/quicktime"

    # ==================================================
    # API
    # ==================================================
    API_V1_PREFIX: str = "/api/v1"

    # ==================================================
    # CORS
    # ==================================================
    # Comma-separated list of extra allowed origins, e.g. the deployed
    # frontend's real domain(s) — "https://app.vizu.academy,https://vizu.academy".
    # localhost/127.0.0.1 (any port) are always allowed for local dev via
    # allow_origin_regex in main.py, so they don't need to be listed here.
    CORS_ALLOWED_ORIGINS: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    # ==================================================
    # AI
    # ==================================================
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.5"

    # ==================================================
    # SECURITY
    # ==================================================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ==================================================
    # DATABASE
    # ==================================================
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()