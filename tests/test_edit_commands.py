"""Unit tests for shellemu.edit_commands (mkdir and mv)."""

import pytest

from conftest import ENTRIES, FIXED_MTIME, write_vfs_csv
from shellemu import edit_commands
from shellemu.edit_commands import run_mkdir, run_mv
from shellemu.errors import CommandError
from shellemu.file_commands import run_cat
from shellemu.nav_commands import run_cd, run_ls
from shellemu.session import Session
from shellemu.vfs import load_vfs

NOW = 5_000_000_000.0


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    """Freeze the clock used to stamp new and touched directories."""
    monkeypatch.setattr(edit_commands, "current_time", lambda: NOW)


def node_at(session, path):
    """Return the node at ``path``."""
    return session.resolve(path)[1]


def names(session, path="."):
    """Return the visible names inside a directory."""
    output = run_ls(["-a", path], session)
    return [name for name in output.split("\n") if name not in (".", "..")]


def test_mkdir_creates_a_directory(session):
    assert run_mkdir(["fresh"], session) == ""
    assert node_at(session, "fresh").is_dir
    assert "fresh" in names(session)


def test_mkdir_stamps_the_new_directory_and_its_parent(session):
    run_mkdir(["docs/fresh"], session)
    assert node_at(session, "docs/fresh").mtime == NOW
    assert node_at(session, "docs").mtime == NOW
    assert node_at(session, "readme.txt").mtime == FIXED_MTIME


def test_mkdir_several_operands(session):
    run_mkdir(["a", "b", "c"], session)
    assert {"a", "b", "c"} <= set(names(session))


def test_mkdir_relative_absolute_and_trailing_slash(session):
    run_cd(["docs"], session)
    run_mkdir(["inner/"], session)
    run_mkdir(["/top/"], session)
    run_mkdir(["../sibling/"], session)
    assert node_at(session, "/docs/inner").is_dir
    assert node_at(session, "/top").is_dir
    assert node_at(session, "/sibling").is_dir


def test_mkdir_existing_name_is_an_error(session):
    assert run_mkdir(["docs"], session) == "mkdir: docs: File exists"
    assert run_mkdir(["readme.txt"], session) == (
        "mkdir: readme.txt: File exists"
    )
    assert run_mkdir(["/"], session) == "mkdir: /: File exists"


def test_mkdir_missing_parent_is_an_error(session):
    output = run_mkdir(["nosuch/inner"], session)
    assert output == "mkdir: nosuch/inner: No such file or directory"


def test_mkdir_through_a_file_is_an_error(session):
    output = run_mkdir(["readme.txt/x"], session)
    assert output == "mkdir: readme.txt/x: Not a directory"


def test_mkdir_keeps_going_after_an_error(session):
    output = run_mkdir(["docs", "fresh", "nosuch/x"], session)
    assert output.split("\n") == [
        "mkdir: docs: File exists",
        "mkdir: nosuch/x: No such file or directory",
    ]
    assert node_at(session, "fresh").is_dir


def test_mkdir_p_creates_the_whole_chain(session):
    run_mkdir(["-p", "one/two/three"], session)
    assert node_at(session, "one/two/three").is_dir
    assert node_at(session, "one/two").is_dir


def test_mkdir_p_works_with_absolute_paths_and_from_a_subdirectory(session):
    run_cd(["docs"], session)
    run_mkdir(["-p", "/x/y/z"], session)
    run_mkdir(["-p", "projects/beta/gamma"], session)
    assert node_at(session, "/x/y/z").is_dir
    assert node_at(session, "/docs/projects/beta/gamma").is_dir


def test_mkdir_p_accepts_existing_directories(session):
    assert run_mkdir(["-p", "docs/projects"], session) == ""
    assert run_mkdir(["-p", "docs/projects/alpha"], session) == ""
    assert run_mkdir(["-p", "/"], session) == ""
    assert node_at(session, "docs/projects/alpha/deep.txt").content == b"deep\n"


def test_mkdir_p_still_fails_on_an_existing_file(session):
    assert run_mkdir(["-p", "readme.txt"], session) == (
        "mkdir: readme.txt: File exists"
    )
    assert run_mkdir(["-p", "readme.txt/x"], session) == (
        "mkdir: readme.txt/x: Not a directory"
    )


def test_mkdir_p_does_not_change_existing_parents(session):
    run_mkdir(["-p", "docs/projects/new"], session)
    assert node_at(session, "docs").mtime == FIXED_MTIME
    assert node_at(session, "docs/projects").mtime == NOW


def test_mkdir_operand_errors(session):
    with pytest.raises(CommandError, match="missing operand"):
        run_mkdir([], session)
    with pytest.raises(CommandError, match="invalid option -- 'x'"):
        run_mkdir(["-x", "a"], session)
    with pytest.raises(CommandError, match="unrecognized option"):
        run_mkdir(["--parents", "a"], session)


def test_mkdir_double_dash_allows_dash_names(session):
    run_mkdir(["--", "-odd"], session)
    assert node_at(session, "-odd").is_dir


def test_commands_need_a_loaded_vfs():
    for command in (run_mkdir, run_mv):
        with pytest.raises(CommandError, match="no VFS loaded"):
            command(["a", "b"], Session())


def test_mkdir_never_touches_the_csv_file(tmp_path):
    csv_path = tmp_path / "vfs.csv"
    write_vfs_csv(csv_path, ENTRIES)
    before = csv_path.read_bytes()
    session = Session(load_vfs(str(csv_path)))
    run_mkdir(["-p", "a/b"], session)
    run_mv(["readme.txt", "a/b"], session)
    assert csv_path.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == ["vfs.csv"]


def test_mv_renames_a_file(session):
    assert run_mv(["readme.txt", "hello.txt"], session) == ""
    assert "readme.txt" not in names(session)
    assert run_cat(["hello.txt"], session) == "Hello"
    assert node_at(session, "hello.txt").name == "hello.txt"


def test_mv_moves_a_file_into_a_directory(session):
    run_mv(["readme.txt", "docs"], session)
    assert "readme.txt" not in names(session)
    assert run_cat(["docs/readme.txt"], session) == "Hello"


def test_mv_moves_and_renames_in_one_step(session):
    run_mv(["readme.txt", "docs/projects/intro.txt"], session)
    assert run_cat(["docs/projects/intro.txt"], session) == "Hello"


def test_mv_renames_a_directory_with_its_contents(session):
    run_mv(["docs", "archive"], session)
    assert "docs" not in names(session)
    assert run_cat(["archive/projects/alpha/deep.txt"], session) == "deep"


def test_mv_moves_a_directory_into_another(session):
    run_mv(["docs", "empty"], session)
    assert run_cat(["empty/docs/notes.txt"], session) == "one\ntwo\nthree"


def test_mv_uses_the_working_directory_for_relative_paths(session):
    run_cd(["docs/projects"], session)
    run_mv(["alpha", "../.."], session)
    assert node_at(session, "/alpha/deep.txt").content == b"deep\n"


def test_mv_several_sources_into_a_directory(session):
    run_mv(["readme.txt", "My Notes.txt", "data", "empty"], session)
    assert names(session, "empty") == ["data", "My Notes.txt", "readme.txt"]


def test_mv_overwrites_a_file_with_a_file(session):
    run_mv(["docs/notes.txt", "docs/long.txt"], session)
    assert run_cat(["docs/long.txt"], session) == "one\ntwo\nthree"
    assert "notes.txt" not in names(session, "docs")


def test_mv_into_a_directory_overwrites_a_same_named_file(session):
    run_mv(["readme.txt", "docs/notes.txt"], session)
    assert run_cat(["docs/notes.txt"], session) == "Hello"


def test_mv_into_a_directory_replaces_a_same_named_empty_directory(session):
    run_mkdir(["-p", "box/projects"], session)
    run_mv(["docs/projects", "box"], session)
    assert node_at(session, "box/projects/alpha/deep.txt").content == b"deep\n"
    assert "projects" not in names(session, "docs")


def test_mv_moves_into_an_empty_directory_instead_of_replacing_it(session):
    run_mkdir(["spare"], session)
    run_mv(["docs/projects", "spare"], session)
    assert run_ls(["spare"], session) == "projects"


def test_mv_touches_both_parents_but_not_the_moved_entry(session):
    run_mv(["readme.txt", "docs"], session)
    assert node_at(session, "/").mtime == NOW
    assert node_at(session, "docs").mtime == NOW
    assert node_at(session, "docs/readme.txt").mtime == FIXED_MTIME


def test_mv_moves_the_current_directory_along_with_the_session(session):
    run_cd(["docs/projects"], session)
    run_mv(["/docs", "/archive"], session)
    assert session.prompt() == "VFS:/archive/projects$ "
    assert run_ls([], session) == "alpha"


def test_mv_rebases_the_previous_directory_too(session):
    run_cd(["docs/projects"], session)
    run_cd(["/"], session)
    run_mv(["docs", "archive"], session)
    assert run_cd(["-"], session) == "/archive/projects"


def test_mv_missing_source(session):
    assert run_mv(["nosuch", "x"], session) == (
        "mv: cannot stat 'nosuch': No such file or directory"
    )
    assert run_mv(["readme.txt/x", "y"], session) == (
        "mv: cannot stat 'readme.txt/x': Not a directory"
    )


def test_mv_destination_parent_problems(session):
    assert run_mv(["readme.txt", "nosuch/new"], session) == (
        "mv: cannot move 'readme.txt' to 'nosuch/new': "
        "No such file or directory"
    )
    assert run_mv(["data", "My Notes.txt/new"], session) == (
        "mv: cannot move 'data' to 'My Notes.txt/new': Not a directory"
    )


def test_mv_several_sources_need_a_directory_target(session):
    with pytest.raises(CommandError, match="target 'readme.txt' is not"):
        run_mv(["data", "docs", "readme.txt"], session)
    with pytest.raises(CommandError, match="target 'nosuch' is not"):
        run_mv(["data", "docs", "nosuch"], session)


def test_mv_keeps_going_after_a_failed_source(session):
    output = run_mv(["nosuch", "readme.txt", "empty"], session)
    assert output == "mv: cannot stat 'nosuch': No such file or directory"
    assert run_cat(["empty/readme.txt"], session) == "Hello"


def test_mv_a_directory_into_itself_or_below(session):
    assert run_mv(["docs", "docs"], session) == (
        "mv: cannot move 'docs' to a subdirectory of itself, 'docs/docs'"
    )
    assert run_mv(["docs", "docs/projects/alpha"], session) == (
        "mv: cannot move 'docs' to a subdirectory of itself, "
        "'docs/projects/alpha/docs'"
    )
    assert run_mv(["docs", "docs/new"], session) == (
        "mv: cannot move 'docs' to a subdirectory of itself, 'docs/new'"
    )
    assert node_at(session, "docs/notes.txt").is_dir is False


def test_mv_onto_itself(session):
    assert run_mv(["readme.txt", "readme.txt"], session) == (
        "mv: 'readme.txt' and 'readme.txt' are the same file"
    )
    assert run_mv(["readme.txt", "."], session) == (
        "mv: 'readme.txt' and './readme.txt' are the same file"
    )
    assert run_cat(["readme.txt"], session) == "Hello"


def test_mv_refuses_root_dot_and_dotdot(session):
    run_cd(["docs"], session)
    for source in ("/", ".", "..", "../docs/.", "~"):
        assert run_mv([source, "/empty"], session).endswith(
            "Device or resource busy"
        )


def test_mv_type_mismatches(session):
    assert run_mv(["docs", "readme.txt"], session) == (
        "mv: cannot overwrite non-directory 'readme.txt' "
        "with directory 'docs'"
    )
    run_mkdir(["empty/readme.txt"], session)
    assert run_mv(["readme.txt", "empty"], session) == (
        "mv: cannot overwrite directory 'empty/readme.txt' with non-directory"
    )


def test_mv_directory_onto_a_non_empty_directory(session):
    run_mkdir(["-p", "box/docs/stuff"], session)
    assert run_mv(["docs", "box"], session) == (
        "mv: cannot move 'docs' to 'box/docs': Directory not empty"
    )
    assert node_at(session, "docs/notes.txt").content == b"one\ntwo\nthree\n"


def test_mv_operand_errors(session):
    with pytest.raises(CommandError, match="missing file operand"):
        run_mv([], session)
    with pytest.raises(CommandError, match="after 'readme.txt'"):
        run_mv(["readme.txt"], session)
    with pytest.raises(CommandError, match="invalid option -- 'f'"):
        run_mv(["-f", "a", "b"], session)


def test_failed_mv_changes_nothing(session):
    before = run_ls(["-a"], session)
    run_mv(["docs", "docs/projects"], session)
    run_mv(["docs", "readme.txt"], session)
    assert run_ls(["-a"], session) == before
