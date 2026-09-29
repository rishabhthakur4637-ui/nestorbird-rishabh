"""
Scraper API Endpoints.
Handles dynamic scraping requests and automatically persists results to PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, status
from psycopg2.extras import Json

from app.database import insert_record
from app.models.schemas import ScrapeExecutionResponse, ScrapeRequest, ScrapedRecordResponse
from app.scraper.engine import ScraperEngine

router = APIRouter(prefix="/api/scrape", tags=["Scraping & Ingestion"])
engine = ScraperEngine()


@router.post(
    "",
    response_model=ScrapeExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Scrape URL & Store in PostgreSQL",
    description="Accepts any website URL, detects dynamic/API characteristics, extracts structured data, and saves into PostgreSQL.",
)
def scrape_and_store(request: ScrapeRequest):
    """
    Main ingestion endpoint:
    1. Scrapes target website using requests and BeautifulSoup / JSON parser.
    2. Identifies dynamic website indicators.
    3. Persists all extracted records into PostgreSQL with raw JSONB payload.
    """
    try:
        scrape_result = engine.scrape(
            url=request.url,
            entity_type=request.entity_type,
            css_selector=request.css_selector,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scraping failed: {str(e)}",
        ) from e

    records = scrape_result.get("records", [])
    saved_records = []

    insert_sql = """
        INSERT INTO scraped_records (source_url, entity_type, title, content, raw_data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, source_url, entity_type, title, content, raw_data, created_at, updated_at;
    """

    for rec in records:
        try:
            row = insert_record(
                insert_sql,
                (
                    rec["source_url"],
                    rec["entity_type"],
                    rec["title"],
                    rec["content"],
                    Json(rec["raw_data"]),
                ),
            )
            if row:
                saved_records.append(ScrapedRecordResponse(**row))
        except Exception as e:
            # Continue saving remaining records if one fails
            print(f"[!] Error inserting scraped record: {e}")

    return ScrapeExecutionResponse(
        success=True,
        message=f"Successfully scraped and stored {len(saved_records)} records from {request.url}",
        source_url=scrape_result["source_url"],
        entity_type=scrape_result["entity_type"],
        dynamism_analysis=scrape_result["dynamism_analysis"],
        total_scraped=len(records),
        total_saved=len(saved_records),
        records=saved_records,
    )
