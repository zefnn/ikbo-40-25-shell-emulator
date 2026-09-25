"""Entry point for launching the shell emulator's GUI."""

from .gui import ReplWindow


def main():
    """Create and run the REPL window's Tkinter event loop."""
    app = ReplWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
