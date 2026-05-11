from fastapi import APIRouter, HTTPException
from typing import Dict
from core.bin_packing import optimize_placement_circular
from core.waste_calc import compute_disk_utilization, compute_disk_saving_rate
import uuid
from backend.utils import log_exception

router = APIRouter(prefix="/optimize", tags=["optimize"])

# Simple in-memory results store
RESULTS: Dict[str, Dict] = {}

# Import the in-memory CASES/FILES from upload module
from backend.routers import upload as upload_module

@router.post("/")
async def optimize(case_id: str):
    # Try to load case from Postgres first
    from backend import db, models
    try:
        with db.SessionLocal() as session:
            row = session.execute(models.cases.select().where(models.cases.c.id == case_id)).first()
            if not row:
                raise HTTPException(status_code=404, detail="case not found")
            disk_config = row._mapping.get("disk_config") or {}
            diameter = float(disk_config.get("diameter", 98.0))
            # load files
            rows = session.execute(models.files.select().where(models.files.c.case_id == case_id)).all()
            items = []
            for r in rows:
                mapping = r._mapping
                if not mapping.get("feasible", 1):
                    continue
                items.append({"file_id": mapping.get("id"), "w": mapping.get("bbox_w"), "h": mapping.get("bbox_h")})
    except Exception:
        # fallback to in-memory
        case = upload_module.CASES.get(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="case not found")
        disk_config = case.get("disk_config", {})
        diameter = float(disk_config.get("diameter", 98.0))
        items = []
        for f in case.get("files", []):
            if not f.get("feasible", True):
                continue
            items.append({"file_id": f["id"], "w": f["bbox_w"], "h": f["bbox_h"]})

    try:
        placement = optimize_placement_circular(items, disk_diameter=diameter)

        # compute per-disk utilizations
        disks = placement.get("disks", [])
        utilizations = []
        for d in disks:
            utilis = compute_disk_utilization(d.get("placed", d.get("items", [])), diameter)
            d["disk_utilization"] = utilis
            utilizations.append(utilis)

        optimized_disk_count = len(disks)
        # naive_disk_count uses number of feasible items in the case (count of files)
        # If DB path, count rows; else fall back to in-memory case
        try:
            # try to load from DB
            rows = session.execute(models.files.select().where(models.files.c.case_id == case_id)).all()
            naive_count = len(rows) if rows else 0
        except Exception:
            # fallback to in-memory
            case = upload_module.CASES.get(case_id, {})
            naive_count = len(case.get("files", []))

        saving_rate = compute_disk_saving_rate(naive_count, optimized_disk_count)
        result_id = str(uuid.uuid4())

        # persist result if possible
        try:
            with db.SessionLocal() as session:
                session.execute(models.results.insert().values(id=result_id, case_id=case_id, placement=placement, waste_rate=None, n_disks=len(placement.get("disks", []))))
                session.commit()
        except Exception:
            RESULTS[result_id] = {"id": result_id, "case_id": case_id, "placement": placement, "disk_saving_rate": saving_rate}

        return {"result_id": result_id, "disk_saving_rate": saving_rate, "n_disks": len(placement.get("disks", [])), "utilizations": utilizations}
    except Exception as exc:
        err_id = log_exception(exc)
        raise HTTPException(status_code=500, detail=f"internal server error (id={err_id})")

@router.get("/result/{result_id}")
async def get_result(result_id: str):
    r = RESULTS.get(result_id)
    if not r:
        raise HTTPException(status_code=404, detail="result not found")
    return r
