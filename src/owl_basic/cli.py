"""Click command-line interface for the OWL BASIC compiler.

A single ``owl-basic`` entry point compiles BBC BASIC source to a .NET assembly
via a code-generation backend (``dotnet`` by default) and optionally runs it::

    owl-basic compile hello.bbc      # -> hello.dll (+ runtimeconfig + OwlRuntime.dll)
    dotnet hello.dll                 # run it
    owl-basic run hello.bbc          # compile and run in one step
    owl-basic backends               # list available backends

It can also visualise a program as a graph, decoupled from compilation::

    owl-basic visualise cfg hello.bbc            # -> hello.cfg.graphml (for yEd)
    owl-basic visualise blocks hello.bbc -f dot  # -> hello.blocks.dot (GraphViz)
    owl-basic graph-sources                      # list views (cfg, blocks, ...)
    owl-basic graph-writers                      # list formats (graphml, dot)

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
_GRAPH_SOURCE_NAMESPACE = "owl_basic.graph_source"
_GRAPH_WRITER_NAMESPACE = "owl_basic.graph_writer"
_DEFAULT_GRAPH_FORMAT = "graphml"


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


# A line-numbered listing line: leading digits (the line number), then the body.
# BBC BASIC does not require a space after the number (10PRINT is as valid as
# 10 PRINT), so the number is the leading run of digits, not "up to the first
# space"; an optional single space between them is consumed.
_LINE_NUMBERED = re.compile(r"\s*(\d+)\s?(.*)", re.DOTALL)


def _analyse_source(source: Path, encoding: str, tolerant: bool = False):
    """Analyse a BASIC *source* file, picking the right front end for its form.

    Three forms are accepted transparently:

    * a tokenised image (``.bbc`` from the benchmark/program discs), recognised
      by its leading line-record marker -- detokenised, then analysed by real
      line number so GOTO/GOSUB targets resolve;
    * a plain-text *listing* whose lines carry explicit BBC line numbers (as
      LISTed or detokenised programs do) -- likewise analysed by line number;
    * a number-free snippet -- analysed with synthesised line numbers.

    When *tolerant*, a program that fails a pass after the control-flow graph is
    built still returns a partial :class:`Program` (forward CFG only) instead of
    raising -- for visualisation. Compilation never passes this.
    """
    data = source.read_bytes()
    if data[:1] == bytes((LINE_RECORD_MARKER,)):
        return analyse_numbered_lines(
            detokenize_lines(data), name=source.stem, source_filepath=str(source),
            tolerant=tolerant,
        )

    text = data.decode(encoding)
    non_blank = [line for line in text.splitlines() if line.strip()]
    matches = [_LINE_NUMBERED.match(line) for line in non_blank]
    if non_blank and all(matches):
        numbered = []
        for match in matches:
            number, body = match.group(1), match.group(2)
            numbered.append((int(number), " " + body if body else body))
        return analyse_numbered_lines(
            numbered, name=source.stem, source_filepath=str(source),
            tolerant=tolerant,
        )

    return analyse(text, name=source.stem, source_filepath=str(source),
                   tolerant=tolerant)


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
        _copy_runtime_dependencies(runtime.parent, output_dir)
    else:
        _status(
            "warning: OwlRuntime.dll not found; place it next to the assembly to run it.",
            fg="yellow",
        )
    return artifact


def _copy_runtime_dependencies(runtime_dir: Path, output_dir: Path) -> None:
    """Copy SkiaSharp (used by graphics modes) and its native library beside the
    program, so a graphics program can run. SkiaSharp loads lazily, so non
    -graphics programs work without these, but copying them is cheap and makes
    every compiled program graphics-capable."""
    skia = runtime_dir / "SkiaSharp.dll"
    if skia.exists():
        shutil.copy(skia, output_dir)
    if sys.platform == "darwin":
        native = "runtimes/osx*/native/libSkiaSharp.dylib"
    elif sys.platform.startswith("linux"):
        native = "runtimes/linux*/native/libSkiaSharp.so"
    else:
        native = "runtimes/win*/native/libSkiaSharp.dll"
    for path in runtime_dir.glob(native):
        shutil.copy(path, output_dir)
        break


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


def _writer_for_extension(suffix: str):
    """The graph-writer name whose file extension is *suffix*, or ``None``."""
    for name in list_extensions(_GRAPH_WRITER_NAMESPACE):
        writer = create_extension("graph_writer", _GRAPH_WRITER_NAMESPACE, name)
        if writer.file_extension() == suffix:
            return name
    return None


def _resolve_format(fmt: str | None, output: str | None) -> str:
    """Choose the graph-writer name from the ``-f`` flag and/or output path.

    An explicit ``-f`` wins; otherwise the writer is inferred from the output
    file's extension; failing that the default (graphml) is used.
    """
    if fmt is not None:
        return fmt
    if output not in (None, "-"):
        inferred = _writer_for_extension(Path(output).suffix)
        if inferred is not None:
            return inferred
    return _DEFAULT_GRAPH_FORMAT


@cli.command("visualise")
@click.argument("view")
@_source_argument
@click.option(
    "-f", "--format", "fmt", default=None,
    help="Output format (graph writer). Default: inferred from -o, else graphml.",
)
@click.option(
    "-o", "--output", default=None,
    help="Output file, or '-' for stdout. Default: <source>.<view><ext>.",
)
@click.option(
    "-r", "--routine", default=None,
    help="Scope the graph to one routine (e.g. MAIN, PROCdraw). Default: whole program.",
)
@_encoding_option
def visualise_command(view: str, source: Path, fmt: str | None, output: str | None,
                      routine: str | None, encoding: str) -> None:
    """Visualise a BBC BASIC SOURCE file as a graph.

    VIEW selects what to draw (see 'owl-basic graph-sources'); the format is
    chosen with -f (see 'owl-basic graph-writers'). Use -r to scope a large
    program to a single routine. For example:

        owl-basic visualise cfg prog.bbc
        owl-basic visualise blocks prog.bbc -f dot -o prog.dot
        owl-basic visualise cfg prog.bbc -r PROCdraw
        owl-basic visualise callgraph prog.bbc -r MAIN -f dot -o - | dot -Tsvg -o m.svg
    """
    try:
        # Tolerant: render the graph even for a program that does not fully
        # analyse (e.g. one rejected at loop correlation) -- the forward CFG is
        # built before those passes, and seeing it is most useful precisely then.
        program = _analyse_source(source, encoding, tolerant=True)
        graph_source = create_extension("graph_source", _GRAPH_SOURCE_NAMESPACE, view)
        writer_name = _resolve_format(fmt, output)
        writer = create_extension("graph_writer", _GRAPH_WRITER_NAMESPACE, writer_name)
        graph = graph_source.build(program, {"routine": routine})
    except OwlBasicError as error:
        _fail(str(error))

    if output == "-":
        writer.write(graph, sys.stdout)
        return

    if output is not None:
        destination = Path(output)
    else:
        suffix = "." + routine if routine else ""
        destination = Path(source.stem + "." + view + suffix + writer.file_extension())
    with open(destination, "w", encoding="utf-8") as stream:
        writer.write(graph, stream)
    _status("Wrote %s graph of %s -> %s" % (view, source, destination))


@cli.command("graph-sources")
def graph_sources_command() -> None:
    """List the available graph sources (visualisation views)."""
    for name in list_extensions(_GRAPH_SOURCE_NAMESPACE):
        click.echo(name)


@cli.command("graph-writers")
def graph_writers_command() -> None:
    """List the available graph writers (visualisation output formats)."""
    for name in list_extensions(_GRAPH_WRITER_NAMESPACE):
        click.echo(name)


@cli.command("routines")
@_source_argument
@_encoding_option
def routines_command(source: Path, encoding: str) -> None:
    """List the routines of a SOURCE file (for 'visualise --routine')."""
    from owl_basic.ext.graph_sources._routines import display_name
    try:
        program = _analyse_source(source, encoding)
    except OwlBasicError as error:
        _fail(str(error))
    for name in sorted(display_name(key) for key in program.entry_points):
        click.echo(name)


def main(argv=None):
    return cli.main(args=argv, prog_name="owl-basic")


if __name__ == "__main__":
    cli.main(prog_name="owl-basic")
