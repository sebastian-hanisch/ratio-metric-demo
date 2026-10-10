"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rat_evaluation as E  # noqa: E402


@pytest.fixture
def mini_demands():
    """Mini-Instanz: Tagesnachfragen 20, 60, 10, 25 mit einem Einschwingtag, Mittel 20, z = 1,0, Wiederbeschaffungszeit 2.
    Handrechnung siehe test_vehicle: Fehlmengen der Tage 1 bis 3 sind 26, 10, 0 (Nachfrage 95, Fehlmenge 36)."""
    return [20, 60, 10, 25]


@pytest.fixture(scope="session")
def sites():
    return E.load_sites()
