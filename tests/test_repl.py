"""Unit tests for shellemu.repl, the UI-independent REPL core."""

from shellemu import repl


def test_stub_command_returns_output():
    output = repl.submit("cd /tmp")
    assert output is not None
    assert "cd" in output


def test_exit_returns_none():
    assert repl.submit("exit") is None


def test_blank_line_returns_empty_string():
    assert repl.submit("   ") == ""


def test_unknown_command_returns_message():
    output = repl.submit("frobnicate")
    assert output == "frobnicate: command not found"


def test_bad_quoting_returns_parse_error_message():
    output = repl.submit('cat "oops')
    assert output.startswith("parse error:")


def test_run_lines_continues_past_errors():
    results = list(repl.run_lines(["foo", "ls"]))
    assert [line for line, _output in results] == ["foo", "ls"]
    assert results[0][1] == "foo: command not found"
    assert "ls" in results[1][1]


def test_run_lines_stops_at_exit():
    results = list(repl.run_lines(["ls", "exit", "cd"]))
    assert [line for line, _output in results] == ["ls", "exit"]
    assert results[-1][1] is None


class _FakeLogger:
    """Records logged calls in memory instead of writing real XML."""

    def __init__(self):
        self.calls = []

    def log(self, name, args):
        self.calls.append((name, args))


def test_submit_logs_successfully_parsed_commands():
    logger = _FakeLogger()
    repl.submit("ls -la", logger=logger)
    assert logger.calls == [("ls", ["-la"])]


def test_submit_does_not_log_blank_lines():
    logger = _FakeLogger()
    repl.submit("   ", logger=logger)
    assert logger.calls == []
