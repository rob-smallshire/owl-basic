"""Internal text utilities used by :mod:`owl_basic.extension`.

Small helpers for rendering extension descriptions. Kept internal
(underscore-prefixed module) because they are not part of the public API.
"""


def _is_blank(line: str) -> bool:
    return not line or line.isspace()


def strip_lines(text: str) -> str:
    """Remove leading and trailing blank lines.

    Interior blank lines are preserved.
    """
    lines = text.splitlines()
    start = 0
    while start < len(lines) and _is_blank(lines[start]):
        start += 1
    end = len(lines)
    while end > start and _is_blank(lines[end - 1]):
        end -= 1
    return "\n".join(lines[start:end])


def normalize_name(name: str) -> str:
    """Normalise a name by converting hyphens to underscores."""
    return name.replace("-", "_")


def first_line(text: str) -> str:
    """Extract the first non-empty line from text, stripped of surrounding space.

    Returns the empty string if text is empty or all-whitespace.
    """
    if not text:
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
