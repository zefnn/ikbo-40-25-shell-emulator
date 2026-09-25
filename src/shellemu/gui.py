"""Tkinter presentation layer for the shell emulator REPL."""


import tkinter as tk
from tkinter import scrolledtext

from . import repl


DEFAULT_VFS_NAME = "vladislav"


class ReplWindow(tk.Tk):
    """Main window: a scrollback pane plus a single input line."""

    def __init__(self, vfs_name=DEFAULT_VFS_NAME):
        super().__init__()
        self.title(f"Эмулятор — VFS: {vfs_name}")
        self._prompt = f"VFS:~$ "
        self._build_widgets()

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
        self._print(self._prompt, newline=False)

    def _on_submit(self, _event):
        """Handle Enter in the input field: run one REPL step."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self._print(line)
        output = repl.submit(line)
        if output is None:
            self.destroy()
            return
        if output:
            self._print(output)
        self._print(self._prompt, newline=False)

    def _print(self, text, newline=True):
        """Append text to the read-only scrollback pane."""
        self.output.configure(state="normal")
        self.output.insert("end", text + ("\n" if newline else ""))
        self.output.configure(state="disabled")
        self.output.see("end")
