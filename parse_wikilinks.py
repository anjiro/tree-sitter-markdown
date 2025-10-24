#!/usr/bin/env python3
"""
Parse wikilinks from a Markdown document using tree-sitter-markdown.

This script uses the MarkdownParser class to parse markdown documents
and extract all wikilinks.
"""

import sys
from markdown_parser import MarkdownParser


def extract_wikilinks(node):
    """Recursively extract all wikilink destinations from the parse tree."""
    wikilinks = []

    if node.type == 'wiki_link':
        # Find the link_destination child
        for child in node.children:
            if child.type == 'link_destination':
                link_text = child.text.decode('utf8')
                wikilinks.append(link_text)
                break

    # Recurse into children
    for child in node.children:
        wikilinks.extend(extract_wikilinks(child))

    return wikilinks


def parse_markdown_wikilinks(markdown_text):
    """
    Parse a markdown document and extract all wikilinks.

    Args:
        markdown_text: String containing the markdown document

    Returns:
        List of wikilink destinations (without the [[ ]] brackets)
    """
    text_bytes = bytes(markdown_text, 'utf8')

    # Create parser and parse document
    parser = MarkdownParser()
    tree = parser.parse(text_bytes)

    if tree is None:
        return []

    # Extract wikilinks from all inline trees
    wikilinks = []
    for inline_tree in tree.inline_trees():
        wikilinks.extend(extract_wikilinks(inline_tree.root_node))

    return wikilinks


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_wikilinks.py <markdown_file>")
        print("\nExample:")
        print("  python parse_wikilinks.py myfile.md")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, 'r') as f:
            markdown_text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)

    wikilinks = parse_markdown_wikilinks(markdown_text)

    print(f"Found {len(wikilinks)} wikilink(s) in {filename}:")
    for i, link in enumerate(wikilinks, 1):
        print(f"  {i}. [[{link}]]")


if __name__ == '__main__':
    main()
