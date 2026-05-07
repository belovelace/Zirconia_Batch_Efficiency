import math


def compute_waste_rate(placed_items, disk_diameter: float) -> float:
    """Compute simple waste rate as 1 - (sum of item areas / disk area).

    Placeholder: Phase2 will use convex hull-based area corrections.
    """
    disk_area = math.pi * (disk_diameter / 2.0) ** 2
    total_area = 0.0
    for it in placed_items:
        total_area += float(it.get("w", 0.0)) * float(it.get("h", 0.0))
    if disk_area == 0:
        return 0.0
    waste = 1.0 - (total_area / disk_area)
    return float(max(0.0, min(1.0, waste)))
