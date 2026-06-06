# Third-Party Notices

OWL BASIC is licensed under the MIT License (see `LICENSE`). It additionally
incorporates, or derives from, third-party material whose attribution and
licensing terms are preserved below. Nothing here imposes copyleft; each item
is compatible with OWL BASIC's permissive licensing, subject to the credit
being retained.

## BBC BASIC detokenizer — `src/owl_basic/decoder.py`

```
(c) 2007 Matt Godbolt.
Updated 2008 Ian Smallshire.
Original: http://xania.org/200711/bbc-basic-v-format
"Use however you like, as long as you put credit where credit's due."
```

The detokenizer that converts tokenized BBC BASIC programs to plain text
originates with Matt Godbolt and was extended by Ian Smallshire (and later
Robert Smallshire). It is used here under its stated terms, which require that
credit be preserved. Some of the token-table information was, per the original
header, obtained from RISC OS Open source code (see below).

## Singleton metaclass — `src/owl_basic/singleton.py`

By Gary Robinson (grobinson@transpose.com). Explicitly placed in the **public
domain** ("No rights reserved"). See
http://www.garyrobinson.net/2004/03/python_singleto.html — no obligations.

## RISC OS Open

Interface and factual information used by the compiler and runtime — BBC BASIC
token values, and SWI / VDU variable numbers in the OwlRuntime runtime library
— was informed by RISC OS Open material (https://www.riscosopen.org/), much of
which is published under the Apache License 2.0 / Castle shared-source terms.
These items are interface facts rather than copied code.

## Hindley–Milner type inference — `src/owl_basic/owltyping/hindley_milner.py`

A Python implementation by Robert Smallshire, based on the Scala code by Andrew
Forrest, the Perl code by Nikita Borisov, and the paper "Basic Polymorphic
Typechecking" by Luca Cardelli. This module is currently unused; if it is
retained in the compiler, the licensing of the upstream example code should be
confirmed (or the module replaced with a clean-room implementation).

## Acorn system font — `OwlRuntime/OwlRuntime/platform/riscos/AcornFont.cs`

The 8×8 bitmap glyph data reproduces the appearance of the Acorn / BBC system
font for VDU emulation. Bitmap font data of this kind derives from Acorn's
original ROM font. This affects only the .NET (CIL) backend's runtime library,
not the compiler. It may be retained with this provenance noted, or replaced
with a freely-licensed equivalent.

## Hindley-Milner type inference — `src/owl_basic/owltyping/inference.py`

Vendored verbatim from https://github.com/rob-smallshire/hindley-milner-python
(MIT). The standalone Hindley-Milner core (the maintained successor to the older
copy this project previously carried); the BBC BASIC type-inference bridge is
being built on top of it. Kept unmodified for easy upstream re-sync.

## PLY (Python Lex-Yacc)

Used as a normal dependency (not vendored). PLY is distributed under the BSD
License. See https://github.com/dabeaz/ply.
