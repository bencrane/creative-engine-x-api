from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.shared.errors import (
    AuthenticationError,
    JobNotFoundError,
    RateLimitExceededError,
    SpecNotFoundError,
    UnknownRouteError,
    ValidationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.db import close_pool, init_pool
    from src.routing.registry import registry
    from src.specs.loader import SpecLoader

    await init_pool()
    specs = SpecLoader.load_all()
    registry.register(specs)
    yield
    await close_pool()


app = FastAPI(title="creative-engine-x-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from src.routing.router import router as generate_router
from src.brand.router import router as brand_router
from src.jobs.router import router as jobs_router
from src.auth.router import router as auth_router
from src.landing_pages.router import router as landing_pages_router

app.include_router(generate_router)
app.include_router(brand_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(landing_pages_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "creative-engine-x"}


# --- Exception handlers ---

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"error": {"code": "authentication_error", "message": exc.detail}})


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(status_code=429, content={"error": {"code": "rate_limit_exceeded", "message": exc.detail}})


@app.exception_handler(UnknownRouteError)
async def unknown_route_handler(request: Request, exc: UnknownRouteError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "unknown_route",
                "message": str(exc),
                "available": [list(k) for k in exc.available],
            }
        },
    )


@app.exception_handler(SpecNotFoundError)
async def spec_not_found_handler(request: Request, exc: SpecNotFoundError):
    return JSONResponse(status_code=404, content={"error": {"code": "spec_not_found", "message": str(exc)}})


@app.exception_handler(JobNotFoundError)
async def job_not_found_handler(request: Request, exc: JobNotFoundError):
    return JSONResponse(status_code=404, content={"error": {"code": "job_not_found", "message": str(exc)}})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": exc.detail}})
