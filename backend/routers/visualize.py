from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.routers import optimize as optimize_router
import io
import platform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import random


def _set_korean_font():
    if platform.system() == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
    elif platform.system() == 'Darwin':
        plt.rcParams['font.family'] = 'AppleGothic'
    else:
        for name in ('NanumGothic', 'NanumBarunGothic', 'UnDotum', 'Noto Sans CJK KR'):
            if any(name in f.name for f in fm.fontManager.ttflist):
                plt.rcParams['font.family'] = name
                break
    plt.rcParams['axes.unicode_minus'] = False


_set_korean_font()

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{result_id}/visualization")
async def visualize(result_id: str):
    r = optimize_router.RESULTS.get(result_id)
    if r is None:
        raise HTTPException(status_code=404, detail="result not found")

    placement = r.get("placement") or r
    disks = placement.get("disks", [])
    if not disks:
        raise HTTPException(status_code=404, detail="no disks to visualize")

    disk_diameter = float(placement.get("disk_diameter", 98.0))
    disk_radius = disk_diameter / 2.0
    shrinkage_factor = float(placement.get("shrinkage_factor", r.get("shrinkage_factor", 1.0)))
    has_shrinkage = shrinkage_factor > 1.001

    n = len(disks)
    fig, axs = plt.subplots(1, n, figsize=(5 * n, 5.5))
    if n == 1:
        axs = [axs]

    rng = random.Random(42)  # deterministic colours per result

    for ax, d in zip(axs, disks):
        disk_index = d.get("disk_index", 0)

        # Disk outline
        circle = plt.Circle((disk_radius, disk_radius), disk_radius,
                             color="#1a3a6b", fill=False, linewidth=1.5)
        ax.add_patch(circle)
        ax.set_xlim(0, disk_diameter)
        ax.set_ylim(0, disk_diameter)
        ax.set_aspect("equal")
        ax.set_facecolor("#f0f4ff")

        util = d.get("disk_utilization", 0.0)
        save_rate = r.get("disk_saving_rate", 0.0)
        title = f"Disk {disk_index}  |  활용률 {util*100:.1f}%"
        if has_shrinkage:
            title += f"  |  수축 ×{shrinkage_factor}"
        ax.set_title(title, fontsize=10)

        for itm in d.get("placed", []):
            x = float(itm.get("x", 0))
            y = float(itm.get("y", 0))
            w = float(itm.get("w", 0))
            h = float(itm.get("h", 0))
            w_d = float(itm.get("w_design", w))
            h_d = float(itm.get("h_design", h))
            color = (rng.random() * 0.6 + 0.2, rng.random() * 0.5 + 0.2, rng.random() * 0.6 + 0.3)

            # Milling rect (outer — what gets machined)
            mill_rect = plt.Rectangle((x, y), w, h, color=color, alpha=0.70, linewidth=0.5,
                                      edgecolor="white")
            ax.add_patch(mill_rect)

            # Design rect (inner dashed — final crown size after sintering)
            if has_shrinkage and (w_d < w - 0.1 or h_d < h - 0.1):
                ox = (w - w_d) / 2
                oy = (h - h_d) / 2
                design_rect = plt.Rectangle(
                    (x + ox, y + oy), w_d, h_d,
                    fill=False, linestyle="--", edgecolor="white", linewidth=0.9, alpha=0.9,
                )
                ax.add_patch(design_rect)

        ax.tick_params(labelsize=7)
        ax.set_xlabel("mm", fontsize=7)
        ax.set_ylabel("mm", fontsize=7)

    # Legend
    legend_handles = [mpatches.Patch(color="#6699cc", alpha=0.7, label="밀링 크기 (가공 치수)")]
    if has_shrinkage:
        legend_handles.append(mpatches.Patch(fill=False, linestyle="--",
                                              edgecolor="gray", label=f"소결 후 크기 (설계 치수, ÷{shrinkage_factor})"))
    fig.legend(handles=legend_handles, loc="lower center", ncol=2, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
