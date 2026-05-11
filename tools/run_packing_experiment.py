"""Run packing experiment on a directory of STL files and write placement_result.json

Usage:
  python tools/run_packing_experiment.py --data-dir <dir> [--disk 98] [--accept 0.05]
"""
import argparse
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', required=True)
parser.add_argument('--disk', type=float, default=98.0)
parser.add_argument('--accept', type=float, default=0.05)
parser.add_argument('--scale', type=int, default=100)
parser.add_argument('--sampling', type=float, default=2.0)
args = parser.parse_args()

root = Path.cwd()
repo_root = Path(__file__).resolve().parents[1]
data_dir = repo_root / args.data_dir
if not data_dir.exists():
    print('Data dir not found:', data_dir)
    sys.exit(2)

from core.stl_parser import parse_stl
from core.bin_packing import optimize_placement_circular
from core.waste_calc import compute_waste_rate

files = sorted([p for p in data_dir.iterdir() if p.suffix.lower() == '.stl'])
items = []
meta = {}
for p in files:
    parsed = parse_stl(str(p), disk_thickness=20.0)
    meta[p.name] = parsed
    if parsed.get('feasible', False):
        items.append({'file_id': p.name, 'w': parsed['width'], 'h': parsed['height']})

placement = optimize_placement_circular(items, disk_diameter=args.disk, scale=args.scale, accept_threshold=args.accept, sampling_resolution=args.sampling)

from math import pi
results = {'n_files': len(files), 'n_feasible': len(items), 'placement': placement}

disks = placement.get('disks', [])
per_disk_waste = []
for d in disks:
    placed_items = d.get('items', [])
    waste = compute_waste_rate(placed_items, args.disk)
    per_disk_waste.append({'disk_index': d.get('disk_index'), 'n_placed': len(placed_items), 'waste_rate': waste})

results['per_disk_waste'] = per_disk_waste
results['n_unplaced'] = len(placement.get('unplaced', []))

from tools.output_utils import output_path
out_path = output_path('placement_result.json')
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(results, fh, ensure_ascii=False, indent=2)

print('Wrote', out_path)
print('Summary:')
print('  files total:', results['n_files'])
print('  feasible:', results['n_feasible'])
print('  disks:', len(disks))
for pd in per_disk_waste:
    print(f"  disk {pd['disk_index']}: placed={pd['n_placed']} waste_rate={pd['waste_rate']:.3f}")
print('  unplaced:', results['n_unplaced'])
