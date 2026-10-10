"""Commands that change the VFS in memory: ``mkdir`` and ``mv``.

Nothing here ever writes to disk: the loaded tree is edited in place
and the CSV file it came from is left untouched.
"""

import time
from dataclasses import dataclass

from . import vfs
from .arguments import split_flags
from .errors import CommandError
from .session import lookup_message, lookup_reason

MKDIR_FLAGS = "p"
MV_FLAGS = ""
MIN_MV_OPERANDS = 2
SINGLE_SOURCE = 1
BUSY_NAMES = (vfs.CURRENT_NAME, vfs.PARENT_NAME)


@dataclass
class Destination:
    """Where a moved entry will land and what it would replace."""

    parent: object
    parent_parts: tuple
    name: str
    shown: str
    existing: object

    @property
    def parts(self):
        """Return the full path components of the new location."""
        return (*self.parent_parts, self.name)


def current_time():
    """Return the current time; a seam so tests can fix the clock."""
    return time.time()


def run_mkdir(args, session):
    """Create directories; ``-p`` also creates missing parents.

    Without ``-p`` the parent must exist and the name must be free. A
    failure for one operand is reported and the others still run.
    """
    letters, paths = split_flags("mkdir", args, MKDIR_FLAGS)
    session.require_vfs("mkdir")
    if not paths:
        raise CommandError("mkdir: missing operand")
    errors = []
    for path in paths:
        try:
            _mkdir(session, path, parents="p" in letters)
        except CommandError as exc:
            errors.append(str(exc))
    return "\n".join(errors)


def run_mv(args, session):
    """Move or rename entries.

    ``mv SRC DEST`` renames SRC, or moves it into DEST when DEST is an
    existing directory; ``mv SRC... DIR`` moves several entries into DIR.
    An existing file is overwritten by a file, like in UNIX.
    """
    _letters, paths = split_flags("mv", args, MV_FLAGS)
    session.require_vfs("mv")
    if not paths:
        raise CommandError("mv: missing file operand")
    if len(paths) < MIN_MV_OPERANDS:
        raise CommandError(
            f"mv: missing destination file operand after '{paths[0]}'"
        )
    *sources, target = paths
    if len(sources) > SINGLE_SOURCE and not _is_directory(session, target):
        raise CommandError(f"mv: target '{target}' is not a directory")
    errors = []
    for source in sources:
        try:
            _move_one(session, source, target)
        except CommandError as exc:
            errors.append(str(exc))
    return "\n".join(errors)


def _mkdir(session, path, parents):
    """Create one directory (and, with ``parents``, its missing parents)."""
    try:
        _parts, node = session.resolve(path)
    except vfs.PathNotFoundError:
        node = None
    except vfs.NotDirectoryError as exc:
        raise CommandError(lookup_message("mkdir", path, exc)) from exc
    if node is not None:
        if parents and node.is_dir:
            return
        raise CommandError(f"mkdir: {path}: File exists")
    if not parents:
        _create_directory(session, path)
        return
    for prefix in _prefixes(path):
        _make_missing(session, prefix)


def _prefixes(path):
    """Yield ``a``, ``a/b``, ``a/b/c`` for the path ``a/b/c``."""
    prefix = vfs.SEPARATOR if path.startswith(vfs.SEPARATOR) else ""
    for component in path.split(vfs.SEPARATOR):
        if not component:
            continue
        if prefix:
            prefix = prefix.rstrip(vfs.SEPARATOR) + vfs.SEPARATOR + component
        else:
            prefix = component
        yield prefix


def _make_missing(session, prefix):
    """Create ``prefix`` if it does not exist yet; it must be a folder."""
    try:
        _parts, node = session.resolve(prefix)
    except vfs.PathNotFoundError:
        _create_directory(session, prefix)
        return
    except vfs.NotDirectoryError as exc:
        raise CommandError(lookup_message("mkdir", prefix, exc)) from exc
    if not node.is_dir:
        raise CommandError(f"mkdir: {prefix}: Not a directory")


def _create_directory(session, path):
    """Create the directory ``path`` whose parent must already exist."""
    head, name = vfs.split_parent(path)
    try:
        _parts, parent = session.resolve(head)
    except vfs.VfsError as exc:
        raise CommandError(lookup_message("mkdir", path, exc)) from exc
    if not parent.is_dir:
        raise CommandError(f"mkdir: {path}: Not a directory")
    now = current_time()
    vfs.attach(parent, vfs.new_directory(name, now), now)


def _is_directory(session, path):
    """Return True if ``path`` names an existing directory."""
    try:
        _parts, node = session.resolve(path)
    except vfs.VfsError:
        return False
    return node.is_dir


def _move_one(session, source, target):
    """Move ``source`` to ``target``, enforcing the UNIX move rules."""
    src_parts, src_node = _find_source(session, source)
    dest = _plan_destination(session, source, target, src_parts)
    _check_location(source, src_parts, src_node, dest)
    _check_overwrite(source, src_node, dest)
    now = current_time()
    src_parent = vfs.find_node(session.vfs_root, src_parts[:-1])
    vfs.detach(src_parent, src_parts[-1], now)
    src_node.name = dest.name
    vfs.attach(dest.parent, src_node, now)
    session.relocate(src_parts, dest.parts)


def _find_source(session, source):
    """Resolve the entry to move; the root, ``.`` and ``..`` are refused."""
    try:
        parts, node = session.resolve(source)
    except vfs.VfsError as exc:
        raise CommandError(
            f"mv: cannot stat '{source}': {lookup_reason(exc)}"
        ) from exc
    last = source.rstrip(vfs.SEPARATOR).rpartition(vfs.SEPARATOR)[2]
    if not parts or last in BUSY_NAMES:
        raise CommandError(
            f"mv: cannot move '{source}': Device or resource busy"
        )
    return parts, node


def _plan_destination(session, source, target, src_parts):
    """Work out where ``source`` lands when moved to ``target``."""
    try:
        parts, node = session.resolve(target)
    except vfs.PathNotFoundError:
        return _new_name_destination(session, source, target)
    except vfs.NotDirectoryError as exc:
        raise CommandError(_move_failure(source, target, exc)) from exc
    if node.is_dir:
        name = src_parts[-1]
        shown = f"{target.rstrip(vfs.SEPARATOR)}/{name}"
        return Destination(node, parts, name, shown, node.children.get(name))
    parent = vfs.find_node(session.vfs_root, parts[:-1])
    return Destination(parent, parts[:-1], parts[-1], target, node)


def _new_name_destination(session, source, target):
    """Plan a move to a name that does not exist yet."""
    head, name = vfs.split_parent(target)
    try:
        parts, parent = session.resolve(head)
    except vfs.VfsError as exc:
        raise CommandError(_move_failure(source, target, exc)) from exc
    if not parent.is_dir:
        message = f"mv: cannot move '{source}' to '{target}': Not a directory"
        raise CommandError(message)
    return Destination(parent, parts, name, target, None)


def _move_failure(source, target, error):
    """Describe a failed destination lookup in the style of GNU mv."""
    return f"mv: cannot move '{source}' to '{target}': {lookup_reason(error)}"


def _check_location(source, src_parts, src_node, dest):
    """Refuse moving an entry onto itself or a folder into itself."""
    if dest.existing is src_node:
        raise CommandError(
            f"mv: '{source}' and '{dest.shown}' are the same file"
        )
    if src_node.is_dir and dest.parts[:len(src_parts)] == src_parts:
        raise CommandError(
            f"mv: cannot move '{source}' to a subdirectory of itself, "
            f"'{dest.shown}'"
        )


def _check_overwrite(source, src_node, dest):
    """Allow replacing only a file by a file or an empty folder by a folder."""
    existing = dest.existing
    if existing is None:
        return
    if existing.is_dir and not src_node.is_dir:
        raise CommandError(
            f"mv: cannot overwrite directory '{dest.shown}' with non-directory"
        )
    if src_node.is_dir and not existing.is_dir:
        raise CommandError(
            f"mv: cannot overwrite non-directory '{dest.shown}' "
            f"with directory '{source}'"
        )
    if existing.is_dir and existing.children:
        raise CommandError(
            f"mv: cannot move '{source}' to '{dest.shown}': Directory not empty"
        )
