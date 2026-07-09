# pyoverview

`pyoverview` is a small terminal outline browser for Python files. It parses a
module with Python's `ast` module and opens a two-pane TUI:

- left pane: classes, functions, async functions, and nested definitions
- right pane: syntax-highlighted source code on the terminal's default background,
  automatically scrolled to the selected symbol

![pyoverview terminal UI showing an outline pane and syntax-highlighted code preview](docs/pyoverview.svg)

## Sections

Add module-level section comments to group the outline into larger chunks:

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

`# %% Title` cell comments are also supported:

```python
# %% SFT

def sft_dataset():
    ...


# %% GRPO

def grpo_dataset():
    ...
```

Markdown-style comment headings are supported too. `#`, `##`, and `###` create
nested sections:

```python
# Training

def load_rows():
    ...


## SFT

def sft_dataset():
    ...


### Formatting

def format_prompt():
    ...
```

`pyoverview` renders those comments and headings as section nodes:

```text
reviewer.py
  section: Training  L1
    function: load_rows()  L3
    section: SFT  L7
      function: sft_dataset()  L9
      section: Formatting  L13
        function: format_prompt()  L15
```

Only comments starting at the beginning of a line with `# region `, `# %% `,
`#%% `, `# `, `## `, or `### ` create sections. A section runs until the next
section marker at the same or higher heading level, or the end of the file.

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
