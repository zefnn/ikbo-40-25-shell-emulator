"""Unit tests for shellemu.commands."""

import pytest

from shellemu.commands import COMMANDS, dispatch
from shellemu.errors import ClearRequested, CommandError, ExitRequested


def test_every_required_command_is_registered():
    required = {"ls", "cd", "cat", "tail", "clear", "exit"}
    assert required <= set(COMMANDS)


def test_dispatch_runs_the_named_command(session):
    assert dispatch("ls", ["docs/projects"], session) == "alpha"


def test_exit_raises_exit_requested(session):
    with pytest.raises(ExitRequested):
        dispatch("exit", [], session)


def test_clear_raises_clear_requested(session):
    with pytest.raises(ClearRequested):
        dispatch("clear", [], session)


def test_clear_takes_no_arguments(session):
    with pytest.raises(CommandError, match="too many arguments"):
        dispatch("clear", ["now"], session)


def test_unknown_command_raises_command_error(session):
    with pytest.raises(CommandError, match="command not found"):
        dispatch("frobnicate", [], session)
