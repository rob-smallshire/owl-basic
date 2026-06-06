"""A clean-room, dialect-aware BBC BASIC (de)tokeniser.

Tokenising converts BBC BASIC source text to the interpreter's internal
tokenised byte form; detokenising reverses it. Both are parameterised by a
:class:`~owl_basic.bbc_basic.tokens.Dialect` (BBC BASIC II, IV, V, BB4W, ...).

This is original work, informed by the public knowledge embodied in the BBC
BASIC ROMs and several reference implementations (beebtools, basictool,
basic_tokens), but not derived from any of their source. It is developed here
and intended for later extraction into a standalone ``oaknut-basic`` package.
"""

from owl_basic.bbc_basic.detokenizer import detokenize
from owl_basic.bbc_basic.tokens import BBC_BASIC_II, Dialect

__all__ = ["detokenize", "Dialect", "BBC_BASIC_II"]
