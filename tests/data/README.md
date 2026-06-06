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
