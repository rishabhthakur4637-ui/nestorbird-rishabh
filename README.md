# Dynamic Web Scraper, PostgreSQL CRUD & Schema Engine

A modular, production-ready Python solution for scraping dynamic and static websites, persisting structured data into PostgreSQL using `psycopg2`, exposing RESTful CRUD and Schema APIs via FastAPI, and generating formatted CSV exports.

---

## 🌟 Key Features

1. **Dynamic Website Scraping (`requests` + `BeautifulSoup`):**
   - Automated dynamic site & client-side rendering (SPA/Next.js/React/Vue) detection.
   - Extracts runtime dynamic JavaScript state variables (e.g. `var data = [...]`), Next.js hydration state (`<script id="__NEXT_DATA__">`), and JSON-LD structured schemas (`schema.org`).
   - Supports direct REST/JSON API endpoints and custom CSS selectors.
   - Fallback semantic DOM parsing for any generic URL.

2. **PostgreSQL Integration (`psycopg2`):**
   - Direct SQL execution using connection pooling and context managers.
   - Universal schema combining relational fields (`id`, `source_url`, `title`, `content`) with PostgreSQL `JSONB` (`raw_data`) for flexible storage across any website.
   - GIN indexes for fast querying into nested JSON metadata.

3. **RESTful APIs (FastAPI):**
   - **Scrape & Ingest:** `POST /api/scrape`
   - **Full CRUD:** `GET /api/data`, `GET /api/data/{id}`, `POST /api/data`, `PUT /api/data/{id}`, `DELETE /api/data/{id}`
   - **Schema Introspection:** `GET /api/schema/tables`, `GET /api/schema/tables/{table_name}`, `GET /api/schema`
   - Auto-generated Swagger documentation at `/docs`.

4. **Standalone CSV Export:**
   - Dedicated CLI tool (`scripts/export_csv.py`) using Python's native `csv` module.
   - Clean headers, organized formatting, and CLI filtering options.

---

## 📁 Project Structure

```text
nestorbird-rishabh/
│
├── app/
│   ├── __init__.py
│   ├── config.py              # Environment configuration & DB settings
│   ├── database.py            # psycopg2 connection management & query helpers
│   │
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── detector.py        # Dynamic site & framework detection
│   │   ├── engine.py          # Scraper orchestrator for any URL
│   │   └── parser.py          # Extraction strategies (inline JS, Next.js, JSON-LD, CSS selectors)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_scraper.py  # Scraping & Ingestion endpoint
│   │   ├── routes_crud.py     # CRUD operations for scraped data
│   │   └── routes_schema.py   # Database schema introspection endpoints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic request/response validation schemas
│   │
│   └── main.py                # FastAPI app entry point & middleware
│
├── scripts/
│   ├── export_csv.py          # Standalone CSV export using Python native csv module
│   └── init_db.py             # Database creation and table initialization
│
├── docs/
│   ├── ARCHITECTURE.md        # Technical architecture & scraping flow
│   └── LOOM_SCRIPT.md         # Word-for-word 3-5 min Loom presentation guide
│
├── .env.example               # Template environment variables
├── .gitignore                 # Standard Python/PostgreSQL gitignore
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- PostgreSQL installed and running on `localhost:5432`

### 2. Environment Setup
Clone the repository and create a virtual environment:
```bash
git clone <your-repo-url>
cd nestorbird-rishabh

# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration
Copy `.env.example` to `.env` and set your PostgreSQL credentials:
```bash
copy .env.example .env
```

Edit `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scrapedb
DB_USER=postgres
DB_PASSWORD=your_postgres_password

API_HOST=127.0.0.1
API_PORT=8000
```

Initialize the database and tables:
```bash
python scripts/init_db.py
```

### 4. Running the API Server
Start the FastAPI server:
```bash
python -m uvicorn app.main:app --reload
```
The API is now live at:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

---

## 🔍 How to Identify a Dynamic Website

1. **Disable JavaScript in Browser Settings:**
   - In Google Chrome or Edge, open DevTools (`F12` or `Ctrl+Shift+I`).
   - Press `Ctrl+Shift+P` (Command Menu) and type `Disable JavaScript`.
   - Refresh the target page (e.g., `https://quotes.toscrape.com/js/`).
   - **Observation:** If quotes/products/data do not load without JavaScript, it confirms the website is dynamic and relies on client-side JS/APIs.
2. **Inspect Network Requests:**
   - Go to the `Network` tab in DevTools and filter by `Fetch/XHR`.
   - Observe AJAX calls returning JSON data.
3. **Inspect Page Source:**
   - Press `Ctrl+U` to view the raw HTML.
   - Dynamic sites often embed data in `<script>` tags (e.g. `var data = [...]` or `<script id="__NEXT_DATA__">`), which our scraper automatically identifies and parses.

---

## 🛠️ API Reference & Examples

### 1. Scrape a Dynamic Website & Save to PostgreSQL
`POST /api/scrape`
```bash
curl -X POST "http://127.0.0.1:8000/api/scrape" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://quotes.toscrape.com/js/",
       "entity_type": "quote"
     }'
```

### 2. Read Scraped Records (with Filtering & Pagination)
`GET /api/data?limit=10&offset=0&entity_type=quote`
```bash
curl -X GET "http://127.0.0.1:8000/api/data?limit=10"
```

### 3. Get Single Record by ID
`GET /api/data/{id}`
```bash
curl -X GET "http://127.0.0.1:8000/api/data/1"
```

### 4. Manually Create a Record
`POST /api/data`
```bash
curl -X POST "http://127.0.0.1:8000/api/data" \
     -H "Content-Type: application/json" \
     -d '{
       "source_url": "https://example.com/custom",
       "entity_type": "note",
       "title": "Sample Title",
       "content": "Custom content description",
       "raw_data": {"category": "tech", "priority": 1}
     }'
```

### 5. Update an Existing Record
`PUT /api/data/{id}`
```bash
curl -X PUT "http://127.0.0.1:8000/api/data/1" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Updated Title",
       "content": "Updated content text"
     }'
```

### 6. Delete a Record
`DELETE /api/data/{id}`
```bash
curl -X DELETE "http://127.0.0.1:8000/api/data/1"
```

### 7. View Database Schema
- **List Tables:** `GET /api/schema/tables`
- **View Column Types:** `GET /api/schema/tables/scraped_records`
- **Full Schema:** `GET /api/schema`
```bash
curl -X GET "http://127.0.0.1:8000/api/schema/tables/scraped_records"
```

---

## 📊 CSV Export Script

A separate script using Python's native `csv` module generates clean CSV files directly from the PostgreSQL database.

```bash
# Export all records to default timestamped file in exports/ directory:
python scripts/export_csv.py

# Export with custom destination file:
python scripts/export_csv.py --output exports/my_quotes.csv

# Filter by source URL or category:
python scripts/export_csv.py --url https://quotes.toscrape.com/js/ --entity-type quote --limit 100
```

---

## 📹 Loom Walkthrough Video

A detailed presentation script is provided in [`docs/LOOM_SCRIPT.md`](file:///c:/Users/rt815/Desktop/1st%20assignment/nestorbird-rishabh/docs/LOOM_SCRIPT.md).  
Use it to record a 3-5 minute video demonstrating:
1. Dynamic website identification by disabling JavaScript in DevTools.
2. Architecture and modular code structure in VS Code.
3. Live execution of Scraping, CRUD, and Schema APIs via Swagger UI (`/docs`).
4. Standalone CSV generation script execution.