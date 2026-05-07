from fastapi import FastAPI
from backend.routers import upload, optimize

app = FastAPI(title="ZirSave API", debug=True)
app.include_router(upload.router)
app.include_router(optimize.router)

@app.get("/health/live")
def live():
    return {"status": "ok"}
