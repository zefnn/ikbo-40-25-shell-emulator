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
