"""In-memory virtual file system, loaded from a CSV description.

The CSV has exactly three columns: ``path``, ``type`` (``file`` or
``dir``) and ``content`` (base64, only meaningful for files). Paths
use ``/`` to express nesting, e.g. ``docs/notes/todo.txt``; a file's
parent directories are created automatically, so only directories
that would otherwise stay empty need their own explicit row.

Nothing here ever writes to disk: the CSV is read once and turned
into a tree of ``VfsNode`` objects kept entirely in memory.
"""

import base64
import csv
import io
from pathlib import Path

REQUIRED_FIELDS = ["path", "type", "content"]
CURRENT_NAME = "."
PARENT_NAME = ".."
HOME_TOKEN = "~"
SEPARATOR = "/"
SKIPPED_SEGMENTS = ("", CURRENT_NAME)


class VfsError(Exception):
    """Raised when a VFS file cannot be read or is not well-formed."""


class PathNotFoundError(VfsError):
    """Raised when a path names an entry that does not exist."""


class NotDirectoryError(VfsError):
    """Raised when a path goes through a file as if it were a folder."""


class VfsNode:
    """One file or directory in the in-memory VFS tree."""

    def __init__(self, name, is_dir, content=b"", mtime=0.0):
        """Create a node; folders get a children dict, files get None."""
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.mtime = mtime
        self.children = {} if is_dir else None


def load_vfs(path):
    """Parse a CSV-described VFS into an in-memory tree.

    Returns the root ``VfsNode`` (a directory). Every node is stamped
    with the CSV file's modification time. Raises ``VfsError`` if the
    file cannot be read, its header does not match, or any row
    describes an invalid or conflicting entry.
    """
    try:
        source = Path(path)
        text = source.read_text(encoding="utf-8")
        mtime = source.stat().st_mtime
    except (OSError, UnicodeDecodeError) as exc:
        raise VfsError(f"cannot read VFS file: {exc}") from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != REQUIRED_FIELDS:
        raise VfsError(
            f"expected CSV header {REQUIRED_FIELDS}, got {reader.fieldnames}"
        )

    root = VfsNode(name="", is_dir=True)
    seen_paths = set()
    for row in reader:
        _add_entry(root, row, seen_paths)
    _stamp(root, mtime)
    return root


def format_path(parts):
    """Render path components as an absolute path, e.g. ``/docs/a``."""
    return SEPARATOR + SEPARATOR.join(parts)


def find_node(root, parts):
    """Return the node at the exact component list ``parts``.

    Raises ``PathNotFoundError`` or ``NotDirectoryError``.
    """
    node = root
    for part in parts:
        node = _child(node, part)
    return node


def resolve(root, cwd_parts, path):
    """Resolve a user-typed path to a ``(parts, node)`` pair.

    ``path`` may be absolute (``/a/b``), home-relative (``~`` or
    ``~/a``; the VFS root plays the role of home) or relative to
    ``cwd_parts``. ``.`` is skipped, ``..`` steps to the parent (and
    stays put at the root), repeated slashes collapse. Raises
    ``PathNotFoundError`` or ``NotDirectoryError`` as the walk fails.
    """
    if path == HOME_TOKEN or path.startswith(HOME_TOKEN + SEPARATOR):
        segments = path[len(HOME_TOKEN):].split(SEPARATOR)
    elif path.startswith(SEPARATOR):
        segments = path.split(SEPARATOR)
    else:
        segments = [*cwd_parts, *path.split(SEPARATOR)]

    parts = []
    nodes = [root]
    for segment in segments:
        if segment == PARENT_NAME:
            if parts:
                parts.pop()
                nodes.pop()
        elif segment not in SKIPPED_SEGMENTS:
            nodes.append(_child(nodes[-1], segment))
            parts.append(segment)
    return tuple(parts), nodes[-1]


def split_parent(path):
    """Split ``path`` into ``(parent path, last name)``.

    A path without a directory part has the working directory (``.``)
    as its parent; ``/name`` has the root (``/``).
    """
    trimmed = path.rstrip(SEPARATOR)
    head, _separator, name = trimmed.rpartition(SEPARATOR)
    if head:
        return head, name
    anchor = SEPARATOR if trimmed.startswith(SEPARATOR) else CURRENT_NAME
    return anchor, name


def new_directory(name, mtime):
    """Return an empty directory node stamped with ``mtime``."""
    return VfsNode(name, is_dir=True, mtime=mtime)


def attach(parent, node, mtime):
    """Put ``node`` into ``parent`` under its own name.

    Replaces any entry with the same name and touches the parent.
    """
    parent.children[node.name] = node
    parent.mtime = mtime


def detach(parent, name, mtime):
    """Remove and return ``parent``'s child ``name``; touch the parent."""
    node = parent.children.pop(name)
    parent.mtime = mtime
    return node


def count_entries(node):
    """Return ``(file_count, dir_count)`` for the subtree at node."""
    files = dirs = 0
    for child in node.children.values():
        if child.is_dir:
            dirs += 1
            child_files, child_dirs = count_entries(child)
            files += child_files
            dirs += child_dirs
        else:
            files += 1
    return files, dirs


def _child(node, name):
    """Return the named child of a directory node, or raise."""
    if not node.is_dir:
        raise NotDirectoryError(name)
    child = node.children.get(name)
    if child is None:
        raise PathNotFoundError(name)
    return child


def _stamp(node, mtime):
    """Set the modification time of ``node`` and everything under it."""
    node.mtime = mtime
    if node.is_dir:
        for child in node.children.values():
            _stamp(child, mtime)


def _split_path(path):
    """Split a VFS path into safe components, or raise VfsError.

    The names ``.`` and ``..`` are reserved for navigation, so they
    cannot be used as the name of a real entry.
    """
    if not path or path.startswith(SEPARATOR) or path.endswith(SEPARATOR):
        raise VfsError(f"invalid VFS path: {path!r}")
    parts = path.split(SEPARATOR)
    reserved = (CURRENT_NAME, PARENT_NAME)
    if any(not part or part in reserved for part in parts):
        raise VfsError(f"invalid VFS path: {path!r}")
    return parts


def _ensure_dir(root, parts):
    """Walk ``parts`` from root, creating directory nodes as needed."""
    node = root
    for part in parts:
        child = node.children.get(part)
        if child is None:
            child = VfsNode(name=part, is_dir=True)
            node.children[part] = child
        elif not child.is_dir:
            raise VfsError(f"'{part}' is both a file and a directory")
        node = child
    return node


def _add_entry(root, row, seen_paths):
    """Insert one CSV row into the tree, validating it along the way."""
    path = row["path"]
    if path in seen_paths:
        raise VfsError(f"duplicate VFS path: {path!r}")
    seen_paths.add(path)

    parts = _split_path(path)
    parent = _ensure_dir(root, parts[:-1])
    name = parts[-1]
    existing = parent.children.get(name)

    entry_type = row["type"]
    if entry_type == "dir":
        if existing is not None and not existing.is_dir:
            raise VfsError(f"'{path}' is both a file and a directory")
        parent.children.setdefault(name, VfsNode(name=name, is_dir=True))
    elif entry_type == "file":
        if existing is not None:
            raise VfsError(f"'{path}' is listed more than once")
        content = _decode_content(path, row["content"])
        parent.children[name] = VfsNode(name, is_dir=False, content=content)
    else:
        raise VfsError(f"unknown VFS entry type: {entry_type!r}")


def _decode_content(path, encoded):
    """Decode a file's base64 content field; an empty field is b""."""
    if not encoded:
        return b""
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise VfsError(f"invalid base64 content for {path!r}: {exc}") from exc
