from fastapi import FastAPI
from app.routers import panchayat

app = FastAPI(
    title="TerraMind API",
    version="1.0.0"
)

app.include_router(panchayat.router)

@app.get("/")
def root():
    return {"message": "TerraMind Backend"}

@app.get("/health")
def health():
    return {"status": "ok"}