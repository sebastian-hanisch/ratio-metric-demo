"""Kennzahl-Definitionen, Delta-Methode, Auswertungen: Handrechnung an Mini-Instanzen und Eigenschaften."""

import numpy as np
import pytest
from scipy import stats

import rat_constants as C
import rat_evaluation as E


def test_estimands_by_hand_on_one_site_one_week():
    # Nachfrage 10, 20, 10, 20, 10, 20, 10 (Summe 100), Fehlmenge 1, 0, 2, 0, 1, 0, 2 (Summe 6)
    d = np.array([[[10, 20, 10, 20, 10, 20, 10]]], dtype=float)
    s = np.array([[[1, 0, 2, 0, 1, 0, 2]]], dtype=float)
    e = E.estimands(d, s, 1)
    assert float(e["summen"][0]) == pytest.approx(0.94)                  # 1 - 6/100
    assert float(e["standort"][0]) == pytest.approx(0.94)                # ein Standort
    assert float(e["wochen"][0]) == pytest.approx(0.94)                  # eine Woche
    # Tagesquoten 0,1 0 0,2 0 0,1 0 0,2: Mittel 0,6/7, Servicegrad 1 - 0,6/7
    assert float(e["tage"][0]) == pytest.approx(1 - 0.6 / 7)


def test_the_mean_of_ratios_differs_from_the_ratio_of_sums_when_sizes_differ():
    d = np.array([[[10, 100, 10, 100, 10, 100, 10]]], dtype=float)
    s = np.array([[[5, 5, 5, 5, 5, 5, 5]]], dtype=float)                  # gleiche Fehlmenge, ungleiche Nachfrage
    e = E.estimands(d, s, 1)
    assert float(e["summen"][0]) == pytest.approx(1 - 35 / 340)
    assert float(e["tage"][0]) < float(e["summen"][0]) - 0.1              # kleine Tage ziehen das Tagesmittel hinunter


def test_delta_method_by_hand():
    # A: D = [10, 10], S = [1, 3]; R_A = 0,2; Summe (S - R D)^2 = 2; Var = 2 * 2 / 400 = 0,01
    # B: D = [10, 10], S = [0, 1]; R_B = 0,05; Summe = 0,5; Var = 2 * 0,5 / 400 = 0,0025; diff = 0,15; se = sqrt(0,0125)
    diff, se, p, lo, hi = E._delta(np.array([[10.0, 10.0]]), np.array([[1.0, 3.0]]),
                                   np.array([[10.0, 10.0]]), np.array([[0.0, 1.0]]))
    assert float(diff[0]) == pytest.approx(0.15)
    assert float(se[0]) == pytest.approx(np.sqrt(0.0125))
    t = 0.15 / np.sqrt(0.0125)
    assert float(p[0]) == pytest.approx(2 * stats.t.sf(t, 2), rel=1e-9)
    q = stats.t.ppf(0.975, 2)
    assert float(lo[0]) == pytest.approx(0.15 - q * np.sqrt(0.0125))
    assert float(hi[0]) == pytest.approx(0.15 + q * np.sqrt(0.0125))


def test_welch_matches_scipy_and_is_a_minus_b():
    rng = np.random.default_rng(7)
    a, b = rng.normal(1.0, 0.3, (1, 12)), rng.normal(0.8, 0.5, (1, 17))
    diff, se, p, lo, hi = E._welch(a, b)
    ref = stats.ttest_ind(a[0], b[0], equal_var=False)
    assert float(p[0]) == pytest.approx(ref.pvalue, rel=1e-9)
    assert float(diff[0]) == pytest.approx(a.mean() - b.mean())
    assert float(lo[0]) < float(diff[0]) < float(hi[0])


def test_population_truths_are_ordered_and_zero_for_aa(sites):
    for pop in C.POPULATIONS:
        t = E.true_effects(sites, pop, 1.4, 8)
        assert t["tage"] < t["wochen"] < t["summen"]
        assert t["tage"] < t["wochen"] < t["standort"]
        assert t["tage"] > 0.01
        assert all(v == 0.0 for v in E.true_effects(sites, pop, 1.0, 8).values())


def test_true_effect_grows_with_z(sites):
    for pop in C.POPULATIONS:
        effects = [E.true_effects(sites, pop, z, 8)["summen"] for z in (1.2, 1.4, 1.8)]
        assert effects == sorted(effects) and effects[0] > 0


def test_draw_has_the_right_shapes(sites):
    d_a, s_a, d_b, s_b = E.draw(sites, "gleich", 1.4, 12, 3, 20, 5)
    assert d_a.shape == s_a.shape == d_b.shape == s_b.shape == (20, 12, 21)
    assert np.all(s_a <= d_a) and np.all(s_b <= d_b)


def test_aa_runs_hold_the_level_for_cluster_methods_and_not_for_naive(sites):
    rows = E.summarize(sites, "gleich", 1.0, 20, 8, reps=1500)["rows"]
    assert rows["cluster"]["reject"] == pytest.approx(0.05, abs=0.02)
    assert rows["standort"]["reject"] == pytest.approx(0.05, abs=0.02)
    assert rows["naiv"]["reject"] > 0.10
    assert rows["naiv"]["coverage"] < 0.90
    assert rows["cluster"]["coverage"] == pytest.approx(0.95, abs=0.02)


def test_dauerhaft_verschiedene_standorte_make_the_naive_analysis_worse(sites):
    same = E.summarize(sites, "gleich", 1.0, 20, 8, reps=1200)["rows"]["naiv"]["reject"]
    diff = E.summarize(sites, "verschieden", 1.0, 20, 8, reps=1200)["rows"]["naiv"]["reject"]
    assert diff > same + 0.08


def test_standard_errors_are_faithful_for_the_cluster_methods(sites):
    rows = E.summarize(sites, "verschieden", 1.4, 20, 8, reps=1500)["rows"]
    assert rows["cluster"]["se_fidelity"] == pytest.approx(1.0, abs=0.10)
    assert rows["naiv"]["se_fidelity"] < 0.75


def test_autocorrelation_of_daily_quotes_is_positive(sites):
    for pop in C.POPULATIONS:
        assert 0.15 < E.lag1_autocorrelation(sites, pop) < 0.45


def test_run_one_is_deterministic(sites):
    s = {"pop": "gleich", "z": 1.4, "n": 10, "weeks": 4, "seed": 3}
    a, b = E.run_one(sites, s), E.run_one(sites, s)
    assert a["a"] == b["a"] and a["methods"]["cluster"]["diff"] == b["methods"]["cluster"]["diff"]
    assert set(a["methods"]) == set(C.METHODS)
