import asyncio
import logging
import logging.handlers
from contextlib import asynccontextmanager
from dataclasses import replace as dc_replace
from functools import partial
from pathlib import Path
from typing import Annotated, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, APIConnectionError
from pydantic import BaseModel, Field

from app import config, db
from app.features import EndingStrategy
from app.story import generate_story, TEMPERATURE, LLMConnectionError, LLMResponseError
from app.variants import VARIANTS

STATIC_DIR = Path(__file__).parent.parent / "static"
LOGS_DIR = Path(__file__).parent.parent / "logs"

# Write ERROR-level logs to logs/app.log so errors persist across terminal sessions.
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


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    db.init_db()
    yield


app = FastAPI(title="Story App", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ── Pydantic models ───────────────────────────────────────────────────────────

class GenerationResult(BaseModel):
    generation_id: int
    condition: str
    body: list[str]
    endings: list[str]


class VariantSelection(BaseModel):
    name: str
    ending_strategy: Optional[str] = None  # None = use variant default


class SessionRequest(BaseModel):
    selections: Annotated[list[VariantSelection], Field(min_length=1, max_length=2)]


class SessionResponse(BaseModel):
    session_id: int
    generations: list[GenerationResult]


class FeedbackRequest(BaseModel):
    generation_id: int
    rating: Annotated[Optional[int], Field(ge=1, le=5)] = None
    tag: Annotated[Optional[str], Field(max_length=120)] = None


# ── Routes ────────────────────────────────────────────────────────────────────

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


@app.get("/api/variants")
async def variants() -> JSONResponse:
    """Return metadata for all available generation variants and configurable features."""
    return JSONResponse({
        "variants": {
            name: {"ending_strategy": vc.ending_strategy.value}
            for name, vc in VARIANTS.items()
        },
        "ending_strategies": [e.value for e in EndingStrategy],
    })


@app.post("/api/session", response_model=SessionResponse)
async def session(request: SessionRequest) -> SessionResponse:
    """
    Generate the requested variants concurrently, persist all to the database,
    and return them as a generations array with a shared session_id.

    Request body: {"selections": [{"name": "baseline", "ending_strategy": "none"}, ...]}
    1–2 selections; each name must be a key in VARIANTS; ending_strategy overrides the default.
    """
    unknown = [s.name for s in request.selections if s.name not in VARIANTS]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown variant(s): {unknown}. Available: {list(VARIANTS.keys())}",
        )

    valid_strategies = {e.value for e in EndingStrategy}
    bad_strategies = [
        s.ending_strategy for s in request.selections
        if s.ending_strategy is not None and s.ending_strategy not in valid_strategies
    ]
    if bad_strategies:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown ending_strategy value(s): {bad_strategies}. "
                   f"Available: {sorted(valid_strategies)}",
        )

    variant_configs = []
    for s in request.selections:
        vc = VARIANTS[s.name]
        if s.ending_strategy is not None:
            vc = dc_replace(vc, ending_strategy=EndingStrategy(s.ending_strategy))
        variant_configs.append(vc)

    loop = asyncio.get_event_loop()
    try:
        results = await asyncio.gather(
            *[loop.run_in_executor(None, partial(generate_story, vc)) for vc in variant_configs]
        )
    except LLMConnectionError as e:
        logger.error("Session generation failed (connection): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except LLMResponseError as e:
        logger.error("Session generation failed (LLMResponseError): %s", e)
        raise HTTPException(status_code=502, detail=str(e))

    generation_ids = []
    for result in results:
        gen_id = db.save_generation(
            condition=result.condition,
            model=config.LM_STUDIO_MODEL,
            system_prompt=result.system_prompt,
            user_prompt=result.user_prompt,
            temperature=TEMPERATURE,
            body=result.body,
            endings=result.endings,
            timing_ms=result.timing_ms,
        )
        generation_ids.append(gen_id)

    session_id = db.save_session(generation_ids=generation_ids)

    logger.info("Session %d created (generation_ids=%s)", session_id, generation_ids)

    return SessionResponse(
        session_id=session_id,
        generations=[
            GenerationResult(
                generation_id=gen_id,
                condition=result.condition,
                body=result.body,
                endings=result.endings,
            )
            for gen_id, result in zip(generation_ids, results)
        ],
    )


@app.post("/api/feedback")
async def feedback(request: FeedbackRequest) -> JSONResponse:
    """Record a star rating and optional tag for a single generation."""
    try:
        db.save_feedback(
            generation_id=request.generation_id,
            rating=request.rating,
            tag=request.tag,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Failed to save feedback for generation %d", request.generation_id)
        raise HTTPException(status_code=500, detail="Failed to save feedback.")

    return JSONResponse({"status": "ok"})
