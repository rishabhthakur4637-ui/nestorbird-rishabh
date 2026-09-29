"""
FastAPI Application Entry Point.
Initializes middleware, registers routers, and configures Swagger/OpenAPI documentation.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import crud_router, export_router, scraper_router, schema_router
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="NestorBird - Dynamic Web Scraper & Database Engine",
    description=(
        "A robust REST API service for dynamic web scraping, PostgreSQL storage using psycopg2, "
        "comprehensive CRUD operations, and PostgreSQL schema introspection."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local testing / frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets Directory
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register API Routers
app.include_router(scraper_router)
app.include_router(crud_router)
app.include_router(schema_router)
app.include_router(export_router)


@app.get("/", summary="Dashboard UI", include_in_schema=False)
def serve_dashboard():
    """Serves the interactive web dashboard."""
    index_file = BASE_DIR / "static" / "index.html"
    return FileResponse(index_file)


@app.get("/api/health", tags=["Health & Info"])
def health_check():
    """Health check and service status."""
    return {
        "status": "online",
        "service": "NestorBird Web Scraper & Database API",
        "version": "1.0.0",
        "database": {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "name": settings.DB_NAME,
        },
        "docs_url": "/docs",
        "dashboard_url": "/",
        "endpoints": {
            "scrape": "POST /api/scrape",
            "crud_data": "/api/data",
            "schema_tables": "GET /api/schema/tables",
            "full_schema": "GET /api/schema",
            "export_csv": "GET /api/export/csv",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
