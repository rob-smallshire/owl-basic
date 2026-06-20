"""The pluggable code-generation backend seam.

A :class:`Backend` lowers a fully-analysed :class:`Program` to a target
artifact. Backends are named for the *target platform*, which in turn implies a
runtime library:

  - ``dotnet``            -> textual CIL assembled to a .NET assembly, run on the
                            CLR or Mono, against the OwlRuntime runtime library.
  - ``acorn-bbc-model-b`` -> 6502 machine code for a BBC Micro Model B, implying
                            that machine's MOS runtime. (future)
  - a C backend, etc.     -> named for the platform whose runtime it targets.

The implied-runtime relationship is the defining characteristic of a backend;
for now it is carried by the backend's identity and documentation, and is the
natural home for a first-class runtime descriptor once a second backend exists.

Backends are stevedore extensions of kind ``"backend"`` (entry-point namespace
``owl_basic.backend``); see :mod:`owl_basic.extension`.
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from owl_basic.extension import Extension


@dataclass(frozen=True)
class Program:
    """A fully-analysed BASIC program, ready for a backend to lower.

    This bundle is backend-agnostic: the same :class:`Program` feeds the
    dotnet, 6502 or C backends. It mirrors what the front-end produces by the
    end of analysis (the arguments the legacy codegen received directly).
    """

    name: str
    source_filepath: str
    entry_points: Any
    ordered_basic_blocks: Any
    global_symbols: Any
    data: Any
    line_mapper: Any
    # The root AST node. Backends lower from the basic blocks and do not need
    # it; it is carried for whole-tree consumers such as visualisation (the
    # ``cfg`` and ``ast`` graph sources walk it). Optional so existing
    # constructions stay valid.
    parse_tree: Any = None
    # Type errors reported while analysing this program. Non-empty means it did
    # not type-check, so a backend must refuse to lower it (analysis recovers to
    # collect every diagnostic, not to license generating code for a broken
    # program). Default empty so hand-built Programs stay valid.
    diagnostics: Any = field(default_factory=list)


class Backend(Extension):
    """Base class for code-generation backends.

    Subclasses lower a :class:`Program` to a target artifact and own both the
    toolchain and the runtime library appropriate to their target platform.
    """

    @classmethod
    def _kind(cls) -> str:
        return "backend"

    @abstractmethod
    def generate(self, program: Program, output_dirpath: Path, options=None) -> Path:
        """Lower *program* to an artifact under *output_dirpath*.

        Returns the path to the primary generated artifact.
        """
        raise NotImplementedError
