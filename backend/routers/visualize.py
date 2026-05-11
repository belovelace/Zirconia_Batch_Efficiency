from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.routers import optimize as optimize_router
from core.bin_packing import optimize_placement_circular
from core.stl_parser import parse_stl
from pathlib import Path
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{case_id}/visualization")
async def visualize(case_id: str):
    # Load result from in-memory RESULTS or DB (optimise router stores results in memory under RESULTS)
    try:
        from backend.routers.optimize import RESULTS
        r = RESULTS.get(case_id)
    except Exception:
        r = None

    if r is None:
        raise HTTPException(status_code=404, detail="result not found")

    placement = r.get('placement') or r

    disks = placement.get('disks', [])
    if not disks:
        raise HTTPException(status_code=404, detail='no disks to visualize')

    n = len(disks)
    fig, axs = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axs = [axs]

    for ax, d in zip(axs, disks):
        disk_index = d.get('disk_index')
        # draw disk
        circle = plt.Circle((placement.get('disk_radius', 49.0), placement.get('disk_radius', 49.0)), placement.get('disk_radius', 49.0), color='black', fill=False)
        ax.add_patch(circle)
        ax.set_xlim(0, placement.get('disk_diameter', 98.0))
        ax.set_ylim(0, placement.get('disk_diameter', 98.0))
        ax.set_aspect('equal')
        # show disk utilization and saving rate if available
        util = d.get('disk_utilization')
        save_rate = placement.get('disk_saving_rate') or placement.get('disk_saving_rate', None)
        title = f"Disk {disk_index} — util {util:.2f}"
        if save_rate is not None:
            title += f" — saving {save_rate*100:.0f}%"
        ax.set_title(title)
        for itm in d.get('placed', []):
            x = itm.get('x')
            y = itm.get('y')
            w = itm.get('w')
            h = itm.get('h')
            color = (random.random(), random.random(), random.random())
            rect = plt.Rectangle((x, y), w, h, color=color, alpha=0.8)
            ax.add_patch(rect)

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')
