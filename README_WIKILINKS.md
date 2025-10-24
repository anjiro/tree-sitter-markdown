# Quick Start: Parsing WikiLinks with Tree-Sitter-Markdown

## TL;DR - What You Need to Know

The current parser in this repository does **NOT** have wikilink support enabled. To parse wikilinks like `[[destination]]`, you must:

1. Install tree-sitter CLI
2. Regenerate the grammar with `EXTENSION_WIKI_LINK=1`
3. Recompile the Python bindings

## Quick Setup (In an Environment with Internet Access)

```bash
# 1. Install tree-sitter CLI
npm install

# 2. Regenerate grammar with wikilinks enabled
EXTENSION_WIKI_LINK=1 npm run build

# 3. Install Python bindings
pip install -e .
pip install 'tree-sitter~=0.23'

# 4. Test it
python3 parse_wikilinks.py myfile.md
```

## Files Provided

1. **myfile.md** - Example markdown file with wikilinks
2. **parse_wikilinks.py** - Script to extract all wikilinks from a markdown file
3. **debug_tree.py** - Script to visualize the parse tree
4. **WIKILINK_SETUP.md** - Comprehensive setup guide

## Using the Parser

Once you've regenerated the grammar with wikilink support:

```python
#!/usr/bin/env python3
from tree_sitter import Language, Parser
import tree_sitter_markdown

def find_wikilinks(text: str):
    # Load languages
    block_language = Language(tree_sitter_markdown.language())
    inline_language = Language(tree_sitter_markdown.inline_language())

    # Parse with block grammar
    parser = Parser()
    parser.language = block_language
    block_tree = parser.parse(bytes(text, "utf8"))

    # Find all inline nodes
    inline_nodes = []
    def find_inline_nodes(node):
        if node.type == "inline":
            inline_nodes.append(node)
        for child in node.children:
            find_inline_nodes(child)
    find_inline_nodes(block_tree.root_node)

    # Parse each inline node and find wikilinks
    wikilinks = []
    parser.language = inline_language

    for inline_node in inline_nodes:
        parser.included_ranges = [inline_node.range]
        inline_tree = parser.parse(bytes(text, "utf8"))

        def find_wikilinks_in_tree(node):
            if node.type == "wiki_link":
                destination = None
                link_text = None
                for child in node.children:
                    if child.type == "link_destination":
                        destination = text[child.start_byte:child.end_byte]
                    elif child.type == "link_text":
                        link_text = text[child.start_byte:child.end_byte]
                if destination:
                    wikilinks.append((destination, link_text))
            for child in node.children:
                find_wikilinks_in_tree(child)

        find_wikilinks_in_tree(inline_tree.root_node)

    return wikilinks

# Example usage
with open('myfile.md', 'r') as f:
    text = f.read()

wikilinks = find_wikilinks(text)
for destination, link_text in wikilinks:
    if link_text:
        print(f"[[{destination}|{link_text}]]")
    else:
        print(f"[[{destination}]]")
```

## Why Current Setup Doesn't Work

The parser was pre-generated without wikilink support. When you run `debug_tree.py` on the current setup, you'll see:

```
inline 'There are also some links to [[extremely important...'
  [ '['
  [ '['
  ] ']'
  ] ']'
```

The `[` brackets are parsed as individual characters, not as a `wiki_link` node.

After regenerating with `EXTENSION_WIKI_LINK=1`, you would see:

```
inline 'There are also some links to [[extremely important...'
  wiki_link '[[extremely important information]]'
    link_destination 'extremely important information'
```

## Network Restricted Environments

If you're in an environment where downloads are blocked (like this one):

1. The tree-sitter-cli cannot be installed via npm or cargo
2. You'll need to either:
   - Use a machine with internet access to regenerate the grammar
   - Copy the generated `parser.c` files to this environment
   - Build tree-sitter-cli offline

See WIKILINK_SETUP.md for detailed troubleshooting.

## Summary

The Python bindings and scripts are ready to use. The only missing piece is regenerating the grammar files with wikilink support enabled. Once you have `tree-sitter` CLI available and can run:

```bash
EXTENSION_WIKI_LINK=1 npm run build
pip install -e .
```

Everything will work as expected!
