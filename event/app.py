"""
Development entry point for Event Service.

Run with: python app.py
For production, use: uvicorn app.main:app
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )