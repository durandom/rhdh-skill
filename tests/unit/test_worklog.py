"""Tests for worklog functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_dir.mkdir()
        with patch("rhdh_plugin.worklog.USER_CONFIG_DIR", config_dir):
            with patch("rhdh_plugin.worklog.WORKLOG_FILE", config_dir / "worklog.jsonl"):
                yield config_dir


class TestAddEntry:
    """Tests for add_entry function."""

    def test_creates_file_if_not_exists(self, temp_config_dir):
        from rhdh_plugin.worklog import WORKLOG_FILE, add_entry

        add_entry("Test message")
        assert WORKLOG_FILE.exists()

    def test_adds_entry_with_timestamp(self, temp_config_dir):
        from rhdh_plugin.worklog import WORKLOG_FILE, add_entry

        add_entry("Test message")
        content = WORKLOG_FILE.read_text()
        entry = json.loads(content.strip())
        assert "ts" in entry
        assert entry["msg"] == "Test message"

    def test_adds_entry_with_tags(self, temp_config_dir):
        from rhdh_plugin.worklog import WORKLOG_FILE, add_entry

        add_entry("Test message", tags=["tag1", "tag2"])
        content = WORKLOG_FILE.read_text()
        entry = json.loads(content.strip())
        assert entry["tags"] == ["tag1", "tag2"]

    def test_appends_multiple_entries(self, temp_config_dir):
        from rhdh_plugin.worklog import WORKLOG_FILE, add_entry

        add_entry("First")
        add_entry("Second")
        lines = WORKLOG_FILE.read_text().strip().split("\n")
        assert len(lines) == 2


class TestReadEntries:
    """Tests for read_entries function."""

    def test_returns_empty_list_if_no_file(self, temp_config_dir):
        from rhdh_plugin.worklog import read_entries

        entries = read_entries()
        assert entries == []

    def test_returns_entries_most_recent_first(self, temp_config_dir):
        from rhdh_plugin.worklog import add_entry, read_entries

        add_entry("First")
        add_entry("Second")
        entries = read_entries()
        assert len(entries) == 2
        assert entries[0]["msg"] == "Second"
        assert entries[1]["msg"] == "First"

    def test_respects_limit(self, temp_config_dir):
        from rhdh_plugin.worklog import add_entry, read_entries

        for i in range(10):
            add_entry(f"Entry {i}")
        entries = read_entries(limit=5)
        assert len(entries) == 5

    def test_since_filter(self, temp_config_dir):
        from rhdh_plugin.worklog import WORKLOG_FILE, read_entries

        # Write entries with known timestamps
        WORKLOG_FILE.write_text(
            '{"ts": "2025-01-01T00:00:00+00:00", "msg": "Old"}\n'
            '{"ts": "2025-06-01T00:00:00+00:00", "msg": "New"}\n'
        )
        entries = read_entries(since="2025-03-01")
        assert len(entries) == 1
        assert entries[0]["msg"] == "New"


class TestSearchEntries:
    """Tests for search_entries function."""

    def test_searches_message(self, temp_config_dir):
        from rhdh_plugin.worklog import add_entry, search_entries

        add_entry("Plugin onboarding started")
        add_entry("Build failed")
        matches = search_entries("plugin")
        assert len(matches) == 1
        assert "onboarding" in matches[0]["msg"]

    def test_searches_tags(self, temp_config_dir):
        from rhdh_plugin.worklog import add_entry, search_entries

        add_entry("Some message", tags=["onboard"])
        add_entry("Other message", tags=["build"])
        matches = search_entries("onboard")
        assert len(matches) == 1

    def test_case_insensitive(self, temp_config_dir):
        from rhdh_plugin.worklog import add_entry, search_entries

        add_entry("UPPERCASE message")
        matches = search_entries("uppercase")
        assert len(matches) == 1
