"""Unit tests for shellemu.formatting."""

import time

import pytest

from shellemu import formatting
from shellemu.formatting import format_mtime, human_size, join_block


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0"),
        (512, "512"),
        (1023, "1023"),
        (1024, "1.0K"),
        (1536, "1.5K"),
        (1025, "1.1K"),
        (10239, "10K"),
        (10240, "10K"),
        (30000, "30K"),
        (1048575, "1.0M"),
        (1048576, "1.0M"),
        (1572864, "1.5M"),
        (5 * 1024**3, "5.0G"),
    ],
)
def test_human_size_matches_ls(size, expected):
    assert human_size(size) == expected


def local_timestamp(year, month, day, hour, minute):
    """Return the epoch seconds of a local time."""
    return time.mktime((year, month, day, hour, minute, 0, 0, 0, -1))


def test_recent_files_show_the_time():
    moment = local_timestamp(2026, 10, 3, 9, 5)
    now = local_timestamp(2026, 10, 10, 12, 0)
    assert format_mtime(moment, now) == "Oct  3 09:05"


def test_old_files_show_the_year():
    moment = local_timestamp(2024, 1, 15, 9, 5)
    now = local_timestamp(2026, 10, 10, 12, 0)
    assert format_mtime(moment, now) == "Jan 15  2024"


def test_far_future_files_show_the_year():
    moment = local_timestamp(2030, 6, 1, 0, 0)
    now = local_timestamp(2026, 10, 10, 12, 0)
    assert format_mtime(moment, now) == "Jun  1  2030"


def test_join_block():
    assert join_block("head", "body") == "head\nbody"
    assert join_block("head", "") == "head"


def test_current_user_falls_back_when_the_os_cannot_say(monkeypatch):
    def broken():
        raise OSError("no user")

    monkeypatch.setattr(formatting.getpass, "getuser", broken)
    assert formatting.current_user() == formatting.FALLBACK_USER
