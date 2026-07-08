# pyoverview

`pyoverview` is a small terminal outline browser for Python files. It parses a
module with Python's `ast` module and opens a two-pane TUI:

- left pane: classes, functions, async functions, and nested definitions
- right pane: source code, automatically scrolled to the selected symbol

## Sections

Add module-level region comments to group the outline into larger chunks:

```python
# region Configuration

DEFAULT_MODEL = "gpt-5"


def load_config():
    ...


# region Review Model

class Finding:
    ...


async def score_patch():
    ...
```

`pyoverview` renders those region comments as section nodes:

```text
reviewer.py
  section: Configuration  L1
    function: load_config()  L6
  section: Review Model  L10
    class: Finding  L12
    async function: async score_patch()  L16
```

Only comments starting at the beginning of a line with `# region ` create
sections. A section runs until the next region marker or the end of the file.

## Install

```sh
uvx pyoverview path/to/module.py
```

If you are developing locally:

```sh
uv run pyoverview path/to/module.py
```

## Keys

- `Up` / `Down`, `k` / `j`: move through the outline
- `PageUp` / `PageDown`: scroll code
- `g` / `G`: jump to first / last outline item
- `Enter`: center the selected symbol in the code pane
- `r`: reload the file from disk
- `q`: quit

## Non-interactive Use

```sh
pyoverview --print path/to/module.py
```

This prints the outline without opening the TUI.
