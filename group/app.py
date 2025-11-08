from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"service": "group", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}