# Python MarkdownParser

This document describes the Python `MarkdownParser` class, which is a translation of the Rust `MarkdownParser` from `bindings/rust/parser.rs`.

## Overview

The `MarkdownParser` provides a convenient wrapper around the block and inline grammars, automatically handling the two-stage parsing process required by tree-sitter-markdown.

## Architecture

Tree-sitter-markdown uses a dual-grammar approach:

1. **Block Grammar** (`LANGUAGE`): Parses document structure (headings, paragraphs, lists, etc.)
2. **Inline Grammar** (`INLINE_LANGUAGE`): Parses inline content (emphasis, links, wikilinks, etc.)

The `MarkdownParser` class abstracts this complexity by:
- Parsing with the block grammar first
- Identifying all inline content nodes (`inline` and `pipe_table_cell`)
- Parsing each inline node with the inline grammar
- Maintaining the relationships between block and inline trees

## Classes

### MarkdownParser

The main parser class that handles document parsing.

```python
from markdown_parser import MarkdownParser

parser = MarkdownParser()
tree = parser.parse(b"# Hello\n\nWith [[wikilink]].")
```

**Methods:**
- `parse(text: bytes, old_tree: Optional[MarkdownTree] = None) -> Optional[MarkdownTree]`
  - Parse UTF8-encoded markdown text
  - Returns `MarkdownTree` on success, `None` on failure
  - Can accept an old tree for incremental parsing

### MarkdownTree

Holds the combined parse tree with both block and inline content.

```python
tree = parser.parse(text)

# Access trees
block_tree = tree.block_tree()
inline_trees = tree.inline_trees()

# Get inline tree for a specific node
inline_node = ...  # some 'inline' or 'pipe_table_cell' node
inline_tree = tree.inline_tree(inline_node)

# Create a cursor for traversal
cursor = tree.walk()
```

**Methods:**
- `block_tree() -> Tree`: Returns the block-level parse tree
- `inline_tree(parent_node: Node) -> Optional[Tree]`: Returns the inline tree for a given inline node
- `inline_trees() -> List[Tree]`: Returns all inline trees
- `walk() -> MarkdownCursor`: Creates a cursor for tree traversal

### MarkdownCursor

A stateful cursor for efficiently walking the combined tree structure.

```python
cursor = tree.walk()

# Navigate the tree
cursor.goto_first_child()
cursor.goto_next_sibling()
cursor.goto_parent()

# Get current node
node = cursor.node()

# Check if in inline content
if cursor.is_inline():
    print("Currently in inline tree")

# Get field name
field = cursor.field_name()
```

**Methods:**
- `node() -> Node`: Get the current node
- `is_inline() -> bool`: Check if cursor is in an inline tree
- `field_name() -> Optional[str]`: Get field name of current node
- `goto_first_child() -> bool`: Move to first child (automatically descends into inline trees)
- `goto_parent() -> bool`: Move to parent (automatically ascends from inline trees)
- `goto_next_sibling() -> bool`: Move to next sibling
- `goto_first_child_for_byte(byte_index: int) -> Optional[int]`: Move to first child after byte offset
- `goto_first_child_for_point(point: Tuple[int, int]) -> Optional[int]`: Move to first child after point

## Key Features

### Automatic Inline Tree Traversal

When using `MarkdownCursor.goto_first_child()` on an `inline` or `pipe_table_cell` node, the cursor automatically descends into the associated inline tree:

```python
cursor = tree.walk()
cursor.goto_first_child()  # section
cursor.goto_first_child()  # paragraph
cursor.goto_first_child()  # inline (block node)
cursor.goto_first_child()  # Now in inline tree! Could be at wiki_link, emphasis, etc.
```

### Seamless Tree Transitions

The cursor handles transitions between block and inline trees transparently:

```python
# Descending into inline content
if cursor.node().type == "inline":
    assert not cursor.is_inline()  # Still in block tree
    cursor.goto_first_child()      # Descends into inline tree
    assert cursor.is_inline()      # Now in inline tree

# Ascending back to block tree
cursor.goto_parent()               # Ascends to root of inline tree
cursor.goto_parent()               # Back in block tree at 'inline' node
```

## Usage Examples

### Basic Wikilink Extraction

```python
from markdown_parser import MarkdownParser

def extract_wikilinks(tree):
    wikilinks = []

    def visit(node):
        if node.type == 'wiki_link':
            for child in node.children:
                if child.type == 'link_destination':
                    wikilinks.append(child.text.decode('utf8'))
        for child in node.children:
            visit(child)

    for inline_tree in tree.inline_trees():
        visit(inline_tree.root_node)

    return wikilinks

parser = MarkdownParser()
tree = parser.parse(b"Text with [[link]].")
links = extract_wikilinks(tree)  # ['link']
```

### Cursor-Based Tree Traversal

```python
from markdown_parser import MarkdownParser

def print_tree(cursor, depth=0):
    node = cursor.node()
    indent = "  " * depth
    is_inline = " (inline)" if cursor.is_inline() else ""
    print(f"{indent}{node.type}{is_inline}")

    if cursor.goto_first_child():
        print_tree(cursor, depth + 1)
        cursor.goto_parent()

    if cursor.goto_next_sibling():
        print_tree(cursor, depth)

parser = MarkdownParser()
tree = parser.parse(b"# Title\n\n[[Link]]")
print_tree(tree.walk())
```

### Working with Tables

```python
from markdown_parser import MarkdownParser

text = b"""| Name | Link |
|------|------|
| Item | [[wikilink]] |
"""

parser = MarkdownParser()
tree = parser.parse(text)

# Tables automatically parse inline content in cells
cursor = tree.walk()
cursor.goto_first_child()  # section
cursor.goto_first_child()  # pipe_table

# Navigate to a table cell
# ... cursor movements ...

# When you reach a pipe_table_cell with goto_first_child(),
# it automatically descends into the inline content
```

## Differences from Rust Implementation

The Python implementation closely follows the Rust version with these adaptations:

1. **Property vs. Method Access**: Uses Python properties where appropriate
2. **Type Hints**: Uses Python type hints instead of Rust's type system
3. **Error Handling**: Returns `None` instead of Rust's `Option` type
4. **API Naming**: Uses Python naming conventions (snake_case)

## Testing

Run the test suite:

```bash
python3 test_markdown_parser.py
```

Tests cover:
- Basic parsing
- Cursor navigation
- Wikilink extraction
- Table parsing
- Inline tree access
- Cross-tree cursor traversal

## Examples

See `example_markdown_parser.py` for comprehensive examples including:
- Simple parsing and extraction
- Cursor-based tree traversal
- Table parsing with inline content
- Incremental parsing

Run the examples:

```bash
python3 example_markdown_parser.py
```

## Comparison with Manual Parsing

**Before (Manual Two-Stage Parsing):**
```python
# Parse with block grammar
block_parser = tree_sitter.Parser()
block_parser.language = block_language
block_tree = block_parser.parse(text)

# Collect inline ranges
inline_ranges = collect_inline_ranges(block_tree.root_node)

# Parse with inline grammar
inline_parser = tree_sitter.Parser()
inline_parser.language = inline_language
inline_parser.included_ranges = ranges
inline_tree = inline_parser.parse(text)
```

**After (Using MarkdownParser):**
```python
parser = MarkdownParser()
tree = parser.parse(text)
# Access both block and inline trees through tree object
```

## Performance

The `MarkdownParser` uses the same two-stage parsing approach as manual parsing but:
- Manages both parsers internally
- Automatically calculates ranges for inline content
- Maintains the mapping between block nodes and their inline trees
- Supports incremental parsing for performance

## See Also

- `WIKILINK_SETUP.md`: Setup guide for wikilink support
- `parse_wikilinks.py`: Simple wikilink extraction script
- Original Rust implementation: `bindings/rust/parser.rs`
