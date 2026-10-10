"""Messreihe vor dem Text: Verhältniskennzahlen, Cluster und die Einheit der Auswertung (Stück 8)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rat_constants as C  # noqa: E402
import rat_evaluation as E  # noqa: E402

sites = E.load_sites()
for pop in C.POPULATIONS:
    print(f"{pop}: Autokorrelation 1. Ordnung der Tagesquoten {E.lag1_autocorrelation(sites, pop):+.3f}")
print("\nWahre Wirkung je Kennzahl-Definition (Pkt.), 8 Wochen")
for pop in C.POPULATIONS:
    for z in (1.2, 1.4, 1.8):
        t = E.true_effects(sites, pop, z, 8)
        print(f"  {pop:12s} z={z}: " + "  ".join(f"{C.KENNZAHL_SHORT[k]} {100*t[k]:.2f}" for k in C.KENNZAHLEN))
print("\nAuswertungen: A/A (z=1.0) und Effekt (z=1.4), 20 Standorte je Arm, 8 Wochen, R=3000")
for pop in C.POPULATIONS:
    for z in (1.0, 1.4):
        s = E.summarize(sites, pop, z, 20, 8, reps=3000)
        print(f"{pop}, z={z}:")
        for m in C.METHODS:
            r = s["rows"][m]
            print(f"    {C.METHOD_SHORT[m]:16s} Befund {100*r['reject']:5.1f} %  Abd. {100*r['coverage']:5.1f} %  Verz. {100*r['bias']:+.3f}  "
                  f"SE-Treue {r['se_fidelity']:.2f}  Breite {100*r['width']:.2f}  (Ziel {C.KENNZAHL_SHORT[r['target']]} {100*r['truth']:.2f})")
print("\nLaenger/kuerzer messen, mehr Standorte: Fehlalarm naiv gegen Cluster (alle gleich, z=1.0)")
for n, w in ((10, 8), (20, 4), (40, 4), (20, 8), (40, 8)):
    s = E.summarize(sites, "gleich", 1.0, n, w, reps=3000)
    print(f"  n={n} Wochen={w}: naiv {100*s['rows']['naiv']['reject']:.1f} %  Cluster {100*s['rows']['cluster']['reject']:.1f} %  "
          f"Standort {100*s['rows']['standort']['reject']:.1f} %  Wochen {100*s['rows']['wochen']['reject']:.1f} %")
