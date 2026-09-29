"""
Schema API Endpoints.
Provides introspection endpoints to inspect database tables, columns, and data types.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from app.database import fetch_all
from app.models.schemas import ColumnSchema, TableSchemaResponse

router = APIRouter(prefix="/api/schema", tags=["Schema Introspection"])


@router.get(
    "/tables",
    summary="List Database Tables",
    description="Retrieve all base tables present in the public schema of the PostgreSQL database.",
)
def list_tables() -> Dict[str, Any]:
    """Inspect and return list of user tables."""
    sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    rows = fetch_all(sql)
    table_names = [r["table_name"] for r in rows]
    return {
        "schema": "public",
        "total_tables": len(table_names),
        "tables": table_names,
    }


@router.get(
    "/tables/{table_name}",
    response_model=TableSchemaResponse,
    summary="Get Table Schema & Columns",
    description="Retrieve column names, data types, nullability, and default values for a specified table.",
)
def get_table_schema(table_name: str):
    """Inspect columns and data types for a given table."""
    # Check if table exists
    check_sql = """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = %s;
    """
    if not fetch_all(check_sql, (table_name,)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table '{table_name}' does not exist in the public schema.",
        )

    columns_sql = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position;
    """
    rows = fetch_all(columns_sql, (table_name,))

    columns = [
        ColumnSchema(
            column_name=r["column_name"],
            data_type=r["data_type"],
            is_nullable=r["is_nullable"],
            column_default=r["column_default"],
        )
        for r in rows
    ]

    return TableSchemaResponse(table_name=table_name, columns=columns)


@router.get(
    "",
    summary="Get Complete Database Schema",
    description="Returns an aggregated schema overview containing all tables and their respective columns.",
)
def get_full_schema():
    """Retrieve full database schema for all public tables."""
    sql = """
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    rows = fetch_all(sql)
    
    schema_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        t_name = r["table_name"]
        if t_name not in schema_map:
            schema_map[t_name] = []
        schema_map[t_name].append({
            "column_name": r["column_name"],
            "data_type": r["data_type"],
            "is_nullable": r["is_nullable"],
            "column_default": r["column_default"],
        })

    return {
        "database": "PostgreSQL",
        "schema": "public",
        "tables_count": len(schema_map),
        "tables": [
            {"table_name": t, "columns": cols}
            for t, cols in schema_map.items()
        ],
    }
