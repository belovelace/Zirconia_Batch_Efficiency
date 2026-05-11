from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from backend.routers import upload, optimize
from backend.routers import visualize, demo
from pathlib import Path

app = FastAPI(title="ZirSave API", debug=True)
app.include_router(upload.router)
app.include_router(optimize.router)
app.include_router(visualize.router)
app.include_router(demo.router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/frontend/index.html")

# Serve frontend — mounted after route so '/' redirect takes priority
_frontend_dir = (Path(__file__).resolve().parent.parent / "frontend")
app.mount("/frontend", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

# Start log shipper at startup if configured
from backend.log_shipper import start_shipper, stop_shipper

@app.on_event("startup")
def startup_event():
    start_shipper()

@app.on_event("shutdown")
def shutdown_event():
    stop_shipper()

@app.get("/health/live")
def live():
    return {"status": "ok"}
