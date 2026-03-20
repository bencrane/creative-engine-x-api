from fastapi import FastAPI

app = FastAPI(title="creative-engine-x-api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "creative-engine-x"}
