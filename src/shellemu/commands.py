"""Command registry and dispatch for the shell emulator.

Each command is a function ``run_xxx(args, session)`` that returns the
text to display (an empty string for no output) or raises one of the
exceptions from ``shellemu.errors`` to signal an error, an exit or a
screen clear.
"""

from .edit_commands import run_mkdir, run_mv
from .errors import ClearRequested, CommandError, ExitRequested
from .file_commands import run_cat, run_tail
from .nav_commands import run_cd, run_ls


def run_exit(_args, _session):
    """Ask the session to end."""
    raise ExitRequested()


def run_clear(args, _session):
    """Ask for the screen to be cleared; takes no arguments."""
    if args:
        raise CommandError("clear: too many arguments")
    raise ClearRequested()


COMMANDS = {
    "ls": run_ls,
    "cd": run_cd,
    "cat": run_cat,
    "tail": run_tail,
    "mkdir": run_mkdir,
    "mv": run_mv,
    "clear": run_clear,
    "exit": run_exit,
}


def dispatch(name, args, session):
    """Run the command ``name`` and return its output.

    Raises ``CommandError`` for an unknown command or invalid use,
    ``ExitRequested`` for ``exit`` and ``ClearRequested`` for ``clear``.
    """
    handler = COMMANDS.get(name)
    if handler is None:
        raise CommandError(f"{name}: command not found")
    return handler(args, session)
