"""Jede Zahl des README (Abschnitt "Befunde") wird hier über dieselben Funktionen wie in der App nachgerechnet.

Die Messreihen sind deterministisch (SplitMix64-Populationen und -Ziehungen); die Bänder sind Rundungs- und Plattformreserve."""

import numpy as np
import pytest
from scipy.special import ndtr

import rat_constants as C
import rat_evaluation as E

REPS = 3000


def pct(x):
    return 100 * x


@pytest.fixture(scope="module")
def sites():
    return E.load_sites()


@pytest.fixture(scope="module")
def runs(sites):
    """Die Zellen des README: (Population, z) bei 20 Standorten je Arm und 8 Wochen."""
    return {(pop, z): E.summarize(sites, pop, z, 20, 8, reps=REPS) for pop in C.POPULATIONS for z in (1.0, 1.4)}


def test_serial_correlation_of_daily_quotes(sites):
    for pop in C.POPULATIONS:
        assert E.lag1_autocorrelation(sites, pop) == pytest.approx(0.28, abs=0.01)


def test_true_effect_depends_on_the_definition(sites):
    expected = {
        ("gleich", 1.2): (1.98, 1.94, 1.74, 1.39),
        ("gleich", 1.4): (3.49, 3.41, 3.04, 2.41),
        ("gleich", 1.8): (5.21, 5.09, 4.50, 3.51),
        ("verschieden", 1.4): (3.51, 3.44, 3.06, 2.42),
    }
    for (pop, z), values in expected.items():
        t = E.true_effects(sites, pop, z, 8)
        got = tuple(pct(t[k]) for k in ("summen", "standort", "wochen", "tage"))
        assert got == pytest.approx(values, abs=0.02), (pop, z)


def test_the_day_mean_shows_about_a_third_less_effect(sites):
    for pop in C.POPULATIONS:
        for z in (1.2, 1.4, 1.8):
            t = E.true_effects(sites, pop, z, 8)
            assert 0.29 < 1 - t["tage"] / t["summen"] < 0.34, (pop, z)


def test_false_alarm_rates_without_effect(runs):
    expected = {
        "gleich": {"naiv": 13.7, "cluster": 5.0, "standort": 5.0, "wochen": 6.4},
        "verschieden": {"naiv": 26.9, "cluster": 5.8, "standort": 5.3, "wochen": 15.1},
    }
    for pop, rates in expected.items():
        for m, value in rates.items():
            assert pct(runs[(pop, 1.0)]["rows"][m]["reject"]) == pytest.approx(value, abs=0.2), (pop, m)


def test_coverage_and_standard_error_fidelity_without_effect(runs):
    g, v = runs[("gleich", 1.0)]["rows"], runs[("verschieden", 1.0)]["rows"]
    assert pct(g["naiv"]["coverage"]) == pytest.approx(86.3, abs=0.2)
    assert pct(v["naiv"]["coverage"]) == pytest.approx(73.1, abs=0.2)
    assert pct(g["cluster"]["coverage"]) == pytest.approx(95.0, abs=0.2)
    assert pct(v["cluster"]["coverage"]) == pytest.approx(94.2, abs=0.2)
    assert g["naiv"]["se_fidelity"] == pytest.approx(0.76, abs=0.01)
    assert v["naiv"]["se_fidelity"] == pytest.approx(0.56, abs=0.01)
    assert g["cluster"]["se_fidelity"] == pytest.approx(1.00, abs=0.01)
    assert v["cluster"]["se_fidelity"] == pytest.approx(0.98, abs=0.01)


def test_naive_interval_is_too_narrow(runs):
    g = runs[("gleich", 1.0)]["rows"]
    assert pct(g["naiv"]["width"]) == pytest.approx(3.77, abs=0.02)
    assert pct(g["cluster"]["width"]) == pytest.approx(5.12, abs=0.02)
    assert 1 - g["naiv"]["width"] / g["cluster"]["width"] == pytest.approx(0.26, abs=0.01)


def test_power_with_effect_and_the_naive_advantage_is_fake(runs):
    g, v = runs[("gleich", 1.4)]["rows"], runs[("verschieden", 1.4)]["rows"]
    assert [pct(g[m]["reject"]) for m in ("naiv", "cluster", "standort", "wochen")] == pytest.approx([95.3, 87.1, 87.3, 92.9], abs=0.2)
    assert [pct(v[m]["reject"]) for m in ("naiv", "cluster", "standort", "wochen")] == pytest.approx([83.0, 52.1, 53.2, 78.8], abs=0.2)
    assert pct(g["naiv"]["coverage"]) == pytest.approx(86.2, abs=0.2)
    assert pct(v["naiv"]["coverage"]) == pytest.approx(74.9, abs=0.2)
    assert pct(g["wochen"]["coverage"]) == pytest.approx(93.3, abs=0.2)


def test_the_estimators_are_unbiased(runs):
    for cell in runs.values():
        for r in cell["rows"].values():
            assert abs(pct(r["bias"])) < 0.05


def test_more_sites_or_weeks_do_not_fix_the_naive_analysis(sites):
    expected = {(10, 8): (13.2, 5.2), (20, 4): (14.1, 5.9), (40, 4): (13.7, 5.3), (20, 8): (13.7, 5.0), (40, 8): (12.9, 4.7)}
    for (n, w), (naive, cluster) in expected.items():
        rows = E.summarize(sites, "gleich", 1.0, n, w, reps=REPS)["rows"]
        assert pct(rows["naiv"]["reject"]) == pytest.approx(naive, abs=0.2), (n, w)
        assert pct(rows["cluster"]["reject"]) == pytest.approx(cluster, abs=0.2), (n, w)


def test_normal_quantile_is_slightly_liberal_with_ten_sites(sites):
    for pop, normal, t in (("gleich", 6.9, 5.2), ("verschieden", 6.0, 4.0)):
        d_a, s_a, d_b, s_b = E.draw(sites, pop, 1.0, 10, 8, REPS, E.experiment_seed(pop, 1.0, 10, 8, 0))
        diff, se, p, _, _ = E._delta(d_a.sum(axis=2), s_a.sum(axis=2), d_b.sum(axis=2), s_b.sum(axis=2))
        z = np.where(se > 0, diff / se, 0.0)
        assert pct(float((p < 0.05).mean())) == pytest.approx(t, abs=0.2), pop
        assert pct(float((2 * ndtr(-np.abs(z)) < 0.05).mean())) == pytest.approx(normal, abs=0.2), pop


def test_shortages_sit_on_the_large_demand_days(sites):
    d = sites["gleich"]
    big = d["demand"] > np.median(d["demand"])
    assert pct(d["demand"][big].sum() / d["demand"].sum()) == pytest.approx(69.0, abs=1.0)
    assert pct(d["short_a"][big].sum() / d["short_a"].sum()) == pytest.approx(93.0, abs=1.0)
