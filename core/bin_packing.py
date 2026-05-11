import math
from typing import List, Dict, Any

from shapely.geometry import box, Point
from shapely.affinity import rotate as shapely_rotate


def is_rect_inside_circle(x: float, y: float, w: float, h: float, cx: float, cy: float, r: float, tol: float = 1e-9) -> bool:
    """Check whether all four corners of the rectangle lie inside the circle.

    Coordinates: x,y are the rectangle's top-left corner in the same coordinate system as cx,cy.
    """
    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    r2 = r * r + tol
    return all((px - cx) ** 2 + (py - cy) ** 2 <= r2 for px, py in corners)


def _rect_poly(x: float, y: float, w: float, h: float, rotation: int = 0):
    """Return shapely polygon for rectangle positioned at top-left (x,y) with given rotation (degrees).

    rotation is applied around the rectangle center. Rotation supports multiples of 90 for efficiency.
    """
    p = box(x, y, x + w, y + h)
    if rotation % 360 == 0:
        return p
    cx = x + w / 2.0
    cy = y + h / 2.0
    return shapely_rotate(p, rotation, origin=(cx, cy))


def optimize_placement_circular(items: List[Dict[str, Any]], disk_diameter: float, disk_thickness: float = 0.0, *, step: float = 2.0, angle_step_deg: int = 10):
    """
    Spiral-based greedy circular packing.

    - items: list of dicts with keys: file_id (or item_id), w, h
    - disk_diameter: mm
    - disk_thickness: unused here but kept for signature compatibility

    Returns structure:
    {
      "disks": [ {"disk_index": 0, "placed": [...], "unplaced": [], "waste_rate": 0.23, "disk_utilization": 0.77} ],
      "total_waste_rate": 0.31,
      "unplaced": [...]
    }
    """
    normalized = []
    for it in items:
        item_id = it.get('file_id') or it.get('item_id') or it.get('id')
        w = float(it.get('w', 0.0))
        h = float(it.get('h', 0.0))
        normalized.append({'item_id': item_id, 'w': w, 'h': h})

    normalized.sort(key=lambda x: x['w'] * x['h'], reverse=True)

    r = disk_diameter / 2.0
    cx = cy = r
    disk_area = math.pi * r * r

    total_area = sum(it['w'] * it['h'] for it in normalized)
    est_disks = max(1, int(math.ceil(total_area / (disk_area if disk_area > 0 else 1))))
    max_disks = est_disks + 2

    disks = []
    unplaced_global = []

    def _valid_position(nx, ny, w, h, rotation, placed_polys, disk_poly, margin: float = 0.5):
        if rotation % 180 == 90:
            poly = box(nx, ny, nx + w, ny + h)
            cx_r = nx + w / 2.0
            cy_r = ny + h / 2.0
            poly = shapely_rotate(poly, rotation, origin=(cx_r, cy_r))
        else:
            poly = box(nx, ny, nx + w, ny + h)

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

    for di in range(max_disks):
        disks.append({'disk_index': di, 'placed': [], 'unplaced': [], 'waste_rate': 1.0})

    disk_polys = [Point(cx, cy).buffer(r, resolution=256) for _ in range(max_disks)]
    placed_polys_per_disk = [[] for _ in range(max_disks)]

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
                        w_eff = it['h'] if rot % 180 == 90 else it['w']
                        h_eff = it['w'] if rot % 180 == 90 else it['h']
                        nx = cx_try - w_eff / 2.0
                        ny = cy_try - h_eff / 2.0
                        if _valid_position(nx, ny, w_eff, h_eff, rot, placed_polys, disk_poly):
                            placed_rec = {'item_id': it['item_id'], 'x': nx, 'y': ny, 'w': w_eff, 'h': h_eff, 'rotation': rot}
                            disks[di]['placed'].append(placed_rec)
                            placed_polys.append(box(nx, ny, nx + w_eff, ny + h_eff))
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            unplaced_global.append({'item_id': it['item_id'], 'w': it['w'], 'h': it['h']})

    from core.waste_calc import compute_disk_utilization

    disk_utils = []
    for di in range(max_disks):
        placed_items = disks[di]['placed']
        if len(placed_items) == 0:
            break
        util = compute_disk_utilization(placed_items, disk_diameter)
        disks[di]['disk_utilization'] = util
        disks[di]['waste_rate'] = float(max(0.0, min(1.0, 1.0 - util)))
        disks[di]['unplaced'] = []
        disk_utils.append(util)

    disks = [d for d in disks if d['placed']]
    total_util = float(sum(disk_utils) / len(disk_utils)) if disk_utils else 0.0

    return {
        'disks': disks,
        'total_waste_rate': float(max(0.0, min(1.0, 1.0 - total_util))),
        'unplaced': unplaced_global,
    }
