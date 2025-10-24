"""
Markdown parser for tree-sitter-markdown.

This module provides a convenience wrapper around the block and inline grammars,
similar to the Rust bindings.
"""

from typing import Optional, List, Dict, Callable, Tuple
import tree_sitter
import tree_sitter_markdown


class MarkdownTree:
    """
    An object that holds a combined markdown tree.

    This represents the parsed structure of a markdown document, with both
    block-level and inline-level trees.
    """

    def __init__(self, block_tree: tree_sitter.Tree, inline_trees: List[tree_sitter.Tree],
                 inline_indices: Dict[int, int]):
        """
        Initialize a MarkdownTree.

        Args:
            block_tree: The block-level parse tree
            inline_trees: List of inline parse trees
            inline_indices: Mapping from node IDs to inline tree indices
        """
        self._block_tree = block_tree
        self._inline_trees = inline_trees
        self._inline_indices = inline_indices

    def block_tree(self) -> tree_sitter.Tree:
        """Returns the block tree for the parsed document."""
        return self._block_tree

    def inline_tree(self, parent_node: tree_sitter.Node) -> Optional[tree_sitter.Tree]:
        """
        Returns the inline tree for the given inline node.

        Args:
            parent_node: A node with type 'inline' or 'pipe_table_cell'

        Returns:
            The inline tree for this node, or None if not found
        """
        index = self._inline_indices.get(parent_node.id)
        if index is None:
            return None
        return self._inline_trees[index]

    def inline_trees(self) -> List[tree_sitter.Tree]:
        """Returns the list of all inline trees."""
        return self._inline_trees

    def walk(self) -> 'MarkdownCursor':
        """Create a new MarkdownCursor starting from the root of the tree."""
        return MarkdownCursor(self)


class MarkdownCursor:
    """
    A stateful object for walking a MarkdownTree efficiently.

    This exposes similar methods to TreeCursor, but abstracts away the
    double block/inline structure of MarkdownTree.
    """

    def __init__(self, markdown_tree: MarkdownTree):
        """
        Initialize a MarkdownCursor.

        Args:
            markdown_tree: The MarkdownTree to traverse
        """
        self._markdown_tree = markdown_tree
        self._block_cursor = markdown_tree.block_tree().walk()
        self._inline_cursor: Optional[tree_sitter.TreeCursor] = None

    def node(self) -> tree_sitter.Node:
        """Get the cursor's current Node."""
        if self._inline_cursor is not None:
            return self._inline_cursor.node
        return self._block_cursor.node

    def is_inline(self) -> bool:
        """Returns True if the current node is from the inline language."""
        return self._inline_cursor is not None

    def field_name(self) -> Optional[str]:
        """
        Get the field name of this tree cursor's current node.

        You will need to call is_inline() to find out if the current node
        is an inline or block node.
        """
        if self._inline_cursor is not None:
            return self._inline_cursor.current_field_name()
        return self._block_cursor.current_field_name()

    def _move_to_inline_tree(self) -> bool:
        """Move from a block node to its associated inline tree if it exists."""
        node = self._block_cursor.node
        if node.type in ('inline', 'pipe_table_cell'):
            inline_tree = self._markdown_tree.inline_tree(node)
            if inline_tree is not None:
                self._inline_cursor = inline_tree.walk()
                return True
        return False

    def _move_to_block_tree(self):
        """Move from inline tree back to block tree."""
        self._inline_cursor = None

    def goto_first_child(self) -> bool:
        """
        Move this cursor to the first child of its current node.

        Returns True if the cursor successfully moved, False if there were no children.
        If the cursor is at a node in the block tree with an associated inline tree,
        it will descend into the inline tree.
        """
        if self._inline_cursor is not None:
            return self._inline_cursor.goto_first_child()

        # Try to move to inline tree first
        if self._move_to_inline_tree():
            if not self._inline_cursor.goto_first_child():
                self._move_to_block_tree()
                return False
            return True

        return self._block_cursor.goto_first_child()

    def goto_parent(self) -> bool:
        """
        Move this cursor to the parent of its current node.

        Returns True if the cursor successfully moved, False if there was no parent.
        If the cursor moves to the root node of an inline tree, it ascends to the
        associated node in the block tree.
        """
        if self._inline_cursor is not None:
            result = self._inline_cursor.goto_parent()
            # Check if we're at the root of the inline tree
            if self._inline_cursor.node.parent is None:
                self._move_to_block_tree()
            return True

        return self._block_cursor.goto_parent()

    def goto_next_sibling(self) -> bool:
        """
        Move this cursor to the next sibling of its current node.

        Returns True if the cursor successfully moved, False if there was no next sibling.
        """
        if self._inline_cursor is not None:
            return self._inline_cursor.goto_next_sibling()
        return self._block_cursor.goto_next_sibling()

    def goto_first_child_for_byte(self, byte_index: int) -> Optional[int]:
        """
        Move to the first child that extends beyond the given byte offset.

        Args:
            byte_index: The byte offset

        Returns:
            The index of the child node if found, None otherwise
        """
        if self._inline_cursor is not None:
            return self._inline_cursor.goto_first_child_for_byte(byte_index)

        if self._move_to_inline_tree():
            return self._inline_cursor.goto_first_child_for_byte(byte_index)

        return self._block_cursor.goto_first_child_for_byte(byte_index)

    def goto_first_child_for_point(self, point: Tuple[int, int]) -> Optional[int]:
        """
        Move to the first child that extends beyond the given point.

        Args:
            point: A tuple of (row, column)

        Returns:
            The index of the child node if found, None otherwise
        """
        if self._inline_cursor is not None:
            return self._inline_cursor.goto_first_child_for_point(point)

        if self._move_to_inline_tree():
            return self._inline_cursor.goto_first_child_for_point(point)

        return self._block_cursor.goto_first_child_for_point(point)


class MarkdownParser:
    """
    A parser that produces MarkdownTrees.

    This is a convenience wrapper around the block and inline languages
    that handles the two-stage parsing process automatically.
    """

    def __init__(self):
        """Initialize a MarkdownParser with both block and inline languages."""
        self._parser = tree_sitter.Parser()
        self._block_language = tree_sitter.Language(tree_sitter_markdown.language())
        self._inline_language = tree_sitter.Language(tree_sitter_markdown.inline_language())

    def parse(self, text: bytes, old_tree: Optional[MarkdownTree] = None) -> Optional[MarkdownTree]:
        """
        Parse UTF8-encoded markdown text.

        Args:
            text: The UTF8-encoded text to parse
            old_tree: A previous syntax tree parsed from the same document.
                     If provided and the text has changed, you should call
                     edit() on the old_tree first.

        Returns:
            A MarkdownTree if parsing succeeded, None if parsing failed
        """
        # Parse with block grammar first
        self._parser.language = self._block_language
        if old_tree:
            block_tree = self._parser.parse(text, old_tree=old_tree.block_tree())
        else:
            block_tree = self._parser.parse(text)

        if block_tree is None:
            return None

        # Prepare storage for inline trees
        inline_trees: List[tree_sitter.Tree] = []
        inline_indices: Dict[int, int] = {}

        # Set up for inline parsing
        self._parser.language = self._inline_language

        # Find all inline and pipe_table_cell nodes
        inline_nodes = self._collect_inline_nodes(block_tree.root_node)

        for i, node in enumerate(inline_nodes):
            # Calculate ranges for this inline node
            ranges = self._calculate_inline_ranges(node)

            if not ranges:
                continue

            # Parse with inline grammar
            self._parser.included_ranges = ranges
            if old_tree and i < len(old_tree.inline_trees()):
                inline_tree = self._parser.parse(text, old_tree=old_tree.inline_trees()[i])
            else:
                inline_tree = self._parser.parse(text)

            if inline_tree is None:
                return None

            inline_trees.append(inline_tree)
            inline_indices[node.id] = i

        return MarkdownTree(block_tree, inline_trees, inline_indices)

    def _collect_inline_nodes(self, root_node: tree_sitter.Node) -> List[tree_sitter.Node]:
        """
        Recursively collect all 'inline' and 'pipe_table_cell' nodes.

        This mimics the traversal logic in the Rust implementation.
        """
        inline_nodes = []
        cursor = root_node.walk()

        reached_root = False
        while not reached_root:
            node = cursor.node

            # Check if current node is an inline node
            if node.type in ('inline', 'pipe_table_cell'):
                inline_nodes.append(node)
                # Don't descend into inline nodes
                # Try to go to next sibling
                if not cursor.goto_next_sibling():
                    # No sibling, go up
                    while not cursor.goto_next_sibling():
                        if not cursor.goto_parent():
                            reached_root = True
                            break
            elif cursor.goto_first_child():
                # Descend into children
                continue
            else:
                # No children, try next sibling
                if not cursor.goto_next_sibling():
                    # No sibling, go up
                    while not cursor.goto_next_sibling():
                        if not cursor.goto_parent():
                            reached_root = True
                            break

        return inline_nodes

    def _calculate_inline_ranges(self, node: tree_sitter.Node) -> List[tree_sitter.Range]:
        """
        Calculate the byte ranges for parsing inline content.

        This excludes any named children (which are already parsed by block grammar).
        """
        ranges = []
        start_byte = node.start_byte
        start_point = node.start_point

        # Check if node has children
        if node.child_count > 0:
            for child in node.children:
                # Skip unnamed children
                if not child.is_named:
                    continue

                # Add range up to this child
                if start_byte < child.start_byte:
                    ranges.append(tree_sitter.Range(
                        start_point,
                        child.start_point,
                        start_byte,
                        child.start_byte
                    ))

                # Update start to after this child
                start_byte = child.end_byte
                start_point = child.end_point

        # Add final range
        if start_byte < node.end_byte:
            ranges.append(tree_sitter.Range(
                start_point,
                node.end_point,
                start_byte,
                node.end_byte
            ))

        return ranges if ranges else [tree_sitter.Range(
            node.start_point,
            node.end_point,
            node.start_byte,
            node.end_byte
        )]
