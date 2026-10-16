"""Unit tests for shellemu.file_commands (cat and tail)."""

import pytest

from shellemu.errors import CommandError
from shellemu.file_commands import DEFAULT_TAIL_LINES, run_cat, run_tail
from shellemu.nav_commands import run_cd
from shellemu.session import Session


def test_cat_prints_a_file(session):
    assert run_cat(["readme.txt"], session) == "Hello"


def test_cat_concatenates_several_files(session):
    output = run_cat(["readme.txt", "docs/notes.txt"], session)
    assert output == "Hello\none\ntwo\nthree"


def test_cat_resolves_relative_paths_from_the_working_directory(session):
    run_cd(["docs/projects"], session)
    assert run_cat(["alpha/deep.txt"], session) == "deep"
    assert run_cat(["../../readme.txt"], session) == "Hello"


def test_cat_handles_a_name_with_spaces(session):
    assert run_cat(["My Notes.txt"], session) == "spaced"


def test_cat_missing_file_keeps_going(session):
    output = run_cat(["nosuch", "readme.txt"], session)
    assert output == "cat: nosuch: No such file or directory\nHello"


def test_cat_on_a_directory(session):
    with_error = run_cat(["docs"], session)
    assert with_error == "cat: docs: Is a directory"


def test_cat_through_a_file_reports_not_a_directory(session):
    output = run_cat(["readme.txt/x"], session)
    assert output == "cat: readme.txt/x: Not a directory"


def test_cat_without_arguments(session):
    with pytest.raises(CommandError, match="missing file operand"):
        run_cat([], session)


def test_cat_rejects_options(session):
    with pytest.raises(CommandError, match="invalid option -- 'n'"):
        run_cat(["-n", "readme.txt"], session)
    with pytest.raises(CommandError, match="unrecognized option '--x'"):
        run_cat(["--x"], session)


def test_cat_binary_content_is_decoded_leniently(session):
    output = run_cat(["data/small.bin"], session)
    assert "�" in output


def test_cat_needs_a_loaded_vfs():
    with pytest.raises(CommandError, match="no VFS loaded"):
        run_cat(["x"], Session())


def test_tail_defaults_to_ten_lines(session):
    lines = run_tail(["docs/long.txt"], session).split("\n")
    assert lines[0] == "line 6"
    assert lines[-1] == "line 15"
    assert len(lines) == DEFAULT_TAIL_LINES


@pytest.mark.parametrize("flags", [["-n", "3"], ["-n3"], ["-3"]])
def test_tail_line_count_forms(session, flags):
    output = run_tail([*flags, "docs/long.txt"], session)
    assert output == "line 13\nline 14\nline 15"


def test_tail_zero_lines_is_empty(session):
    assert run_tail(["-n", "0", "docs/long.txt"], session) == ""


def test_tail_more_lines_than_the_file_has(session):
    output = run_tail(["-n", "99", "docs/notes.txt"], session)
    assert output == "one\ntwo\nthree"


def test_tail_option_after_the_file_name(session):
    output = run_tail(["docs/notes.txt", "-n", "1"], session)
    assert output == "three"


def test_tail_several_files_get_headers(session):
    output = run_tail(["-n", "1", "docs/notes.txt", "readme.txt"], session)
    assert output == (
        "==> docs/notes.txt <==\nthree\n\n==> readme.txt <==\nHello"
    )


def test_tail_missing_file(session):
    with pytest.raises(CommandError):
        run_tail([], session)
    assert run_tail(["nosuch"], session) == (
        "tail: nosuch: No such file or directory"
    )


def test_tail_on_a_directory(session):
    assert run_tail(["docs"], session) == "tail: docs: Is a directory"


@pytest.mark.parametrize("bad", ["x", "-1", "1.5", "", "²"])
def test_tail_rejects_bad_line_counts(session, bad):
    with pytest.raises(CommandError, match="invalid number of lines"):
        run_tail(["-n", bad, "readme.txt"], session)


def test_tail_option_without_a_value(session):
    with pytest.raises(CommandError, match="requires an argument"):
        run_tail(["readme.txt", "-n"], session)


def test_tail_unknown_option(session):
    with pytest.raises(CommandError, match="invalid option -- 'x'"):
        run_tail(["-x", "readme.txt"], session)
