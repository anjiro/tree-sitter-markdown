# Wikilink Parser Setup Guide

This document explains how to compile the tree-sitter-markdown Python bindings with wikilink support enabled and how to parse wikilinks from Markdown documents.

## Background

The tree-sitter-markdown parser supports wikilinks (like `[[link text]]`) as an optional extension that must be enabled at compile time using the `EXTENSION_WIKI_LINK` environment variable.

## Setup Steps Completed

### 1. Installed Required Tools

- **tree-sitter-cli**: Installed via `cargo install tree-sitter-cli`
  - Required to regenerate the parser with extensions enabled
  - Location: `/root/.cargo/bin/tree-sitter`

- **tree-sitter Python package**: Built from source
  - Cloned from: https://github.com/tree-sitter/py-tree-sitter
  - Provides the Python bindings for tree-sitter

### 2. Regenerated Parsers with Wikilink Support

```bash
# Regenerate the inline parser (where wikilinks are defined)
cd tree-sitter-markdown-inline
EXTENSION_WIKI_LINK=1 tree-sitter generate

# Regenerate the block parser
cd tree-sitter-markdown
EXTENSION_WIKI_LINK=1 tree-sitter generate
```

### 3. Rebuilt Python Bindings

```bash
# From the repository root
pip3 install -e . --no-deps
```

## How to Parse Wikilinks

The tree-sitter-markdown parser uses a two-stage parsing approach:

1. **Block Grammar**: Parse the document structure (paragraphs, headings, etc.)
2. **Inline Grammar**: Parse inline content (emphasis, links, **wikilinks**, etc.)

### Example Usage

See `parse_wikilinks.py` for a complete example. Here's the basic process:

```python
import tree_sitter
import tree_sitter_markdown

# Load the grammars
markdown_lang = tree_sitter.Language(tree_sitter_markdown.language())
inline_lang = tree_sitter.Language(tree_sitter_markdown.inline_language())

# Parse with block grammar
block_parser = tree_sitter.Parser()
block_parser.language = markdown_lang
block_tree = block_parser.parse(bytes(markdown_text, 'utf8'))

# Collect inline content ranges
inline_ranges = collect_inline_ranges(block_tree.root_node)

# Parse inline content with inline grammar
inline_parser = tree_sitter.Parser()
inline_parser.language = inline_lang
ranges = [tree_sitter.Range((0, start), (0, end), start, end)
          for start, end in inline_ranges]
inline_parser.included_ranges = ranges
inline_tree = inline_parser.parse(bytes(markdown_text, 'utf8'))

# Extract wikilinks
wikilinks = extract_wikilinks(inline_tree.root_node, text_bytes)
```

### Running the Example Script

```bash
python3 parse_wikilinks.py myfile.md
```

Output:
```
Found 2 wikilink(s) in myfile.md:
  1. [[extremely important information]]
  2. [[very important things]]
```

## Tree Structure

When wikilinks are properly parsed, they appear in the parse tree as:

```
wiki_link: '[[extremely important information]]'
  [: '['
  [: '['
  link_destination: 'extremely important information'
  ]: ']'
  ]: ']'
```

The `link_destination` node contains the actual wikilink text without the brackets.

## Important Notes

1. **Extension is compile-time only**: You must regenerate the parsers with `EXTENSION_WIKI_LINK=1` set. It cannot be enabled at runtime.

2. **Two-stage parsing required**: You must use both the block and inline grammars. The wikilinks only appear when parsing with the inline grammar.

3. **Included ranges**: The inline parser must be configured with `included_ranges` to specify which portions of the document to parse as inline content.

## Files Created

- `parse_wikilinks.py`: Complete example script for parsing wikilinks
- `myfile.md`: Example markdown file with wikilinks
- `WIKILINK_SETUP.md`: This documentation file

## Dependencies

- Python 3.9+
- tree-sitter (Python package) - installed from source
- tree-sitter-markdown (Python package) - installed from this repository with wikilink support enabled
