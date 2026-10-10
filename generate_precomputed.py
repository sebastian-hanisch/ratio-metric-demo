"""Erzeugt `precomputed_sites.json`: je Standort-Population Standorte mit persistenter Eigenheit (wahre Nachfrage-Dispersion) und
je Standort die tägliche Nachfrage und die tägliche Fehlmenge unter Regel A und B (mehrere Sicherheitsfaktoren), über 56 Tage.

Regel A und B sehen am selben Standort dieselbe Nachfrage (gemeinsame Zufallszahlen auf Standortebene): so ist die Wirkung
je Standort und Tag definiert, und ein Experiment beobachtet je Standort nur die zugeteilte Regel.

    python generate_precomputed.py            # wenige Sekunden bis eine halbe Minute"""

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import rat_constants as C
from rat_rng import SplitMix64
from rat_vehicle import daily_shortages, draw_demand

OUT = Path(__file__).resolve().parent / "precomputed_sites.json"


def shape_of(pop, site):
    shapes = C.POPULATION_SHAPES[pop]
    return shapes[SplitMix64(70_001 + 977 * C.POPULATIONS.index(pop) + 13 * site).next() % len(shapes)]


def _site(args):
    pop, pop_index, site = args
    shape = shape_of(pop, site)
    rng = SplitMix64(2_000_003 * (pop_index + 1) + 8_191 * site + 5)
    demands = [draw_demand(rng, C.BASE_MEAN, shape) for _ in range(C.BURN_DAYS + C.DAYS)]
    d = demands[C.BURN_DAYS:]
    short_a = daily_shortages(C.Z_A, demands, C.BURN_DAYS)
    short_b = {f"{z:.1f}": daily_shortages(z, demands, C.BURN_DAYS) for z in C.Z_GRID}
    return shape, d, short_a, short_b


def main():
    t0 = time.time()
    data = {"meta": {"sites": C.SITES_PER_POPULATION, "days": C.DAYS, "burn_days": C.BURN_DAYS, "z_grid": list(C.Z_GRID),
                     "disp_assumed": C.DISP}, "populations": {}}
    with mp.Pool() as pool:
        for pi, pop in enumerate(C.POPULATIONS):
            rows = pool.map(_site, [(pop, pi, s) for s in range(C.SITES_PER_POPULATION)], chunksize=25)
            data["populations"][pop] = {
                "shape": [r[0] for r in rows], "demand": [r[1] for r in rows], "short_a": [r[2] for r in rows],
                "short_b": {f"{z:.1f}": [r[3][f"{z:.1f}"] for r in rows] for z in C.Z_GRID},
            }
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT.name}: {len(C.POPULATIONS)} Populationen à {C.SITES_PER_POPULATION} Standorte, {time.time() - t0:.0f} s, "
          f"{OUT.stat().st_size / 1024:.0f} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
