"""
CRUD API Endpoints for Scraped Data.
Provides full Create, Read, Update, and Delete operations over scraped records.
Works dynamically for records from any website.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from psycopg2.extras import Json

from app.database import execute_query, fetch_all, fetch_one, insert_record
from app.models.schemas import (
    ScrapedRecordCreate,
    ScrapedRecordResponse,
    ScrapedRecordUpdate,
)

router = APIRouter(prefix="/api/data", tags=["CRUD Operations"])


@router.get(
    "",
    response_model=List[ScrapedRecordResponse],
    summary="List Scraped Data",
    description="Retrieve scraped records with optional filtering by URL, entity type, search keywords, and pagination.",
)
def list_records(
    source_url: Optional[str] = Query(None, description="Filter by original source URL"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    search: Optional[str] = Query(None, description="Case-insensitive keyword search in title and content"),
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Read multiple records from PostgreSQL with filtering and pagination."""
    conditions = []
    params = []

    if source_url:
        conditions.append("source_url = %s")
        params.append(source_url)
    if entity_type:
        conditions.append("entity_type = %s")
        params.append(entity_type)
    if search:
        conditions.append("(title ILIKE %s OR content ILIKE %s)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT id, source_url, entity_type, title, content, raw_data, created_at, updated_at
        FROM scraped_records
        {where_clause}
        ORDER BY id DESC
        LIMIT %s OFFSET %s;
    """
    params.extend([limit, offset])

    rows = fetch_all(sql, tuple(params))
    return [ScrapedRecordResponse(**r) for r in rows]


@router.get(
    "/{record_id}",
    response_model=ScrapedRecordResponse,
    summary="Get Single Record by ID",
    description="Fetch a specific scraped record by its primary key ID.",
)
def get_record(record_id: int):
    """Read a single record by primary key."""
    sql = """
        SELECT id, source_url, entity_type, title, content, raw_data, created_at, updated_at
        FROM scraped_records
        WHERE id = %s;
    """
    row = fetch_one(sql, (record_id,))
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found.",
        )
    return ScrapedRecordResponse(**row)


@router.post(
    "",
    response_model=ScrapedRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Record Manually",
    description="Manually create and insert a new record into the database.",
)
def create_record(record: ScrapedRecordCreate):
    """Insert a new record into PostgreSQL."""
    sql = """
        INSERT INTO scraped_records (source_url, entity_type, title, content, raw_data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, source_url, entity_type, title, content, raw_data, created_at, updated_at;
    """
    row = insert_record(
        sql,
        (
            record.source_url,
            record.entity_type,
            record.title,
            record.content,
            Json(record.raw_data),
        ),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create record.",
        )
    return ScrapedRecordResponse(**row)


@router.put(
    "/{record_id}",
    response_model=ScrapedRecordResponse,
    summary="Update Existing Record",
    description="Update fields of an existing record by ID.",
)
def update_record(record_id: int, update_data: ScrapedRecordUpdate):
    """Update fields of an existing record."""
    # Check existence
    check_sql = "SELECT id FROM scraped_records WHERE id = %s;"
    existing = fetch_one(check_sql, (record_id,))
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found.",
        )

    updates = []
    params = []

    if update_data.entity_type is not None:
        updates.append("entity_type = %s")
        params.append(update_data.entity_type)
    if update_data.title is not None:
        updates.append("title = %s")
        params.append(update_data.title)
    if update_data.content is not None:
        updates.append("content = %s")
        params.append(update_data.content)
    if update_data.raw_data is not None:
        updates.append("raw_data = %s")
        params.append(Json(update_data.raw_data))

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update.",
        )

    updates.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"""
        UPDATE scraped_records
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, source_url, entity_type, title, content, raw_data, created_at, updated_at;
    """
    params.append(record_id)

    with_updated = insert_record(sql, tuple(params))
    return ScrapedRecordResponse(**with_updated)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Record",
    description="Permanently delete a scraped record by ID.",
)
def delete_record(record_id: int):
    """Delete a record from PostgreSQL."""
    check_sql = "SELECT id FROM scraped_records WHERE id = %s;"
    existing = fetch_one(check_sql, (record_id,))
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found.",
        )

    delete_sql = "DELETE FROM scraped_records WHERE id = %s;"
    execute_query(delete_sql, (record_id,))
    return {"success": True, "message": f"Record {record_id} deleted successfully."}
