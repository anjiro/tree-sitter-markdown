#!/usr/bin/env python3
"""
Example usage of MarkdownParser.

This demonstrates how to use the MarkdownParser class to parse markdown
documents and extract wikilinks and other inline content.
"""

from markdown_parser import MarkdownParser


def extract_wikilinks(tree):
    """Extract all wikilinks from a MarkdownTree."""
    wikilinks = []

    def visit_node(node):
        """Recursively visit nodes to find wikilinks."""
        if node.type == 'wiki_link':
            # Find the link_destination child
            for child in node.children:
                if child.type == 'link_destination':
                    wikilinks.append(child.text.decode('utf8'))
                    break

        for child in node.children:
            visit_node(child)

    # Visit all inline trees
    for inline_tree in tree.inline_trees():
        visit_node(inline_tree.root_node)

    return wikilinks


def extract_headings(tree):
    """Extract all headings from a MarkdownTree."""
    headings = []

    def visit_node(node):
        """Recursively visit nodes to find headings."""
        if node.type.startswith('atx_heading'):
            # Get the inline content
            for child in node.children:
                if child.type == 'inline':
                    headings.append({
                        'level': int(node.type[-1]) if node.type[-1].isdigit() else 1,
                        'text': child.text.decode('utf8')
                    })
                    break

        for child in node.children:
            visit_node(child)

    # Visit the block tree
    visit_node(tree.block_tree().root_node)

    return headings


def example_simple_parsing():
    """Example: Simple parsing with MarkdownParser."""
    print("Example 1: Simple parsing")
    print("-" * 50)

    markdown_text = b"""# My Document

This document has some [[wikilinks]] in it.

## Section 1

Here's [[another link]] to something interesting.

## Section 2

And [[one more]] for good measure.
"""

    parser = MarkdownParser()
    tree = parser.parse(markdown_text)

    if tree:
        wikilinks = extract_wikilinks(tree)
        print(f"Found {len(wikilinks)} wikilinks:")
        for link in wikilinks:
            print(f"  - [[{link}]]")

        headings = extract_headings(tree)
        print(f"\nFound {len(headings)} headings:")
        for heading in headings:
            indent = "  " * (heading['level'] - 1)
            print(f"{indent}{'#' * heading['level']} {heading['text']}")
    else:
        print("Failed to parse document")

    print()


def example_cursor_traversal():
    """Example: Traversing with MarkdownCursor."""
    print("Example 2: Cursor traversal")
    print("-" * 50)

    markdown_text = b"""# Title

Paragraph with **bold** and *italic* text.

And a [[wikilink]].
"""

    parser = MarkdownParser()
    tree = parser.parse(markdown_text)

    if tree:
        cursor = tree.walk()
        print("Tree structure:")

        def print_tree(depth=0):
            """Print the tree structure at current cursor position."""
            node = cursor.node()
            indent = "  " * depth
            text = node.text.decode('utf8')[:30].replace('\n', '\\n')
            is_inline = " (inline)" if cursor.is_inline() else ""
            print(f"{indent}{node.type}{is_inline}: {repr(text)}")

            if cursor.goto_first_child():
                print_tree(depth + 1)
                cursor.goto_parent()

            if cursor.goto_next_sibling():
                print_tree(depth)

        print_tree()
    else:
        print("Failed to parse document")

    print()


def example_table_parsing():
    """Example: Parsing tables with inline content."""
    print("Example 3: Table parsing")
    print("-" * 50)

    markdown_text = b"""| Name | Link |
|------|------|
| First | [[link-one]] |
| Second | [[link-two]] |
"""

    parser = MarkdownParser()
    tree = parser.parse(markdown_text)

    if tree:
        print(f"Number of inline trees: {len(tree.inline_trees())}")

        wikilinks = extract_wikilinks(tree)
        print(f"Wikilinks in table: {wikilinks}")

        # Show that we can access inline trees from table cells
        cursor = tree.walk()
        cursor.goto_first_child()  # section
        cursor.goto_first_child()  # pipe_table

        print("\nTable structure:")

        def show_table_structure(depth=0):
            """Print table structure."""
            node = cursor.node()
            indent = "  " * depth
            print(f"{indent}{node.type}")

            if cursor.goto_first_child():
                show_table_structure(depth + 1)
                cursor.goto_parent()

            if cursor.goto_next_sibling():
                show_table_structure(depth)

        show_table_structure()
    else:
        print("Failed to parse document")

    print()


def example_incremental_parsing():
    """Example: Incremental parsing with old tree."""
    print("Example 4: Incremental parsing")
    print("-" * 50)

    markdown_text1 = b"# Title\n\nOld text with [[old-link]].\n"
    markdown_text2 = b"# Title\n\nNew text with [[new-link]].\n"

    parser = MarkdownParser()

    # Parse initial document
    tree1 = parser.parse(markdown_text1)
    wikilinks1 = extract_wikilinks(tree1)
    print(f"First parse: {wikilinks1}")

    # Parse updated document (without old_tree for simplicity)
    tree2 = parser.parse(markdown_text2)
    wikilinks2 = extract_wikilinks(tree2)
    print(f"Second parse: {wikilinks2}")

    # In a real application, you would use tree.edit() and pass old_tree
    # to enable incremental parsing for better performance

    print()


def main():
    """Run all examples."""
    example_simple_parsing()
    example_cursor_traversal()
    example_table_parsing()
    example_incremental_parsing()


if __name__ == '__main__':
    main()
