from core.bin_packing import is_rect_inside_circle, optimize_placement_circular


def test_is_rect_inside_circle():
    # circle radius 10 at origin (cx=10,cy=10)
    assert is_rect_inside_circle(5, 5, 2, 2, 10, 10, 10) == True
    # rectangle that sticks out
    assert is_rect_inside_circle(0, 0, 20, 20, 10, 10, 10) == False


def test_optimize_single_item_inside():
    items = [{"file_id": "a", "w": 10, "h": 10}]
    res = optimize_placement_circular(items, disk_diameter=50, disk_thickness=10)
    assert "disks" in res
    assert len(res["disks"]) >= 1
    assert len(res["disks"][0]["placed"]) == 1


def test_optimize_spill_to_next_disk():
    # two very large items that cannot fit both on one disk
    items = [{"file_id": "a", "w": 60, "h": 60}, {"file_id": "b", "w": 60, "h": 60}]
    res = optimize_placement_circular(items, disk_diameter=50, disk_thickness=10)
    assert len(res["disks"]) >= 2 or len(res["unplaced"]) > 0


def test_waste_rate_range():
    items = [{"file_id": "a", "w": 10, "h": 10}]
    res = optimize_placement_circular(items, disk_diameter=50, disk_thickness=10)
    wr = res["disks"][0]["waste_rate"]
    assert 0.0 <= wr <= 1.0


def test_rotation_applied():
    items = [{"file_id": "a", "w": 40, "h": 10}]
    res = optimize_placement_circular(items, disk_diameter=50, disk_thickness=10)
    # if rotation allowed then the item may be placed with rotation 90 causing swapped w/h
    placed = res["disks"][0]["placed"]
    assert any(p.get("rotation") in (0, 90) for p in placed)
