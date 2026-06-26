"""CASE ... OF / WHEN / OTHERWISE / ENDCASE -- the BASIC V multi-way switch.

  CASE <expr> OF
    WHEN v1[,v2,...] : <statements>
    ...
    [OTHERWISE <statements>]
  ENDCASE

The control expression is evaluated once; each WHEN's value(s) are tested
top-to-bottom and the first match's body runs, then control resumes after
ENDCASE -- expressions in later WHENs are not evaluated (short-circuit, confirmed
against a real Archimedes). OTHERWISE catches a value no WHEN matched; with no
OTHERWISE an unmatched value falls straight through. Surfaced across many Acorn
User Archimedes type-ins.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_case_selects_the_matching_when(compile_and_run):
    out = compile_and_run(analyse(
        'A%=2\nCASE A% OF\nWHEN 1:PRINT "one"\nWHEN 2:PRINT "two"\nENDCASE\n'
        'PRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["two", "after"]


@requires_dotnet_toolchain
def test_case_first_when(compile_and_run):
    out = compile_and_run(analyse(
        'A%=1\nCASE A% OF\nWHEN 1:PRINT "one"\nWHEN 2:PRINT "two"\nENDCASE\n'
        'PRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["one", "after"]


@requires_dotnet_toolchain
def test_case_otherwise(compile_and_run):
    out = compile_and_run(analyse(
        'A%=9\nCASE A% OF\nWHEN 1:PRINT "one"\nOTHERWISE PRINT "other"\nENDCASE\n'
        'PRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["other", "after"]


@requires_dotnet_toolchain
def test_case_multi_value_when(compile_and_run):
    out = compile_and_run(analyse(
        'A%=3\nCASE A% OF\nWHEN 1:PRINT "one"\nWHEN 2,3,4:PRINT "mid"\nENDCASE\n'
        'PRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["mid", "after"]


@requires_dotnet_toolchain
def test_case_no_match_no_otherwise_falls_through(compile_and_run):
    out = compile_and_run(analyse(
        'A%=9\nCASE A% OF\nWHEN 1:PRINT "one"\nWHEN 2:PRINT "two"\nENDCASE\n'
        'PRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["after"]


@requires_dotnet_toolchain
def test_case_multi_statement_body(compile_and_run):
    out = compile_and_run(analyse(
        'A%=1\nCASE A% OF\nWHEN 1:PRINT "a":PRINT "b"\nOTHERWISE PRINT "x"\nENDCASE\n'
        'PRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["a", "b", "after"]


@requires_dotnet_toolchain
def test_case_on_string(compile_and_run):
    out = compile_and_run(analyse(
        'A$="b"\nCASE A$ OF\nWHEN "a":PRINT "first"\nWHEN "b":PRINT "second"\n'
        'OTHERWISE PRINT "other"\nENDCASE\nPRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["second", "after"]


@requires_dotnet_toolchain
def test_case_on_float_condition(compile_and_run):
    # A non-integer control value; integer WHEN values are coerced to match.
    out = compile_and_run(analyse(
        'x=2.0\nCASE x OF\nWHEN 1:PRINT "a"\nWHEN 2:PRINT "b"\nOTHERWISE PRINT "c"\n'
        'ENDCASE\nPRINT "after"\nEND\n', name="case"))
    assert out.splitlines() == ["b", "after"]


@requires_dotnet_toolchain
def test_case_only_matched_body_runs(compile_and_run):
    # Pin the short-circuit selection: exactly one body runs, then ENDCASE.
    out = compile_and_run(analyse(
        'FOR I%=1 TO 3\nCASE I% OF\nWHEN 1:PRINT "one"\nWHEN 2:PRINT "two"\n'
        'OTHERWISE PRINT "many"\nENDCASE\nNEXT\nEND\n', name="case"))
    assert out.splitlines() == ["one", "two", "many"]
