"""The vendored Hindley-Milner core (owl_basic.owltyping.inference).

This is the maintained standalone implementation (from rob-smallshire/
hindley-milner-python); these tests pin the behaviour we will build the BBC
BASIC type-inference bridge on top of.
"""

import re

import pytest

from owl_basic.owltyping import inference as hm


def _env():
    return {
        "true": hm.Bool,
        "zero": hm.Function(hm.Integer, hm.Bool),
        "pred": hm.Function(hm.Integer, hm.Integer),
        "times": hm.Function(hm.Integer, hm.Function(hm.Integer, hm.Integer)),
    }


def test_integer_literals_infer_as_int():
    assert str(hm.analyse(hm.Identifier("42"), {})) == "int"


def test_application_of_a_function_infers_its_result_type():
    # times 2 3  ->  int
    term = hm.Apply(hm.Apply(hm.Identifier("times"), hm.Identifier("2")),
                    hm.Identifier("3"))
    assert str(hm.analyse(term, _env())) == "int"


def test_identity_function_is_polymorphic():
    # fn x => x  ->  (X -> X) for some single type variable X
    rendered = str(hm.analyse(hm.Lambda("x", hm.Identifier("x")), {}))
    m = re.fullmatch(r"\((\w+) -> (\w+)\)", rendered)
    assert m is not None and m.group(1) == m.group(2)


def test_type_mismatch_is_detected():
    # zero true  ->  zero expects int, true is bool
    with pytest.raises(hm.InferenceError):
        hm.analyse(hm.Apply(hm.Identifier("zero"), hm.Identifier("true")), _env())
