"""An array's backing field is declared and referenced at one consistent rank.

An array's rank is intrinsic -- fixed by its DIM -- so its static field type
(``element[,...]``) must be settled once, before any method is emitted. The
JigArc regression (Acorn User Tau91-a/APR91) declared a ``grid$`` field as 1-D
``string[]`` while element accesses and a whole-array op referenced it as 2-D
``string[,]``: a reference whose rank was guessed from its subscript count won
the field declaration ahead of the DIM (which lived in a later-emitted PROC),
and ilasm then failed to resolve the mismatched references.

The fix settles each array field from its DIM, program-wide, before any method
is emitted (``_register_array_fields``), and ``_array_field`` then honours that
registered type for every reference rather than re-deriving it from the call's
local rank. These tests pin both halves directly.
"""
from owl_basic.analysis import analyse
from owl_basic.ext.backends.dotnet import emitter as E


def test_register_array_fields_seeds_rank_from_dim():
    # A 2-D DIM in a PROC pre-registers the field at rank 2 before emission.
    prog = analyse(
        'PROCa\nEND\nDEFPROCa\nDIM g$(2,2)\ng$(1,1)="#"\nENDPROC\n', name="t")
    registry = {}
    E._register_array_fields(prog.ordered_basic_blocks, registry)
    assert registry["arr_s_g"] == "string[,]"


def test_array_field_honours_registered_rank():
    # Once the field is registered (its intrinsic rank), a reference that guesses
    # a different local rank must still get the registered type -- not re-derive
    # a mismatched one. Pre-fix this returned "string[]" for rank=1.
    em = E._MethodEmitter(globals_registry={"arr_s_g": "string[,]"})
    field, array_il, _element = em._array_field("g$(", 1)
    assert field == "arr_s_g"
    assert array_il == "string[,]"


def test_jigarc_shape_field_is_self_consistent():
    # The JigArc shape end to end: the DIM lives in a later-emitted PROC while
    # the array is used (whole-array op + element read) from main and another
    # PROC. The emitted field type must agree everywhere.
    import re
    src = (
        'PROCfill\n'
        'PRINT g$(0,0)\n'
        'PROCshow\n'
        'END\n'
        'DEFPROCfill\n'
        'DIM g$(2,2)\n'
        'g$()="#"\n'
        'ENDPROC\n'
        'DEFPROCshow\n'
        'PRINT g$(1,1)\n'
        'ENDPROC\n'
    )
    backend_il = _emit(src)
    types = set(re.findall(r"(\S+) arr_s_g\b", backend_il))
    assert types == {"string[,]"}, types


def _emit(src):
    from owl_basic.extension import create_extension
    backend = create_extension("backend", "owl_basic.backend", "dotnet")
    return backend.emit_il(analyse(src, name="t"))
