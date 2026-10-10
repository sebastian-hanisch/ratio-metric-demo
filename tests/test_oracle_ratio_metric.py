"""Orakel-Tests: der Kern gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2).

1. Delta-Methode (Standardfehler der Quote der Summen) gegen den Cluster-Bootstrap.
2. Welch über Standort-Quoten gegen scipy.
3. Naive Auswertung hat bei Serienkorrelation (AR(1)) eine weit überhöhte Fehlalarmrate; die Cluster-Auswertung hält 5 %.
4. Kennzahlen gegen eine direkte Schleife."""

import numpy as np
import pytest
from scipy import stats

import rat_constants as C
import rat_evaluation as E


def test_delta_se_equals_the_cluster_bootstrap_se():
    rng = np.random.default_rng(41)
    n, t = 40, 20
    d = rng.integers(5, 15, (1, n, t)).astype(float)
    s = rng.binomial(d.astype(int), 0.12).astype(float)
    dd, ss = d.sum(axis=2)[0], s.sum(axis=2)[0]
    ratio = ss.sum() / dd.sum()
    se_delta = float(np.sqrt(((ss - ratio * dd) ** 2).sum() * n / (n - 1)) / dd.sum())
    boots = []
    for _ in range(4000):
        idx = rng.integers(0, n, n)
        boots.append(ss[idx].sum() / dd[idx].sum())
    assert se_delta == pytest.approx(np.std(boots, ddof=1), rel=0.08)
    # und die Funktion der Demo liefert denselben Wert: A und B gleiche Daten, der Standardfehler der Differenz ist sqrt(2) mal größer
    _, se, _, _, _ = E._delta(dd[None], ss[None], dd[None], ss[None])
    assert float(se[0]) == pytest.approx(se_delta * np.sqrt(2), rel=1e-9)


def test_site_level_welch_equals_scipy():
    rng = np.random.default_rng(42)
    n, t = 12, 14
    d_a, d_b = rng.integers(100, 200, (1, n, t)).astype(float), rng.integers(100, 200, (1, n, t)).astype(float)
    s_a = rng.binomial(d_a.astype(int), 0.10).astype(float)
    s_b = rng.binomial(d_b.astype(int), 0.07).astype(float)
    res = E.analyze(d_a, s_a, d_b, s_b, 2)
    qa = 1 - s_a[0].sum(axis=1) / d_a[0].sum(axis=1)
    qb = 1 - s_b[0].sum(axis=1) / d_b[0].sum(axis=1)
    ref = stats.ttest_ind(qb, qa, equal_var=False)
    assert res["standort"]["p"][0] == pytest.approx(ref.pvalue, rel=1e-9)
    assert res["standort"]["diff"][0] == pytest.approx(qb.mean() - qa.mean())


def test_naive_inflates_the_false_alarm_rate_with_ar1_series_and_clusters_do_not():
    rng = np.random.default_rng(43)
    reps, n, t, rho = 1500, 20, 28, 0.5

    def series():
        e = rng.normal(0, 1, (reps, n, t))
        x = np.empty_like(e)
        x[..., 0] = e[..., 0]
        for k in range(1, t):
            x[..., k] = rho * x[..., k - 1] + np.sqrt(1 - rho**2) * e[..., k]
        return x

    d = np.full((reps, n, t), 100.0)
    s_a, s_b = 10 + 3 * series(), 10 + 3 * series()
    res = E.analyze(d, s_a, d, s_b, 4)
    naive = float((res["naiv"]["p"] < 0.05).mean())
    cluster = float((res["cluster"]["p"] < 0.05).mean())
    assert naive > 0.2                                  # Varianz des Mittels etwa dreimal zu klein (1 + rho) / (1 - rho)
    assert cluster == pytest.approx(0.05, abs=0.02)


def test_estimands_against_a_plain_loop(sites):
    d = sites["verschieden"]
    t = 14
    sub_d, sub_s = d["demand"][:30, :t], d["short_a"][:30, :t]
    e = E.estimands(sub_d[None], sub_s[None], 2)
    summen = 1 - sub_s.sum() / sub_d.sum()
    standort = 1 - np.mean([sub_s[i].sum() / sub_d[i].sum() for i in range(30)])
    wochen = 1 - np.mean([sub_s[i, w * 7:(w + 1) * 7].sum() / sub_d[i, w * 7:(w + 1) * 7].sum()
                          for i in range(30) for w in range(2)])
    tage = 1 - np.mean([sub_s[i, k] / sub_d[i, k] for i in range(30) for k in range(t) if sub_d[i, k] > 0])
    assert float(e["summen"][0]) == pytest.approx(summen)
    assert float(e["standort"][0]) == pytest.approx(standort)
    assert float(e["wochen"][0]) == pytest.approx(wochen)
    assert float(e["tage"][0]) == pytest.approx(tage)
    assert set(e) == set(C.KENNZAHLEN)
