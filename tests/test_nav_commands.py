"""Unit tests for shellemu.nav_commands (cd and ls)."""

import pytest

from conftest import FIXED_MTIME, LONG_TEXT
from shellemu import nav_commands
from shellemu.errors import CommandError
from shellemu.formatting import format_mtime
from shellemu.nav_commands import run_cd, run_ls
from shellemu.session import Session


@pytest.fixture(autouse=True)
def fixed_user(monkeypatch):
    """Make the owner column deterministic."""
    monkeypatch.setattr(nav_commands, "current_user", lambda: "tester")


def cwd_of(session):
    """Return the session's working directory as an absolute path."""
    return "/" + "/".join(session.cwd)


def test_cd_absolute_path(session):
    run_cd(["/docs/projects"], session)
    assert cwd_of(session) == "/docs/projects"


def test_cd_relative_path_and_dotdot(session):
    run_cd(["docs/projects/alpha"], session)
    assert cwd_of(session) == "/docs/projects/alpha"
    run_cd(["../.."], session)
    assert cwd_of(session) == "/docs"


def test_cd_dot_stays_in_place(session):
    run_cd(["docs"], session)
    run_cd(["."], session)
    assert cwd_of(session) == "/docs"


def test_cd_dotdot_at_root_stays_at_root(session):
    run_cd([".."], session)
    assert cwd_of(session) == "/"


def test_cd_without_arguments_goes_to_root(session):
    run_cd(["docs"], session)
    run_cd([], session)
    assert cwd_of(session) == "/"


def test_cd_tilde_means_the_vfs_root(session):
    run_cd(["docs/projects"], session)
    run_cd(["~"], session)
    assert cwd_of(session) == "/"
    run_cd(["~/docs"], session)
    assert cwd_of(session) == "/docs"


def test_cd_dash_returns_to_previous_and_prints_it(session):
    run_cd(["docs"], session)
    run_cd(["projects"], session)
    assert run_cd(["-"], session) == "/docs"
    assert cwd_of(session) == "/docs"


def test_cd_dash_without_history_is_an_error(session):
    with pytest.raises(CommandError, match="OLDPWD"):
        run_cd(["-"], session)


def test_cd_tolerates_redundant_slashes(session):
    run_cd(["//docs///projects/"], session)
    assert cwd_of(session) == "/docs/projects"


def test_cd_dotdot_cannot_cross_a_missing_directory(session):
    with pytest.raises(CommandError, match="no such file or directory"):
        run_cd(["nosuch/.."], session)


def test_cd_missing_directory(session):
    with pytest.raises(CommandError, match="no such file or directory"):
        run_cd(["nosuch"], session)


def test_cd_into_file_is_an_error(session):
    with pytest.raises(CommandError, match="not a directory"):
        run_cd(["readme.txt"], session)
    with pytest.raises(CommandError, match="not a directory"):
        run_cd(["readme.txt/x"], session)


def test_cd_too_many_arguments(session):
    with pytest.raises(CommandError, match="too many arguments"):
        run_cd(["docs", "empty"], session)


def test_failed_cd_keeps_working_directory(session):
    run_cd(["docs"], session)
    with pytest.raises(CommandError):
        run_cd(["nosuch"], session)
    assert cwd_of(session) == "/docs"


def test_commands_need_a_loaded_vfs():
    empty = Session()
    with pytest.raises(CommandError, match="no VFS loaded"):
        run_cd(["/"], empty)
    with pytest.raises(CommandError, match="no VFS loaded"):
        run_ls([], empty)


def test_ls_plain_hides_dotfiles_and_sorts(session):
    names = run_ls([], session).split("\n")
    assert names == ["data", "docs", "empty", "My Notes.txt", "readme.txt"]


def test_ls_all_shows_hidden_entries_and_dots(session):
    names = run_ls(["-a"], session).split("\n")
    assert names[:3] == [".", "..", ".hidden"]
    assert "readme.txt" in names


def test_ls_accepts_absolute_and_relative_paths(session):
    assert run_ls(["/docs/projects"], session) == "alpha"
    run_cd(["docs"], session)
    assert run_ls(["projects/alpha"], session) == "deep.txt"
    assert run_ls(["../empty"], session) == ""


def test_ls_on_a_file_prints_the_name_as_typed(session):
    assert run_ls(["docs/notes.txt"], session) == "docs/notes.txt"


def test_ls_several_paths_get_headers(session):
    output = run_ls(["readme.txt", "docs/projects", "empty"], session)
    assert output == "readme.txt\n\ndocs/projects:\nalpha\n\nempty:"


def test_ls_missing_path_reports_error_and_lists_the_rest(session):
    output = run_ls(["nosuch", "docs/projects"], session)
    assert output.startswith("ls: nosuch: No such file or directory")
    assert "alpha" in output


def test_ls_through_a_file_reports_not_a_directory(session):
    output = run_ls(["readme.txt/x"], session)
    assert output == "ls: readme.txt/x: Not a directory"


def test_ls_long_format_row_fields(session):
    lines = run_ls(["-l", "docs"], session).split("\n")
    perms, links, owner, group, size = lines[1].split()[:5]
    assert (perms, links) == ("-rw-r--r--", "1")
    assert (owner, group) == ("tester", "tester")
    assert size == str(len(LONG_TEXT))
    assert lines[1].endswith(f"{format_mtime(FIXED_MTIME)} long.txt")


def test_ls_long_format_total_counts_blocks(session):
    assert run_ls(["-l", "docs"], session).split("\n")[0] == "total 6"


def test_ls_long_format_directories(session):
    lines = run_ls(["-l"], session).split("\n")
    docs = next(line for line in lines if line.endswith(" docs"))
    assert docs.startswith("drwxr-xr-x 3 tester tester 4096 ")


def test_ls_long_format_columns_line_up(session):
    rows = run_ls(["-l", "docs"], session).split("\n")[1:]
    stamp = format_mtime(FIXED_MTIME)
    positions = {row.index(stamp) for row in rows}
    assert len(positions) == 1


@pytest.mark.parametrize(
    "variants",
    [
        (["-l", "-h"], ["-lh"], ["-hl"]),
        (["-l", "-a"], ["-la"], ["-al"]),
        (["-h", "-a", "-l"], ["-lah"], ["-hla"], ["-ahl"], ["-alh"]),
    ],
)
def test_flags_combine_in_any_form(session, variants):
    outputs = [run_ls([*flags, "docs"], session) for flags in variants]
    assert all(output == outputs[0] for output in outputs)


def test_combined_flags_really_apply_every_flag(session):
    output = run_ls(["-lah", "data"], session)
    lines = output.split("\n")
    assert lines[0] == "total 10K"
    assert lines[1].endswith(" .")
    assert lines[2].endswith(" ..")
    assert " 1.5K " in lines[3]


def test_human_flag_alone_does_not_change_plain_listing(session):
    assert run_ls(["-h"], session) == run_ls([], session)


def test_human_flag_changes_sizes_and_total(session):
    plain = run_ls(["-l", "data"], session).split("\n")
    human = run_ls(["-lh", "data"], session).split("\n")
    assert plain[0] == "total 2"
    assert human[0] == "total 2.0K"
    assert " 1536 " in plain[1]
    assert " 1.5K " in human[1]


def test_long_format_with_all_lists_dot_entries_first(session):
    lines = run_ls(["-la", "docs"], session).split("\n")
    names = [line.split(" ")[-1] for line in lines[1:]]
    assert names[:2] == [".", ".."]
    assert ".draft" in names


def test_dotdot_of_the_root_describes_the_root_itself(session):
    lines = run_ls(["-la"], session).split("\n")
    dot = next(line for line in lines if line.endswith(" ."))
    dotdot = next(line for line in lines if line.endswith(" .."))
    assert dot.rsplit(" ", 1)[0] == dotdot.rsplit(" ", 1)[0]


def test_ls_invalid_short_option(session):
    with pytest.raises(CommandError, match="invalid option -- 'x'"):
        run_ls(["-lx"], session)


def test_ls_long_option_is_rejected(session):
    with pytest.raises(CommandError, match="unrecognized option '--all'"):
        run_ls(["--all"], session)


def test_ls_double_dash_ends_options(session):
    assert run_ls(["--", "docs/projects"], session) == "alpha"
