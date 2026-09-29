"""
Project Runner Script.
Allows starting the FastAPI server directly with:
    python run.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(" 🚀 Starting NestorBird Dynamic Scraper & Database Studio")
    print(f" 🌐 Dashboard URL:    http://{settings.API_HOST}:{settings.API_PORT}")
    print(f" 📖 Swagger API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
