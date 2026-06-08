"""Extract OwlRuntime method signatures from the built assembly.

So the emitter can look up the CIL signature of a runtime call (and pick the
right overload by argument type) instead of hand-writing it -- removing a
maintenance burden and a class of "the hand-written signature drifted from the
DLL" bugs.

Extraction uses ``monodis``, the Mono IL disassembler. Mono is retired as a
*runtime* here (OwlRuntime targets net10 via the dotnet SDK), but ``monodis`` is
a standalone tool that still reads modern assemblies. It renders each method as::

    .method public static hidebysig
           default string LeftStr (string s, int32 length)  cil managed

We parse the ``default <ret> <Name> (<typed params>) cil managed`` lines of the
OwlRuntime classes into a manifest keyed by ``(class, method)``.
"""
import re
import shutil
import subprocess

# The assembly/namespace the runtime classes live in, as referenced in CIL.
_NAMESPACE = "[OwlRuntime]OwlRuntime"

# .class flag keywords to skip when finding the class name (the name is the first
# token after `.class` that is not one of these).
_CLASS_FLAGS = frozenset({
    "public", "private", "nested", "auto", "ansi", "unicode", "sealed",
    "abstract", "beforefieldinit", "interface", "serializable", "explicit",
    "sequential", "value", "enum",
})

_SIGNATURE = re.compile(
    r"^\s*default\s+(?P<ret>.+?)\s+(?P<name>'[^']+'|[A-Za-z_]\w*)\s*"
    r"\((?P<params>.*)\)\s+cil managed"
)


def find_monodis():
    """The monodis executable, or None if it is not installed."""
    return shutil.which("monodis")


def _normalise_type(text):
    """Render a monodis type as the emitter's CIL type convention."""
    text = text.strip()
    text = text.replace("unsigned int8", "uint8")
    text = text.replace("[mscorlib]", "[System.Runtime]")
    return text


def _param_types(params):
    """The parameter *types* of a ``(type name, type name, ...)`` list.

    The name is the last whitespace-delimited token of each part (it may be a
    quoted keyword like ``'value'``); the type is everything before it.
    """
    params = params.strip()
    if not params:
        return []
    types = []
    for part in params.split(","):
        tokens = part.split()
        type_str = " ".join(tokens[:-1]) if len(tokens) > 1 else tokens[0]
        types.append(_normalise_type(type_str))
    return types


def _class_name(line):
    """The class name on a monodis ``.class`` line, or None."""
    tokens = line.split()
    if not tokens or tokens[0] != ".class":
        return None
    for token in tokens[1:]:
        if token == "extends":
            return None
        if token not in _CLASS_FLAGS:
            return token
    return None


def parse_monodis(text):
    """Parse monodis output into ``{(class, method): [(ret, [param_types])]}``.

    Constructors and the static initialiser are skipped; a method may appear
    under its key more than once (overloads).
    """
    manifest = {}
    current_class = None
    for line in text.splitlines():
        name = _class_name(line)
        if name is not None:
            current_class = name
            continue
        match = _SIGNATURE.match(line)
        if not match or current_class is None:
            continue
        method = match.group("name").strip("'")
        if method in (".ctor", ".cctor", "ctor", "cctor"):
            continue
        manifest.setdefault((current_class, method), []).append(
            (_normalise_type(match.group("ret")), _param_types(match.group("params")))
        )
    return manifest


class SignatureManifest:
    """Runtime call signatures extracted from the assembly."""

    def __init__(self, overloads):
        # {(class, method): [(return_type, [param_types]), ...]}
        self._overloads = overloads

    @classmethod
    def from_assembly(cls, dll_filepath, monodis=None):
        """Build a manifest by disassembling *dll_filepath* with monodis.

        monodis (Mono 6.x) emits the full disassembly to stdout but can then
        SIGABRT during teardown on a framework type it cannot resolve (e.g.
        System.Drawing.Color, from the graphics layer excluded from the net10
        build) -- *after* the OwlRuntime methods we need. So we keep whatever it
        printed rather than treating a non-zero exit as failure; we only fail if
        it produced nothing.
        """
        monodis = monodis or find_monodis()
        if monodis is None:
            raise RuntimeError("monodis is required to extract runtime signatures")
        result = subprocess.run(
            [monodis, str(dll_filepath)], capture_output=True, text=True
        )
        if not result.stdout.strip():
            raise RuntimeError(
                "monodis produced no output for %s (exit %d): %s"
                % (dll_filepath, result.returncode, result.stderr.strip()[:200])
            )
        return cls(parse_monodis(result.stdout))

    def overloads(self, class_name, method):
        """All (return_type, [param_types]) overloads of a method."""
        return list(self._overloads.get((class_name, method), []))

    def resolve(self, class_name, method, arg_types):
        """The (return_type, [param_types]) overload matching *arg_types*."""
        candidates = self._overloads.get((class_name, method), [])
        wanted = list(arg_types)
        for return_type, params in candidates:
            if params == wanted:
                return return_type, params
        raise KeyError(
            "no overload of %s::%s matches (%s); candidates: %s"
            % (class_name, method, ", ".join(wanted),
               [p for _, p in candidates])
        )

    def call(self, class_name, method, arg_types=(), instance=False):
        """The full CIL ``call`` instruction for a runtime method.

        *arg_types* are the CIL types of the pushed arguments, used to select
        the overload. ``instance=True`` emits ``callvirt``-style instance call.
        """
        return_type, params = self.resolve(class_name, method, arg_types)
        op = "callvirt instance" if instance else "call"
        return "%s %s %s.%s::%s(%s)" % (
            op, return_type, _NAMESPACE, class_name, method, ", ".join(params)
        )
