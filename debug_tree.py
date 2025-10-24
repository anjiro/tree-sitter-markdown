#!/usr/bin/env python3
"""Debug script to see the parse tree."""

import sys
from tree_sitter import Language, Parser
import tree_sitter_markdown


def print_tree(node, text, indent=0):
    """Print the parse tree."""
    node_text = text[node.start_byte:node.end_byte]
    if len(node_text) > 50:
        node_text = node_text[:50] + "..."
    node_text = repr(node_text)
    print("  " * indent + f"{node.type} {node_text}")
    for child in node.children:
        print_tree(child, text, indent + 1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_tree.py <markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Parse with block grammar
    block_language = Language(tree_sitter_markdown.language())
    parser = Parser()
    parser.language = block_language
    block_tree = parser.parse(bytes(text, "utf8"))

    print("=== BLOCK TREE ===")
    print_tree(block_tree.root_node, text)

    # Parse with inline grammar
    inline_language = Language(tree_sitter_markdown.inline_language())
    parser.language = inline_language
    inline_tree = parser.parse(bytes(text, "utf8"))

    print("\n=== INLINE TREE (full text) ===")
    print_tree(inline_tree.root_node, text)


if __name__ == "__main__":
    main()
