"""Run two-step experiment: spiral tuning then simulated annealing.

Outputs JSON with waste rates and execution times.
"""
import time
import json
from pathlib import Path
import sys
repo_root = Path('C:/dev/dev_zrco').resolve()
sys.path.insert(0, str(repo_root))
from core.stl_parser import parse_stl
from core.bin_packing import optimize_placement_circular
from backend.routers import optimize as optimize_router
from shapely.geometry import box, Point

# build items similar to previous auto test
items = []
for i in range(4):
    items.append({'file_id': f'big{i}', 'w': 40.0, 'h': 20.0})
for i in range(3):
    items.append({'file_id': f'med{i}', 'w': 35.0, 'h': 25.0})
for i in range(3):
    items.append({'file_id': f'sml{i}', 'w': 30.0, 'h': 20.0})

out = {}

# Step 1: spiral parameter tuning (step=0.5, angle_step_deg=5)
start = time.time()
res1 = optimize_placement_circular(items, disk_diameter=98.0, disk_thickness=20.0, step=0.5, angle_step_deg=5)
end = time.time()
out['spiral_tuned'] = {'result': res1, 'time': end - start}

# If average waste <= 0.4 we stop; otherwise run SA
avg_waste = res1['total_waste_rate']

# Step 2: simulated annealing applied to res1 initial solution
# Implement SA below
import random
import math
from shapely.geometry import box

def compute_covered_area(disks):
    total = 0.0
    for d in disks:
        for it in d['placed']:
            total += it['w'] * it['h']
    return total

def run_simulated_annealing(initial_res, disk_diameter, iterations=2000, T0=1000, cooling=0.995):
    # flatten items with disk index
    disks = initial_res['disks']
    disk_polys = []
    r = disk_diameter/2.0
    for d in disks:
        disk_polys.append(Point(r, r).buffer(r, resolution=256))
    # map items to locations
    items = []
    for di, d in enumerate(disks):
        for it in d['placed']:
            items.append({'disk': di, 'item': it})
    best = {'disks': disks, 'covered': compute_covered_area(disks)}
    current = {'disks': [ {'placed': [it.copy() for it in d['placed']] } for d in disks ] }
    current['covered'] = best['covered']
    T = T0
    for k in range(iterations):
        # pick random item
        if not items:
            break
        idx = random.randrange(len(items))
        rec = items[idx]
        di = rec['disk']
        placed = current['disks'][di]['placed']
        if not placed:
            continue
        j = random.randrange(len(placed))
        # propose neighbor: move ±2mm or rotate 90
        proposal = placed[j].copy()
        if random.random() < 0.5:
            proposal['x'] += random.uniform(-2, 2)
            proposal['y'] += random.uniform(-2, 2)
        else:
            proposal['rotation'] = 0 if proposal.get('rotation',0)==90 else 90
            # swap w/h if rotating by 90
            proposal['w'], proposal['h'] = proposal['h'], proposal['w']
        # check validity
        disk_poly = disk_polys[di]
        poly = box(proposal['x'], proposal['y'], proposal['x']+proposal['w'], proposal['y']+proposal['h'])
        if not disk_poly.contains(poly):
            continue
        # check overlap with other items in same disk
        overlap = False
        for ii, other in enumerate(placed):
            if ii == j:
                continue
            op = box(other['x'], other['y'], other['x']+other['w'], other['y']+other['h'])
            if poly.intersection(op).area > 1e-6:
                overlap = True
                break
        if overlap:
            continue
        # accept based on covered area delta
        old_area = placed[j]['w'] * placed[j]['h']
        new_area = proposal['w'] * proposal['h']
        delta = new_area - old_area
        if delta >= 0 or math.exp(delta / T) > random.random():
            placed[j] = proposal
            current['covered'] += delta
            if current['covered'] > best['covered']:
                best['covered'] = current['covered']
                best['disks'] = [ {'placed': [it.copy() for it in d['placed']] } for d in current['disks'] ]
        T *= cooling
    # compute waste rates for best
    # TODO: compute waste rates using core.waste_calc
    return best

start = time.time()
best = run_simulated_annealing(res1, 98.0, iterations=2000)
end = time.time()
out['simulated_annealing'] = {'best_covered': best['covered'], 'time': end - start}

from tools.output_utils import output_path
out_path = output_path('packing_bench_result.json')
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, indent=2)

print('Wrote', out_path)
print('avg waste after spiral:', res1['total_waste_rate'])
print('SA best covered:', out['simulated_annealing']['best_covered'])
print('time stats:', out['spiral_tuned']['time'], out['simulated_annealing']['time'])
