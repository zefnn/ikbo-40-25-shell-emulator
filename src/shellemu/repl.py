"""REPL control flow, independent of any particular UI toolkit.

Kept free of Tkinter (or any UI) imports so both the GUI layer and
the test suite can exercise the exact same request-handling logic.
"""

from .commands import CommandError, ExitRequested, dispatch
from .parser import ParseError, parse_command_line


def submit(line):
    """Process one input line and return text to display, or None.

    A ``None`` return means the session should end (the user ran
    ``exit``); any other return value is text to show in the
    scrollback, possibly an empty string for a blank input line.
    """
    try:
        name, args = parse_command_line(line)
    except ParseError as exc:
        return f"parse error: {exc}"
    if not name:
        return ""
    try:
        return dispatch(name, args)
    except ExitRequested:
        return None
    except CommandError as exc:
        return str(exc)
