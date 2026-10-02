"""XML event log for command invocations."""

import datetime
import xml.etree.ElementTree as et


class EventLog:
    """Appends command-invocation events to an XML log file.

    Events persist across runs: an existing log file is loaded and
    new events are appended to it rather than starting over, so the
    file is a running history, not a per-session snapshot.
    """

    def __init__(self, path):
        """Open the log at ``path``, creating it on first write."""
        self._path = path
        self._root = self._load_or_create()

    def _load_or_create(self):
        """Load the existing <log> root, or start a fresh one."""
        try:
            return et.parse(self._path).getroot()
        except (OSError, et.ParseError):
            return et.Element("log")

    def log(self, name, args):
        """Record one command invocation with the current timestamp."""
        event = et.SubElement(self._root, "event")
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        event.set("timestamp", timestamp)
        et.SubElement(event, "command").text = name
        args_element = et.SubElement(event, "args")
        for arg in args:
            et.SubElement(args_element, "arg").text = arg
        self._save()

    def _save(self):
        """Write the full event tree back to the log file."""
        et.indent(self._root)
        et.ElementTree(self._root).write(
            self._path, encoding="UTF-8", xml_declaration=True
        )
