import logging
import logging.handlers
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, APIConnectionError
from pydantic import BaseModel

from app import config
from app.story import generate_story, LLMConnectionError, LLMResponseError, LLMParseError

STATIC_DIR = Path(__file__).parent.parent / "static"
LOGS_DIR = Path(__file__).parent.parent / "logs"

# Write ERROR-level logs to logs/app.log so errors persist across terminal sessions.
# Agents and humans can read this file when investigating issues on a future PR.
LOGS_DIR.mkdir(exist_ok=True)
_file_handler = logging.handlers.RotatingFileHandler(
    LOGS_DIR / "app.log", maxBytes=1_000_000, backupCount=3
)
_file_handler.setLevel(logging.ERROR)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
)
logging.getLogger().addHandler(_file_handler)

logger = logging.getLogger(__name__)

app = FastAPI(title="Story App")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class StoryResponse(BaseModel):
    body: list[str]
    endings: list[str]


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> JSONResponse:
    """
    Probe LM Studio connectivity using a lightweight models-list call.
    Always returns HTTP 200 — callers check the 'status' field.
    """
    try:
        client = OpenAI(
            base_url=config.LM_STUDIO_BASE_URL,
            api_key=config.LM_STUDIO_API_KEY,
            timeout=5.0,
        )
        client.models.list()
        return JSONResponse({"status": "ok", "lm_studio": "reachable"})
    except APIConnectionError as e:
        logger.error(
            "Health check: LM Studio unreachable at %s — %s",
            config.LM_STUDIO_BASE_URL,
            e,
        )
        return JSONResponse({
            "status": "degraded",
            "lm_studio": "unreachable",
            "detail": (
                f"Cannot reach LM Studio at {config.LM_STUDIO_BASE_URL}. "
                f"Ensure LM Studio is running with the local server enabled."
            ),
        })


@app.post("/api/story", response_model=StoryResponse)
async def story() -> StoryResponse:
    try:
        result = generate_story()
    except LLMConnectionError as e:
        logger.error("Story generation failed (connection): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except (LLMResponseError, LLMParseError) as e:
        logger.error("Story generation failed (%s): %s", type(e).__name__, e)
        raise HTTPException(status_code=502, detail=str(e))

    logger.info("Story generated successfully")
    return StoryResponse(body=result.body, endings=result.endings)
