  * `LET` can be used in all assignments including to pseudovariables and arrays, unlike in BBC BASIC.
  * In BBC BASIC, the function `RND(x)` can return either a float or integer.  In OWL BASIC we always return a 64-bit float.
  * Array operations have been merged with normal scalar expressions making them much more general than in BBC BASIC and supporting arbitrary complexity.
  * Computed `GOTO`s (explicit or implicit in `IF` statements) are not supported by OWL BASIC. The value of a `GOTO` must be a literal integer.