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

    # Chunked upload: each chunk is one HTTP request, so this must stay
    # well under whatever the edge (Cloudflare) allows through in a single
    # request — live-tested at 50MB OK / 100MB+ rejected with a 413 before
    # ever reaching this server, hence 25MB, not just "large but safe."
    VIDEO_UPLOAD_CHUNK_SIZE_MB: int = 25

    # An upload session (and its temp chunk files) older than this with no
    # successful /complete is treated as abandoned — browser closed,
    # network died, admin gave up — and swept by
    # VideoService.cleanup_stale_upload_sessions().
    VIDEO_UPLOAD_SESSION_MAX_AGE_HOURS: int = 24

    # Lifetime of the signed token embedded in a video's playback URL (see
    # create_video_stream_token) while local storage is active. Long enough
    # to cover one lesson-watching session including replays/seeking, short
    # enough that a leaked URL goes stale the same day. Distinct from
    # R2_SIGNED_URL_EXPIRE_SECONDS above, which is for the not-yet-active R2
    # backend and assumes a URL-refresh mechanism this player doesn't have.
    VIDEO_STREAM_TOKEN_EXPIRE_MINUTES: int = 240

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

    # Mock Exam writing/speaking evaluation (Phase 4). Empty by default —
    # AIEvaluationService raises a clear, caught error rather than silently
    # no-opping when a key isn't configured; see app/services/mock_exam/ai_service.py.
    GEMINI_API_KEY: str = ""
    # "-latest" alias rather than a pinned version — a pinned model
    # (previously "gemini-2.0-flash") silently starts 404ing once Google
    # retires that specific version, which is exactly what broke this
    # setting before it was ever exercised end-to-end; confirmed live
    # against the API this key can actually reach.
    GEMINI_MODEL: str = "gemini-flash-latest"

    # Bulk vocabulary generator (see app/services/vocabulary/ai_enrichment.py
    # and bulk_service.py) — reuses GEMINI_API_KEY for text enrichment.
    # Audio uses Gemini's own native TTS-capable model (generateContent
    # with responseModalities=["AUDIO"]) rather than the separate Google
    # Cloud Text-to-Speech product — that product requires OAuth2/
    # service-account credentials and rejects plain API keys outright
    # (confirmed live: "API keys are not supported by this API"), so it
    # could never work with GEMINI_API_KEY no matter how it's configured.
    GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    GEMINI_TTS_VOICE: str = "Kore"

    # This caps how many TTS requests run at once so a 100-word import
    # doesn't fire 100 concurrent calls. Live-tested with 6 (the feature
    # spec's "5-10 concurrent") against the real account: every request
    # past the 1st failed with 429 RESOURCE_EXHAUSTED. Lowered to 2 —
    # concurrency beyond what VOCAB_BULK_TTS_MAX_PER_MINUTE allows through
    # anyway only adds coroutines waiting on the rate limiter below, not
    # real throughput.
    VOCAB_BULK_TTS_CONCURRENCY: int = 2

    # Confirmed live via Google's own 429 response: gemini-2.5-flash-tts's
    # free tier allows exactly 3 requests/minute (and separately, only 10
    # /day — a hard ceiling no amount of pacing can raise; that needs a
    # paid plan on this Google Cloud project). synthesize_word_audio()
    # enforces this as a real sliding-window rate limiter, not just a
    # concurrency cap, since fast calls can exceed a per-minute quota even
    # at low concurrency. Raise this once billing is enabled.
    VOCAB_BULK_TTS_MAX_PER_MINUTE: int = 3

    # ==================================================
    # SECURITY
    # ==================================================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Stateless password-reset JWTs (see core/security/jwt.py) live this
    # long before they're rejected regardless of use.
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Used to build the reset link logged by /auth/forgot-password (no
    # email-sending infrastructure exists yet — see that endpoint).
    FRONTEND_URL: str = "http://localhost:3000"

    # Shared passphrase for the Super Admin's second verification screen.
    # Never sent to or embedded in the frontend — compared server-side
    # only, in POST /auth/verify-admin-password.
    SUPER_ADMIN_VERIFICATION_PASSWORD: str = "Zz_20020614"

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