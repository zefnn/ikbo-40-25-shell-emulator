"""Unit tests for shellemu.session."""

from shellemu.session import Session, lookup_message
from shellemu.vfs import NotDirectoryError, PathNotFoundError


def test_prompt_follows_the_working_directory(session):
    assert session.prompt() == "VFS:/$ "
    session.change_dir(("docs", "projects"))
    assert session.prompt() == "VFS:/docs/projects$ "


def test_change_dir_remembers_the_previous_directory(session):
    session.change_dir(("docs",))
    session.change_dir(("empty",))
    assert session.previous_cwd == ("docs",)
    assert session.cwd == ("empty",)


def test_session_without_a_vfs_still_has_a_prompt():
    assert Session().prompt() == "VFS:/$ "


def test_lookup_message_wording():
    missing = lookup_message("cat", "x", PathNotFoundError("x"))
    through_file = lookup_message("cat", "x/y", NotDirectoryError("x"))
    assert missing == "cat: x: No such file or directory"
    assert through_file == "cat: x/y: Not a directory"


def test_relocate_rebases_the_working_and_previous_directories(session):
    session.change_dir(("docs", "projects"))
    session.change_dir(("docs",))
    session.relocate(("docs",), ("archive",))
    assert session.cwd == ("archive",)
    assert session.previous_cwd == ("archive", "projects")


def test_relocate_leaves_unrelated_directories_alone(session):
    session.change_dir(("data",))
    session.relocate(("docs",), ("archive",))
    assert session.cwd == ("data",)
    assert session.previous_cwd == ()


def test_relocate_does_not_match_a_sibling_with_a_common_prefix(session):
    session.change_dir(("docs-old",))
    session.relocate(("docs",), ("archive",))
    assert session.cwd == ("docs-old",)


def test_relocate_without_a_previous_directory(session):
    session.cwd = ("docs",)
    session.relocate(("docs",), ("archive",))
    assert session.cwd == ("archive",)
    assert session.previous_cwd is None
