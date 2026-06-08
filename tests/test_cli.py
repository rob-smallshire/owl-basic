"""The owl-basic click CLI.

Covers the plumbing that needs no .NET toolchain (help, version, backend
listing, error handling). The actual compile-and-run path is exercised in
test_dotnet_emitter.py.
"""

import os
from pathlib import Path

from click.testing import CliRunner

from helpers import FIXTURES_DIRPATH

from owl_basic.cli import cli, _analyse_source
from owl_basic.codegen.backend import Program


def test_analyse_source_handles_a_tokenised_bbc_image(tmp_path):
    # A tokenised .bbc image (here a real benchmark) is detokenised and
    # analysed by its real line numbers, so GOTO/GOSUB targets resolve.
    source = Path(FIXTURES_DIRPATH) / "data" / "benchmarks" / "CLKSP3.bbc"
    program = _analyse_source(source, "acorn")
    assert isinstance(program, Program)


def test_analyse_source_handles_a_numbered_listing(tmp_path):
    # A plain-text listing whose lines carry explicit BBC line numbers is
    # analysed by line number; the GOTO target must resolve.
    listing = tmp_path / "numbered.bas"
    listing.write_text('10 PRINT "a"\n20 GOTO 40\n30 PRINT "skip"\n40 END\n')
    program = _analyse_source(listing, "latin-1")
    assert isinstance(program, Program)


def test_analyse_source_handles_a_number_free_snippet(tmp_path):
    # A snippet without line numbers gets synthesised numbers.
    snippet = tmp_path / "snippet.bas"
    snippet.write_text('PRINT "x"\nPRINT 6 * 7\n')
    program = _analyse_source(snippet, "latin-1")
    assert isinstance(program, Program)


def test_help_lists_the_commands():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Compile and run BBC BASIC" in result.output
    for command in ("compile", "run", "backends"):
        assert command in result.output


def test_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "owl-basic" in result.output


def test_backends_lists_the_dotnet_backend():
    result = CliRunner().invoke(cli, ["backends"])
    assert result.exit_code == 0
    assert "dotnet" in result.output.split()


def test_compile_reports_a_missing_source_file():
    result = CliRunner().invoke(cli, ["compile", "no_such_file.bbc"])
    assert result.exit_code != 0
