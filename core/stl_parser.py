from stl import mesh
import numpy as np


def _pca_align(points: np.ndarray) -> np.ndarray:
    """Rotate point cloud so its principal axes align with X, Y, Z.

    Largest variance maps to X, smallest to Z. This handles STL files exported
    in arbitrary 3D orientation (including non-axis-aligned tilts), giving a
    stable bbox for milling-feasibility and 2D nesting decisions.

    Note: PCA aligns with variance, not literal minimum bbox. For typical dental
    crowns the two coincide closely; pathological cases (e.g. an L-shape) may
    yield slightly larger bboxes than a true minimum-volume bbox, which would
    require a more expensive rotating-calipers / Chan-style algorithm.
    """
    if points.shape[0] < 2:
        return points
    centered = points - points.mean(axis=0)
    cov = np.cov(centered, rowvar=False)
    if not np.all(np.isfinite(cov)):
        return centered
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    R = eigvecs[:, order]
    return centered @ R


def parse_stl(stl_path: str, disk_thickness: float = 20.0) -> dict:
    """Parse STL and return PCA-aligned bounding-box dimensions.

    Steps:
      1. Read all triangle vertices.
      2. PCA-align the point cloud so principal axes match X, Y, Z.
      3. Take the axis-aligned bbox of the rotated points.
      4. Sort extents descending: width >= height >= depth.
         depth is the milling-axis dimension; feasibility = depth <= disk_thickness.

    Returns:
        {"width": float, "height": float, "depth": float, "feasible": bool}
    """
    m = mesh.Mesh.from_file(stl_path)
    # m.vectors has shape (n_faces, 3 vertices, 3 coords). Flatten to (3*n_faces, 3).
    pts = m.vectors.reshape(-1, 3).astype(np.float64)

    aligned = _pca_align(pts)

    extents = sorted([
        float(aligned[:, 0].max() - aligned[:, 0].min()),
        float(aligned[:, 1].max() - aligned[:, 1].min()),
        float(aligned[:, 2].max() - aligned[:, 2].min()),
    ], reverse=True)
    width, height, depth = extents[0], extents[1], extents[2]

    feasible = depth <= float(disk_thickness)

    return {"width": width, "height": height, "depth": depth, "feasible": bool(feasible)}
