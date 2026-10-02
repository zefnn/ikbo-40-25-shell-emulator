"""Entry point for launching the shell emulator's GUI."""

from .config import parse_cli_args, resolve_config
from .eventlog import EventLog
from .gui import ReplWindow
from .vfs import VfsError, load_vfs


def main():
    """Resolve config, load the VFS, then create and run the window."""
    cli_args = parse_cli_args()
    config, config_error = resolve_config(cli_args)
    logger = EventLog(config.log_path)

    vfs_root = None
    vfs_error = None
    if config.vfs_path:
        try:
            vfs_root = load_vfs(config.vfs_path)
        except VfsError as exc:
            vfs_error = str(exc)

    app = ReplWindow(config, config_error, vfs_root, vfs_error, logger)
    app.mainloop()


if __name__ == "__main__":
    main()
