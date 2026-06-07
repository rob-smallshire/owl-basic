"""Build a runnable Sphinx Adventure: detokenise -> analyse -> assemble.

    python tools/build_sphinx.py [OUTPUT_DIR]

Then play it interactively:  dotnet OUTPUT_DIR/sphinx.dll
"""
import glob, os, shutil, sys
from owl_basic.bbc_basic.detokenizer import detokenize_lines
from owl_basic.analysis import analyse_numbered_lines
from owl_basic.extension import create_extension

HERE = os.path.dirname(os.path.abspath(__file__))
SPHINX = os.path.join(HERE, "..", "tests", "data", "sphinx2-deprotected.bbc")

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    program = analyse_numbered_lines(
        detokenize_lines(open(SPHINX, "rb").read()), name="sphinx")
    backend = create_extension("backend", "owl_basic.backend", "dotnet")
    dll = backend.generate(program, out_dir)
    runtime = max(glob.glob(os.path.join(HERE, "..", "OwlRuntime", "OwlRuntime",
                  "bin", "**", "net10.0", "OwlRuntime.dll"), recursive=True),
                  key=os.path.getmtime)
    shutil.copy(runtime, out_dir)
    print("Built %s" % dll)
    print("Play it with:  dotnet %s" % dll)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/sphinx")
