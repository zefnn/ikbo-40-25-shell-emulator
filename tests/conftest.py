"""Shared pytest fixtures: a small VFS built through the real loader."""

import base64
import csv

import pytest

from shellemu.session import Session
from shellemu.vfs import load_vfs

FIXED_MTIME = 1_700_000_000
LONG_TEXT = "".join(f"line {number}\n" for number in range(1, 16))

ENTRIES = [
    ("readme.txt", "file", b"Hello\n"),
    (".hidden", "file", b"secret\n"),
    ("My Notes.txt", "file", b"spaced\n"),
    ("docs", "dir", None),
    ("docs/notes.txt", "file", b"one\ntwo\nthree\n"),
    ("docs/long.txt", "file", LONG_TEXT.encode()),
    ("docs/.draft", "file", b"draft\n"),
    ("docs/projects/alpha/deep.txt", "file", b"deep\n"),
    ("data/small.bin", "file", bytes(range(256)) * 6),
    ("empty", "dir", None),
]


def write_vfs_csv(path, entries):
    """Write ``(path, type, bytes-or-None)`` entries as a VFS CSV."""
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "type", "content"])
        for entry_path, kind, content in entries:
            encoded = b"" if content is None else base64.b64encode(content)
            writer.writerow([entry_path, kind, encoded.decode()])


@pytest.fixture
def session(tmp_path):
    """Return a Session over the sample VFS, positioned at the root."""
    csv_path = tmp_path / "vfs.csv"
    write_vfs_csv(csv_path, ENTRIES)
    root = load_vfs(str(csv_path))
    stamp_all(root)
    return Session(root)


def stamp_all(node):
    """Give every node the same fixed modification time."""
    node.mtime = FIXED_MTIME
    if node.is_dir:
        for child in node.children.values():
            stamp_all(child)
