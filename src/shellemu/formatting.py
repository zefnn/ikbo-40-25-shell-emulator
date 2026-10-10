"""Presentation helpers shared by the shell commands."""

import getpass
import math
import time

BLOCK_BYTES = 1024
SIZE_SUFFIXES = ("K", "M", "G", "T", "P")
DECIMAL_LIMIT = 10
SIX_MONTHS_SECONDS = 182 * 24 * 60 * 60
FALLBACK_USER = "user"
MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def human_size(size):
    """Format a byte count the way ``ls -h`` does: 512, 1.5K, 12M.

    Values are rounded up, with one decimal while the number is
    below ten and none from ten on.
    """
    if size < BLOCK_BYTES:
        return str(size)
    value = float(size)
    for suffix in SIZE_SUFFIXES:
        value /= BLOCK_BYTES
        if math.ceil(value) < BLOCK_BYTES:
            break
    rounded = math.ceil(value * DECIMAL_LIMIT) / DECIMAL_LIMIT
    if rounded < DECIMAL_LIMIT:
        return f"{rounded:.1f}{suffix}"
    return f"{math.ceil(value)}{suffix}"


def format_mtime(timestamp, now=None):
    """Format a timestamp like ``ls -l``: time if recent, else year."""
    current = time.time() if now is None else now
    moment = time.localtime(timestamp)
    month = MONTHS[moment.tm_mon - 1]
    if abs(current - timestamp) > SIX_MONTHS_SECONDS:
        clock = f"{moment.tm_year:>5}"
    else:
        clock = f"{moment.tm_hour:02d}:{moment.tm_min:02d}"
    return f"{month} {moment.tm_mday:>2} {clock}"


def current_user():
    """Return the name of the OS user running the emulator."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return FALLBACK_USER


def join_block(header, body):
    """Put ``header`` above ``body``; skip the line break if empty."""
    if not body:
        return header
    return f"{header}\n{body}"
