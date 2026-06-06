"""The Acorn / BBC Micro text codec."""

import owl_basic  # noqa: F401  (importing registers the "acorn" codec)


def test_pound_sign_round_trips():
    assert b"COST\x60100".decode("acorn") == "COST£100"
    assert "COST£100".encode("acorn") == b"COST\x60100"


def test_broken_bar():
    assert b"\x7c".decode("acorn") == "¦"


def test_plain_ascii_passes_through():
    assert b"PRINT \"HELLO\"".decode("acorn") == 'PRINT "HELLO"'


def test_unencodable_character_is_rejected():
    import pytest

    with pytest.raises(UnicodeEncodeError):
        "snowman ☃".encode("acorn")
