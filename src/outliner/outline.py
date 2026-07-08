from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


class OutlineError(Exception):
    """Raised when a Python file cannot be parsed into an outline."""


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    lineno: int
    end_lineno: int
    children: tuple["Symbol", ...] = field(default_factory=tuple)

    @property
    def display_name(self) -> str:
        if self.kind == "module":
            return self.name
        if self.kind == "async function":
            return f"async {self.name}()"
        if self.kind == "function":
            return f"{self.name}()"
        return self.name


def parse_python_file(path: Path) -> tuple[Symbol, list[str]]:
    path = path.expanduser()
    if not path.exists():
        raise OutlineError(f"{path} does not exist")
    if not path.is_file():
        raise OutlineError(f"{path} is not a file")
    if path.suffix != ".py":
        raise OutlineError(f"{path} is not a .py file")

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise OutlineError(f"{path} is not valid UTF-8") from exc
    except OSError as exc:
        raise OutlineError(f"could not read {path}: {exc}") from exc

    root = parse_python_source(source, module_name=path.name)
    return root, source.splitlines()


def parse_python_source(source: str, module_name: str = "<module>") -> Symbol:
    try:
        tree = ast.parse(source, filename=module_name)
    except SyntaxError as exc:
        location = f"{exc.lineno}:{exc.offset}" if exc.lineno else "unknown"
        raise OutlineError(f"could not parse {module_name} at {location}: {exc.msg}") from exc

    children = tuple(_symbols_from_body(tree.body))
    line_count = max(1, len(source.splitlines()))
    return Symbol(module_name, "module", 1, line_count, children)


def format_outline(root: Symbol) -> str:
    if not root.children:
        return f"{root.display_name}\n  (no classes or functions found)"
    lines = [root.display_name]
    for child in root.children:
        _append_symbol(lines, child, depth=1)
    return "\n".join(lines)


def flatten_outline(root: Symbol) -> list[tuple[int, Symbol]]:
    items: list[tuple[int, Symbol]] = []

    def walk(symbol: Symbol, depth: int) -> None:
        items.append((depth, symbol))
        for child in symbol.children:
            walk(child, depth + 1)

    for child in root.children:
        walk(child, 0)
    return items


def _symbols_from_body(body: list[ast.stmt]) -> list[Symbol]:
    symbols: list[Symbol] = []
    for node in body:
        symbol = _symbol_from_node(node)
        if symbol is not None:
            symbols.append(symbol)
    return symbols


def _symbol_from_node(node: ast.AST) -> Symbol | None:
    if isinstance(node, ast.ClassDef):
        return Symbol(
            name=node.name,
            kind="class",
            lineno=node.lineno,
            end_lineno=_end_lineno(node),
            children=tuple(_symbols_from_body(node.body)),
        )

    if isinstance(node, ast.AsyncFunctionDef):
        return Symbol(
            name=node.name,
            kind="async function",
            lineno=node.lineno,
            end_lineno=_end_lineno(node),
            children=tuple(_symbols_from_body(node.body)),
        )

    if isinstance(node, ast.FunctionDef):
        return Symbol(
            name=node.name,
            kind="function",
            lineno=node.lineno,
            end_lineno=_end_lineno(node),
            children=tuple(_symbols_from_body(node.body)),
        )

    return None


def _append_symbol(lines: list[str], symbol: Symbol, depth: int) -> None:
    indent = "  " * depth
    lines.append(f"{indent}{symbol.kind}: {symbol.display_name}  L{symbol.lineno}")
    for child in symbol.children:
        _append_symbol(lines, child, depth + 1)


def _end_lineno(node: ast.AST) -> int:
    end_lineno = getattr(node, "end_lineno", None)
    if isinstance(end_lineno, int):
        return end_lineno
    lineno = getattr(node, "lineno", 1)
    return lineno if isinstance(lineno, int) else 1
