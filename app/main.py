"""FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import admin, auth, bookings, leads, payments, stories, trips, webhooks

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Symphony of Summits — booking, payments (UPI QR), WhatsApp notifications.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error" if not settings.DEBUG else str(exc)},
    )


# ---------------- ROUTERS ----------------
api = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api)
app.include_router(trips.router, prefix=api)
app.include_router(bookings.router, prefix=api)
app.include_router(payments.router, prefix=api)
app.include_router(leads.router, prefix=api)
app.include_router(stories.router, prefix=api)
app.include_router(webhooks.router, prefix=api)
app.include_router(admin.router, prefix=api)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "ok",
        "docs": "/docs",
        "env": settings.APP_ENV,
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
