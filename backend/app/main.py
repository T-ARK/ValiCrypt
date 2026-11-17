"""MediaVault FastAPI Application Entrypoint.

Provides modular REST APIs for hiding and recovering encrypted data in image and video carriers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.routes.capacity import router as capacity_router
from app.api.routes.decode import router as decode_router
from app.api.routes.download import router as download_router
from app.api.routes.encode import router as encode_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.verify import router as verify_router
from app.core.config import settings
from app.core.errors import MediaVaultError
from app.core.logging import logger
from app.db.session import init_db


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard security response headers."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


# Initialize database tables
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database tables exist
    init_db()
    yield
    # Shutdown
    logger.info("MediaVault backend shutting down cleanly.")


app = FastAPI(
    title="ValiCrypt API",
    description=(
        "Production-quality steganography platform for hiding encrypted ZIP archives "
        "and text messages inside image and video carriers using Argon2id and AES-256-GCM."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)


# Exception Handlers
@app.exception_handler(MediaVaultError)
async def mediavault_error_handler(request: Request, exc: MediaVaultError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please contact the administrator.",
                "details": {},
            },
        },
    )


# API Routes
api_v1_prefix = "/api/v1"
app.include_router(health_router, prefix=api_v1_prefix)
app.include_router(capacity_router, prefix=api_v1_prefix)
app.include_router(encode_router, prefix=api_v1_prefix)
app.include_router(decode_router, prefix=api_v1_prefix)
app.include_router(verify_router, prefix=api_v1_prefix)
app.include_router(jobs_router, prefix=api_v1_prefix)
app.include_router(download_router, prefix=api_v1_prefix)

# Standard Root Health Endpoint (compatible with Render, Docker, Kubernetes)
@app.get("/health", tags=["System"])
async def root_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


# SEO and Crawler Endpoints
@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    robots_path = settings.BASE_DIR / "frontend" / "public" / "robots.txt"
    dist_robots = settings.BASE_DIR / "frontend" / "dist" / "robots.txt"
    target = dist_robots if dist_robots.exists() else robots_path
    if target.exists():
        return FileResponse(target, media_type="text/plain")
    return Response(
        content="User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: https://valicrypt.onrender.com/sitemap.xml\n",
        media_type="text/plain",
    )


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    sitemap_path = settings.BASE_DIR / "frontend" / "public" / "sitemap.xml"
    dist_sitemap = settings.BASE_DIR / "frontend" / "dist" / "sitemap.xml"
    target = dist_sitemap if dist_sitemap.exists() else sitemap_path
    if target.exists():
        return FileResponse(target, media_type="application/xml")
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://valicrypt.onrender.com/</loc></url></urlset>',
        media_type="application/xml",
    )

# Serve Frontend static assets if built
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", tags=["Frontend"])
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "error": {"code": "NOT_FOUND", "message": "API endpoint not found", "details": {}}},
            )
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/", tags=["System"])
    async def root():
        return {
            "service": f"{settings.PROJECT_NAME} API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
            "api_health": "/api/v1/health",
        }
