from fastapi import APIRouter, HTTPException
from typing import Dict
from core.bin_packing import optimize_placement_circular
from core.waste_calc import compute_waste_rate
import uuid

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

    placement = optimize_placement_circular(items, disk_diameter=diameter)

    # compute simple waste rate
    placed_items = placement.get("disks", [])[0].get("items", []) if placement.get("disks") else []
    waste_rate = compute_waste_rate(placed_items, diameter)

    result_id = str(uuid.uuid4())

    # persist result if possible
    try:
        with db.SessionLocal() as session:
            session.execute(models.results.insert().values(id=result_id, case_id=case_id, placement=placement, waste_rate=waste_rate, n_disks=len(placement.get("disks", []))))
            session.commit()
    except Exception:
        RESULTS[result_id] = {"id": result_id, "case_id": case_id, "placement": placement, "waste_rate": waste_rate}

    return {"result_id": result_id, "waste_rate": waste_rate, "n_disks": len(placement.get("disks", []))}

@router.get("/result/{result_id}")
async def get_result(result_id: str):
    r = RESULTS.get(result_id)
    if not r:
        raise HTTPException(status_code=404, detail="result not found")
    return r
