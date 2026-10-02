"""Unit tests for shellemu.eventlog."""

import xml.etree.ElementTree as et

from shellemu.eventlog import EventLog


def test_log_creates_file_with_event(tmp_path):
    log_path = tmp_path / "log.xml"
    logger = EventLog(str(log_path))
    logger.log("ls", ["-la"])

    root = et.parse(log_path).getroot()
    events = root.findall("event")
    assert len(events) == 1
    assert events[0].find("command").text == "ls"
    assert events[0].get("timestamp")
    args = [el.text for el in events[0].find("args").findall("arg")]
    assert args == ["-la"]


def test_log_appends_across_instances(tmp_path):
    log_path = tmp_path / "log.xml"
    EventLog(str(log_path)).log("ls", [])
    EventLog(str(log_path)).log("cd", ["/tmp"])

    root = et.parse(log_path).getroot()
    commands = [event.find("command").text for event in root.findall("event")]
    assert commands == ["ls", "cd"]


def test_log_starts_fresh_if_file_missing(tmp_path):
    log_path = tmp_path / "does_not_exist_yet.xml"
    logger = EventLog(str(log_path))
    logger.log("exit", [])
    assert log_path.exists()
