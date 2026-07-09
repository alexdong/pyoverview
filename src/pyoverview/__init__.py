"""Terminal outline browser for Python and Markdown files."""

from .outline import (
    Symbol,
    parse_file,
    parse_markdown_file,
    parse_markdown_source,
    parse_python_file,
    parse_python_source,
)

__all__ = [
    "Symbol",
    "parse_file",
    "parse_markdown_file",
    "parse_markdown_source",
    "parse_python_file",
    "parse_python_source",
]

__version__ = "0.4.2"
