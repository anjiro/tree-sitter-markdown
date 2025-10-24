#!/usr/bin/env python3
"""
Test script for MarkdownParser.

This tests the MarkdownParser class to ensure it correctly handles
the two-stage parsing process and provides a convenient API.
"""

from markdown_parser import MarkdownParser, MarkdownTree, MarkdownCursor


def test_basic_parsing():
    """Test basic parsing of a markdown document."""
    print("Test 1: Basic parsing")
    text = b"# title\n\nInline [content].\n"
    parser = MarkdownParser()
    tree = parser.parse(text)

    assert tree is not None, "Parser should return a tree"
    assert tree.block_tree() is not None, "Should have block tree"
    assert len(tree.inline_trees()) > 0, "Should have inline trees"

    print("  ✓ Basic parsing works")


def test_cursor_navigation():
    """Test cursor navigation through block and inline content."""
    print("\nTest 2: Cursor navigation")
    text = b"# title\n\nInline [content].\n"
    parser = MarkdownParser()
    tree = parser.parse(text)

    cursor = tree.walk()
    assert cursor.node().type == "document", f"Root should be document, got {cursor.node().type}"

    # Navigate to section
    assert cursor.goto_first_child(), "Should have first child"
    assert cursor.node().type == "section", f"Should be section, got {cursor.node().type}"

    # Navigate to heading
    assert cursor.goto_first_child(), "Section should have children"
    assert cursor.node().type == "atx_heading", f"Should be atx_heading, got {cursor.node().type}"

    # Navigate to paragraph
    assert cursor.goto_next_sibling(), "Should have sibling"
    assert cursor.node().type == "paragraph", f"Should be paragraph, got {cursor.node().type}"

    # Navigate to inline content
    assert cursor.goto_first_child(), "Paragraph should have inline child"
    assert cursor.node().type == "inline", f"Should be inline, got {cursor.node().type}"

    # This should descend into the inline tree
    assert cursor.goto_first_child(), "Inline should have children"
    node_type = cursor.node().type
    assert node_type == "shortcut_link" or cursor.is_inline(), \
        f"Should be in inline content, got {node_type}"

    print("  ✓ Cursor navigation works")


def test_wikilinks():
    """Test parsing wikilinks."""
    print("\nTest 3: Wikilink parsing")
    text = b"# Document\n\nHere is a [[wikilink]] and [[another one]].\n"
    parser = MarkdownParser()
    tree = parser.parse(text)

    assert tree is not None, "Should parse successfully"

    # Find inline nodes and check for wikilinks
    block_root = tree.block_tree().root_node
    wikilinks_found = []

    def find_wikilinks(node):
        if node.type == "wiki_link":
            # Get the link destination
            for child in node.children:
                if child.type == "link_destination":
                    wikilinks_found.append(child.text.decode('utf8'))
        for child in node.children:
            find_wikilinks(child)

    # Check inline trees
    for inline_tree in tree.inline_trees():
        find_wikilinks(inline_tree.root_node)

    assert len(wikilinks_found) == 2, f"Should find 2 wikilinks, found {len(wikilinks_found)}"
    assert "wikilink" in wikilinks_found, "Should find 'wikilink'"
    assert "another one" in wikilinks_found, "Should find 'another one'"

    print(f"  ✓ Found wikilinks: {wikilinks_found}")


def test_table_parsing():
    """Test parsing tables with inline content."""
    print("\nTest 4: Table parsing")
    text = b"| foo |\n| --- |\n| *bar*|\n"
    parser = MarkdownParser()
    tree = parser.parse(text)

    assert tree is not None, "Should parse table successfully"
    assert len(tree.inline_trees()) > 0, "Table cells should have inline trees"

    # Navigate with cursor
    cursor = tree.walk()
    assert cursor.goto_first_child(), "Should have document child"
    assert cursor.goto_first_child(), "Should have section"
    assert cursor.node().type == "pipe_table", f"Should be pipe_table, got {cursor.node().type}"

    print("  ✓ Table parsing works")


def test_inline_tree_access():
    """Test accessing inline trees through parent nodes."""
    print("\nTest 5: Inline tree access")
    text = b"# title\n\nInline [content].\n"
    parser = MarkdownParser()
    tree = parser.parse(text)

    # Find the inline node in block tree
    block_root = tree.block_tree().root_node
    section = block_root.child(0)
    paragraph = section.child(1)
    inline_node = paragraph.child(0)

    assert inline_node.type == "inline", f"Should be inline node, got {inline_node.type}"

    # Access its inline tree
    inline_tree = tree.inline_tree(inline_node)
    assert inline_tree is not None, "Should have inline tree for inline node"

    # Check inline tree has parsed content
    inline_root = inline_tree.root_node
    assert inline_root.child_count > 0, "Inline tree should have children"

    print("  ✓ Inline tree access works")


def test_cursor_with_inline_traversal():
    """Test that cursor properly traverses into inline content."""
    print("\nTest 6: Cursor inline traversal")
    text = b"Text with [[wikilink]].\n"
    parser = MarkdownParser()
    tree = parser.parse(text)

    cursor = tree.walk()

    # Navigate to inline content
    assert cursor.goto_first_child(), "Should have first child (section)"
    assert cursor.goto_first_child(), "Should have first child (paragraph)"
    assert cursor.goto_first_child(), "Should have first child (inline)"

    # Now we should be at inline node in block tree
    assert cursor.node().type == "inline", "Should be at inline node"
    assert not cursor.is_inline(), "Should not be in inline tree yet"

    # Go to first child should descend into inline tree
    if cursor.goto_first_child():
        # We should now be in the inline tree
        print(f"  Current node type: {cursor.node().type}")
        # Could be wiki_link or other inline content
        assert cursor.is_inline() or cursor.node().type in ("wiki_link", "."), \
            f"Should be in inline content, got {cursor.node().type}, is_inline={cursor.is_inline()}"

    print("  ✓ Cursor inline traversal works")


def main():
    """Run all tests."""
    print("Testing MarkdownParser\n" + "=" * 50)

    try:
        test_basic_parsing()
        test_cursor_navigation()
        test_wikilinks()
        test_table_parsing()
        test_inline_tree_access()
        test_cursor_with_inline_traversal()

        print("\n" + "=" * 50)
        print("All tests passed! ✓")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()
