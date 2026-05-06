"""Tests for envchain.scorer."""
import pytest

from envchain.profile import Profile
from envchain.scorer import ScoreResult, ScoreBreakdown, score_profile, _grade


def _make_profile(name="web", context="production", variables=None):
    return Profile(
        name=name,
        context=context,
        variables=variables or {"DB_URL": "postgres://", "API_KEY": "abc", "PORT": "8080"},
    )


def test_grade_a():
    assert _grade(95) == "A"


def test_grade_b():
    assert _grade(80) == "B"


def test_grade_c():
    assert _grade(65) == "C"


def test_grade_d():
    assert _grade(45) == "D"


def test_grade_f():
    assert _grade(30) == "F"


def test_perfect_profile_scores_100():
    profile = _make_profile()
    result = score_profile(profile)
    assert result.total == 100
    assert result.grade == "A"


def test_empty_profile_scores_zero():
    profile = _make_profile(variables={})
    result = score_profile(profile)
    assert result.total == 0
    assert result.grade == "F"


def test_profile_with_empty_values_loses_points():
    profile = _make_profile(variables={"A": "", "B": "", "C": "ok"})
    result = score_profile(profile)
    # non_empty=20, no_empty_values=10 (2 empty → 30-20=10), valid_context=20, variable_count=30
    assert result.total == 80


def test_unknown_context_loses_points():
    profile = _make_profile(context="dev")
    result = score_profile(profile)
    # loses 20 pts for unknown context
    assert result.total == 80
    assert result.grade == "B"


def test_few_variables_loses_points():
    profile = _make_profile(variables={"A": "1"})
    result = score_profile(profile)
    # non_empty=20, no_empty=30, valid_context=20, variable_count=10
    assert result.total == 80


def test_breakdown_has_four_categories():
    result = score_profile(_make_profile())
    categories = {b.category for b in result.breakdown}
    assert categories == {"non_empty", "no_empty_values", "valid_context", "variable_count"}


def test_score_result_percentage():
    result = score_profile(_make_profile())
    assert result.percentage == 100.0


def test_score_result_summary_contains_name():
    result = score_profile(_make_profile(name="myprofile"))
    assert "myprofile" in result.summary()


def test_score_breakdown_to_dict():
    b = ScoreBreakdown("non_empty", 20, 20, "ok")
    d = b.to_dict()
    assert d["category"] == "non_empty"
    assert d["points"] == 20
    assert d["max_points"] == 20
    assert d["reason"] == "ok"


def test_zero_max_total_percentage_safe():
    result = ScoreResult("x", 0, 0, "F")
    assert result.percentage == 0.0
