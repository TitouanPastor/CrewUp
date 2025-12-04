from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

@app.get("/")
async def root():
    return {"service": "rating", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}