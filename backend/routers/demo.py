from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

from core.bin_packing import optimize_placement_circular
from core.waste_calc import compute_disk_utilization, compute_disk_saving_rate
from backend.routers.optimize import RESULTS

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoItem(BaseModel):
    item_id: str
    w: float
    h: float


class DemoRequest(BaseModel):
    items: List[DemoItem]
    disk_diameter: float = 98.0


@router.post("/optimize")
def demo_optimize(req: DemoRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="items is empty")

    raw_items = [{"file_id": it.item_id, "w": it.w, "h": it.h} for it in req.items]
    placement = optimize_placement_circular(raw_items, disk_diameter=req.disk_diameter)

    disks = placement.get("disks", [])
    utilizations = []
    for d in disks:
        u = compute_disk_utilization(d.get("placed", d.get("items", [])), req.disk_diameter)
        d["disk_utilization"] = u
        utilizations.append(u)

    naive_count = len(req.items)
    optimized_count = len(disks)
    saving_rate = compute_disk_saving_rate(naive_count, optimized_count)

    result_id = str(uuid.uuid4())
    RESULTS[result_id] = {
        "id": result_id,
        "placement": {**placement, "disk_diameter": req.disk_diameter, "disk_radius": req.disk_diameter / 2},
        "disk_saving_rate": saving_rate,
    }

    return {
        "result_id": result_id,
        "disk_saving_rate": saving_rate,
        "n_disks": optimized_count,
        "utilizations": utilizations,
    }
