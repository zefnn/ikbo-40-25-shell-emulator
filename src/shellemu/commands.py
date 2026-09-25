"""Command dispatch for the shell emulator's Stage 1 prototype.

Every command besides ``exit`` is currently a stub: it reports its
own name and the arguments it received without touching any state.
Real behaviour (``ls``, ``cd`` and friends) is added in later stages.
"""

STUB_COMMANDS = ("ls", "cd")
EXIT_COMMAND = "exit"


class CommandError(Exception):
    """Raised when a command name is not recognized."""


class ExitRequested(Exception):
    """Raised when the user invokes the exit command."""


def dispatch(name, args):
    """Execute one already-parsed command and return its output.

    Raises ``ExitRequested`` for the exit command and
    ``CommandError`` for any unrecognized command name.
    """
    if name == EXIT_COMMAND:
        raise ExitRequested()
    if name in STUB_COMMANDS:
        return f"[stub] command={name} args={args}"
    raise CommandError(f"{name}: command not found")
