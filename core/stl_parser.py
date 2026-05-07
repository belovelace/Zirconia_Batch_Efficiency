from stl import mesh
import numpy as np


def parse_stl(stl_path: str, disk_thickness: float = 20.0) -> dict:
    """Parse STL and return width, height, depth and feasible flag.

    Returns:
        {"width": float, "height": float, "depth": float, "feasible": bool}
    """
    m = mesh.Mesh.from_file(stl_path)
    # mesh vectors shape: (n, 3) flattened across faces; numpy-stl presents x,y,z arrays
    xs = m.x.flatten()
    ys = m.y.flatten()
    zs = m.z.flatten()

    min_x, max_x = float(xs.min()), float(xs.max())
    min_y, max_y = float(ys.min()), float(ys.max())
    min_z, max_z = float(zs.min()), float(zs.max())

    width = max_x - min_x
    height = max_y - min_y
    depth = max_z - min_z

    feasible = depth <= float(disk_thickness)

    return {"width": width, "height": height, "depth": depth, "feasible": feasible}
