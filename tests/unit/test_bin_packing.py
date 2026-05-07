from core.bin_packing import is_rect_inside_circle, optimize_placement_circular


def test_is_rect_inside_circle():
    # circle radius 10 at origin (cx=10,cy=10)
    assert is_rect_inside_circle(5, 5, 2, 2, 10, 10, 10) == True
    # rectangle that sticks out
    assert is_rect_inside_circle(0, 0, 20, 20, 10, 10, 10) == False


def test_optimize_basic():
    items = [{"file_id": "a", "w": 10, "h": 10}, {"file_id": "b", "w": 20, "h": 20}]
    res = optimize_placement_circular(items, disk_diameter=50)
    assert "disks" in res and "unplaced" in res
    assert isinstance(res["disks"], list)
