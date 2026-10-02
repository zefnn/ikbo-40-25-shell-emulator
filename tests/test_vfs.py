"""Unit tests for shellemu.vfs."""

import base64

import pytest

from shellemu.vfs import VfsError, count_entries, load_vfs

HEADER = "path,type,content\n"


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
