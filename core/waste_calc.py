import math


def compute_waste_rate(placed_items, disk_diameter: float, n_disks: int = 1) -> float:
    """Waste rate across all used disks: 1 - (sum of placed item areas / total disk area).

    placed_items: flat list of placed item dicts across ALL disks.
    n_disks: number of disks actually used. Pass len(placement["disks"]).

    Phase 2 will replace bbox areas with convex-hull areas.
    """
    n = max(1, int(n_disks))
    total_disk_area = math.pi * (disk_diameter / 2.0) ** 2 * n
    total_area = 0.0
    for it in placed_items:
        total_area += float(it.get("w", 0.0)) * float(it.get("h", 0.0))
    if total_disk_area == 0:
        return 0.0
    waste = 1.0 - (total_area / total_disk_area)
    return float(max(0.0, min(1.0, waste)))
