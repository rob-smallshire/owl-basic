"""Visualisation of analysed BBC BASIC programs as graphs.

Visualisation has two pluggable axes, both stevedore extension points:

* a *graph source* (kind ``"graph_source"``, namespace ``owl_basic.graph_source``)
  derives a neutral :class:`~owl_basic.visualise.model.Graph` from an analysed
  :class:`~owl_basic.codegen.backend.Program` -- e.g. the control-flow graph or
  the basic-block graph;
* a *graph writer* (kind ``"graph_writer"``, namespace ``owl_basic.graph_writer``)
  serialises that neutral graph to a concrete format -- e.g. yEd GraphML or
  GraphViz DOT.

Because they meet only at the neutral graph model, any source pairs with any
writer. New views and formats are added as plug-ins without touching the CLI or
the analysis pipeline; see :mod:`owl_basic.extension`.
"""
