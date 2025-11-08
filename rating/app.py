from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"service": "rating", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}