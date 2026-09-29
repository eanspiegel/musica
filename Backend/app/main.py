import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logger.info("Starting music-downloader-api")
    yield
    logger.info("Shutting down music-downloader-api")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Music Downloader API",
        version="0.1.0",
        docs_url="/docs" if settings.openapi_enabled else None,
        redoc_url="/redoc" if settings.openapi_enabled else None,
        openapi_url="/openapi.json" if settings.openapi_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next) -> Response:
        # Always let CORS preflights through — they never carry X-API-Key
        if request.method == "OPTIONS" or request.url.path in _PUBLIC_PATHS:
            return await call_next(request)
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
        return await call_next(request)

    app.include_router(v1_router)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
