"""Binary / non-text input is rejected with an accurate, informative message.

Garbage toots, tokenised images and programs that embed graphics or machine-code
bytes are not text BASIC listings. The lexer cannot tokenise such bytes, so a
naive parse reports a misleading "Syntax error at <whatever token the skipped
bytes formed>" -- or worse, claims an unsupported feature because the garbage
happened to contain a USR or '[' token. OWL now counts the untokenisable
characters and says plainly that the input is not a text BASIC program. Control
bytes *inside a string* are fine (the string rule consumes them), so a real
program with embedded VDU codes still compiles.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def _reject(source):
    with pytest.raises(CompileError) as excinfo:
        analyse(source, name="t")
    return str(excinfo.value)


def test_binary_input_is_named_as_non_text():
    # Control bytes interleaved through what would be a keyword: the bytes break
    # the token stream so it cannot parse, and they are named as non-text. (Stray
    # bytes the lexer can simply skip around a *valid* statement are tolerated --
    # only a genuine parse failure is diagnosed -- so the binary must actually
    # corrupt the structure.)
    msg = _reject("P\x00R\x01I\x02N\x03T \x16\x13\n")
    assert "not valid BASIC text" in msg
    assert "Syntax error" not in msg


def test_garbage_containing_a_usr_token_is_reported_as_binary_not_usr():
    # The misleading case: binary keyword-soup that happens to contain USR must
    # be reported as binary, not "USR is not supported".
    msg = _reject("\x00\x01 USR RETURN VPOS \x16\x13 PRINT\n")
    assert "not valid BASIC text" in msg
    assert "USR is not supported" not in msg


def test_clean_usr_still_reports_usr():
    assert "USR is not supported" in _reject("A=USR(&FFF4)\nEND\n")


def test_inline_assembly_still_reported():
    assert "assembl" in _reject("P%=0\n[OPT0:RTS:]\n").lower()


def test_control_bytes_inside_a_string_still_compile():
    # VDU codes embedded in a PRINT string: the string rule consumes them, so
    # there are no illegal characters and the program is fine.
    program = analyse('PRINT "' + chr(17) + chr(2) + chr(5) + '"\n', name="t")
    assert not program.diagnostics


def test_prose_still_reports_a_syntax_error_not_binary():
    # Prose is printable text -- it tokenises (into words), so it is a genuine
    # syntax error, not binary. The message should not claim binary content.
    msg = _reject("this is not a program\n")
    assert "not valid BASIC text" not in msg
