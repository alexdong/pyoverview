from __future__ import annotations

import curses
from pathlib import Path
from typing import Final, Optional

from .outline import OutlineError, Symbol, flatten_outline, parse_file
from .syntax import HighlightSpan, python_highlight_spans


class CursesUnavailableError(Exception):
    """Raised when the terminal cannot run the curses TUI."""


HELP: Final = "q quit | up/down select | pgup/pgdn code | enter center | r reload"


def run_tui(path: Path, root: Symbol, source_lines: list[str]) -> None:
    try:
        curses.wrapper(_run, path, root, source_lines)
    except curses.error as exc:
        raise CursesUnavailableError("could not initialize terminal UI") from exc


class State:
    def __init__(self, path: Path, root: Symbol, source_lines: list[str]) -> None:
        self.path = path
        self.root = root
        self.source_lines = source_lines
        self.highlight_spans = _highlight_spans(path, source_lines)
        self.items = flatten_outline(root)
        self.selected = 0
        self.outline_top = 0
        self.code_top = 0
        self.message = ""
        self.center_selected_symbol()

    @property
    def current_symbol(self) -> Optional[Symbol]:
        if not self.items:
            return None
        return self.items[self.selected][1]

    def move_selection(self, delta: int) -> None:
        if not self.items:
            return
        self.selected = max(0, min(len(self.items) - 1, self.selected + delta))
        self.center_selected_symbol()

    def center_selected_symbol(self) -> None:
        symbol = self.current_symbol
        if symbol is None:
            self.code_top = 0
            return
        self.code_top = max(0, symbol.lineno - 4)

    def scroll_code(self, delta: int) -> None:
        max_top = max(0, len(self.source_lines) - 1)
        self.code_top = max(0, min(max_top, self.code_top + delta))

    def reload(self) -> None:
        try:
            root, source_lines = parse_file(self.path)
        except OutlineError as exc:
            self.message = str(exc)
            return
        selected_lineno = self.current_symbol.lineno if self.current_symbol else 1
        self.root = root
        self.source_lines = source_lines
        self.highlight_spans = _highlight_spans(self.path, source_lines)
        self.items = flatten_outline(root)
        self.selected = _closest_symbol_index(self.items, selected_lineno)
        self.message = "reloaded"
        self.center_selected_symbol()


def _run(stdscr: curses.window, path: Path, root: Symbol, source_lines: list[str]) -> None:
    state = State(path, root, source_lines)
    curses.curs_set(0)
    curses.use_default_colors()
    _init_colors()
    stdscr.keypad(True)

    while True:
        _draw(stdscr, state)
        key = stdscr.getch()

        if key in (ord("q"), 27):
            return
        if key in (curses.KEY_UP, ord("k")):
            state.move_selection(-1)
        elif key in (curses.KEY_DOWN, ord("j")):
            state.move_selection(1)
        elif key in (curses.KEY_NPAGE,):
            state.scroll_code(_code_page_size(stdscr))
        elif key in (curses.KEY_PPAGE,):
            state.scroll_code(-_code_page_size(stdscr))
        elif key in (ord("g"),):
            state.selected = 0
            state.center_selected_symbol()
        elif key in (ord("G"),):
            state.selected = max(0, len(state.items) - 1)
            state.center_selected_symbol()
        elif key in (curses.KEY_ENTER, 10, 13):
            state.center_selected_symbol()
        elif key in (ord("r"),):
            state.reload()
        elif key == curses.KEY_RESIZE:
            continue


def _draw(stdscr: curses.window, state: State) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < 8 or width < 50:
        _addnstr(stdscr, 0, 0, "terminal is too small for pyoverview", max(0, width - 1), curses.A_BOLD)
        stdscr.refresh()
        return

    status_y = height - 1
    content_height = height - 2
    left_width = _left_width(width)
    right_x = left_width
    right_width = width - left_width

    _draw_outline(stdscr, state, 0, 0, content_height, left_width)
    _draw_code(stdscr, state, right_x, 0, content_height, right_width)
    _draw_status(stdscr, state, status_y, width)

    stdscr.refresh()


def _draw_outline(
    stdscr: curses.window,
    state: State,
    x: int,
    y: int,
    height: int,
    width: int,
) -> None:
    _draw_box(stdscr, y, x, height, width, f" outline: {state.root.display_name} ")
    body_height = max(0, height - 2)

    if not state.items:
        _addnstr(stdscr, y + 1, x + 2, "(no sections, classes, or functions)", max(0, width - 4), curses.color_pair(4))
        return

    state.outline_top = _adjust_top(state.selected, state.outline_top, body_height)
    visible = state.items[state.outline_top : state.outline_top + body_height]
    for row, (depth, symbol) in enumerate(visible):
        index = state.outline_top + row
        line_y = y + 1 + row
        marker = ">" if index == state.selected else " "
        prefix = "  " * depth
        label = f"{marker} {prefix}{_kind_marker(symbol)} {symbol.display_name}"
        attr = curses.A_REVERSE if index == state.selected else curses.A_NORMAL
        if symbol.kind == "class" and index != state.selected:
            attr |= curses.color_pair(2)
        elif symbol.kind == "section" and index != state.selected:
            attr |= curses.A_BOLD
        elif symbol.kind in {"function", "async function"} and index != state.selected:
            attr |= curses.color_pair(3)
        _addnstr(stdscr, line_y, x + 1, label, max(0, width - 2), attr)


def _draw_code(
    stdscr: curses.window,
    state: State,
    x: int,
    y: int,
    height: int,
    width: int,
) -> None:
    symbol = state.current_symbol
    title = " source "
    if symbol is not None:
        title = f" source: {symbol.display_name} L{symbol.lineno} "
    _draw_box(stdscr, y, x, height, width, title)

    body_height = max(0, height - 2)
    gutter_width = max(4, len(str(max(1, len(state.source_lines)))) + 1)
    code_width = max(0, width - gutter_width - 4)
    max_top = max(0, len(state.source_lines) - body_height)
    state.code_top = max(0, min(max_top, state.code_top))

    selected_lineno = symbol.lineno if symbol else -1
    selected_end = symbol.end_lineno if symbol else -1

    for row in range(body_height):
        line_index = state.code_top + row
        if line_index >= len(state.source_lines):
            break
        lineno = line_index + 1
        raw_line = state.source_lines[line_index]
        display_line = raw_line.expandtabs(4)
        in_symbol = selected_lineno <= lineno <= selected_end
        base_attr = curses.A_BOLD if in_symbol else curses.A_NORMAL

        gutter = f"{lineno:>{gutter_width - 1}} "
        gutter_attr = curses.color_pair(4) | (curses.A_BOLD if lineno == selected_lineno else curses.A_NORMAL)
        _addnstr(stdscr, y + 1 + row, x + 1, gutter, gutter_width, gutter_attr)
        _draw_highlighted_line(
            stdscr,
            y + 1 + row,
            x + 1 + gutter_width,
            display_line,
            code_width,
            state.highlight_spans.get(lineno, []),
            base_attr,
        )


def _draw_status(stdscr: curses.window, state: State, y: int, width: int) -> None:
    path = str(state.path)
    suffix = f" | {state.message}" if state.message else ""
    text = f" {path} | {HELP}{suffix}"
    _addnstr(stdscr, y, 0, text.ljust(max(0, width - 1)), max(0, width - 1), curses.A_REVERSE)


def _draw_highlighted_line(
    stdscr: curses.window,
    y: int,
    x: int,
    line: str,
    width: int,
    spans: list[HighlightSpan],
    base_attr: int,
) -> None:
    cursor = 0
    for span in spans:
        if cursor >= width:
            return
        start = max(0, min(width, span.start))
        end = max(start, min(width, span.end))
        if start > cursor:
            _addnstr(stdscr, y, x + cursor, line[cursor:start], start - cursor, base_attr)
        if end > start:
            _addnstr(stdscr, y, x + start, line[start:end], end - start, base_attr | _syntax_attr(span.style))
        cursor = max(cursor, end)

    if cursor < width:
        _addnstr(stdscr, y, x + cursor, line[cursor:width], width - cursor, base_attr)


def _draw_box(stdscr: curses.window, y: int, x: int, height: int, width: int, title: str) -> None:
    if height <= 0 or width <= 0:
        return
    right = x + width - 1
    bottom = y + height - 1
    horizontal = "-"
    vertical = "|"

    _addnstr(stdscr, y, x, "+", 1)
    _addnstr(stdscr, y, x + 1, horizontal * max(0, width - 2), max(0, width - 2))
    _addnstr(stdscr, y, right, "+", 1)
    _addnstr(stdscr, bottom, x, "+", 1)
    _addnstr(stdscr, bottom, x + 1, horizontal * max(0, width - 2), max(0, width - 2))
    _addnstr(stdscr, bottom, right, "+", 1)

    for line_y in range(y + 1, bottom):
        _addnstr(stdscr, line_y, x, vertical, 1)
        _addnstr(stdscr, line_y, right, vertical, 1)

    if width > 4:
        _addnstr(stdscr, y, x + 2, title[: width - 4], width - 4, curses.A_BOLD)


def _addnstr(stdscr: curses.window, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
    if width <= 0:
        return
    height, screen_width = stdscr.getmaxyx()
    if y < 0 or y >= height or x < 0 or x >= screen_width:
        return
    try:
        stdscr.addnstr(y, x, text, min(width, screen_width - x), attr)
    except curses.error:
        pass


def _init_colors() -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    curses.init_pair(1, curses.COLOR_MAGENTA, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)
    curses.init_pair(5, curses.COLOR_GREEN, -1)
    curses.init_pair(6, curses.COLOR_YELLOW, -1)
    curses.init_pair(7, curses.COLOR_BLUE, -1)
    curses.init_pair(8, curses.COLOR_CYAN, -1)


def _syntax_attr(style: str) -> int:
    if style == "keyword":
        return curses.color_pair(1) | curses.A_BOLD
    if style == "string":
        return curses.color_pair(5)
    if style == "number":
        return curses.color_pair(6)
    if style == "comment":
        return curses.color_pair(7)
    if style == "builtin":
        return curses.color_pair(8)
    return curses.A_NORMAL


def _highlight_spans(path: Path, source_lines: list[str]) -> dict[int, list[HighlightSpan]]:
    if path.suffix == ".py":
        return python_highlight_spans(source_lines)
    return {}


def _left_width(total_width: int) -> int:
    return max(24, min(54, int(total_width * 0.36)))


def _adjust_top(selected: int, top: int, height: int) -> int:
    if selected < top:
        return selected
    if selected >= top + height:
        return selected - height + 1
    return top


def _code_page_size(stdscr: curses.window) -> int:
    height, _ = stdscr.getmaxyx()
    return max(1, height - 4)


def _kind_marker(symbol: Symbol) -> str:
    if symbol.kind == "section":
        return "S"
    if symbol.kind == "class":
        return "C"
    if symbol.kind == "async function":
        return "A"
    return "F"


def _closest_symbol_index(items: list[tuple[int, Symbol]], lineno: int) -> int:
    if not items:
        return 0
    distances = [abs(symbol.lineno - lineno) for _, symbol in items]
    return distances.index(min(distances))
