"""Unit tests for shellemu.config."""

from shellemu.config import parse_cli_args, resolve_config


def test_cli_only():
    args = parse_cli_args(
        ["--vfs", "a.csv", "--log", "a.xml", "--script", "s.txt"]
    )
    config, error = resolve_config(args)
    assert config.vfs_path == "a.csv"
    assert config.log_path == "a.xml"
    assert config.script_path == "s.txt"
    assert error is None


def test_config_file_only(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "vfs_path: b.csv\nlog_path: b.xml\nscript_path: s2.txt\n"
    )
    args = parse_cli_args(["--config", str(config_file)])
    config, error = resolve_config(args)
    assert config.vfs_path == "b.csv"
    assert config.log_path == "b.xml"
    assert config.script_path == "s2.txt"
    assert error is None


def test_cli_overrides_config_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("vfs_path: from_file.csv\n")
    args = parse_cli_args(
        ["--config", str(config_file), "--vfs", "from_cli.csv"]
    )
    config, _error = resolve_config(args)
    assert config.vfs_path == "from_cli.csv"


def test_missing_config_file_reports_error():
    args = parse_cli_args(["--config", "/no/such/file.yaml"])
    config, error = resolve_config(args)
    assert error is not None
    assert "cannot read" in error
    assert config.config_path == "/no/such/file.yaml"


def test_invalid_yaml_reports_error(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("key: [unclosed")
    args = parse_cli_args(["--config", str(config_file)])
    _config, error = resolve_config(args)
    assert error is not None


def test_log_path_defaults_when_unset():
    args = parse_cli_args([])
    config, _error = resolve_config(args)
    assert config.log_path == "shellemu_log.xml"
