# Loom Video Walkthrough Script (3-5 Minutes)

Use this guide while recording your Loom video presentation for NestorBird.

---

## 🎯 Recording Checklist Before You Start
1. Have your code open in VS Code.
2. Have PostgreSQL running.
3. Have your terminal open with the FastAPI server running (`python -m uvicorn app.main:app --reload`).
4. Have your browser open with two tabs:
   - Tab 1: `http://127.0.0.1:8000/docs` (Interactive Swagger API documentation)
   - Tab 2: `https://quotes.toscrape.com/js/` (Example dynamic website)

---

## ⏱️ Video Timeline & Talking Points

### [0:00 - 0:45] Introduction & Understanding Dynamic Websites
- **What to say:**
  > "Hello everyone! In this video, I will walk you through my implementation of Assignment 1 for NestorBird: building a dynamic web scraper, storing the data in PostgreSQL using psycopg2, providing CRUD and Schema APIs, and exporting data to CSV.
  >
  > Let's first address the core question: *How do we identify a dynamic website?*
  > If I visit `quotes.toscrape.com/js/`, open Chrome DevTools, open the command menu with Ctrl+Shift+P, and select 'Disable JavaScript', then refresh—the quotes vanish!
  > This confirms that the website relies on client-side JavaScript to render its data at runtime.
  > In dynamic sites, the data often resides either in runtime API endpoints or embedded JavaScript variables. Our scraper identifies and parses these automatically."

### [0:45 - 1:30] Architecture & Folder Structure
- **What to show:** Open your VS Code editor and show the file tree.
- **What to say:**
  > "To ensure the code is modular and maintainable, I organized the project into clean layers:
  > - `app/scraper/`: Contains `detector.py` for spotting dynamic frameworks and script tags, `parser.py` for structured DOM and JSON extraction, and `engine.py` to coordinate requests.
  > - `app/database.py`: Handles PostgreSQL connections using `psycopg2` and parameterized SQL queries.
  > - `app/api/`: Implements FastAPI routers for scraping, CRUD, and schema introspection.
  > - `scripts/`: Contains `init_db.py` for database setup and `export_csv.py` using Python's native `csv` module."

### [1:30 - 2:45] Live Demo: Scrape & CRUD APIs via Swagger UI
- **What to show:** Switch to `http://127.0.0.1:8000/docs`.
- **What to say & do:**
  1. **Scraping Endpoint:**
     - Open `POST /api/scrape`. Click *Try it out*.
     - Enter URL: `https://quotes.toscrape.com/js/`, entity type: `quote`.
     - Click *Execute*.
     - Show the response:
       > "Notice that our scraper detected that this was a dynamic JavaScript site, extracted all 10 quotes with their authors, tags, and text, and saved each record into PostgreSQL."
  2. **Read / List Endpoint:**
     - Open `GET /api/data`. Click *Execute*.
     - Show that the records are retrieved from PostgreSQL with pagination and filtering.
  3. **Create & Update:**
     - Demonstrate `POST /api/data` or `PUT /api/data/{id}` to show that full CRUD operations work seamlessly.
  4. **Schema APIs:**
     - Open `GET /api/schema/tables` and `GET /api/schema/tables/scraped_records`.
     - Show how it introspects PostgreSQL's `information_schema` to return column names and data types.

### [2:45 - 3:30] Standalone CSV Export Demonstration
- **What to show:** Switch to terminal.
- **What to say & do:**
  - Run the command:
    ```bash
    python scripts/export_csv.py
    ```
  - Open the generated CSV file in VS Code or Excel.
  - Show the clean headers (`Record ID`, `Source URL`, `Title`, `Content`, `Raw JSON Metadata`, `Created At`).
  - Explain:
    > "Here is our standalone CSV generation script. It uses Python's built-in `csv` module, queries PostgreSQL using `psycopg2`, formats headers cleanly, and exports the data ready for reporting or analysis."

### [3:30 - 4:00] Conclusion
- **What to say:**
  > "To summarize, the solution handles dynamic and static websites, stores structured heterogeneous data in PostgreSQL via pure psycopg2 SQL queries, provides full CRUD and Schema REST APIs with Swagger documentation, and includes a standalone CSV generator.
  > Thank you for your time, and I look forward to your feedback!"
