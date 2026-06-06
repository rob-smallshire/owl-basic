"""OWL BASIC — a BBC BASIC compiler for the .NET CLR with pluggable backends."""

# Registers the "acorn" text codec (BBC Micro character set) as a side effect,
# so source can be read with `encoding="acorn"` anywhere in the package.
from owl_basic import acorn_encoding as _acorn_encoding  # noqa: F401

__version__ = "0.6.0"
