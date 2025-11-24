"""Tests for the CalculationFactory and operation objects (TDD)."""

import pytest

from app.factory import CalculationFactory, Operation


def test_factory_returns_operation_instances_and_compute():
    fac = CalculationFactory()

    add_op = fac.get("add")
    assert isinstance(add_op, Operation)
    assert add_op.compute(1, 2) == 3

    sub_op = fac.get("subtract")
    assert sub_op.compute(5, 2) == 3

    mul_op = fac.get("multiply")
    assert mul_op.compute(3, 4) == 12

    div_op = fac.get("divide")
    assert div_op.compute(10, 2) == 5


def test_factory_rejects_unknown_type():
    fac = CalculationFactory()
    with pytest.raises(ValueError):
        fac.get("noop")


def test_operations_handle_zero_division():
    fac = CalculationFactory()
    div_op = fac.get("divide")
    with pytest.raises(ZeroDivisionError):
        div_op.compute(1, 0)
