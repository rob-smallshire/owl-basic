"""Generic extension / plug-in machinery built on top of stevedore.

Extension classes are loaded via entry points. Each :class:`Extension`
subclass declares a ``kind`` (a short identifier such as ``"backend"``) and is
registered under a namespace of the form ``"owl_basic.<kind>"`` in
``pyproject.toml``. Consumers then use :func:`create_extension`,
:func:`extension`, or :func:`list_extensions` to load them.

This is OWL BASIC's seam for pluggable code-generation backends (and any other
future plug-in points): a backend for CIL, C, 6502, etc. is just an
:class:`Extension` of the appropriate kind, discovered by name at runtime.
"""

import functools
import importlib.resources
import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

import stevedore
import stevedore.exception

from owl_basic._text import first_line, normalize_name, strip_lines
from owl_basic.exceptions import OwlBasicError, ExtensionError


logger = logging.getLogger(__name__)


class Extension(ABC):
    """Base class for all named, entry-point-discovered plug-ins."""

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self._name = name

    @classmethod
    def kind(cls) -> str:
        """The kind of extension; used to distinguish extension points."""
        return cls._kind()

    @classmethod
    @abstractmethod
    def _kind(cls) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def dirpath(cls) -> Path:
        """The directory path to the extension package."""
        package_name = inspect.getmodule(cls).__package__
        return Path(importlib.resources.files(package_name))

    @classmethod
    def version(cls) -> str:
        """The extension version."""
        return "1.0.0"

    @classmethod
    def describe(cls, *, single_line: bool = False) -> str:
        """A description of the extension.

        By default this is the class docstring; override for something else.
        With ``single_line=True`` only the first non-empty line is returned.
        """
        if cls.__doc__ is None:
            return "No description available."
        full_description = strip_lines(inspect.cleandoc(cls.__doc__))
        if single_line:
            return first_line(full_description)
        return full_description

    @classmethod
    @functools.lru_cache(maxsize=None)
    def entry_point_name(cls) -> str:
        """The entry point name (key) under which this class is registered.

        Performs a reverse lookup from class to entry point name by searching
        the appropriate namespace. Cached indefinitely (names are immutable).
        """
        namespace = f"owl_basic.{cls.kind()}"
        return extension_name_from_class(namespace, cls)


def create_extension(kind, namespace, name, exception_type=None, **kwargs) -> Extension:
    """Instantiate an extension.

    Args:
        kind: The kind of extension.
        namespace: The entry-point namespace for the extension.
        name: The name of the extension to be loaded.
        exception_type: Exception type raised if the extension can't be loaded.
        **kwargs: Forwarded to the extension constructor.
    """
    ext = extension(kind, namespace, name, exception_type)
    obj = ext(name=normalize_name(name), **kwargs)
    return obj


def extension(
    kind: str,
    namespace: str,
    name: str,
    exception_type: BaseException,
) -> Type[Extension]:
    """Get the extension class without instantiating it."""
    exception_type = exception_type or ExtensionError
    normal_name = normalize_name(name)
    try:
        manager = stevedore.driver.DriverManager(
            namespace=namespace,
            name=normal_name,
            invoke_on_load=False,
            on_load_failure_callback=load_failure_callback,
        )
    except stevedore.exception.NoMatches as no_matches:
        names = list_extensions(namespace)
        name_list = ", ".join(names)
        raise exception_type(
            f"No {kind} matching {name!r}. Available {kind}s: {name_list}"
        ) from no_matches
    return manager.driver


def describe_extension(kind, namespace, name, exception_type=None, *, single_line: bool = False) -> str:
    """Describe an extension by name."""
    driver = extension(kind, namespace, name, exception_type)
    return driver.describe(single_line=single_line)


def list_extensions(namespace) -> list[str]:
    """List the names of the extensions available in a given namespace."""
    extensions = stevedore.ExtensionManager(
        namespace=namespace,
        invoke_on_load=False,
        on_load_failure_callback=load_failure_callback,
    )
    return extensions.names()


def load_failure_callback(manager, entrypoint, exception):
    raise ExtensionError(
        f"Could not load extension {entrypoint.name!r} from plug-in manager "
        f"{manager.namespace!r} because: {exception}"
    ) from exception


def list_dirpaths(namespace):
    """A mapping of extension names to extension package paths."""
    extensions = stevedore.ExtensionManager(
        namespace=namespace,
        invoke_on_load=False,
        on_load_failure_callback=load_failure_callback,
    )
    return {name: _extension_dirpath(ext) for name, ext in list(extensions.items())}


def _extension_dirpath(ext: "stevedore.extension.Extension") -> Path:
    """The directory path to an extension package."""
    return Path(importlib.resources.files(ext.module_name))


def extension_name_from_class(namespace: str, extension_class: Type[Extension]) -> str:
    """Reverse-lookup the entry point name for an extension class."""
    manager = stevedore.ExtensionManager(
        namespace=namespace,
        invoke_on_load=False,
        on_load_failure_callback=load_failure_callback,
    )
    for ext in manager:
        if ext.plugin == extension_class:
            return ext.name
    raise ExtensionError(
        f"Extension class {extension_class.__name__} not found in namespace {namespace!r}"
    )
