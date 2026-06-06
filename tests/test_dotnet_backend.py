"""The dotnet backend is discoverable through the stevedore extension seam.

The backend's actual code generation (emit_il, assemble, compile-and-run) is
exercised in test_dotnet_emitter.py.
"""

from owl_basic.extension import create_extension, list_extensions


def test_dotnet_backend_is_discoverable():
    assert "dotnet" in list_extensions("owl_basic.backend")


def test_dotnet_backend_loads_by_name():
    backend = create_extension("backend", "owl_basic.backend", "dotnet")
    assert backend.name == "dotnet"
    assert backend.kind() == "backend"
