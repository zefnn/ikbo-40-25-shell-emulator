"""Entry point for launching the shell emulator's GUI."""

from .config import parse_cli_args, resolve_config
from .eventlog import EventLog
from .gui import ReplWindow


def main():
    """Resolve configuration, then create and run the REPL window."""
    cli_args = parse_cli_args()
    config, config_error = resolve_config(cli_args)
    logger = EventLog(config.log_path)
    app = ReplWindow(config, config_error, logger)
    app.mainloop()


if __name__ == "__main__":
    main()
