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


class VfsError(Exception):
    """Raised when a VFS file cannot be read or is not well-formed."""


class VfsNode:
    """One file or directory in the in-memory VFS tree."""

    def __init__(self, name, is_dir, content=b""):
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.children = {} if is_dir else None


def load_vfs(path):
    """Parse a CSV-described VFS into an in-memory tree.

    Returns the root ``VfsNode`` (a directory). Raises ``VfsError``
    if the file cannot be read, its header does not match, or any
    row describes an invalid or conflicting entry.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
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
    return root


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


def _split_path(path):
    """Split a VFS path into safe components, or raise VfsError."""
    if not path or path.startswith("/") or path.endswith("/"):
        raise VfsError(f"invalid VFS path: {path!r}")
    parts = path.split("/")
    if any(not part or part == ".." for part in parts):
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
