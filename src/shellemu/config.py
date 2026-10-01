"""Command-line arguments and YAML config file resolution."""

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_LOG_PATH = "shellemu_log.xml"


class ConfigError(Exception):
    """Raised when the config file cannot be read or parsed."""


@dataclass
class AppConfig:
    """Fully resolved settings the emulator runs with."""

    vfs_path: str | None
    log_path: str
    script_path: str | None
    config_path: str | None


def parse_cli_args(argv=None):
    """Define and parse the emulator's command-line parameters."""
    parser = argparse.ArgumentParser(description="UNIX-like shell emulator")
    parser.add_argument("--vfs", dest="vfs_path", default=None)
    parser.add_argument("--log", dest="log_path", default=None)
    parser.add_argument("--script", dest="script_path", default=None)
    parser.add_argument("--config", dest="config_path", default=None)
    return parser.parse_args(argv)


def load_yaml_config(path):
    """Read a YAML config file and return its mapping of settings."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config file: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in config file: {exc}") from exc
    return data or {}


def resolve_config(cli_args):
    """Merge CLI arguments with the YAML config file (CLI wins).

    Returns an ``(AppConfig, error)`` pair. ``error`` is a message
    string when the config file was given but failed to load, else
    ``None``. Even when loading fails, the returned config still
    carries whatever values the CLI arguments supplied.
    """
    file_values = {}
    error = None
    if cli_args.config_path:
        try:
            file_values = load_yaml_config(cli_args.config_path)
        except ConfigError as exc:
            error = str(exc)

    config = AppConfig(
        vfs_path=cli_args.vfs_path or file_values.get("vfs_path"),
        log_path=(
            cli_args.log_path
            or file_values.get("log_path")
            or DEFAULT_LOG_PATH
        ),
        script_path=cli_args.script_path or file_values.get("script_path"),
        config_path=cli_args.config_path,
    )
    return config, error
