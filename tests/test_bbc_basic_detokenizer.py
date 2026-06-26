"""Golden-master tests for OWL's BBC BASIC detokeniser facade.

Detokenisation is delegated to oaknut-basic, defaulting to the BASIC V dialect
(see owl_basic.bbc_basic.detokenizer). These pin the behaviour OWL relies on."""

from owl_basic.bbc_basic import detokenize
from owl_basic.bbc_basic.detokenizer import decode_line_reference, detokenize_lines


def _program(*lines):
    """Build a tokenised program from (line_number, content_bytes) tuples."""
    out = bytearray()
    for number, content in lines:
        out += bytes([0x0D, (number >> 8) & 0xFF, number & 0xFF, 4 + len(content)])
        out += bytes(content)
    out += bytes([0x0D, 0xFF])  # end-of-program marker
    return bytes(out)


def test_keyword_and_string():
    # 10 PRINT"HELLO"  ->  PRINT=0xF1, then the quoted string verbatim
    data = _program((10, [0xF1, 0x22, ord("H"), ord("I"), 0x22]))
    assert detokenize(data) == '10PRINT"HI"\n'


def test_keywords_inside_strings_are_not_expanded():
    # The bytes spelling END inside a string must stay literal, not become a token
    data = _program((10, [0xF1, 0x22, ord("E"), ord("N"), ord("D"), 0x22]))
    assert detokenize(data) == '10PRINT"END"\n'


def test_rem_is_literal_to_end_of_line():
    # 20 REMPRINT  ->  after REM (0xF4) the rest is literal, so PRINT is not a token
    data = _program((20, [0xF4, ord("P"), ord("R"), ord("I"), ord("N"), ord("T")]))
    assert detokenize(data) == "20REMPRINT\n"


def test_pseudo_variable_statement_and_function_forms():
    # PAGE function form 0x90; statement form 0xD0 (0x90 + 0x40) -> both -> PAGE
    func = _program((10, [0xF1, 0x90]))            # PRINT PAGE
    stmt = _program((20, [0xD0, ord("="), ord("0")]))  # PAGE=0
    assert detokenize(func) == "10PRINTPAGE\n"
    assert detokenize(stmt) == "20PAGE=0\n"


def test_line_number_reference_decoding():
    # GOTO 100 -> GOTO=0xE5 then 0x8D + encoded(100) = 0x44 0x64 0x40
    assert decode_line_reference(0x44, 0x64, 0x40) == 100
    data = _program((10, [0xE5, 0x8D, 0x44, 0x64, 0x40]))
    assert detokenize(data) == "10GOTO100\n"


def test_multiple_lines_and_numbers():
    data = _program((10, [0xF5]), (20, [0xFD]))  # REPEAT / UNTIL
    assert detokenize_lines(data) == [(10, "REPEAT"), (20, "UNTIL")]


def test_basic_v_is_the_default_dialect():
    # OWL defaults to BASIC V. The 0xC6-0xCD bytes that were BASIC II's
    # command-mode keywords (AUTO/DELETE/LOAD/LIST/NEW/OLD/RENUMBER/SAVE) are
    # reassigned in BASIC V -- 0xC9 is WHEN, not LIST. Those command keywords
    # never appear in a saved program body, so defaulting to BASIC V loses
    # nothing on BBC Micro programs and gains BASIC V (Archimedes) support.
    assert detokenize(_program((10, [0xC9]))) == "10WHEN\n"


def test_truncated_image_keeps_its_valid_prefix():
    # A program whose bytes are cut off mid-record (common in cover-disc rips)
    # keeps the lines decoded before the truncation rather than raising.
    good = _program((10, [0xF5]), (20, [0xFD]))    # REPEAT / UNTIL + end marker
    truncated = good[:-2] + bytes([0x0D, 0x00, 0x1E])  # start a line, then cut off
    assert detokenize_lines(truncated) == [(10, "REPEAT"), (20, "UNTIL")]


def test_basic_v_escape_token_decodes():
    # 0xC8 0x91 is a single BASIC V keyword (ORIGIN) reached through the
    # 0xC6/0xC7/0xC8 escape mechanism -- not LOAD + TIME, the BASIC II
    # mis-reading that produced the bogus "LOADTIME" (oaknut issue #44).
    data = _program((10, [0xC8, 0x91, ord(" "), ord("0")]))
    assert detokenize(data) == "10ORIGIN 0\n"
