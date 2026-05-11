import math
from typing import List, Dict, Any


def compute_disk_utilization(placed_items: List[Dict[str, Any]], disk_diameter: float) -> float:
    """Disk utilization = sum(item areas) / disk area. Returns fraction in [0,1]."""
    disk_area = math.pi * (disk_diameter / 2.0) ** 2
    total_area = 0.0
    for it in placed_items:
        total_area += float(it.get("w", 0.0)) * float(it.get("h", 0.0))
    if disk_area == 0:
        return 0.0
    util = total_area / disk_area
    return float(max(0.0, min(1.0, util)))


def compute_disk_saving_rate(total_items_count: int, optimized_disk_count: int) -> float:
    """Disk saving rate = (naive_disk_count - optimized_disk_count) / naive_disk_count

    naive_disk_count is the baseline number of disks if milling one item per disk (== total_items_count)
    optimized_disk_count is the number of disks used by the packing result.
    Returns fraction in [0,1]. If total_items_count == 0 returns 0.0
    """
    if total_items_count <= 0:
        return 0.0
    saving = (total_items_count - optimized_disk_count) / total_items_count
    return float(max(0.0, min(1.0, saving)))
