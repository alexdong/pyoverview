from __future__ import annotations

import builtins
import io
import keyword
import token
import tokenize
from dataclasses import dataclass
from typing import Optional


BUILTIN_NAMES = frozenset(name for name in dir(builtins) if not name.startswith("_"))
KEYWORDS = frozenset(keyword.kwlist) | frozenset(getattr(keyword, "softkwlist", ()))
TABSIZE = 4


@dataclass(frozen=True)
class HighlightSpan:
    start: int
    end: int
    style: str


def python_highlight_spans(source_lines: list[str]) -> dict[int, list[HighlightSpan]]:
    spans_by_line: dict[int, list[HighlightSpan]] = {}
    source = "\n".join(source_lines)
    if source_lines:
        source += "\n"

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token_info in tokens:
            style = _token_style(token_info)
            if style is None:
                continue
            _append_token_spans(spans_by_line, source_lines, token_info, style)
    except tokenize.TokenError:
        return spans_by_line

    for spans in spans_by_line.values():
        spans.sort(key=lambda span: (span.start, span.end))
    return spans_by_line


def _token_style(token_info: tokenize.TokenInfo) -> Optional[str]:
    token_type = token_info.type
    token_text = token_info.string

    if token_type == token.NAME:
        if token_text in KEYWORDS:
            return "keyword"
        if token_text in BUILTIN_NAMES:
            return "builtin"
    if token_type == token.STRING:
        return "string"
    if token_type == token.NUMBER:
        return "number"
    if token_type == tokenize.COMMENT:
        return "comment"
    return None


def _append_token_spans(
    spans_by_line: dict[int, list[HighlightSpan]],
    source_lines: list[str],
    token_info: tokenize.TokenInfo,
    style: str,
) -> None:
    start_row, start_col = token_info.start
    end_row, end_col = token_info.end

    for row in range(start_row, end_row + 1):
        line = source_lines[row - 1] if 0 <= row - 1 < len(source_lines) else ""
        col_start = start_col if row == start_row else 0
        col_end = end_col if row == end_row else len(line)
        display_start = _display_column(line, col_start)
        display_end = _display_column(line, col_end)
        if display_end > display_start:
            spans_by_line.setdefault(row, []).append(HighlightSpan(display_start, display_end, style))


def _display_column(line: str, column: int) -> int:
    return len(line[:column].expandtabs(TABSIZE))
