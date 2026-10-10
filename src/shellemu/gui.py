"""Tkinter presentation layer for the shell emulator REPL."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

from . import repl, vfs

DEFAULT_VFS_NAME = "(не задана)"


class ReplWindow(tk.Tk):
    """Main window: a scrollback pane plus a single input line."""

    def __init__(self, config, config_error, session, vfs_error, logger):
        """Build the window for the given resolved configuration."""
        super().__init__()
        self._logger = logger
        self._session = session
        vfs_name = (
            os.path.basename(config.vfs_path)
            if config.vfs_path
            else DEFAULT_VFS_NAME
        )
        self.title(f"Эмулятор — VFS: {vfs_name}")
        self._build_widgets()
        self._print_startup_info(config, config_error, vfs_error)
        self._print(self._session.prompt(), newline=False)
        if config.script_path:
            self._run_startup_script(config.script_path)

    def _build_widgets(self):
        """Create and lay out the scrollback pane and input entry."""
        self.output = scrolledtext.ScrolledText(
            self, state="disabled", width=100, height=30
        )
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(self)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self._on_submit)
        self.entry.focus_set()

    def _print_startup_info(self, config, config_error, vfs_error):
        """Echo the resolved configuration, VFS and any load errors."""
        for key, value in [
            ("vfs_path", config.vfs_path),
            ("log_path", config.log_path),
            ("script_path", config.script_path),
            ("config_path", config.config_path),
        ]:
            self._print(f"[config] {key} = {value}")
        if config_error:
            self._print(f"config error: {config_error}")
        if self._session.vfs_root is not None:
            files, dirs = vfs.count_entries(self._session.vfs_root)
            self._print(f"[vfs] loaded: {files} files, {dirs} directories")
        if vfs_error:
            self._print(f"VFS error: {vfs_error}")

    def _run_startup_script(self, path):
        """Replay every line of the startup script, then resume input."""
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            self._print(f"startup script error: {exc}")
            self._print(self._session.prompt(), newline=False)
            return
        for line in lines:
            if self._run_one_line(line):
                return

    def _on_submit(self, _event):
        """Handle Enter in the input field: run one REPL step."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self._run_one_line(line)

    def _run_one_line(self, line):
        """Echo, execute and show the result of one input line.

        The prompt for this line is assumed to already be on screen
        (printed by the previous step); this prints the next prompt
        itself once done. Returns True if the window was closed.
        """
        self._print(line)
        output = repl.submit(line, self._session, logger=self._logger)
        if output is None:
            self.destroy()
            return True
        if output is repl.CLEAR_SCREEN:
            self._clear()
        elif output:
            self._print(output)
        self._print(self._session.prompt(), newline=False)
        return False

    def _clear(self):
        """Erase everything shown in the scrollback pane."""
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _print(self, text, newline=True):
        """Append text to the read-only scrollback pane."""
        self.output.configure(state="normal")
        self.output.insert("end", text + ("\n" if newline else ""))
        self.output.configure(state="disabled")
        self.output.see("end")
