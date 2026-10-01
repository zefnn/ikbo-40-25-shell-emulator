"""REPL control flow, independent of any particular UI toolkit.

Kept free of Tkinter (or any UI) imports so both the GUI layer and
the test suite can exercise the exact same request-handling logic.
"""

from .commands import CommandError, ExitRequested, dispatch
from .parser import ParseError, parse_command_line


def submit(line, logger=None):
    """Process one input line and return text to display, or None.

    A ``None`` return means the session should end (the user ran
    ``exit``); any other return value is text to show in the
    scrollback, possibly an empty string for a blank input line.

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
        return dispatch(name, args)
    except ExitRequested:
        return None
    except CommandError as exc:
        return str(exc)


def run_lines(lines, logger=None):
    """Feed each line through ``submit``, yielding ``(line, output)``.

    An erroneous line's output is just its error message, and the
    loop continues to the next line regardless; only a line that
    resolves to ``exit`` (output is ``None``) ends iteration early.
    """
    for line in lines:
        output = submit(line, logger=logger)
        yield line, output
        if output is None:
            return
