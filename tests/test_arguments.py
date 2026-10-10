"""Unit tests for shellemu.arguments."""

import pytest

from shellemu.arguments import split_flags
from shellemu.errors import CommandError


def test_flags_and_operands_are_separated():
    letters, operands = split_flags("ls", ["-l", "a", "-h", "b"], "lh")
    assert letters == {"l", "h"}
    assert operands == ["a", "b"]


def test_grouped_flags():
    letters, _operands = split_flags("ls", ["-lah"], "lah")
    assert letters == {"l", "a", "h"}


def test_no_flags_at_all():
    assert split_flags("cat", ["x", "y"], "") == (set(), ["x", "y"])


def test_lone_dash_is_an_operand():
    assert split_flags("ls", ["-"], "l") == (set(), ["-"])


def test_double_dash_ends_the_options():
    letters, operands = split_flags("mkdir", ["-p", "--", "-p", "--"], "p")
    assert letters == {"p"}
    assert operands == ["-p", "--"]


def test_unknown_letter_names_the_first_offender():
    with pytest.raises(CommandError, match="ls: invalid option -- 'x'"):
        split_flags("ls", ["-lxy"], "l")


def test_long_options_are_rejected():
    with pytest.raises(CommandError, match="mv: unrecognized option '--f'"):
        split_flags("mv", ["--f", "a"], "")
