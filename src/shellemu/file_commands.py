"""File-reading commands: ``cat`` and ``tail``."""

from . import vfs
from .arguments import DASH, split_flags
from .errors import CommandError
from .formatting import join_block
from .session import lookup_message

LINES_FLAG = "-n"
DEFAULT_TAIL_LINES = 10
SINGLE_FILE = 1


def run_cat(args, session):
    """Print the contents of the given files, one after another."""
    _letters, paths = split_flags("cat", args, "")
    session.require_vfs("cat")
    if not paths:
        raise CommandError("cat: missing file operand")
    chunks = []
    for path in paths:
        try:
            chunks.append(_read_text(session, "cat", path))
        except CommandError as exc:
            chunks.append(f"{exc}\n")
    return "".join(chunks).removesuffix("\n")


def run_tail(args, session):
    """Print the last lines (default 10) of each given file.

    ``-n N``, ``-nN`` and ``-N`` choose the number of lines. With more
    than one file each block is introduced by ``==> name <==``.
    """
    count, paths = _parse_tail_args(args)
    session.require_vfs("tail")
    if not paths:
        raise CommandError("tail: missing file operand")
    show_headers = len(paths) > SINGLE_FILE
    blocks = []
    for path in paths:
        try:
            text = _read_text(session, "tail", path)
        except CommandError as exc:
            blocks.append(str(exc))
            continue
        body = "\n".join(_last_lines(text, count))
        if show_headers:
            body = join_block(f"==> {path} <==", body)
        blocks.append(body)
    return "\n\n".join(blocks)


def _parse_tail_args(args):
    """Return ``(line_count, paths)`` parsed from tail's arguments."""
    count = DEFAULT_TAIL_LINES
    paths = []
    pending = list(args)
    while pending:
        arg = pending.pop(0)
        if arg == LINES_FLAG:
            if not pending:
                raise CommandError("tail: option requires an argument -- 'n'")
            count = _parse_count(pending.pop(0))
        elif arg.startswith(LINES_FLAG):
            count = _parse_count(arg[len(LINES_FLAG):])
        elif arg[len(DASH):].isdecimal() and arg.startswith(DASH):
            count = _parse_count(arg[len(DASH):])
        elif arg.startswith(DASH) and arg != DASH:
            raise CommandError(f"tail: invalid option -- '{arg[1]}'")
        else:
            paths.append(arg)
    return count, paths


def _parse_count(text):
    """Convert a line count typed by the user, or raise CommandError."""
    if not (text.isascii() and text.isdecimal()):
        raise CommandError(f"tail: invalid number of lines: '{text}'")
    return int(text)


def _last_lines(text, count):
    """Return the final ``count`` lines of ``text``."""
    lines = text.splitlines()
    return lines[max(len(lines) - count, 0):]


def _read_text(session, command, path):
    """Return the file at ``path`` as text, or raise ``CommandError``."""
    try:
        _parts, node = session.resolve(path)
    except vfs.VfsError as exc:
        raise CommandError(lookup_message(command, path, exc)) from exc
    if node.is_dir:
        raise CommandError(f"{command}: {path}: Is a directory")
    return node.content.decode("utf-8", errors="replace")
