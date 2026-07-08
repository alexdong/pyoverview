from __future__ import annotations

from pyoverview.syntax import python_highlight_spans


def test_python_highlight_spans_marks_common_tokens() -> None:
    spans = python_highlight_spans(
        [
            "# comment",
            "class Runner:",
            "    value = 42",
            "    text = 'ok'",
            "    return len(text)",
        ]
    )

    assert [(span.start, span.end, span.style) for span in spans[1]] == [(0, 9, "comment")]
    assert (0, 5, "keyword") in [(span.start, span.end, span.style) for span in spans[2]]
    assert (12, 14, "number") in [(span.start, span.end, span.style) for span in spans[3]]
    assert (11, 15, "string") in [(span.start, span.end, span.style) for span in spans[4]]
    assert (4, 10, "keyword") in [(span.start, span.end, span.style) for span in spans[5]]
    assert (11, 14, "builtin") in [(span.start, span.end, span.style) for span in spans[5]]


def test_python_highlight_spans_expands_tabs_for_display_columns() -> None:
    spans = python_highlight_spans(["\treturn 1"])

    assert [(span.start, span.end, span.style) for span in spans[1]] == [
        (4, 10, "keyword"),
        (11, 12, "number"),
    ]
