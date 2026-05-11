from fastapi import APIRouter, HTTPException
from typing import Dict
from core.bin_packing import optimize_placement_circular
from core.waste_calc import compute_disk_utilization, compute_disk_saving_rate
import uuid
from backend.utils import log_exception

router = APIRouter(prefix="/optimize", tags=["optimize"])

RESULTS: Dict[str, Dict] = {}

from backend.routers import upload as upload_module


def _load_case(case_id: str):
    """Load disk_config + feasible items for a case. Returns (disk_config, items)."""
    from backend import db, models
    try:
        with db.SessionLocal() as session:
            row = session.execute(models.cases.select().where(models.cases.c.id == case_id)).first()
            if not row:
                raise HTTPException(status_code=404, detail="case not found")
            disk_config = row._mapping.get("disk_config") or {}
            rows = session.execute(models.files.select().where(models.files.c.case_id == case_id)).all()
            items = []
            for r in rows:
                m = r._mapping
                if not m.get("feasible", 1):
                    continue
                items.append({"file_id": m.get("id"), "w": m.get("bbox_w"), "h": m.get("bbox_h")})
            return disk_config, items
    except HTTPException:
        raise
    except Exception:
        pass

    # fallback to in-memory
    case = upload_module.CASES.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    disk_config = case.get("disk_config", {})
    items = [
        {"file_id": f["id"], "w": f["bbox_w"], "h": f["bbox_h"]}
        for f in case.get("files", [])
        if f.get("feasible", True)
    ]
    return disk_config, items


def _save_result(result_id: str, case_id: str, placement: dict, saving_rate: float,
                 shrinkage_factor: float, diameter: float, item_count: int):
    from backend import db, models
    try:
        with db.SessionLocal() as session:
            session.execute(models.results.insert().values(
                id=result_id, case_id=case_id, placement=placement,
                waste_rate=None, n_disks=len(placement.get("disks", []))
            ))
            session.commit()
    except Exception:
        pass
    RESULTS[result_id] = {
        "id": result_id,
        "case_id": case_id,
        "placement": placement,
        "disk_saving_rate": saving_rate,
        "shrinkage_factor": shrinkage_factor,
        "disk_diameter": diameter,
        "item_count": item_count,
    }


@router.post("/")
async def optimize(case_id: str):
    try:
        disk_config, items = _load_case(case_id)
        diameter = float(disk_config.get("diameter", 98.0))
        shrinkage_factor = float(disk_config.get("shrinkage_factor", 1.25))

        placement = optimize_placement_circular(
            items, disk_diameter=diameter, shrinkage_factor=shrinkage_factor
        )

        disks = placement.get("disks", [])
        utilizations = []
        for d in disks:
            u = compute_disk_utilization(d.get("placed", []), diameter)
            d["disk_utilization"] = u
            utilizations.append(u)

        naive_count = len(items)
        saving_rate = compute_disk_saving_rate(naive_count, len(disks))
        result_id = str(uuid.uuid4())
        _save_result(result_id, case_id, placement, saving_rate, shrinkage_factor, diameter, naive_count)

        return {
            "result_id": result_id,
            "disk_saving_rate": saving_rate,
            "n_disks": len(disks),
            "utilizations": utilizations,
            "shrinkage_factor": shrinkage_factor,
            "unplaced_count": len(placement.get("unplaced", [])),
        }
    except HTTPException:
        raise
    except Exception as exc:
        err_id = log_exception(exc)
        raise HTTPException(status_code=500, detail=f"internal server error (id={err_id})")


@router.post("/incremental")
async def optimize_incremental(result_id: str, new_case_id: str):
    """
    Add new STL files (new_case_id) onto the disks from an existing result (result_id).
    Items are placed into already-used disks first; new disks are opened only if needed.
    Returns a new result_id with the merged placement.
    """
    try:
        existing = RESULTS.get(result_id)
        if not existing:
            raise HTTPException(status_code=404, detail="existing result not found")

        existing_placement = existing.get("placement", {})
        initial_placements = existing_placement.get("disks", [])
        diameter = float(existing.get("disk_diameter", existing_placement.get("disk_diameter", 98.0)))
        shrinkage_factor = float(existing.get("shrinkage_factor", existing_placement.get("shrinkage_factor", 1.25)))
        prev_item_count = int(existing.get("item_count", 0))

        disk_config, new_items = _load_case(new_case_id)

        placement = optimize_placement_circular(
            new_items,
            disk_diameter=diameter,
            shrinkage_factor=shrinkage_factor,
            initial_placements=initial_placements,
        )

        disks = placement.get("disks", [])
        utilizations = []
        for d in disks:
            u = compute_disk_utilization(d.get("placed", []), diameter)
            d["disk_utilization"] = u
            utilizations.append(u)

        total_items = prev_item_count + len(new_items)
        saving_rate = compute_disk_saving_rate(total_items, len(disks))
        new_result_id = str(uuid.uuid4())
        _save_result(new_result_id, new_case_id, placement, saving_rate, shrinkage_factor, diameter, total_items)

        return {
            "result_id": new_result_id,
            "disk_saving_rate": saving_rate,
            "n_disks": len(disks),
            "utilizations": utilizations,
            "shrinkage_factor": shrinkage_factor,
            "total_items": total_items,
            "unplaced_count": len(placement.get("unplaced", [])),
        }
    except HTTPException:
        raise
    except Exception as exc:
        err_id = log_exception(exc)
        raise HTTPException(status_code=500, detail=f"internal server error (id={err_id})")


@router.get("/result/{result_id}")
async def get_result(result_id: str):
    r = RESULTS.get(result_id)
    if not r:
        raise HTTPException(status_code=404, detail="result not found")
    return r
