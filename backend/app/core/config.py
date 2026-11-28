from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app settings in one place.

    Each field below is read from an environment variable with the same name
    (not case sensitive). For example, database_url is read from DATABASE_URL.
    If the variable is not set, the default value after "=" is used.
    """

    # Database
    database_url: str = "sqlite:///./gaincheck.db"

    # Firebase
    firebase_web_api_key: str = ""
    firebase_service_account_path: str = "./firebase-service-account.json"

    # Where the frontend runs. Separate several addresses with commas.
    cors_origins: str = "http://localhost:8501"

    # Language model. llm_provider is "ollama" (runs on your machine) or "openai".
    llm_provider: str = "ollama"
    llm_temperature: float = 0.2  # low means steadier, less random answers
    llm_timeout_seconds: int = 180  # local models can be slow
    llm_max_retries: int = 2  # extra tries when the model gives an unusable answer

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Read values from a file called .env in the folder where we start the server.
    # extra="ignore" means unknown variables in .env are skipped instead of causing an error.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def cors_origin_list(self) -> list[str]:
        """Turn "a,b" into ["a", "b"]."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create one Settings object and import it from everywhere else:
#   from app.core.config import settings
settings = Settings()
