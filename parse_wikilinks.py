#!/usr/bin/env python3
"""
Script to parse wikilinks from a markdown document using tree-sitter-markdown.
"""

import sys
from tree_sitter import Language, Parser
import tree_sitter_markdown


def find_wikilinks(text: str):
    """
    Parse markdown text and extract all wikilinks.

    Args:
        text: Markdown text to parse

    Returns:
        List of tuples (destination, display_text) where display_text may be None
    """
    # Load the block and inline languages
    block_language = Language(tree_sitter_markdown.language())
    inline_language = Language(tree_sitter_markdown.inline_language())

    # Create parser and parse with block grammar
    parser = Parser()
    parser.language = block_language
    block_tree = parser.parse(bytes(text, "utf8"))

    # Find all inline nodes in the block tree
    inline_nodes = []

    def find_inline_nodes(node):
        """Recursively find all 'inline' nodes in the tree."""
        if node.type == "inline":
            inline_nodes.append(node)
        for child in node.children:
            find_inline_nodes(child)

    find_inline_nodes(block_tree.root_node)

    # Parse each inline node with the inline grammar
    wikilinks = []
    parser.language = inline_language

    for inline_node in inline_nodes:
        # Create ranges for the inline content
        ranges = [inline_node.range]

        # Parse the inline content
        parser.included_ranges = ranges
        inline_tree = parser.parse(bytes(text, "utf8"))

        # Find wikilinks in the inline tree
        def find_wikilinks_in_tree(node):
            """Recursively find all 'wiki_link' nodes."""
            if node.type == "wiki_link":
                # Extract destination and optional text
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_wikilinks.py <markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    wikilinks = find_wikilinks(text)

    print(f"Found {len(wikilinks)} wikilink(s):")
    for i, (destination, link_text) in enumerate(wikilinks, 1):
        if link_text:
            print(f"{i}. [[{destination}|{link_text}]]")
            print(f"   - Destination: {destination}")
            print(f"   - Display text: {link_text}")
        else:
            print(f"{i}. [[{destination}]]")
            print(f"   - Destination: {destination}")


if __name__ == "__main__":
    main()
