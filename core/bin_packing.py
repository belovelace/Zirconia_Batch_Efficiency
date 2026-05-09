import math
from typing import List, Dict, Any, Tuple, Optional

import numpy as np


def is_rect_inside_circle(x: float, y: float, w: float, h: float, cx: float, cy: float, r: float) -> bool:
    """Check whether all four corners of the rectangle lie inside the circle.

    Since both rectangle and circle are convex and a rectangle is the convex hull
    of its four corners, this check is exact.
    """
    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    r2 = r * r
    return all((px - cx) ** 2 + (py - cy) ** 2 <= r2 for px, py in corners)


def _rects_overlap(r1: Tuple[float, float, float, float], r2: Tuple[float, float, float, float]) -> bool:
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    if x1 + w1 <= x2 or x2 + w2 <= x1:
        return False
    if y1 + h1 <= y2 or y2 + h2 <= y1:
        return False
    return True


def _find_position(
    w: float,
    h: float,
    cx: float,
    cy: float,
    r: float,
    placed_rects: List[Tuple[float, float, float, float]],
    step: float,
) -> Optional[Tuple[float, float]]:
    """Vectorized grid scan returning the bottom-left-most (x, y) that:
    - keeps the rectangle inside the circle (all 4 corners)
    - does not overlap any already-placed rectangle
    """
    x_min = cx - r
    x_max = cx + r - w
    y_min = cy - r
    y_max = cy + r - h
    if x_max < x_min - 1e-9 or y_max < y_min - 1e-9:
        return None

    xs = np.arange(x_min, x_max + 1e-9, step)
    ys = np.arange(y_min, y_max + 1e-9, step)
    if xs.size == 0 or ys.size == 0:
        return None

    X, Y = np.meshgrid(xs, ys, indexing="xy")
    r2 = r * r
    valid = ((X - cx) ** 2 + (Y - cy) ** 2 <= r2)
    valid &= ((X + w - cx) ** 2 + (Y - cy) ** 2 <= r2)
    valid &= ((X - cx) ** 2 + (Y + h - cy) ** 2 <= r2)
    valid &= ((X + w - cx) ** 2 + (Y + h - cy) ** 2 <= r2)

    for (px, py, pw, ph) in placed_rects:
        overlap = (X + w > px) & (X < px + pw) & (Y + h > py) & (Y < py + ph)
        valid &= ~overlap

    if not valid.any():
        return None

    # argmax on row-major flatten finds first True scanning rows (y) then columns (x):
    # bottom-left fill order since ys is ascending.
    idx = int(np.argmax(valid))
    iy, ix = np.unravel_index(idx, valid.shape)
    return (float(xs[ix]), float(ys[iy]))


def _pack_one_disk(
    items: List[Dict[str, Any]],
    disk_diameter: float,
    step: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Greedy place items onto a single circular disk. Returns (placed, remaining).

    Items are tried largest-first. For each item, both orientations (0° and 90°)
    are attempted; the first valid position wins.
    """
    r = disk_diameter / 2.0
    cx = cy = r
    placed: List[Dict[str, Any]] = []
    placed_rects: List[Tuple[float, float, float, float]] = []
    remaining: List[Dict[str, Any]] = []

    sorted_items = sorted(items, key=lambda it: float(it["w"]) * float(it["h"]), reverse=True)

    for it in sorted_items:
        w = float(it["w"])
        h = float(it["h"])

        pos = _find_position(w, h, cx, cy, r, placed_rects, step)
        angle = 0
        chosen_w, chosen_h = w, h

        if pos is None and abs(w - h) > 1e-9:
            pos2 = _find_position(h, w, cx, cy, r, placed_rects, step)
            if pos2 is not None:
                pos = pos2
                angle = 90
                chosen_w, chosen_h = h, w

        if pos is None:
            remaining.append(it)
        else:
            x, y = pos
            placed.append({
                "file_id": it.get("file_id"),
                "x": float(x),
                "y": float(y),
                "angle": angle,
                "w": float(chosen_w),
                "h": float(chosen_h),
            })
            placed_rects.append((x, y, chosen_w, chosen_h))

    return placed, remaining


def optimize_placement_circular(
    items: List[Dict[str, Any]],
    disk_diameter: float,
    step: float = 1.0,
    timeout: float = 30.0,
    max_disks: int = 10,
) -> Dict[str, Any]:
    """Place rectangular items onto one or more circular disks.

    items: list of dicts with keys: file_id, w, h
    Returns placement_result matching docs/TSD.md placement json format.

    Algorithm:
    1. Filter out items whose diagonal exceeds disk diameter (cannot fit at any angle).
    2. Greedy place onto disk 0 (largest-first, 0° then 90°).
    3. Items that didn't fit roll over to disk 1, and so on, up to max_disks.
    """
    d = float(disk_diameter)
    d2 = d * d

    fits: List[Dict[str, Any]] = []
    unplaced: List[Dict[str, Any]] = []
    for it in items:
        w = float(it["w"])
        h = float(it["h"])
        # Axis-aligned rect fits inside circle iff diagonal <= diameter (w^2 + h^2 <= d^2).
        # Rotation-invariant since w/h are symmetric here.
        if w * w + h * h <= d2 + 1e-9:
            fits.append(it)
        else:
            unplaced.append({"file_id": it.get("file_id"), "reason": "too_large_for_disk"})

    disks: List[Dict[str, Any]] = []
    remaining = fits
    disk_idx = 0
    while remaining and disk_idx < max_disks:
        placed, new_remaining = _pack_one_disk(remaining, d, step)
        if not placed:
            # No progress on this disk: avoid infinite loop.
            break
        disks.append({"disk_index": disk_idx, "items": placed})
        disk_idx += 1
        remaining = new_remaining

    for it in remaining:
        unplaced.append({"file_id": it.get("file_id"), "reason": "no_space"})

    if not disks:
        disks = [{"disk_index": 0, "items": []}]

    return {"disks": disks, "unplaced": unplaced}
