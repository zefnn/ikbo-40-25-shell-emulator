"""Unit tests for shellemu.repl, the UI-independent REPL core."""

from shellemu import repl
from shellemu.session import Session


def test_listing_command_returns_output(session):
    assert repl.submit("ls docs/projects", session) == "alpha"


def test_exit_returns_none(session):
    assert repl.submit("exit", session) is None


def test_clear_returns_the_clear_marker(session):
    assert repl.submit("clear", session) is repl.CLEAR_SCREEN


def test_blank_line_returns_empty_string(session):
    assert repl.submit("   ", session) == ""


def test_silent_command_returns_empty_string(session):
    assert repl.submit("cd docs", session) == ""


def test_unknown_command_returns_message(session):
    output = repl.submit("frobnicate", session)
    assert output == "frobnicate: command not found"


def test_command_errors_become_messages(session):
    assert repl.submit("cd nosuch", session) == (
        "cd: no such file or directory: nosuch"
    )


def test_bad_quoting_returns_parse_error_message(session):
    output = repl.submit('cat "oops', session)
    assert output.startswith("parse error:")


def test_quoted_argument_reaches_the_command_as_one_path(session):
    assert repl.submit('cat "My Notes.txt"', session) == "spaced"


def test_cd_changes_state_between_submissions(session):
    repl.submit("cd docs/projects", session)
    assert session.prompt() == "VFS:/docs/projects$ "
    assert repl.submit("ls", session) == "alpha"
    assert repl.submit("cat alpha/deep.txt", session) == "deep"


def test_commands_without_a_vfs_report_it():
    assert repl.submit("ls", Session()) == "ls: no VFS loaded"


def test_run_lines_continues_past_errors(session):
    results = list(repl.run_lines(["foo", "ls docs/projects"], session))
    assert [line for line, _output in results] == ["foo", "ls docs/projects"]
    assert results[0][1] == "foo: command not found"
    assert results[1][1] == "alpha"


def test_run_lines_stops_at_exit(session):
    results = list(repl.run_lines(["ls", "exit", "cd"], session))
    assert [line for line, _output in results] == ["ls", "exit"]
    assert results[-1][1] is None


def test_run_lines_keeps_the_working_directory_between_lines(session):
    lines = ["cd docs", "ls projects"]
    results = list(repl.run_lines(lines, session))
    assert results[-1][1] == "alpha"


class FakeLogger:
    """Records logged calls in memory instead of writing real XML."""

    def __init__(self):
        self.calls = []

    def log(self, name, args):
        """Record one (name, args) call instead of writing to disk."""
        self.calls.append((name, args))


def test_submit_logs_successfully_parsed_commands(session):
    logger = FakeLogger()
    repl.submit("ls -la docs", session, logger=logger)
    assert logger.calls == [("ls", ["-la", "docs"])]


def test_submit_logs_failed_and_special_commands_too(session):
    logger = FakeLogger()
    repl.submit("nosuch", session, logger=logger)
    repl.submit("clear", session, logger=logger)
    assert [name for name, _args in logger.calls] == ["nosuch", "clear"]


def test_submit_does_not_log_blank_lines(session):
    logger = FakeLogger()
    repl.submit("   ", session, logger=logger)
    assert logger.calls == []
