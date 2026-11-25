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

    # Read values from a file called .env in the folder where we start the server.
    # extra="ignore" means unknown variables in .env (like the LLM ones we
    # have not used yet) are skipped instead of causing an error.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def cors_origin_list(self) -> list[str]:
        """Turn "a,b" into ["a", "b"]."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create one Settings object and import it from everywhere else:
#   from app.core.config import settings
settings = Settings()
