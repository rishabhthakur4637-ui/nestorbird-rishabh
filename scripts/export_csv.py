"""
CSV Generation Script.
Exports scraped data from the PostgreSQL database into a cleanly formatted CSV file
using Python's native `csv` module.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import fetch_all


def export_scraped_data_to_csv(
    output_path: str,
    source_url: str = None,
    entity_type: str = None,
    limit: int = None,
) -> str:
    """
    Queries PostgreSQL for scraped records and writes them to a formatted CSV file.
    """
    conditions = []
    params = []

    if source_url:
        conditions.append("source_url = %s")
        params.append(source_url)
    if entity_type:
        conditions.append("entity_type = %s")
        params.append(entity_type)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT 
            id,
            source_url,
            entity_type,
            title,
            content,
            raw_data,
            created_at,
            updated_at
        FROM scraped_records
        {where_clause}
        ORDER BY id ASC
        {limit_clause};
    """

    print(f"[*] Querying records from '{settings.DB_NAME}.scraped_records'...")
    rows = fetch_all(query, tuple(params) if params else None)

    if not rows:
        print("[!] No records found matching the criteria.")
        return ""

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Record ID",
        "Source URL",
        "Entity Type",
        "Title",
        "Content",
        "Raw JSON Metadata",
        "Created At",
        "Updated At",
    ]

    print(f"[*] Writing {len(rows)} rows to '{output_file}' using standard csv module...")
    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
        # Write clean header row
        writer.writerow(headers)

        for row in rows:
            # Format raw_data JSON nicely for readability in spreadsheets
            raw_json_str = (
                json.dumps(row.get("raw_data", {}), ensure_ascii=False)
                if isinstance(row.get("raw_data"), (dict, list))
                else str(row.get("raw_data") or "")
            )

            # Clean and truncate text if necessary for neat cell formatting
            title = (row.get("title") or "").replace("\r", " ").replace("\n", " ").strip()
            content = (row.get("content") or "").replace("\r", " ").replace("\n", " ").strip()

            writer.writerow([
                row.get("id"),
                row.get("source_url"),
                row.get("entity_type"),
                title,
                content,
                raw_json_str,
                str(row.get("created_at") or ""),
                str(row.get("updated_at") or ""),
            ])

    file_size_kb = output_file.stat().st_size / 1024
    print(f"[OK] Successfully exported {len(rows)} records!")
    print(f"[OK] File: {output_file.resolve()} ({file_size_kb:.2f} KB)")
    return str(output_file.resolve())


def main():
    parser = argparse.ArgumentParser(
        description="Export scraped records from PostgreSQL database into a formatted CSV file.",
    )
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"exports/scraped_data_{timestamp_str}.csv"

    parser.add_argument(
        "-o",
        "--output",
        default=default_filename,
        help=f"Destination CSV file path (default: {default_filename})",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Filter exports by specific source URL",
    )
    parser.add_argument(
        "--entity-type",
        default=None,
        help="Filter exports by entity category (e.g., quote, product)",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="Limit number of exported records",
    )

    args = parser.parse_args()
    export_scraped_data_to_csv(
        output_path=args.output,
        source_url=args.url,
        entity_type=args.entity_type,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
