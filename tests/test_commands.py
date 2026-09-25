"""Unit tests for shellemu.commands."""

import pytest

from shellemu.commands import CommandError, ExitRequested, dispatch


def test_stub_command_reports_name_and_args():
    output = dispatch("ls", ["-la"])
    assert "ls" in output
    assert "-la" in output


def test_exit_raises_exit_requested():
    with pytest.raises(ExitRequested):
        dispatch("exit", [])


def test_unknown_command_raises_command_error():
    with pytest.raises(CommandError):
        dispatch("frobnicate", [])
