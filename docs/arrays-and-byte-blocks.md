# Typed arrays vs byte blocks: two different things `DIM` creates

`DIM` in BBC BASIC builds one of two unrelated things, chosen by syntax:

| Syntax | What it creates | How it is reached |
|---|---|---|
| `DIM A(10)`, `DIM A%(3,4)`, `DIM A$(9)` | a **typed array** (0..N per dimension) | element access `A(i)`, `A%(i,j)`, `A$(k)` |
| `DIM b% 100` | a **byte block** of 100+1 bytes; the integer scalar `b%` holds its base address | byte/word indirection `b%?n`, `b%!n`, `$b%` |

These share no storage and are addressed in completely different ways. A typed
array `A%()` and the integer scalar `A%` are *already* distinct variables in BBC
BASIC; a byte block reuses that scalar to hold an address.

## Indexing a byte block as an array is an `Array` error

Because the block's name is only a scalar (plus the array of the *same* name
that was never `DIM`med), indexing it as an array references a non-existent
array:

```basic
DIM b% 100
PRINT b%(5)      REM -> "Array" error on a real BBC (BASIC II), at run time
```

`b%(5)` is **not** the byte at `b%+5` -- that is `b%?5`. It is element 5 of an
array `b%()` that does not exist, so BBC BASIC II raises `Array`. Verified
against BBC BASIC II.

This shape shows up in the corpus as a dropped `?`: A&B Computing `ADVRUN`
line 2640 has `... Cy%?(M%?9)<>3 AND Cy%(M%?9)<>5 ...` -- the first reference is
byte indirection, the second lost its `?` and so reads as the undimensioned
array `Cy%()`. A real BBC errors on it; it is a genuine bug in the listing.

## What OWL does

OWL is a whole-program compiler, so it reports this statically rather than at run
time, as a diagnostic (codegen then refuses -- it is not lowered to invalid IL):

* a name DIMmed only as a byte block, indexed as an array ->
  *"`b%` is a byte block (DIM b% <size>), not an array; indexing it as `b%()` is
  an 'Array' error in BBC BASIC"*;
* a name with no `DIM` at all (and not a formal array parameter) ->
  *"the array `A%()` is used but never DIMmed"*.

The two messages are kept distinct so the byte-block case is not mis-described as
simply undimensioned. Both are correct rejections of broken programs, not
compiler gaps. Pinned by `tests/test_undimensioned_array.py`
(`test_byte_block_used_as_an_array_is_diagnosed`,
`test_genuinely_undimensioned_array_keeps_its_message`) and the byte-block
round-trip tests in `tests/test_arrays.py`.
