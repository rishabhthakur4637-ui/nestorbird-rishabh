"""
CSV Export API Route.
Provides an endpoint to dynamically trigger CSV generation and download the file.
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from scripts.export_csv import export_scraped_data_to_csv

router = APIRouter(prefix="/api/export", tags=["CSV Export"])


@router.get(
    "/csv",
    summary="Download Scraped Data as CSV",
    description="Generates a formatted CSV file using Python's native csv module and streams it as a download.",
)
def download_csv(
    source_url: Optional[str] = Query(None, description="Optional filter by source URL"),
    entity_type: Optional[str] = Query(None, description="Optional filter by entity category"),
    limit: Optional[int] = Query(None, description="Optional row limit"),
):
    try:
        from datetime import datetime
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"exports/scraped_data_{timestamp_str}.csv"
        
        file_path_str = export_scraped_data_to_csv(
            output_path=output_path,
            source_url=source_url,
            entity_type=entity_type,
            limit=limit,
        )

        if not file_path_str or not Path(file_path_str).exists():
            raise HTTPException(status_code=404, detail="No records found to export.")

        file_path = Path(file_path_str)
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="text/csv",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}") from e
