"""Presets: Vollständigkeit, gültige Werte, Einrasten der Permalink-Werte."""

import rat_constants as C
import rat_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_on_the_grid():
    for preset in C.PRESETS.values():
        assert C.Z_MIN <= preset["z"] <= C.Z_MAX
        steps = (preset["z"] - C.Z_MIN) / C.Z_STEP
        assert abs(steps - round(steps)) < 1e-9
        assert C.N_MIN <= preset["n"] <= C.N_MAX and (preset["n"] - C.N_MIN) % C.N_STEP == 0
        assert C.W_MIN <= preset["w"] <= C.W_MAX
        assert 0 <= preset["pop"] < len(C.POPULATIONS)
        assert 0 <= preset["seed"] <= C.SEED_MAX


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_labels_are_complete():
    assert set(C.KENNZAHL_LABELS) == set(C.KENNZAHL_SHORT) == set(C.KENNZAHLEN)
    assert set(C.METHOD_LABELS) == set(C.METHOD_SHORT) == set(C.METHOD_COLORS) == set(C.METHODS)
    assert set(C.POPULATION_LABELS) == set(C.POPULATION_SHAPES) == set(C.POPULATIONS)


def test_permalink_values_are_clamped_and_snapped_to_the_slider_grid():
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P.clamp_to_spec(n_spec, 23) == 20 and P.clamp_to_spec(n_spec, 1) == 10 and P.clamp_to_spec(n_spec, 999) == 60
    w_spec = P.SETTING_SPECS["w_slider"]
    assert P.clamp_to_spec(w_spec, 0) == 4 and P.clamp_to_spec(w_spec, 99) == 8
    assert P.clamp_to_spec(P.SETTING_SPECS["pop_radio"], 5) == 1
