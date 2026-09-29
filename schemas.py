"""
Pydantic Schemas for Request & Response Data Validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ScrapeRequest(BaseModel):
    """Payload to trigger dynamic website scraping."""
    url: str = Field(..., description="Target website URL to scrape (e.g., https://quotes.toscrape.com)")
    entity_type: Optional[str] = Field("generic", description="Classification tag for the scraped data (e.g. quote, product, news)")
    css_selector: Optional[str] = Field(None, description="Optional CSS selector to target specific DOM containers (e.g. .quote, .card)")


class ScrapedRecordCreate(BaseModel):
    """Payload to manually create a scraped record."""
    source_url: str = Field(..., description="Source URL where data originated")
    entity_type: str = Field("generic", description="Entity category")
    title: Optional[str] = Field(None, description="Title or headline")
    content: Optional[str] = Field(None, description="Main text content or description")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary JSON data extracted from the site")


class ScrapedRecordUpdate(BaseModel):
    """Payload to update an existing record."""
    entity_type: Optional[str] = Field(None, description="Updated entity category")
    title: Optional[str] = Field(None, description="Updated title")
    content: Optional[str] = Field(None, description="Updated content")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Updated JSON payload")


class ScrapedRecordResponse(BaseModel):
    """Representation of a persisted scraped record."""
    id: int
    source_url: str
    entity_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    raw_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ScrapeExecutionResponse(BaseModel):
    """Response returned upon completing a scrape operation."""
    success: bool
    message: str
    source_url: str
    entity_type: str
    dynamism_analysis: Dict[str, Any]
    total_scraped: int
    total_saved: int
    records: List[ScrapedRecordResponse]


class ColumnSchema(BaseModel):
    """Metadata describing a single database column."""
    column_name: str
    data_type: str
    is_nullable: str
    column_default: Optional[str] = None


class TableSchemaResponse(BaseModel):
    """Metadata describing a PostgreSQL table and its columns."""
    table_name: str
    columns: List[ColumnSchema]
