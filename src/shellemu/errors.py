"""Exceptions that signal the outcome of a shell command."""


class CommandError(Exception):
    """Raised when a command fails: unknown name, bad arguments, etc."""


class ExitRequested(Exception):
    """Raised when the user invokes the exit command."""


class ClearRequested(Exception):
    """Raised when the user invokes the clear command."""
