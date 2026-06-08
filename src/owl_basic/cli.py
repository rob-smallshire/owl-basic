"""Click command-line interface for the OWL BASIC compiler.

A single ``owl-basic`` entry point compiles BBC BASIC source to a .NET assembly
via a code-generation backend (``dotnet`` by default) and optionally runs it::

    owl-basic compile hello.bbc      # -> hello.dll (+ runtimeconfig + OwlRuntime.dll)
    dotnet hello.dll                 # run it
    owl-basic run hello.bbc          # compile and run in one step
    owl-basic backends               # list available backends

Status and diagnostics are written to stderr; stdout is reserved for the
compiled program's own output, so ``owl-basic run prog.bbc | ...`` stays clean.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click

from owl_basic import __version__
from owl_basic.analysis import analyse, analyse_numbered_lines
from owl_basic.bbc_basic.detokenizer import detokenize_lines
from owl_basic.bbc_basic.tokens import LINE_RECORD_MARKER
from owl_basic.exceptions import OwlBasicError
from owl_basic.extension import create_extension, list_extensions

_BACKEND_NAMESPACE = "owl_basic.backend"


def _colour_enabled() -> bool:
    """Whether stderr may carry ANSI colour (honours NO_COLOR / CLICOLOR / TTY)."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("CLICOLOR") == "0":
        return False
    return sys.stderr.isatty()


def _status(message: str, *, fg: str = "green") -> None:
    click.echo(click.style(message, fg=fg) if _colour_enabled() else message, err=True)


def _fail(message: str) -> None:
    text = "owl-basic: " + message
    click.echo(click.style(text, fg="red") if _colour_enabled() else text, err=True)
    raise SystemExit(1)


def _find_owlruntime_dll() -> Path | None:
    """Locate the newest built net10 OwlRuntime.dll in the source tree."""
    repo_root = Path(__file__).resolve().parents[2]
    matches = list(repo_root.glob("OwlRuntime/OwlRuntime/bin/**/net10.0/OwlRuntime.dll"))
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


_LINE_NUMBERED = re.compile(r"\s*\d")


def _analyse_source(source: Path, encoding: str):
    """Analyse a BASIC *source* file, picking the right front end for its form.

    Three forms are accepted transparently:

    * a tokenised image (``.bbc`` from the benchmark/program discs), recognised
      by its leading line-record marker -- detokenised, then analysed by real
      line number so GOTO/GOSUB targets resolve;
    * a plain-text *listing* whose lines carry explicit BBC line numbers (as
      LISTed or detokenised programs do) -- likewise analysed by line number;
    * a number-free snippet -- analysed with synthesised line numbers.
    """
    data = source.read_bytes()
    if data[:1] == bytes((LINE_RECORD_MARKER,)):
        return analyse_numbered_lines(
            detokenize_lines(data), name=source.stem, source_filepath=str(source)
        )

    text = data.decode(encoding)
    non_blank = [line for line in text.splitlines() if line.strip()]
    if non_blank and all(_LINE_NUMBERED.match(line) for line in non_blank):
        numbered = []
        for line in non_blank:
            number, _, body = line.strip().partition(" ")
            numbered.append((int(number), " " + body if body else body))
        return analyse_numbered_lines(
            numbered, name=source.stem, source_filepath=str(source)
        )

    return analyse(text, name=source.stem, source_filepath=str(source))


def _compile(source: Path, output_dir: Path, backend_name: str, encoding: str) -> Path:
    """Compile *source* to an assembly under *output_dir*; return its path."""
    program = _analyse_source(source, encoding)
    backend = create_extension("backend", _BACKEND_NAMESPACE, backend_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = backend.generate(program, output_dir)

    # The .NET host resolves dependencies from the assembly's directory.
    runtime = _find_owlruntime_dll()
    if runtime is not None:
        shutil.copy(runtime, output_dir)
    else:
        _status(
            "warning: OwlRuntime.dll not found; place it next to the assembly to run it.",
            fg="yellow",
        )
    return artifact


_source_argument = click.argument(
    "source", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
_backend_option = click.option(
    "-b", "--backend", default="dotnet", show_default=True,
    help="Code-generation backend.",
)
_output_option = click.option(
    "-o", "--output-dir", type=click.Path(file_okay=False, path_type=Path),
    default=Path("."), show_default=True,
    help="Directory for the compiled assembly.",
)
_encoding_option = click.option(
    "-e", "--encoding", default="acorn", show_default=True,
    help="Character encoding of the source file (e.g. acorn, latin-1, utf-8).",
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="owl-basic")
def cli() -> None:
    """Compile and run BBC BASIC programs on .NET."""


@cli.command("compile")
@_source_argument
@_backend_option
@_output_option
@_encoding_option
def compile_command(source: Path, backend: str, output_dir: Path, encoding: str) -> None:
    """Compile a BBC BASIC SOURCE file to a .NET assembly."""
    try:
        artifact = _compile(source, output_dir, backend, encoding)
    except OwlBasicError as error:
        _fail(str(error))
    _status("Compiled %s -> %s" % (source, artifact))


@cli.command("run")
@_source_argument
@_backend_option
@_output_option
@_encoding_option
def run_command(source: Path, backend: str, output_dir: Path, encoding: str) -> None:
    """Compile a BBC BASIC SOURCE file and run it on .NET."""
    try:
        artifact = _compile(source, output_dir, backend, encoding)
    except OwlBasicError as error:
        _fail(str(error))
    _status("Running %s ..." % artifact)
    sys.stdout.flush()
    result = subprocess.run(["dotnet", str(artifact)])
    raise SystemExit(result.returncode)


@cli.command("backends")
def backends_command() -> None:
    """List the available code-generation backends."""
    for name in list_extensions(_BACKEND_NAMESPACE):
        click.echo(name)


def main(argv=None):
    return cli.main(args=argv, prog_name="owl-basic")


if __name__ == "__main__":
    cli.main(prog_name="owl-basic")
