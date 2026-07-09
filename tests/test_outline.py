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


def test_region_comments_group_top_level_symbols_into_sections() -> None:
    source = '''
def before():
    return None


# region Configuration
SETTING = "on"


def load_config():
    return SETTING


# region Review Model
class Finding:
    pass


async def score():
    return Finding()
'''

    root = parse_python_source(source, module_name="sectioned.py")

    assert [(child.kind, child.display_name) for child in root.children] == [
        ("function", "before()"),
        ("section", "Configuration"),
        ("section", "Review Model"),
    ]
    assert [child.display_name for child in root.children[1].children] == ["load_config()"]
    assert [child.display_name for child in root.children[2].children] == ["Finding", "async score()"]


def test_region_comments_are_included_in_flattened_outline() -> None:
    source = '''
# region First
def one():
    return 1


# region Second
def two():
    return 2
'''

    root = parse_python_source(source, module_name="sectioned.py")

    assert [(depth, symbol.kind, symbol.display_name) for depth, symbol in flatten_outline(root)] == [
        (0, "section", "First"),
        (1, "function", "one()"),
        (0, "section", "Second"),
        (1, "function", "two()"),
    ]


def test_cell_comments_group_top_level_symbols_into_sections() -> None:
    source = '''
# %% SFT
def sft_dataset():
    return []


#%% GRPO
def grpo_dataset():
    return []


# %%
def unsectioned():
    return None
'''

    root = parse_python_source(source, module_name="cells.py")

    assert [(child.kind, child.display_name) for child in root.children] == [
        ("section", "SFT"),
        ("section", "GRPO"),
    ]
    assert [child.display_name for child in root.children[0].children] == ["sft_dataset()"]
    assert [child.display_name for child in root.children[1].children] == ["grpo_dataset()", "unsectioned()"]


def test_markdown_heading_comments_group_symbols_into_nested_sections() -> None:
    source = '''
# Overview
def parse():
    return "parse"


## CLI
def main():
    return None


### Flags
def build_parser():
    return object()


# Runtime
def run():
    return main()
'''

    root = parse_python_source(source, module_name="headings.py")

    assert format_outline(root).splitlines() == [
        "headings.py",
        "  section: Overview  L2",
        "    function: parse()  L3",
        "    section: CLI  L7",
        "      function: main()  L8",
        "      section: Flags  L12",
        "        function: build_parser()  L13",
        "  section: Runtime  L17",
        "    function: run()  L18",
    ]


def test_format_outline_prints_sections() -> None:
    source = '''
# region First
def one():
    return 1
'''

    root = parse_python_source(source, module_name="sectioned.py")

    assert format_outline(root).splitlines() == [
        "sectioned.py",
        "  section: First  L2",
        "    function: one()  L3",
    ]


def test_parse_error_is_reported_as_outline_error() -> None:
    with pytest.raises(OutlineError, match="could not parse bad.py"):
        parse_python_source("def nope(:\n", module_name="bad.py")
