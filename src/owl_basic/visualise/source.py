"""The pluggable *graph source* seam.

A :class:`GraphSource` derives a neutral :class:`~owl_basic.visualise.model.Graph`
from an analysed :class:`~owl_basic.codegen.backend.Program`. Each source is one
*view* of the program -- the control-flow graph, the basic-block graph, the AST,
a call graph -- and is selected by name on the command line.

Sources are stevedore extensions of kind ``"graph_source"`` (entry-point
namespace ``owl_basic.graph_source``); see :mod:`owl_basic.extension`.
"""

from abc import abstractmethod

from owl_basic.extension import Extension
from owl_basic.visualise.model import Graph


class GraphSource(Extension):
    """Base class for graph sources: a program in, a neutral graph out."""

    @classmethod
    def _kind(cls) -> str:
        return "graph_source"

    @abstractmethod
    def build(self, program, options=None) -> Graph:
        """Build the neutral graph for *program*.

        Returns a :class:`~owl_basic.visualise.model.Graph` for any registered
        :class:`~owl_basic.visualise.writer.GraphWriter` to render.
        """
        raise NotImplementedError
