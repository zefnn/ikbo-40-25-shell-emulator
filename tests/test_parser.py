"""Unit tests for shellemu.parser."""

import pytest

from shellemu.parser import ParseError, parse_command_line


def test_splits_command_and_args():
    name, args = parse_command_line("ls -la /tmp")
    assert name == "ls"
    assert args == ["-la", "/tmp"]


def test_double_quoted_argument_stays_one_token():
    name, args = parse_command_line('cat "my file.txt"')
    assert name == "cat"
    assert args == ["my file.txt"]


def test_single_quoted_argument_stays_one_token():
    _name, args = parse_command_line("cat 'my file.txt'")
    assert args == ["my file.txt"]


def test_blank_line_returns_empty_name():
    name, args = parse_command_line("   ")
    assert name == ""
    assert args == []


def test_unclosed_quote_raises_parse_error():
    with pytest.raises(ParseError):
        parse_command_line('cat "unterminated')


def test_multiple_spaces_collapse_to_one_separator():
    name, args = parse_command_line("ls   -la    /tmp")
    assert name == "ls"
    assert args == ["-la", "/tmp"]


def test_text_glued_around_quotes_forms_one_token():
    name, args = parse_command_line('echo a"b c"d')
    assert name == "echo"
    assert args == ["ab cd"]
