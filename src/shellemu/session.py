"""Per-run shell state: the loaded VFS and the working directory."""

from . import vfs
from .errors import CommandError


class Session:
    """Holds the VFS root and the current directory of one run."""

    def __init__(self, vfs_root=None):
        """Start at the VFS root, or with no VFS if ``vfs_root`` is None."""
        self.vfs_root = vfs_root
        self.cwd = ()
        self.previous_cwd = None

    def require_vfs(self, command):
        """Raise ``CommandError`` when ``command`` has no VFS to work on."""
        if self.vfs_root is None:
            raise CommandError(f"{command}: no VFS loaded")

    def resolve(self, path):
        """Resolve ``path`` against the working directory.

        Returns ``(parts, node)``; raises a ``VfsError`` subclass when
        the path does not lead to an existing entry.
        """
        return vfs.resolve(self.vfs_root, self.cwd, path)

    def change_dir(self, parts):
        """Make ``parts`` the working directory, remembering the old one."""
        self.previous_cwd = self.cwd
        self.cwd = parts

    def relocate(self, old_parts, new_parts):
        """Follow a moved directory: rebase cwd and previous cwd.

        Like a real shell whose directory was renamed under it, the
        session keeps working inside the same folder at its new path.
        """
        self.cwd = _rebase(self.cwd, old_parts, new_parts)
        if self.previous_cwd is not None:
            self.previous_cwd = _rebase(self.previous_cwd, old_parts, new_parts)

    def prompt(self):
        """Return the input prompt showing the working directory."""
        return f"VFS:{vfs.format_path(self.cwd)}$ "


def lookup_reason(error):
    """Return the UNIX wording for a failed path lookup."""
    if isinstance(error, vfs.NotDirectoryError):
        return "Not a directory"
    return "No such file or directory"


def lookup_message(command, path, error):
    """Describe a failed lookup as ``command: path: reason``."""
    return f"{command}: {path}: {lookup_reason(error)}"


def _rebase(parts, old_parts, new_parts):
    """Replace the prefix ``old_parts`` of ``parts`` with ``new_parts``."""
    if parts[:len(old_parts)] == old_parts:
        return new_parts + parts[len(old_parts):]
    return parts
