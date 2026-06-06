# Test data

Binary fixtures for the test suite that are not generated on the fly — chiefly
Acorn disc images used as real-world compiler inputs.

## Provenance and status

These images contain software for Acorn machines (BBC Micro / Master, RISC OS).
Acorn Computers and Acornsoft are long defunct and this material is treated as
abandonware; it is retained here as test data, with no commercial use. The
images are committed so the end-to-end tests are reproducible from a clean
checkout and in CI.

## Sphinx Adventure

Acornsoft's *Sphinx Adventure* (a text-only adventure) was the original
compiler's torture-test. Place its Acorn DFS image here:

    tests/data/sphinx.ssd

The end-to-end test reads the SSD with `oaknut-disc`, extracts the tokenised
BBC BASIC program, detokenises it with `owl_basic.decoder`, compiles it with the
`dotnet` backend, and runs it on .NET — checking the introductory screen.

### De-protected working copy

Sphinx has one anti-listing/copy-protection line: logical line **173** is
*duplicated* — the genuine line (the adventure's verb vocabulary `DATA`) sits in
its proper place, and a corrupted copy full of control bytes and fake line-number
tokens is placed last, out of order, to break `LIST`/`RENUMBER` and detokenisers.

`tools/deprotect_sphinx.py` drops the out-of-order duplicate, keeping the genuine
program, producing the committed derived artifacts:

- `sphinx2-deprotected.bbc` — the de-protected tokenised program (376 lines,
  monotonic, no duplicates).
- `sphinx2.bas` — its detokenised source (regenerable from the `.bbc`).

Reproduce with::

    disc cat tests/data/SphinxAdventureFIN.ssd:$.SPHINX2 > sphinx2.tok
    python tools/deprotect_sphinx.py sphinx2.tok \
        tests/data/sphinx2-deprotected.bbc tests/data/sphinx2.bas
