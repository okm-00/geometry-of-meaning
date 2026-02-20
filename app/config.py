import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in the value."
        )
    return value


LM_STUDIO_BASE_URL: str = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_API_KEY: str = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
LM_STUDIO_MODEL: str = _require("LM_STUDIO_MODEL")
LM_STUDIO_TIMEOUT_SECONDS: float = float(os.getenv("LM_STUDIO_TIMEOUT_SECONDS", "60"))
