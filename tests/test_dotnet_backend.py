"""The dotnet backend, exercised through the stevedore extension seam.

The CIL-text generation runs everywhere (pure Python). The assemble-and-run
test is skipped unless Mono's ilasm and the mono runtime are present, so CI
without a .NET/Mono toolchain stays green.
"""

import shutil
import subprocess

import pytest

from owl_basic.codegen.backend import Program
from owl_basic.extension import create_extension, list_extensions


def _program(name="six_times_seven"):
    return Program(
        name=name,
        source_filepath="x.bas",
        entry_points={},
        ordered_basic_blocks=[],
        global_symbols=None,
        data=None,
        line_mapper=None,
    )


def _dotnet_backend():
    return create_extension("backend", "owl_basic.backend", "dotnet")


def test_dotnet_backend_is_discoverable():
    assert "dotnet" in list_extensions("owl_basic.backend")


def test_dotnet_backend_emits_valid_il_skeleton(tmp_path):
    il_filepath = _dotnet_backend().generate(_program(), tmp_path)
    text = il_filepath.read_text(encoding="utf-8")
    assert il_filepath.name == "six_times_seven.il"
    assert ".assembly extern mscorlib" in text
    assert ".entrypoint" in text


needs_mono = pytest.mark.skipif(
    shutil.which("ilasm") is None or shutil.which("mono") is None,
    reason="requires Mono ilasm and the mono runtime",
)


@needs_mono
def test_dotnet_backend_assembles_and_runs(tmp_path):
    backend = _dotnet_backend()
    il_filepath = backend.generate(_program(), tmp_path)
    exe_filepath = backend.assemble(il_filepath)
    result = subprocess.run(["mono", str(exe_filepath)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
