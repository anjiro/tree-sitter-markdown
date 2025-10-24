# Setting Up Tree-Sitter-Markdown with WikiLink Support

This guide explains how to properly compile the Python bindings for tree-sitter-markdown with wikilink support enabled.

## Problem

The default tree-sitter-markdown parser is generated **without** wikilink support. Wikilinks are an optional extension that must be enabled at **grammar generation time** (not just compilation time).

When you try to parse `[[wikilink]]` syntax without the extension enabled, the parser treats the `[` characters as individual tokens instead of recognizing them as wikilink nodes.

## Solution

You need to regenerate the grammar with the `EXTENSION_WIKI_LINK` environment variable set, then recompile the Python bindings.

### Step 1: Install tree-sitter CLI

You need the tree-sitter command-line tool to regenerate the grammar. Choose one method:

**Option A: Via npm (recommended)**
```bash
npm install -g tree-sitter-cli
```

**Option B: Via cargo**
```bash
cargo install tree-sitter-cli
```

**Option C: Download pre-built binary**
Download from: https://github.com/tree-sitter/tree-sitter/releases

### Step 2: Regenerate the Grammar with WikiLink Support

```bash
cd /path/to/tree-sitter-markdown

# Set the extension environment variable
export EXTENSION_WIKI_LINK=1

# Regenerate both grammars
cd tree-sitter-markdown
tree-sitter generate
cd ..

cd tree-sitter-markdown-inline
tree-sitter generate
cd ..
```

Alternatively, use the npm build script:
```bash
EXTENSION_WIKI_LINK=1 npm run build
```

### Step 3: Compile the Python Bindings

```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .

# Don't forget to install the tree-sitter Python package
pip install 'tree-sitter~=0.23'
```

### Step 4: Verify WikiLink Support

Run the test script:
```bash
python3 parse_wikilinks.py myfile.md
```

You should see output like:
```
Found 2 wikilink(s):
1. [[extremely important information]]
   - Destination: extremely important information
2. [[very important things]]
   - Destination: very important things
```

## Alternative: Enable Other Extensions

You can enable multiple extensions at once:

```bash
# Enable wikilinks only
export EXTENSION_WIKI_LINK=1

# Enable tags only
export EXTENSION_TAGS=1

# Enable all non-default extensions
export ALL_EXTENSIONS=1

# Then regenerate
npm run build
```

Available extensions:
- `EXTENSION_WIKI_LINK` - WikiLinks `[[destination]]` or `[[destination|text]]`
- `EXTENSION_TAGS` - Tags `#tag`
- `EXTENSION_LATEX` - LaTeX math
- `EXTENSION_GFM` - GitHub Flavored Markdown (enabled by default)
- `EXTENSION_TASK_LIST` - Task lists (enabled by default)
- `EXTENSION_STRIKETHROUGH` - Strikethrough (enabled by default)
- `EXTENSION_PIPE_TABLE` - Pipe tables (enabled by default)
- `EXTENSION_MINUS_METADATA` - YAML frontmatter (enabled by default)
- `EXTENSION_PLUS_METADATA` - TOML frontmatter (enabled by default)

## WikiLink Syntax

Once enabled, you can parse two types of wikilinks:

1. **Simple wikilink**: `[[destination]]`
   - Creates a link to "destination"
   - Display text is the same as the destination

2. **Wikilink with custom text**: `[[destination|custom text]]`
   - Creates a link to "destination"
   - Displays "custom text" to the user

## Troubleshooting

### WikiLinks not being parsed

If `[[wikilink]]` is being parsed as individual `[` characters:
- The grammar was not regenerated with `EXTENSION_WIKI_LINK=1`
- You must regenerate the grammar (Step 2 above), not just recompile

### tree-sitter command not found

- Make sure tree-sitter-cli is installed and in your PATH
- Try `npm install` in the repo to install it as a dev dependency
- Check with `tree-sitter --version`

### ImportError when importing tree_sitter_markdown

- Make sure you installed the Python bindings: `pip install -e .`
- Make sure you installed tree-sitter: `pip install 'tree-sitter~=0.23'`

## Technical Details

### Why regeneration is needed

The tree-sitter grammar is defined in JavaScript files (`grammar.js`). These files use environment variables to conditionally include or exclude grammar rules. The `tree-sitter generate` command reads these `.js` files and generates C parser code.

The wikilink rules are only included in the generated `parser.c` if `EXTENSION_WIKI_LINK` is set when running `tree-sitter generate`. Setting the variable at compile time (during `pip install`) has no effect because the C code has already been generated.

### Parse tree structure

With wikilinks enabled, you'll see nodes like:
```
wiki_link
  link_destination "extremely important information"
```

Or with custom text:
```
wiki_link
  link_destination "destination"
  link_text "custom text"
```

Without wikilinks enabled, you'll see:
```
[ "["
[ "["
```

This is why the extension must be enabled at grammar generation time.
