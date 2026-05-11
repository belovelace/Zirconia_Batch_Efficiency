from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'outputs'

def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR

def output_path(filename: str):
    d = ensure_output_dir()
    return d / filename
