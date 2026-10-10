"""Shared parsing of UNIX-style command-line flags."""

from .errors import CommandError

DASH = "-"
LONG_PREFIX = "--"
END_OF_OPTIONS = "--"


def split_flags(command, args, allowed):
    """Split ``args`` into ``(flag letters, operands)``.

    Short flags may be grouped (``-lah``); a lone ``-`` and anything
    after ``--`` are operands. A letter not listed in ``allowed`` or
    any ``--long`` option raises ``CommandError``.
    """
    letters = set()
    operands = []
    options_done = False
    for arg in args:
        if options_done or arg == DASH or not arg.startswith(DASH):
            operands.append(arg)
        elif arg == END_OF_OPTIONS:
            options_done = True
        elif arg.startswith(LONG_PREFIX):
            raise CommandError(f"{command}: unrecognized option '{arg}'")
        else:
            letters.update(_check_letters(command, arg, allowed))
    return letters, operands


def _check_letters(command, arg, allowed):
    """Return the letters of a ``-xyz`` group, rejecting unknown ones."""
    for letter in arg[len(DASH):]:
        if letter not in allowed:
            raise CommandError(f"{command}: invalid option -- '{letter}'")
    return set(arg[len(DASH):])
