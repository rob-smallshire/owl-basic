# Test data

Binary fixtures for the test suite that are **not** generated on the fly.

## Copyright

Acorn disc images (`*.ssd`, `*.dsd`, `*.adf`, …) placed here are **local-only**
and are git-ignored (see the repository `.gitignore`). They typically contain
copyrighted software (e.g. Acornsoft titles) and **must not be committed or
published**. Tests that need them skip automatically when the image is absent,
so the suite stays green on a clean checkout and in CI.

This mirrors how the original project treated Acornsoft's *Sphinx Adventure*:
used as a compiler torture-test on the developer's disc, never checked in.

## Sphinx Adventure

Drop the Acorn DFS image here:

    tests/data/sphinx.ssd

The (forthcoming) end-to-end test will:

1. read the SSD with `oaknut-disc`,
2. extract the tokenised BBC BASIC program,
3. detokenise it with `owl_basic.decoder`,
4. compile it with the `dotnet` backend, and
5. run it on .NET, checking the introductory screen.
