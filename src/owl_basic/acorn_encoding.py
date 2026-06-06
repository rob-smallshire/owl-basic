"""Character encoding for the Acorn / BBC Micro character set.

The BBC Micro used a variant of ASCII with a few UK-specific characters (most
visibly ``£`` in place of the backtick). This module registers a Python codec
named ``"acorn"`` so source and string data can be decoded/encoded faithfully::

    "COST£100".encode("acorn")     # -> b"COST\\x60100"
    b"COST\\x60100".decode("acorn")  # -> "COST£100"

Provenance: cloned from the sixty-north ``oaknut`` project
(``oaknut.file.acorn_encoding``), trimmed to the codec itself (the DFS
filename helpers are omitted). Intended to be replaced by a shared installable
package later.

References:
- https://beebwiki.mdfs.net/ASCII
"""

import codecs
from typing import Optional, Tuple

# BBC Micro byte values that differ from ASCII.
BBC_MICRO_TO_UNICODE = {
    0x60: "£",  # backtick -> pound sign
    0x7C: "¦",  # vertical bar -> broken bar
}
UNICODE_TO_BBC_MICRO = {v: k for k, v in BBC_MICRO_TO_UNICODE.items()}


class AcornCodec(codecs.Codec):
    """Codec for the Acorn / BBC Micro character encoding."""

    def encode(self, input: str, errors: str = "strict") -> Tuple[bytes, int]:
        output = bytearray()
        for i, char in enumerate(input):
            if char in UNICODE_TO_BBC_MICRO:
                output.append(UNICODE_TO_BBC_MICRO[char])
            else:
                code_point = ord(char)
                if code_point > 255:
                    if errors == "ignore":
                        continue
                    if errors == "replace":
                        output.append(ord("?"))
                        continue
                    raise UnicodeEncodeError(
                        "acorn", input, i, i + 1,
                        "Character %r (U+%04X) cannot be encoded in the Acorn "
                        "character set" % (char, code_point),
                    )
                else:
                    output.append(code_point)
        return bytes(output), len(input)

    def decode(self, input: bytes, errors: str = "strict") -> Tuple[str, int]:
        output = [
            BBC_MICRO_TO_UNICODE.get(byte, chr(byte)) for byte in input
        ]
        return "".join(output), len(input)


# The codec is stateless, so one shared instance backs every entry point.
_SHARED_ACORN_CODEC = AcornCodec()


class AcornIncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input: str, final: bool = False) -> bytes:
        return _SHARED_ACORN_CODEC.encode(input, self.errors)[0]


class AcornIncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input: bytes, final: bool = False) -> str:
        return _SHARED_ACORN_CODEC.decode(input, self.errors)[0]


class AcornStreamWriter(AcornCodec, codecs.StreamWriter):
    pass


class AcornStreamReader(AcornCodec, codecs.StreamReader):
    pass


def getregentry(name: Optional[str] = None) -> codecs.CodecInfo:
    return codecs.CodecInfo(
        name="acorn",
        encode=_SHARED_ACORN_CODEC.encode,
        decode=_SHARED_ACORN_CODEC.decode,
        incrementalencoder=AcornIncrementalEncoder,
        incrementaldecoder=AcornIncrementalDecoder,
        streamreader=AcornStreamReader,
        streamwriter=AcornStreamWriter,
    )


def _search_function(encoding: str) -> Optional[codecs.CodecInfo]:
    if encoding.lower() == "acorn":
        return getregentry(encoding)
    return None


codecs.register(_search_function)


def acorn_to_unicode(data: bytes) -> str:
    """Decode Acorn-encoded bytes to a Unicode string."""
    return data.decode("acorn")


def unicode_to_acorn(text: str) -> bytes:
    """Encode a Unicode string to Acorn-encoded bytes."""
    return text.encode("acorn")
