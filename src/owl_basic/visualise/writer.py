"""The pluggable *graph writer* seam.

A :class:`GraphWriter` serialises a neutral
:class:`~owl_basic.visualise.model.Graph` to a concrete format -- yEd GraphML,
GraphViz DOT, and so on. Writers own the look of the output: they map each
node/edge ``kind`` to a shape, style or arrow.

Writers are stevedore extensions of kind ``"graph_writer"`` (entry-point
namespace ``owl_basic.graph_writer``); see :mod:`owl_basic.extension`.
"""

from abc import abstractmethod

from owl_basic.extension import Extension
from owl_basic.visualise.model import Graph


class GraphWriter(Extension):
    """Base class for graph writers: a neutral graph in, text out."""

    @classmethod
    def _kind(cls) -> str:
        return "graph_writer"

    @classmethod
    @abstractmethod
    def file_extension(cls) -> str:
        """The conventional file extension for this format, with leading dot."""
        raise NotImplementedError

    @abstractmethod
    def write(self, graph: Graph, stream) -> None:
        """Serialise *graph* to the text *stream*."""
        raise NotImplementedError
