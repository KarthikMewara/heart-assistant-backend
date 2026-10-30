from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")

    secret_key: str = "dev-only-change-me"
    token_minutes: int = 60 * 24
    database_url: str = f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"
    upload_dir: Path = BASE_DIR / "storage" / "uploads"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    tesseract_cmd: str | None = None
    whisper_model: str = "base.en"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()