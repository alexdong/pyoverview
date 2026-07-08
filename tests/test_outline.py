from __future__ import annotations

import pytest

from pyoverview.outline import OutlineError, flatten_outline, format_outline, parse_python_source


SAMPLE = '''
def top():
    def nested():
        return 1
    return nested()


class Widget:
    def render(self):
        return "ok"

    async def refresh(self):
        return None


async def run():
    return Widget()
'''


def test_parse_python_source_builds_nested_outline() -> None:
    root = parse_python_source(SAMPLE, module_name="sample.py")

    assert root.display_name == "sample.py"
    assert [child.display_name for child in root.children] == ["top()", "Widget", "async run()"]
    assert [child.display_name for child in root.children[0].children] == ["nested()"]
    assert [child.display_name for child in root.children[1].children] == ["render()", "async refresh()"]


def test_flatten_outline_preserves_depth_first_order() -> None:
    root = parse_python_source(SAMPLE, module_name="sample.py")

    flattened = [(depth, symbol.display_name) for depth, symbol in flatten_outline(root)]

    assert flattened == [
        (0, "top()"),
        (1, "nested()"),
        (0, "Widget"),
        (1, "render()"),
        (1, "async refresh()"),
        (0, "async run()"),
    ]


def test_format_outline_includes_line_numbers() -> None:
    root = parse_python_source(SAMPLE, module_name="sample.py")

    assert format_outline(root).splitlines() == [
        "sample.py",
        "  function: top()  L2",
        "    function: nested()  L3",
        "  class: Widget  L8",
        "    function: render()  L9",
        "    async function: async refresh()  L12",
        "  async function: async run()  L16",
    ]


def test_parse_error_is_reported_as_outline_error() -> None:
    with pytest.raises(OutlineError, match="could not parse bad.py"):
        parse_python_source("def nope(:\n", module_name="bad.py")
