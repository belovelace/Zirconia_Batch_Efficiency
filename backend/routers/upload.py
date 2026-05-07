from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import uuid
import json
import os
from core.stl_parser import parse_stl

router = APIRouter(prefix="/upload", tags=["upload"])

# In-memory DB stub
CASES = {}
FILES = {}

@router.post("/", summary="Upload STL files and create case")
async def upload_files(files: List[UploadFile] = File(...), disk_config: str = Form(None)):
    """Accept multiple STL files, parse them, and create a case record (in-memory stub).

    disk_config: JSON string or omitted — disk_diameter and thickness may be provided.
    """
    try:
        config = json.loads(disk_config) if disk_config else {"diameter": 98.0, "thickness": 20.0}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid disk_config JSON")

    case_id = str(uuid.uuid4())
    CASES[case_id] = {"id": case_id, "disk_config": config, "files": []}

    # Save uploads to a temp folder and parse
    tmpdir = os.path.join("/tmp", "zirsave_uploads")
    os.makedirs(tmpdir, exist_ok=True)

    for up in files:
        contents = await up.read()
        fname = f"{uuid.uuid4()}_{up.filename}"
        path = os.path.join(tmpdir, fname)
        with open(path, "wb") as f:
            f.write(contents)
        # parse
        parsed = parse_stl(path, disk_thickness=config.get("thickness", 20.0))
        file_id = str(uuid.uuid4())
        file_rec = {"id": file_id, "filename": up.filename, "path": path, "bbox_w": parsed["width"], "bbox_h": parsed["height"], "depth": parsed["depth"], "feasible": parsed["feasible"]}
        FILES[file_id] = file_rec
        CASES[case_id]["files"].append(file_rec)

    return {"case_id": case_id, "n_files": len(CASES[case_id]["files"])}
