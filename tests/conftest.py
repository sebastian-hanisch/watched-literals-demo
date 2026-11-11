"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b): das Handbeispiel F2."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import wlt_constants as C  # noqa: E402


@pytest.fixture
def f2():
    """Sechs 3-Klauseln über x1 bis x5 (von Hand nachgerechnet, siehe tests/test_algorithm.py)."""
    return C.F2_N, C.F2_KLAUSELN
