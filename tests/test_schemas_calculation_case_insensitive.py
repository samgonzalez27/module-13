"""Tests that `CalculationCreate` accepts case-insensitive operation names."""

import pytest

from pydantic import ValidationError

from app.schemas import CalculationCreate


def test_calculationcreate_accepts_capitalized_types():
    for input_type, expected in [("Add", "add"), ("Subtract", "subtract"), ("Multiply", "multiply"), ("Divide", "divide")]:
        cc = CalculationCreate(a=1, b=2, type=input_type)
        assert cc.type == expected


def test_calculationcreate_rejects_invalid_type_case_insensitive():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type="NoOp")


def test_calculationcreate_rejects_non_string_type():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type=123)
