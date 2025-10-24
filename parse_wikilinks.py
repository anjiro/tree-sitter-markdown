#!/usr/bin/env python3
"""
Parse wikilinks from a Markdown document using tree-sitter-markdown.

This script demonstrates how to:
1. Parse a markdown document with the block grammar
2. Extract inline content ranges
3. Parse inline content with the inline grammar (which includes wikilink support)
4. Extract all wikilinks from the document
"""

import sys
import tree_sitter
import tree_sitter_markdown


def collect_inline_ranges(node):
    """Recursively collect all 'inline' node ranges from the parse tree."""
    ranges = []
    if node.type == 'inline':
        ranges.append((node.start_byte, node.end_byte))
    for child in node.children:
        ranges.extend(collect_inline_ranges(child))
    return ranges


def extract_wikilinks(node, text_bytes):
    """Recursively extract all wikilink destinations from the parse tree."""
    wikilinks = []

    if node.type == 'wiki_link':
        # Find the link_destination child
        for child in node.children:
            if child.type == 'link_destination':
                link_text = text_bytes[child.start_byte:child.end_byte].decode('utf8')
                wikilinks.append(link_text)
                break

    # Recurse into children
    for child in node.children:
        wikilinks.extend(extract_wikilinks(child, text_bytes))

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

    # Create language objects
    markdown_lang = tree_sitter.Language(tree_sitter_markdown.language())
    inline_lang = tree_sitter.Language(tree_sitter_markdown.inline_language())

    # Step 1: Parse with block grammar to identify inline content
    block_parser = tree_sitter.Parser()
    block_parser.language = markdown_lang
    block_tree = block_parser.parse(text_bytes)

    # Step 2: Collect ranges of inline content
    inline_ranges = collect_inline_ranges(block_tree.root_node)

    # Step 3: Parse inline content with inline grammar
    inline_parser = tree_sitter.Parser()
    inline_parser.language = inline_lang

    # Convert byte ranges to tree-sitter Range objects
    ranges = [tree_sitter.Range((0, start_byte), (0, end_byte), start_byte, end_byte)
              for start_byte, end_byte in inline_ranges]

    inline_parser.included_ranges = ranges
    inline_tree = inline_parser.parse(text_bytes)

    # Step 4: Extract wikilinks
    wikilinks = extract_wikilinks(inline_tree.root_node, text_bytes)

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
