# pyoverview

`pyoverview` is a small terminal outline browser for Python files. It parses a
module with Python's `ast` module and opens a two-pane TUI:

- left pane: classes, functions, async functions, and nested definitions
- right pane: source code, automatically scrolled to the selected symbol

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
