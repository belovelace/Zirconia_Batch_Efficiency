import math
from rectpack import newPacker
from typing import List, Dict, Any, Tuple


def is_rect_inside_circle(x: float, y: float, w: float, h: float, cx: float, cy: float, r: float) -> bool:
    """Check whether all four corners of the rectangle lie inside the circle."""
    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    r2 = r * r
    return all((px - cx) ** 2 + (py - cy) ** 2 <= r2 for px, py in corners)


def optimize_placement_circular(items: List[Dict[str, Any]], disk_diameter: float, step: float = 1.0, timeout: float = 30.0) -> Dict[str, Any]:
    """Place rectangular items onto circular disks.

    items: list of dicts with keys: file_id, w, h
    Returns placement_result matching docs/TSD.md placement json format.
    """
    r = disk_diameter / 2.0
    cx = cy = r

    # First attempt: pack rectangles into square bounding box of the disk using rectpack
    packing_width = packing_height = disk_diameter

    packer = newPacker(rotation=False)

    for it in items:
        # rectpack expects integer sizes; use floats but cast to int for simplicity
        packer.add_rect(int(math.ceil(it["w"])), int(math.ceil(it["h"])), rid=it.get("file_id"))

    packer.add_bin(int(math.ceil(packing_width)), int(math.ceil(packing_height)))
    packer.pack()

    placed = []
    unplaced = []

    # rectpack provides a rect_list; handle either (x,y,w,h,rid) or (bin_index,x,y,w,h,rid)
    rects = packer.rect_list()
    for rect in rects:
        # Unpack flexibly depending on rectpack version
        if len(rect) == 6:
            _, x, y, w, h, fid = rect
        else:
            x, y, w, h, fid = rect
        # Verify rectangle inside circle
        if is_rect_inside_circle(x, y, w, h, cx, cy, r):
            placed.append({"file_id": fid, "x": float(x), "y": float(y), "angle": 0, "w": float(w), "h": float(h)})
        else:
            unplaced.append({"file_id": fid, "reason": "outside_circle_after_rectpack"})

    # Any items not added to packer (due to size) should be marked unplaced
    packed_ids = {p["file_id"] for p in placed} | {u["file_id"] for u in unplaced}
    for it in items:
        if it.get("file_id") not in packed_ids:
            unplaced.append({"file_id": it.get("file_id"), "reason": "too_large_for_bin"})

    # Simple single-disk result for now
    result = {"disks": [{"disk_index": 0, "items": placed}], "unplaced": unplaced}
    return result
