import math
from typing import List, Dict, Any, Optional

from shapely.geometry import box, Point
from shapely.affinity import rotate as shapely_rotate


def is_rect_inside_circle(x: float, y: float, w: float, h: float,
                          cx: float, cy: float, r: float, tol: float = 1e-9) -> bool:
    """Return True if all four corners of the rectangle lie inside the circle."""
    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    r2 = r * r + tol
    return all((px - cx) ** 2 + (py - cy) ** 2 <= r2 for px, py in corners)


def optimize_placement_circular(
    items: List[Dict[str, Any]],
    disk_diameter: float,
    disk_thickness: float = 0.0,
    *,
    step: float = 2.0,
    angle_step_deg: int = 10,
    shrinkage_factor: float = 1.0,
    initial_placements: Optional[List[Dict]] = None,
):
    """
    Spiral-based greedy circular packing.

    shrinkage_factor: multiply item w/h by this before packing so the milled blank
                      accounts for sintering shrinkage. Typically 1.20-1.25 for zirconia.
                      Each placed item stores both milling dims (w, h) and design dims
                      (w_design, h_design).

    initial_placements: list of {disk_index, placed: [{x,y,w,h,rotation,...}]} representing
                        items already on existing disks.  New items are fitted into these
                        disks first before opening new ones.
    """
    normalized = []
    for it in items:
        item_id = it.get("file_id") or it.get("item_id") or it.get("id")
        w = float(it.get("w", 0.0))
        h = float(it.get("h", 0.0))
        normalized.append({
            "item_id": item_id,
            "w": w * shrinkage_factor,
            "h": h * shrinkage_factor,
            "w_design": w,
            "h_design": h,
        })

    normalized.sort(key=lambda x: x["w"] * x["h"], reverse=True)

    r = disk_diameter / 2.0
    cx = cy = r
    disk_area = math.pi * r * r

    total_new_area = sum(it["w"] * it["h"] for it in normalized)
    est_new_disks = max(1, int(math.ceil(total_new_area / (disk_area or 1))))
    init_disk_count = len(initial_placements) if initial_placements else 0
    max_disks = init_disk_count + est_new_disks + 2

    disks = [{"disk_index": di, "placed": [], "unplaced": [], "waste_rate": 1.0} for di in range(max_disks)]
    disk_polys = [Point(cx, cy).buffer(r, resolution=256) for _ in range(max_disks)]
    placed_polys_per_disk: List[list] = [[] for _ in range(max_disks)]

    # Seed existing placements so new items respect already-occupied space
    if initial_placements:
        for disk_init in initial_placements:
            di = disk_init.get("disk_index", 0)
            if di >= max_disks:
                continue
            for itm in disk_init.get("placed", []):
                x, y = float(itm["x"]), float(itm["y"])
                w, h = float(itm["w"]), float(itm["h"])
                rot = itm.get("rotation", 0)
                poly = box(x, y, x + w, y + h)
                if rot % 180 == 90:
                    poly = shapely_rotate(poly, rot, origin=(x + w / 2, y + h / 2))
                placed_polys_per_disk[di].append(poly)
                disks[di]["placed"].append(itm)

    def _valid_position(nx, ny, w, h, rotation, placed_polys, disk_poly, margin=0.5):
        poly = box(nx, ny, nx + w, ny + h)
        if rotation % 180 == 90:
            poly = shapely_rotate(poly, rotation, origin=(nx + w / 2, ny + h / 2))
        try:
            inner = disk_poly.buffer(-margin)
            if inner.is_empty:
                inner = disk_poly
        except Exception:
            inner = disk_poly
        if not inner.contains(poly):
            return False
        for p in placed_polys:
            if poly.intersects(p) and poly.intersection(p).area > 1e-6:
                return False
        return True

    unplaced_global = []

    for it in normalized:
        placed = False
        for di in range(max_disks):
            disk_poly = disk_polys[di]
            placed_polys = placed_polys_per_disk[di]
            max_layers = int(math.ceil(r / step))
            for layer in range(0, max_layers + 1):
                radius = layer * step
                angles = [0] if radius == 0 else list(range(0, 360, angle_step_deg))
                for ang in angles:
                    rad = math.radians(ang)
                    cx_try = cx + radius * math.cos(rad)
                    cy_try = cy + radius * math.sin(rad)
                    for rot in (0, 90):
                        if rot == 90:
                            w_eff, h_eff = it["h"], it["w"]
                            w_d, h_d = it["h_design"], it["w_design"]
                        else:
                            w_eff, h_eff = it["w"], it["h"]
                            w_d, h_d = it["w_design"], it["h_design"]
                        nx = cx_try - w_eff / 2.0
                        ny = cy_try - h_eff / 2.0
                        if _valid_position(nx, ny, w_eff, h_eff, rot, placed_polys, disk_poly):
                            placed_rec = {
                                "item_id": it["item_id"],
                                "x": nx, "y": ny,
                                "w": w_eff, "h": h_eff,
                                "w_design": w_d, "h_design": h_d,
                                "rotation": rot,
                                "shrinkage_factor": shrinkage_factor,
                            }
                            disks[di]["placed"].append(placed_rec)
                            placed_polys_per_disk[di].append(box(nx, ny, nx + w_eff, ny + h_eff))
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            unplaced_global.append({"item_id": it["item_id"], "w": it["w"], "h": it["h"]})

    from core.waste_calc import compute_disk_utilization

    disk_utils = []
    for di in range(max_disks):
        placed_items = disks[di]["placed"]
        if not placed_items:
            break
        util = compute_disk_utilization(placed_items, disk_diameter)
        disks[di]["disk_utilization"] = util
        disks[di]["waste_rate"] = float(max(0.0, min(1.0, 1.0 - util)))
        disks[di]["unplaced"] = []
        disk_utils.append(util)

    disks = [d for d in disks if d["placed"]]
    total_util = float(sum(disk_utils) / len(disk_utils)) if disk_utils else 0.0

    return {
        "disks": disks,
        "disk_diameter": disk_diameter,
        "disk_radius": r,
        "shrinkage_factor": shrinkage_factor,
        "total_waste_rate": float(max(0.0, min(1.0, 1.0 - total_util))),
        "unplaced": unplaced_global,
    }
