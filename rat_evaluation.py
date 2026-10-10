"""Auswertung: Verhältniskennzahlen (Servicegrad) und die Frage, welche Einheit die Statistik braucht.

Ein Standort liefert über Tage eine Nachfrage D_t und eine Fehlmenge S_t, je Regel (gleiche Nachfrage in A und B am selben
Standort). Die Kennzahl ist ein Verhältnis: Servicegrad = 1 - Σ S / Σ D. Ein Experiment zieht n Standorte je Arm und teilt sie zu;
beobachtet wird je Standort nur die zugeteilte Regel. Vier Kennzahl-Definitionen (Quote der Summen, Mittel der Standort-, Tages-
und Wochenquoten) und vier Auswertungen (je mit der passenden Einheit oder fälschlich unabhängigen Tagen/Wochen)."""

import json
from pathlib import Path

import numpy as np
from scipy.special import stdtr, stdtrit

import rat_constants as C
from rat_rng import uniform_block

PRECOMPUTED = Path(__file__).resolve().parent / "precomputed_sites.json"


def load_sites(path=PRECOMPUTED):
    """{Population: dict(shape (P,), demand (P, 56), short_a (P, 56), short_b {z: (P, 56)})}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for name, d in data["populations"].items():
        out[name] = {"shape": np.asarray(d["shape"]), "demand": np.asarray(d["demand"], dtype=float),
                     "short_a": np.asarray(d["short_a"], dtype=float),
                     "short_b": {round(float(k), 1): np.asarray(v, dtype=float) for k, v in d["short_b"].items()}}
    return out


def nearest_z(z):
    grid = (C.Z_A,) + tuple(C.Z_GRID)
    return min(grid, key=lambda g: abs(g - z))


def _short_b(d, z):
    return d["short_a"] if z <= C.Z_A else d["short_b"][z]


def estimands(demand, short, weeks):
    """Die vier Kennzahlen (als Servicegrad = 1 - Quote) aus Arrays (..., Standorte, Tage). Rückgabe: dict von Arrays über
    die führenden Achsen. Tage mit Nachfrage null werden in den Tages- und Wochenquoten ausgelassen."""
    t = 7 * weeks
    d, s = demand[..., :t], short[..., :t]
    out = {"summen": 1.0 - s.sum(axis=(-1, -2)) / d.sum(axis=(-1, -2))}
    site_q = s.sum(axis=-1) / d.sum(axis=-1)
    out["standort"] = 1.0 - site_q.mean(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        day_q = np.where(d > 0, s / d, np.nan)
    out["tage"] = 1.0 - np.nanmean(day_q.reshape(*day_q.shape[:-2], -1), axis=-1)
    wd = d.reshape(*d.shape[:-1], weeks, 7).sum(axis=-1)
    ws = s.reshape(*s.shape[:-1], weeks, 7).sum(axis=-1)
    out["wochen"] = 1.0 - (ws / wd).reshape(*wd.shape[:-2], -1).mean(axis=-1)
    return out


def true_effects(sites, pop, z, weeks):
    """Wahre Wirkung je Kennzahl-Definition über die ganze Population (B minus A beim Servicegrad); bei z = 1,0 genau 0."""
    z = nearest_z(z)
    d = sites[pop]
    ea = estimands(d["demand"][None], d["short_a"][None], weeks)
    eb = estimands(d["demand"][None], _short_b(d, z)[None], weeks)
    return {k: float(eb[k][0] - ea[k][0]) for k in C.KENNZAHLEN}


def _ints(upper, count, seed):
    return np.minimum((uniform_block(seed, count) * upper).astype(np.int64), upper - 1)


def draw(sites, pop, z, n, weeks, reps, seed):
    """Je Experiment n Standorte je Arm (Standorte mit Zurücklegen aus der Population). Rückgabe: (D_a, S_a, D_b, S_b) mit Form
    (reps, n, 7 * weeks)."""
    z = nearest_z(z)
    d = sites[pop]
    p = len(d["shape"])
    t = 7 * weeks
    idx = _ints(p, reps * 2 * n, seed).reshape(reps, 2 * n)
    dem = d["demand"][:, :t][idx]
    sa = d["short_a"][:, :t][idx[:, :n]]
    sb = _short_b(d, z)[:, :t][idx[:, n:]]
    return dem[:, :n], sa, dem[:, n:], sb


def _welch(a, b):
    """Welch-Test über die letzte Achse (a, b: (R, na), (R, nb)); Differenz a minus b. Rückgabe: diff, se, p, lo, hi."""
    na, nb = a.shape[-1], b.shape[-1]
    va, vb = a.var(axis=-1, ddof=1) / na, b.var(axis=-1, ddof=1) / nb
    diff = a.mean(axis=-1) - b.mean(axis=-1)
    se = np.sqrt(va + vb)
    with np.errstate(divide="ignore", invalid="ignore"):
        df = (va + vb) ** 2 / (va**2 / (na - 1) + vb**2 / (nb - 1))
        t = diff / se
    df = np.where(np.isfinite(df) & (df > 0), df, na + nb - 2)
    t = np.where(se > 0, t, 0.0)
    q = stdtrit(df, 0.975)
    return diff, se, 2 * stdtr(df, -np.abs(t)), diff - q * se, diff + q * se


def _delta(d_a, s_a, d_b, s_b):
    """Delta-Methode für die Differenz zweier Quoten der Summen: Einheiten sind die letzte Achse. Servicegrad-Differenz B minus A
    = Quote_A - Quote_B. Rückgabe: diff, se, p, lo, hi (Arrays (R,))."""
    na, nb = d_a.shape[-1], d_b.shape[-1]
    ra = s_a.sum(axis=-1) / d_a.sum(axis=-1)
    rb = s_b.sum(axis=-1) / d_b.sum(axis=-1)
    va = ((s_a - ra[:, None] * d_a) ** 2).sum(axis=-1) * na / (na - 1) / d_a.sum(axis=-1) ** 2
    vb = ((s_b - rb[:, None] * d_b) ** 2).sum(axis=-1) * nb / (nb - 1) / d_b.sum(axis=-1) ** 2
    diff = ra - rb
    se = np.sqrt(va + vb)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(se > 0, diff / se, 0.0)
    df = na + nb - 2
    q = float(stdtrit(df, 0.975))
    return diff, se, 2 * stdtr(df, -np.abs(t)), diff - q * se, diff + q * se


def analyze(d_a, s_a, d_b, s_b, weeks):
    """Die vier Auswertungen. Rückgabe: {Methode: dict(diff, se, p, lo, hi)} (Servicegrad-Differenz B minus A) und die zur Methode
    gehörende Kennzahl-Definition in `target`."""
    r, n, t = d_a.shape
    out = {}
    out["naiv"] = dict(zip(("diff", "se", "p", "lo", "hi"),
                           _delta(d_a.reshape(r, n * t), s_a.reshape(r, n * t), d_b.reshape(r, n * t), s_b.reshape(r, n * t))))
    out["naiv"]["target"] = "summen"
    out["cluster"] = dict(zip(("diff", "se", "p", "lo", "hi"), _delta(d_a.sum(axis=2), s_a.sum(axis=2), d_b.sum(axis=2), s_b.sum(axis=2))))
    out["cluster"]["target"] = "summen"
    qa = 1.0 - s_a.sum(axis=2) / d_a.sum(axis=2)
    qb = 1.0 - s_b.sum(axis=2) / d_b.sum(axis=2)
    diff, se, p, lo, hi = _welch(qb, qa)
    out["standort"] = {"diff": diff, "se": se, "p": p, "lo": lo, "hi": hi, "target": "standort"}
    wa = (d_a.reshape(r, n, weeks, 7).sum(axis=3), s_a.reshape(r, n, weeks, 7).sum(axis=3))
    wb = (d_b.reshape(r, n, weeks, 7).sum(axis=3), s_b.reshape(r, n, weeks, 7).sum(axis=3))
    qwa = (1.0 - wa[1] / wa[0]).reshape(r, n * weeks)
    qwb = (1.0 - wb[1] / wb[0]).reshape(r, n * weeks)
    diff, se, p, lo, hi = _welch(qwb, qwa)
    out["wochen"] = {"diff": diff, "se": se, "p": p, "lo": lo, "hi": hi, "target": "wochen"}
    return out


def experiment_seed(pop, z, n, weeks, tag=0):
    return (29_000_000 + 10_007 * C.POPULATIONS.index(pop) + 1_009 * int(round(z * 10)) + 131 * n + 17 * weeks + 13 * tag)


def summarize(sites, pop, z, n, weeks, reps=C.LIVE_REPS, tag=0):
    """Viele Experimente: je Auswertung Anteil mit Befund (bei z = 1,0 der Fehlalarm), Abdeckung der wahren Wirkung ihrer Kennzahl,
    Verzerrung und die Treue des Standardfehlers (mittlerer SE / empirische Streuung der Schätzung; Soll 1)."""
    z = nearest_z(z)
    d_a, s_a, d_b, s_b = draw(sites, pop, z, n, weeks, reps, experiment_seed(pop, z, n, weeks, tag))
    res = analyze(d_a, s_a, d_b, s_b, weeks)
    truth = true_effects(sites, pop, z, weeks)
    rows = {}
    for m, r in res.items():
        t = truth[r["target"]]
        rows[m] = {
            "target": r["target"], "truth": t,
            "reject": float((r["p"] < C.ALPHA).mean()),
            "coverage": float(((r["lo"] <= t) & (t <= r["hi"])).mean()),
            "bias": float(r["diff"].mean() - t),
            "mean": float(r["diff"].mean()),
            "se_fidelity": float(r["se"].mean() / r["diff"].std(ddof=1)),
            "width": float((r["hi"] - r["lo"]).mean()),
        }
    return {"pop": pop, "z": z, "n": n, "weeks": weeks, "reps": reps, "truth": truth, "rows": rows}


def lag1_autocorrelation(sites, pop):
    """Mittlere Autokorrelation 1. Ordnung der Tagesquoten innerhalb der Standorte (Tage mit Nachfrage über null)."""
    d = sites[pop]
    q = 1.0 - d["short_a"] / np.maximum(d["demand"], 1)
    q = q - q.mean(axis=1, keepdims=True)
    num = (q[:, 1:] * q[:, :-1]).sum()
    den = (q * q).sum()
    return float(num / den)


def run_one(sites, settings):
    """Das eine Experiment der Seitenleiste: die vier Kennzahlen je Arm und die vier Auswertungen."""
    s = settings
    d_a, s_a, d_b, s_b = draw(sites, s["pop"], s["z"], s["n"], s["weeks"], 1, 1_000_003 * (s["seed"] + 1) + 5)
    est_a = estimands(d_a, s_a, s["weeks"])
    est_b = estimands(d_b, s_b, s["weeks"])
    res = analyze(d_a, s_a, d_b, s_b, s["weeks"])
    return {"a": {k: float(v[0]) for k, v in est_a.items()}, "b": {k: float(v[0]) for k, v in est_b.items()},
            "truth": true_effects(sites, s["pop"], s["z"], s["weeks"]),
            "methods": {m: {k: (float(v[0]) if k != "target" else v) for k, v in r.items()} for m, r in res.items()}}
