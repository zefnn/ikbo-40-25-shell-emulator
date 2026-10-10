"""Navigation commands: ``cd`` and ``ls``."""

import math
from dataclasses import dataclass

from . import vfs
from .arguments import DASH, split_flags
from .errors import CommandError
from .formatting import (
    BLOCK_BYTES,
    current_user,
    format_mtime,
    human_size,
    join_block,
)
from .session import lookup_message

HIDDEN_PREFIX = "."
LS_FLAGS = "lha"
MAX_CD_ARGS = 1
SINGLE_TARGET = 1
DIR_PERMISSIONS = "drwxr-xr-x"
FILE_PERMISSIONS = "-rw-r--r--"
DIR_SIZE = 4096
DIR_BASE_LINKS = 2
FILE_LINKS = 1
COLUMN_ALIGN = "<><<><"


@dataclass
class LsOptions:
    """The flags accepted by ``ls``."""

    long_format: bool = False
    human: bool = False
    show_all: bool = False


def run_cd(args, session):
    """Change the working directory.

    Accepts absolute paths (``/a/b``), relative paths (``a/b``,
    ``../x``), ``.``, ``..``, ``~`` and no argument (both mean the
    VFS root) and ``-`` (the previous directory, which is printed).
    """
    if len(args) > MAX_CD_ARGS:
        raise CommandError("cd: too many arguments")
    session.require_vfs("cd")
    target = args[0] if args else vfs.HOME_TOKEN
    if target == DASH:
        destination = session.previous_cwd
        if destination is None:
            raise CommandError("cd: OLDPWD not set")
        output = vfs.format_path(destination)
    else:
        destination = _resolve_directory(session, target)
        output = ""
    session.change_dir(destination)
    return output


def run_ls(args, session):
    """List directory contents; ``-l``, ``-h`` and ``-a`` combine freely."""
    letters, paths = split_flags("ls", args, LS_FLAGS)
    options = LsOptions("l" in letters, "h" in letters, "a" in letters)
    session.require_vfs("ls")
    targets = paths or [vfs.CURRENT_NAME]
    errors, files, dirs = _collect_targets(session, targets)
    sections = []
    if files:
        entries = [(path, node) for path, _parts, node in files]
        sections.append(_render(entries, options, with_total=False))
    show_headers = len(paths) > SINGLE_TARGET
    for path, parts, node in dirs:
        entries = _dir_entries(session, parts, node, options)
        body = _render(entries, options, with_total=True)
        sections.append(join_block(f"{path}:", body) if show_headers else body)
    blocks = ["\n".join(errors)] if errors else []
    return "\n\n".join(blocks + [text for text in sections if text])


def _resolve_directory(session, target):
    """Resolve ``target`` for ``cd``, requiring that it is a directory."""
    try:
        parts, node = session.resolve(target)
    except vfs.PathNotFoundError as exc:
        raise CommandError(f"cd: no such file or directory: {target}") from exc
    except vfs.NotDirectoryError as exc:
        raise CommandError(f"cd: not a directory: {target}") from exc
    if not node.is_dir:
        raise CommandError(f"cd: not a directory: {target}")
    return parts


def _collect_targets(session, paths):
    """Look every path up; return (error lines, files, directories)."""
    errors, files, dirs = [], [], []
    for path in paths:
        try:
            parts, node = session.resolve(path)
        except vfs.VfsError as exc:
            errors.append(lookup_message("ls", path, exc))
            continue
        (dirs if node.is_dir else files).append((path, parts, node))
    return errors, files, dirs


def _dir_entries(session, parts, node, options):
    """Return the sorted ``(name, node)`` pairs shown for a directory."""
    entries = [
        (name, child)
        for name, child in node.children.items()
        if options.show_all or not name.startswith(HIDDEN_PREFIX)
    ]
    entries.sort(key=lambda item: (item[0].casefold(), item[0]))
    if options.show_all:
        parent = vfs.find_node(session.vfs_root, parts[:-1])
        dots = [(vfs.CURRENT_NAME, node), (vfs.PARENT_NAME, parent)]
        entries = dots + entries
    return entries


def _render(entries, options, with_total):
    """Format entries as plain names or as ``ls -l`` rows."""
    if not options.long_format:
        return "\n".join(name for name, _node in entries)
    rows = [_long_row(name, node, options) for name, node in entries]
    lines = _align_rows(rows) if rows else []
    if with_total:
        lines.insert(0, _total_line(entries, options))
    return "\n".join(lines)


def _long_row(name, node, options):
    """Build the seven ``ls -l`` columns for one entry."""
    if node.is_dir:
        permissions = DIR_PERMISSIONS
        subdirs = sum(child.is_dir for child in node.children.values())
        links = DIR_BASE_LINKS + subdirs
    else:
        permissions = FILE_PERMISSIONS
        links = FILE_LINKS
    size = _entry_size(node)
    shown_size = human_size(size) if options.human else str(size)
    owner = current_user()
    date = format_mtime(node.mtime)
    return (permissions, str(links), owner, owner, shown_size, date, name)


def _entry_size(node):
    """Return the size ``ls`` reports: content length, or a folder's 4096."""
    return DIR_SIZE if node.is_dir else len(node.content)


def _align_rows(rows):
    """Pad the first six columns to equal width and join each row."""
    columns = range(len(COLUMN_ALIGN))
    widths = [max(len(row[i]) for row in rows) for i in columns]
    lines = []
    for row in rows:
        cells = [f"{row[i]:{COLUMN_ALIGN[i]}{widths[i]}}" for i in columns]
        lines.append(" ".join([*cells, row[-1]]))
    return lines


def _total_line(entries, options):
    """Build the ``total`` line: allocated size in 1K blocks."""
    blocks = sum(
        math.ceil(_entry_size(node) / BLOCK_BYTES) for _name, node in entries
    )
    shown = human_size(blocks * BLOCK_BYTES) if options.human else str(blocks)
    return f"total {shown}"
