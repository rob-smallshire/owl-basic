"""The owl-basic click CLI.

Covers the plumbing that needs no .NET toolchain (help, version, backend
listing, error handling). The actual compile-and-run path is exercised in
test_dotnet_emitter.py.
"""

from click.testing import CliRunner

from owl_basic.cli import cli


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
