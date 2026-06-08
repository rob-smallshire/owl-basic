"""The OwlRuntime signature manifest extracted from the built assembly.

The parser tests run everywhere (pure text). The extraction test needs monodis
and a built OwlRuntime.dll.
"""
import pytest

from helpers import find_owlruntime_dll

from owl_basic.ext.backends.dotnet.signatures import (
    SignatureManifest,
    find_monodis,
    parse_monodis,
)

# A representative slice of monodis output (two classes, an overloaded method,
# a no-arg method, and a static constructor to skip).
_SAMPLE = """
  .class public auto ansi abstract sealed BasicCommands
         extends [System.Runtime]System.Object
  {
    .method public static hidebysig
           default void Print (int32 channel, object[] items)  cil managed
    {
    }
    .method public static hidebysig
           default string LeftStr (string s, int32 length)  cil managed
    {
    }
    .method public static hidebysig
           default string LeftStr (string s)  cil managed
    {
    }
    .method public static hidebysig
           default void NewLine ()  cil managed
    {
    }
    .method public static hidebysig specialname rtspecialname
           default void '.cctor' ()  cil managed
    {
    }
  }
  .class public auto ansi abstract sealed MemoryMap
  {
    .method public static hidebysig
           default int32 Allocate (int32 count)  cil managed
    {
    }
  }
"""


def test_parse_groups_methods_by_class_and_skips_ctor():
    manifest = parse_monodis(_SAMPLE)
    assert ("BasicCommands", "LeftStr") in manifest
    assert ("MemoryMap", "Allocate") in manifest
    assert ("BasicCommands", ".cctor") not in manifest


def test_parse_captures_overloads_return_and_param_types():
    manifest = parse_monodis(_SAMPLE)
    assert manifest[("BasicCommands", "Print")] == [("void", ["int32", "object[]"])]
    assert manifest[("BasicCommands", "NewLine")] == [("void", [])]
    left = manifest[("BasicCommands", "LeftStr")]
    assert ("string", ["string", "int32"]) in left
    assert ("string", ["string"]) in left


def test_manifest_resolves_call_by_argument_types():
    manifest = SignatureManifest(parse_monodis(_SAMPLE))
    assert manifest.call("BasicCommands", "LeftStr", ["string", "int32"]) == (
        "call string [OwlRuntime]OwlRuntime.BasicCommands::LeftStr(string, int32)")
    assert manifest.call("BasicCommands", "LeftStr", ["string"]) == (
        "call string [OwlRuntime]OwlRuntime.BasicCommands::LeftStr(string)")
    assert manifest.call("BasicCommands", "NewLine") == (
        "call void [OwlRuntime]OwlRuntime.BasicCommands::NewLine()")
    assert manifest.call("MemoryMap", "Allocate", ["int32"]) == (
        "call int32 [OwlRuntime]OwlRuntime.MemoryMap::Allocate(int32)")


def test_manifest_raises_for_an_unmatched_overload():
    manifest = SignatureManifest(parse_monodis(_SAMPLE))
    with pytest.raises(KeyError):
        manifest.call("BasicCommands", "LeftStr", ["int32"])


@pytest.mark.skipif(find_monodis() is None or find_owlruntime_dll() is None,
                    reason="needs monodis and a built OwlRuntime.dll")
def test_extracts_known_signatures_from_the_real_assembly():
    manifest = SignatureManifest.from_assembly(find_owlruntime_dll())
    # Known runtime calls the emitter makes resolve to real signatures.
    assert manifest.call("BasicCommands", "NewLine") == (
        "call void [OwlRuntime]OwlRuntime.BasicCommands::NewLine()")
    assert manifest.call("BasicCommands", "Chr", ["int32"]).endswith("::Chr(int32)")
    assert manifest.call("MemoryMap", "Allocate", ["int32"]).endswith("::Allocate(int32)")
    # Print is overloaded; the int32 one exists.
    assert manifest.call("BasicCommands", "Print", ["int32"]).startswith("call void")


# A program exercising many OwlRuntime calls, so the cross-check below sees them.
_RUNTIME_HEAVY = (
    'A$ = "hello"\n'
    'PRINT LEFT$(A$, 2)\nPRINT RIGHT$(A$, 2)\nPRINT MID$(A$, 2, 2)\n'
    'PRINT CHR$(65)\nPRINT ASC(A$)\nPRINT INSTR(A$, "l")\nPRINT VAL("42")\n'
    'PRINT ABS(-3)\nPRINT SGN(-3)\nPRINT SQR(9)\nPRINT RND(6)\n'
    'PRINT 42\nPRINT A$\nMODE 7\nEND\n'
)


@pytest.mark.skipif(find_monodis() is None or find_owlruntime_dll() is None,
                    reason="needs monodis and a built OwlRuntime.dll")
def test_emitter_runtime_signatures_match_the_dll(dotnet_backend):
    """Every [OwlRuntime] call the emitter generates must name a real method/
    overload in the assembly -- so a hand-written signature can't drift from it."""
    import re
    from owl_basic.analysis import analyse

    manifest = SignatureManifest.from_assembly(find_owlruntime_dll())
    il = dotnet_backend.emit_il(analyse(_RUNTIME_HEAVY, name="rt"))
    calls = re.findall(
        r"\[OwlRuntime\]OwlRuntime\.(\w+)::(\w+)\(([^)]*)\)", il)
    assert calls, "expected the emitter to make OwlRuntime calls"
    unmatched = []
    for class_name, method, params in calls:
        arg_types = [p.strip() for p in params.split(",") if p.strip()]
        try:
            manifest.resolve(class_name, method, arg_types)
        except KeyError:
            unmatched.append("%s::%s(%s)" % (class_name, method, params))
    assert not unmatched, "emitter signatures absent from the DLL: %s" % unmatched
