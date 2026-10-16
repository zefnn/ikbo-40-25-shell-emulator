"""Unit tests for shellemu.vfs."""

import base64

import pytest

from shellemu.vfs import (
    NotDirectoryError,
    PathNotFoundError,
    VfsError,
    attach,
    count_entries,
    detach,
    find_node,
    format_path,
    load_vfs,
    new_directory,
    resolve,
    split_parent,
)

HEADER = "path,type,content\n"
ATTACH_TIME = 42.0
DETACH_TIME = 99.0


def _write_csv(tmp_path, body):
    csv_path = tmp_path / "vfs.csv"
    csv_path.write_text(HEADER + body, encoding="utf-8")
    return csv_path


def _b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def test_minimal_single_file(tmp_path):
    csv_path = _write_csv(tmp_path, f"readme.txt,file,{_b64('hi')}\n")
    root = load_vfs(str(csv_path))
    assert set(root.children) == {"readme.txt"}
    assert root.children["readme.txt"].content == b"hi"
    assert count_entries(root) == (1, 0)


def test_several_files_at_top_level(tmp_path):
    body = (
        f"a.txt,file,{_b64('a')}\n"
        f"b.txt,file,{_b64('b')}\n"
        f"c.txt,file,{_b64('c')}\n"
    )
    root = load_vfs(str(_write_csv(tmp_path, body)))
    assert set(root.children) == {"a.txt", "b.txt", "c.txt"}
    assert count_entries(root) == (3, 0)


def test_nested_directories_created_implicitly(tmp_path):
    body = f"a/b/c/deep.txt,file,{_b64('deep')}\n"
    root = load_vfs(str(_write_csv(tmp_path, body)))
    a = root.children["a"]
    b = a.children["b"]
    c = b.children["c"]
    assert a.is_dir and b.is_dir and c.is_dir
    assert c.children["deep.txt"].content == b"deep"
    assert count_entries(root) == (1, 3)


def test_explicit_empty_directory(tmp_path):
    body = "empty,dir,\n"
    root = load_vfs(str(_write_csv(tmp_path, body)))
    assert root.children["empty"].is_dir
    assert root.children["empty"].children == {}
    assert count_entries(root) == (0, 1)


def test_explicit_dir_row_for_already_implied_directory_is_fine(tmp_path):
    body = f"docs,dir,\ndocs/readme.txt,file,{_b64('x')}\n"
    root = load_vfs(str(_write_csv(tmp_path, body)))
    assert root.children["docs"].is_dir
    assert "readme.txt" in root.children["docs"].children


def test_empty_content_means_empty_file(tmp_path):
    root = load_vfs(str(_write_csv(tmp_path, "empty.txt,file,\n")))
    assert root.children["empty.txt"].content == b""


def test_missing_file_raises_vfs_error():
    with pytest.raises(VfsError, match="cannot read"):
        load_vfs("/no/such/vfs.csv")


def test_wrong_header_raises_vfs_error(tmp_path):
    csv_path = tmp_path / "vfs.csv"
    csv_path.write_text("name,kind,data\na,file,x\n", encoding="utf-8")
    with pytest.raises(VfsError, match="header"):
        load_vfs(str(csv_path))


def test_invalid_base64_raises_vfs_error(tmp_path):
    body = "broken.txt,file,not-valid-base64!!!\n"
    with pytest.raises(VfsError, match="base64"):
        load_vfs(str(_write_csv(tmp_path, body)))


def test_duplicate_path_raises_vfs_error(tmp_path):
    body = f"a.txt,file,{_b64('1')}\na.txt,file,{_b64('2')}\n"
    with pytest.raises(VfsError, match="duplicate"):
        load_vfs(str(_write_csv(tmp_path, body)))


def test_file_dir_conflict_raises_vfs_error(tmp_path):
    body = f"a,file,{_b64('x')}\na/b.txt,file,{_b64('y')}\n"
    with pytest.raises(VfsError):
        load_vfs(str(_write_csv(tmp_path, body)))


def test_unknown_type_raises_vfs_error(tmp_path):
    body = "a.txt,symlink,\n"
    with pytest.raises(VfsError, match="unknown VFS entry type"):
        load_vfs(str(_write_csv(tmp_path, body)))


@pytest.mark.parametrize("bad_path", ["/leading", "trailing/", "a//b", "../x"])
def test_unsafe_paths_raise_vfs_error(tmp_path, bad_path):
    with pytest.raises(VfsError, match="invalid VFS path"):
        load_vfs(str(_write_csv(tmp_path, f"{bad_path},file,\n")))


def test_dot_names_are_reserved_for_navigation(tmp_path):
    for bad_path in ["./x", "a/./b", "a/.."]:
        with pytest.raises(VfsError, match="invalid VFS path"):
            load_vfs(str(_write_csv(tmp_path, f"{bad_path},file,\n")))


def test_non_utf8_csv_is_a_vfs_error_not_a_crash(tmp_path):
    csv_path = tmp_path / "vfs.csv"
    csv_path.write_bytes(b"path,type,content\n\xff\xfe,file,\n")
    with pytest.raises(VfsError, match="cannot read"):
        load_vfs(str(csv_path))


def test_every_node_is_stamped_with_the_csv_mtime(tmp_path):
    body = f"a/b.txt,file,{_b64('x')}\nempty,dir,\n"
    csv_path = _write_csv(tmp_path, body)
    root = load_vfs(str(csv_path))
    expected = csv_path.stat().st_mtime
    assert root.mtime == expected
    assert root.children["a"].children["b.txt"].mtime == expected
    assert root.children["empty"].mtime == expected


def _small_tree(tmp_path):
    body = f"a/b/c.txt,file,{_b64('c')}\nroot.txt,file,{_b64('r')}\n"
    return load_vfs(str(_write_csv(tmp_path, body)))


def test_resolve_absolute_relative_and_dotdot(tmp_path):
    root = _small_tree(tmp_path)
    assert resolve(root, (), "/a/b")[0] == ("a", "b")
    assert resolve(root, ("a",), "b/c.txt")[0] == ("a", "b", "c.txt")
    assert resolve(root, ("a", "b"), "../../root.txt")[0] == ("root.txt",)
    assert resolve(root, ("a",), "..")[0] == ()
    assert resolve(root, (), "..")[0] == ()


def test_resolve_home_dot_and_extra_slashes(tmp_path):
    root = _small_tree(tmp_path)
    assert resolve(root, ("a",), "~")[0] == ()
    assert resolve(root, ("a",), "~/a/b")[0] == ("a", "b")
    assert resolve(root, ("a",), ".")[0] == ("a",)
    assert resolve(root, (), "//a///b/")[0] == ("a", "b")


def test_resolve_returns_the_node(tmp_path):
    root = _small_tree(tmp_path)
    parts, node = resolve(root, (), "a/b/c.txt")
    assert not node.is_dir
    assert node.content == b"c"
    assert resolve(root, (), "/")[1] is root


def test_resolve_failures_are_distinguished(tmp_path):
    root = _small_tree(tmp_path)
    with pytest.raises(PathNotFoundError):
        resolve(root, (), "a/nosuch")
    with pytest.raises(NotDirectoryError):
        resolve(root, (), "root.txt/x")
    with pytest.raises(PathNotFoundError):
        resolve(root, (), "nosuch/..")


def test_find_node_and_format_path(tmp_path):
    root = _small_tree(tmp_path)
    assert find_node(root, ("a", "b")).is_dir
    assert find_node(root, ()) is root
    assert format_path(()) == "/"
    assert format_path(("a", "b")) == "/a/b"


def test_split_parent():
    assert split_parent("a") == (".", "a")
    assert split_parent("a/b") == ("a", "b")
    assert split_parent("a/b/") == ("a", "b")
    assert split_parent("/a") == ("/", "a")
    assert split_parent("/a/b") == ("/a", "b")
    assert split_parent("~/a") == ("~", "a")


def test_attach_and_detach_edit_the_tree_and_touch_the_parent(tmp_path):
    root = _small_tree(tmp_path)
    folder = new_directory("fresh", ATTACH_TIME)
    attach(root, folder, ATTACH_TIME)
    assert root.children["fresh"] is folder
    assert root.mtime == ATTACH_TIME
    assert folder.mtime == ATTACH_TIME
    assert detach(root, "fresh", DETACH_TIME) is folder
    assert "fresh" not in root.children
    assert root.mtime == DETACH_TIME


def test_attach_replaces_a_same_named_entry(tmp_path):
    root = _small_tree(tmp_path)
    replacement = new_directory("root.txt", 1.0)
    attach(root, replacement, 1.0)
    assert root.children["root.txt"] is replacement
