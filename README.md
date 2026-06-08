A BBC BASIC compiler for .NET, written in Python and C#.

What it does
============

Allows you to write BBC BASIC code and run it with a similar performance profile to C#.

The compiler (Python) parses BBC BASIC and emits textual CIL, which is assembled
by the CoreCLR `ilasm` and run on .NET; compiled programs link against the
OwlRuntime support library (C#).

Is it finished?
===============

No. OWL BASIC compiles some simple programs and some complex commercial programs,
including Acornsoft's Sphinx adventure. There are still many features to be added, bugs
to be fixed and improvements to be made.

Building and running
====================

Prerequisites: the .NET SDK (providing `dotnet` and a CoreCLR `ilasm`) and
Python 3.14 or later.

Install the compiler into a virtual environment with [uv](https://docs.astral.sh/uv/):

    uv sync
    source .venv/bin/activate

Build the OwlRuntime support library once; compiled programs link against it:

    dotnet build -c Release OwlRuntime/OwlRuntime

Compile and run a BBC BASIC program. The `run` command accepts tokenised disc
files (`.bbc`) as well as plain-text listings:

    owl-basic run path/to/program.bbc      # compile and run
    owl-basic compile path/to/program.bbc  # compile to a .dll only
    owl-basic --help                        # all commands and options

Two examples are included in the repository:

    # ClockSP -- a CPU timing benchmark
    owl-basic run tests/data/benchmarks/CLKSP3.bbc

    # Acornsoft's Sphinx Adventure (interactive -- type commands at the prompt)
    owl-basic run tests/data/sphinx2-deprotected.bbc
