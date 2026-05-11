from fastapi import FastAPI
from backend.routers import upload, optimize
from backend.routers import visualize
from fastapi import FastAPI

app = FastAPI(title="ZirSave API", debug=True)
app.include_router(upload.router)
app.include_router(optimize.router)
app.include_router(visualize.router)

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
