"""OWL BASIC ``dotnet`` backend.

Emits textual CIL (``.il``), assembles it with the CoreCLR ``ilasm`` into a .NET
assembly, and runs on modern .NET (``dotnet``) against the OwlRuntime runtime
library — no IronPython, no mono. The runtime's default screen mode is the
headless raw console, so text programs print to stdout.
"""

import glob
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from owl_basic.codegen.backend import Backend as BackendBase, Program
from owl_basic.ext.backends.dotnet.emitter import emit_program

logger = logging.getLogger(__name__)

_NON_IDENT = re.compile(r"[^A-Za-z0-9_]")

# The framework the generated assembly targets and the runtimeconfig it needs.
_TFM = "net10.0"
_FRAMEWORK = "Microsoft.NETCore.App"
_FRAMEWORK_VERSION = "10.0.0"


class Backend(BackendBase):
    """Generate a .NET executable by emitting textual CIL and assembling it with
    the CoreCLR ilasm. Runs on modern .NET against the OwlRuntime runtime library.
    """

    def generate(self, program: Program, output_dirpath, options=None) -> Path:
        """Emit, assemble and configure a runnable .NET assembly for *program*.

        Returns the path to the generated ``.dll``. ``OwlRuntime.dll`` must be
        placed alongside it (or otherwise resolvable) for the program to run.
        """
        output_dirpath = Path(output_dirpath)
        name = self._assembly_name(program)

        il_filepath = output_dirpath / (name + ".il")
        il_filepath.write_text(self.emit_il(program), encoding="utf-8")
        logger.debug("Wrote CIL to %s", il_filepath)

        dll_filepath = output_dirpath / (name + ".dll")
        self.assemble(il_filepath, dll_filepath)
        self._write_runtimeconfig(dll_filepath)
        return dll_filepath

    def emit_il(self, program: Program) -> str:
        """Render *program* as textual CIL."""
        return emit_program(program, self._assembly_name(program))

    def assemble(self, il_filepath, dll_filepath=None) -> Path:
        """Assemble a ``.il`` file into a .NET assembly with the CoreCLR ilasm.

        Kept separate from :meth:`generate` so the pure CIL-text generation can
        be unit-tested without the assembler present.
        """
        il_filepath = Path(il_filepath)
        if dll_filepath is None:
            dll_filepath = il_filepath.with_suffix(".dll")
        ilasm = self.find_ilasm()
        if ilasm is None:
            raise FileNotFoundError(
                "CoreCLR ilasm not found. Install the "
                "runtime.<rid>.Microsoft.NETCore.ILAsm NuGet package (or put "
                "ilasm on PATH)."
            )
        subprocess.run(
            [ilasm, "-dll", "-output:" + str(dll_filepath), str(il_filepath)],
            check=True,
            capture_output=True,
            text=True,
        )
        return dll_filepath

    @staticmethod
    def find_ilasm():
        """Locate a CoreCLR ilasm: the NuGet runtime package, else PATH."""
        home = os.path.expanduser("~")
        pattern = os.path.join(
            home,
            ".nuget", "packages",
            "runtime.*.microsoft.netcore.ilasm", "*", "runtimes", "*", "native",
            "ilasm*",
        )
        matches = sorted(glob.glob(pattern))
        for candidate in matches:
            if os.path.isfile(candidate):
                return candidate
        return shutil.which("ilasm")

    @staticmethod
    def _write_runtimeconfig(dll_filepath):
        config = {
            "runtimeOptions": {
                "tfm": _TFM,
                "framework": {"name": _FRAMEWORK, "version": _FRAMEWORK_VERSION},
            }
        }
        config_filepath = Path(dll_filepath).with_suffix(".runtimeconfig.json")
        config_filepath.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return config_filepath

    @staticmethod
    def _assembly_name(program: Program) -> str:
        name = _NON_IDENT.sub("_", program.name) or "owl_program"
        # An IL identifier may not start with a digit (the corpus names programs
        # by share id, e.g. "5df6cac4d936"); prefix one that does so .assembly /
        # .module names stay valid without quoting.
        if name[0].isdigit():
            name = "_" + name
        return name
