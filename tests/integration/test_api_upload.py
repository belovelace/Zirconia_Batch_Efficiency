from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

MINIMAL_STL = b"""solid test
facet normal 0 0 0
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 1 0
 endloop
endfacet
endsolid test
"""


def test_upload_minimal_stl():
    files = {"files": ("test.stl", MINIMAL_STL, "application/sla")}
    resp = client.post("/upload/", files=files, data={})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "case_id" in data and data["n_files"] >= 0
