"""API routes package."""
from app.api.routes_scraper import router as scraper_router
from app.api.routes_crud import router as crud_router
from app.api.routes_schema import router as schema_router
from app.api.routes_export import router as export_router

__all__ = ["scraper_router", "crud_router", "schema_router", "export_router"]
