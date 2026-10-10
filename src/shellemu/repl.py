"""REPL control flow, independent of any particular UI toolkit.

Kept free of Tkinter (or any UI) imports so both the GUI layer and
the test suite can exercise the exact same request-handling logic.
"""

from .commands import dispatch
from .errors import ClearRequested, CommandError, ExitRequested
from .parser import ParseError, parse_command_line

CLEAR_SCREEN = object()


def submit(line, session, logger=None):
    """Process one input line and return what the UI should do.

    The result is ``None`` when the session should end (``exit``),
    the ``CLEAR_SCREEN`` marker when the screen should be wiped
    (``clear``), and otherwise the text to show in the scrollback,
    possibly an empty string for a blank line or a silent command.

    When ``logger`` is given and the line resolves to a command
    name (even an unrecognized one), ``logger.log(name, args)`` is
    called before dispatching it.
    """
    try:
        name, args = parse_command_line(line)
    except ParseError as exc:
        return f"parse error: {exc}"
    if not name:
        return ""
    if logger is not None:
        logger.log(name, args)
    try:
        return dispatch(name, args, session)
    except ExitRequested:
        return None
    except ClearRequested:
        return CLEAR_SCREEN
    except CommandError as exc:
        return str(exc)


def run_lines(lines, session, logger=None):
    """Feed each line through ``submit``, yielding ``(line, output)``.

    An erroneous line's output is just its error message, and the
    loop continues to the next line regardless; only a line that
    resolves to ``exit`` (output is ``None``) ends iteration early.
    """
    for line in lines:
        output = submit(line, session, logger=logger)
        yield line, output
        if output is None:
            return
