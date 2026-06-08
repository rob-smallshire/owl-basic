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

Compile a BBC BASIC program to a .NET assembly, then run it with the `dotnet`
host. The compiler accepts tokenised disc files (`.bbc`) as well as plain-text
listings:

    owl-basic compile path/to/program.bbc -o out   # -> out/program.dll
    dotnet out/program.dll                          # run the compiled assembly

Alongside `program.dll`, `compile` writes everything it needs to run into the
output directory: `program.runtimeconfig.json` (which tells the `dotnet` host
which runtime to use), the `OwlRuntime.dll` support library it links against,
and the textual CIL (`program.il`) for inspection. If you move the `.dll`, keep
`program.runtimeconfig.json` and `OwlRuntime.dll` beside it.

For a quick edit-run loop, `run` compiles and runs in one step:

    owl-basic run path/to/program.bbc
    owl-basic --help                                # all commands and options

Two examples are included in the repository. ClockSP, compiled and run as two
steps:

    owl-basic compile tests/data/benchmarks/CLKSP3.bbc -o out
    dotnet out/CLKSP3.dll                            # a CPU timing benchmark

Acornsoft's Sphinx Adventure (interactive -- type commands at the prompt):

    owl-basic run tests/data/sphinx2-deprotected.bbc
