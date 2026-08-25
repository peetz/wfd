"""Tests for WFD voting helpers."""

import pytest

from .voting import VotingSelectionError, validate_selection


def test_exact_selection_required():
    validate_selection(["meal-a", "meal-b"], 2)


def test_invalid_selection_count():
    with pytest.raises(VotingSelectionError):
        validate_selection(["meal-a"], 2)


def test_duplicate_selection_rejected():
    with pytest.raises(VotingSelectionError):
        validate_selection(["meal-a", "meal-a"], 2)
