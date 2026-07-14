"""Unit tests for skills/rhdh-release/scripts/ — jql.py, slack_templates.py, release.py, rich_filter.py."""

import json
import sys
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RELEASE_SCRIPTS = PROJECT_ROOT / "skills" / "rhdh-release" / "scripts"
if str(_RELEASE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_RELEASE_SCRIPTS))

import jql  # noqa: E402
import release  # noqa: E402
import rich_filter  # noqa: E402
import slack_templates  # noqa: E402

# =========================================================================
# jql.py
# =========================================================================


class TestJqlLoadTemplates:
    def setup_method(self):
        jql._TEMPLATE_CACHE = None
        jql._RICH_FILTER_PATH = None
        rich_filter.reset_cache()

    def teardown_method(self):
        jql._TEMPLATE_CACHE = None
        jql._RICH_FILTER_PATH = None
        rich_filter.reset_cache()

    def test_loads_11_markdown_templates(self):
        templates = jql.load_templates()
        assert len(templates) == 11

    def test_known_markdown_template_names(self):
        names = jql.list_templates()
        assert "active_release" in names
        assert "open_issues" in names
        assert "open_issues_by_type" in names
        assert "epics" in names
        assert "cves" in names
        assert "feature_demos" in names
        assert "feature_subtasks" in names
        assert "test_day_features" in names
        assert "features_added_to_release" in names
        assert "blockers" in names
        assert "open_issues_by_team" in names

    def test_rich_filter_templates_not_in_markdown(self):
        names = jql.list_templates()
        assert "feature_freeze_issues" not in names
        assert "feature_freeze_issues_by_team" not in names
        assert "code_freeze_issues" not in names
        assert "code_freeze_issues_by_team" not in names
        assert "release_notes" not in names


class TestJqlGetTemplate:
    def test_get_existing(self):
        tpl = jql.get_template("active_release")
        assert "rhdhplan" in tpl.lower()

    def test_get_nonexistent_raises(self):
        try:
            jql.get_template("nonexistent_query")
            assert False, "Expected KeyError"
        except KeyError as e:
            assert "nonexistent_query" in str(e)


class TestJqlRender:
    def test_render_version(self):
        rendered = jql.render("open_issues", version="1.9.0")
        assert '"1.9.0"' in rendered
        assert "{{RELEASE_VERSION}}" not in rendered

    def test_render_version_and_type(self):
        rendered = jql.render("open_issues_by_type", version="1.9.0", issue_type="Bug")
        assert '"1.9.0"' in rendered
        assert '"Bug"' in rendered
        assert "{{RELEASE_VERSION}}" not in rendered
        assert "{{ISSUE_TYPE}}" not in rendered

    def test_render_no_substitution(self):
        rendered = jql.render("active_release")
        assert "{{" not in rendered


class TestJqlUrl:
    def test_url_encoding(self):
        jql_str = "project = RHIDP AND status != closed"
        url = jql.jira_url(jql_str)
        assert url.startswith("https://issues.redhat.com/issues/?jql=")
        assert "%20" in url or "+" in url
        assert "project" not in url.split("jql=")[1].split("%")[0] or quote(jql_str, safe="") in url

    def test_url_encodes_special_chars(self):
        jql_str = 'fixVersion = "1.9.0" AND issuetype IN (Bug, Feature)'
        url = jql.jira_url(jql_str)
        encoded_part = url.split("jql=")[1]
        assert " " not in encoded_part
        assert '"' not in encoded_part
        assert "(" not in encoded_part

    def test_render_with_url(self):
        rendered, url = jql.render_with_url("open_issues", version="1.9.0")
        assert '"1.9.0"' in rendered
        assert url.startswith("https://issues.redhat.com/issues/?jql=")
        assert quote(rendered, safe="") in url


# =========================================================================
# slack_templates.py
# =========================================================================


class TestSlackLoadTemplates:
    def test_loads_4_templates(self):
        templates = slack_templates.load_templates()
        assert len(templates) == 4

    def test_known_template_keys(self):
        keys = slack_templates.list_templates()
        assert "feature_freeze_update" in keys
        assert "feature_freeze" in keys
        assert "code_freeze_update" in keys
        assert "code_freeze" in keys


class TestSlackGetTemplate:
    def test_get_existing(self):
        tpl = slack_templates.get_template("feature_freeze")
        assert "{{RELEASE_VERSION}}" in tpl

    def test_get_nonexistent_raises(self):
        try:
            slack_templates.get_template("nonexistent")
            assert False, "Expected KeyError"
        except KeyError as e:
            assert "nonexistent" in str(e)


class TestSlackFillPlaceholders:
    def test_basic_fill(self):
        template = "Hello {{NAME}}, version {{VERSION}}"
        result = slack_templates.fill_placeholders(
            template,
            {
                "NAME": "World",
                "VERSION": "1.0",
            },
        )
        assert result == "Hello World, version 1.0"

    def test_no_match_preserved(self):
        template = "{{UNKNOWN}} stays"
        result = slack_templates.fill_placeholders(template, {"OTHER": "val"})
        assert "{{UNKNOWN}}" in result


class TestSlackExpandTeamLines:
    def test_expands_team_block(self):
        template = (
            "Header\n"
            "• *{{TEAM_NAME}}* - [{{ISSUE_COUNT}}](url)\n"
            "(repeat for each active engineering team)\n"
            "Footer"
        )
        teams = [
            {"TEAM_NAME": "Alpha", "ISSUE_COUNT": "5"},
            {"TEAM_NAME": "Beta", "ISSUE_COUNT": "3"},
        ]
        result = slack_templates.expand_team_lines(template, teams)
        assert "• *Alpha* - [5](url)" in result
        assert "• *Beta* - [3](url)" in result
        assert "(repeat for each" not in result
        assert "Footer" in result


# =========================================================================
# release.py — CLI parsing
# =========================================================================


class TestReleaseParser:
    def test_no_args_exits_zero(self):
        try:
            release.main([])
        except SystemExit as e:
            assert e.code == 0

    def test_check_subcommand(self):
        parser = release.build_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"

    def test_status_subcommand(self):
        parser = release.build_parser()
        args = parser.parse_args(["status", "1.9.0"])
        assert args.command == "status"
        assert args.version == "1.9.0"

    def test_slack_subcommand(self):
        parser = release.build_parser()
        args = parser.parse_args(["slack", "feature-freeze", "1.9.0"])
        assert args.command == "slack"
        assert args.slack_command == "feature-freeze"
        assert args.version == "1.9.0"

    def test_global_json_flag(self):
        parser = release.build_parser()
        args = parser.parse_args(["--json", "status", "1.9.0"])
        assert args.output_mode == "json"

    def test_global_human_flag(self):
        parser = release.build_parser()
        args = parser.parse_args(["--human", "status", "1.9.0"])
        assert args.output_mode == "human"

    def test_verbose_flag(self):
        parser = release.build_parser()
        args = parser.parse_args(["--verbose", "check"])
        assert args.verbose is True

    def test_teams_category(self):
        parser = release.build_parser()
        args = parser.parse_args(["teams", "--category", "Engineering"])
        assert args.command == "teams"
        assert args.category == "Engineering"

    def test_all_subcommands_parse(self):
        parser = release.build_parser()
        for cmd in ["check", "dates", "slack"]:
            args = parser.parse_args([cmd])
            assert args.command == cmd
        for cmd in [
            "future-dates",
            "status",
            "team-breakdown",
            "blockers",
            "epics",
            "cves",
            "notes",
        ]:
            args = parser.parse_args([cmd, "1.0.0"])
            assert args.command == cmd
        args = parser.parse_args(["teams"])
        assert args.command == "teams"

    def test_all_slack_subcommands_parse(self):
        parser = release.build_parser()
        for cmd in ["feature-freeze-update", "feature-freeze", "code-freeze-update", "code-freeze"]:
            args = parser.parse_args(["slack", cmd, "1.0.0"])
            assert args.slack_command == cmd


class TestParseAcliCount:
    def test_standard_output(self):
        output = "✓ Number of work items in the search: 42"
        assert release._parse_acli_count(output) == 42

    def test_multiline_with_noise(self):
        output = "Connecting...\nSearching...\n✓ Number of work items in the search: 128\n"
        assert release._parse_acli_count(output) == 128

    def test_zero_count(self):
        output = "✓ Number of work items in the search: 0"
        assert release._parse_acli_count(output) == 0

    def test_large_count(self):
        output = "✓ Number of work items in the search: 12086"
        assert release._parse_acli_count(output) == 12086

    def test_no_count_raises(self):
        try:
            release._parse_acli_count("No numbers here")
            assert False, "Expected ValueError"
        except ValueError:
            pass


class TestCommandMapping:
    def test_all_commands_mapped(self):
        expected_commands = {
            "check",
            "dates",
            "future-dates",
            "status",
            "teams",
            "team-breakdown",
            "blockers",
            "epics",
            "cves",
            "notes",
        }
        assert expected_commands == set(release.COMMANDS.keys())

    def test_all_slack_commands_mapped(self):
        expected = {
            "feature-freeze-update",
            "feature-freeze",
            "code-freeze-update",
            "code-freeze",
        }
        assert expected == set(release.SLACK_COMMANDS.keys())


# =========================================================================
# release.py — _find_parse_issues discovery
# =========================================================================


class TestFindParseIssues:
    def test_returns_path_or_none(self):
        result = release._find_parse_issues()
        assert result is None or isinstance(result, Path)

    def test_sibling_path_resolves(self):
        sibling = (
            Path(__file__).resolve().parent.parent.parent
            / "skills"
            / "rhdh-jira"
            / "scripts"
            / "parse_issues.py"
        )
        result = release._find_parse_issues()
        if sibling.exists():
            assert result is not None
            assert result.exists()


# =========================================================================
# release.py — schedule parsing (inlined from schedule.py)
# =========================================================================


class TestNormalizeTeamName:
    def test_strips_rhdh_prefix(self):
        assert release._normalize_team_name("RHDH AI") == "ai"

    def test_case_insensitive_prefix(self):
        assert release._normalize_team_name("rhdh Cope") == "cope"

    def test_no_prefix(self):
        assert release._normalize_team_name("AI") == "ai"

    def test_whitespace_stripped(self):
        assert release._normalize_team_name("  RHDH AI  ") == "ai"

    def test_exact_match_lowered(self):
        assert release._normalize_team_name("Cope") == "cope"


class TestNormalizeVersion:
    def test_simple_version(self):
        assert release._normalize_version("1.9.0") == "1.9"

    def test_rhdh_prefix(self):
        assert release._normalize_version("RHDH 1.6") == "1.6"

    def test_dash_prefix(self):
        assert release._normalize_version("rhdh-1.6") == "1.6"

    def test_v_prefix(self):
        assert release._normalize_version("v1.6") == "1.6"


class TestParseDate:
    def test_iso_format(self):
        assert release._parse_date("2025-06-15") == "2025-06-15"

    def test_us_format(self):
        assert release._parse_date("06/15/2025") == "2025-06-15"

    def test_long_format(self):
        assert release._parse_date("June 15, 2025") == "2025-06-15"

    def test_unparseable(self):
        assert release._parse_date("not a date") is None


class TestFindScheduleTab:
    def test_finds_current_year(self):
        from datetime import datetime

        year = str(datetime.now().year)
        tabs = [f"RHDH {year} schedule", "Other", "Archive"]
        assert release._find_schedule_tab(tabs) == f"RHDH {year} schedule"

    def test_fallback_to_schedule(self):
        tabs = ["Other", "Schedule", "Archive"]
        assert release._find_schedule_tab(tabs) == "Schedule"

    def test_no_match(self):
        tabs = ["Sheet1", "Sheet2"]
        assert release._find_schedule_tab(tabs) is None


class TestFindMilestones:
    def test_finds_ga_and_freezes(self):
        rows = [
            ["Date", "Event", "Version"],
            ["2025-05-01", "Feature Freeze", "RHDH 1.9"],
            ["2025-05-15", "Code Freeze", "RHDH 1.9"],
            ["2025-06-01", "GA Announce", "RHDH 1.9"],
        ]
        result = release._find_milestones(rows, "1.9")
        assert result.get("ga_date") == "2025-06-01"
        assert result.get("code_freeze") == "2025-05-15"
        assert result.get("feature_freeze") == "2025-05-01"

    def test_version_not_found(self):
        rows = [
            ["Date", "Event"],
            ["2025-06-01", "GA Announce RHDH 1.8"],
        ]
        assert release._find_milestones(rows, "2.0") == {}


# =========================================================================
# rich_filter.py
# =========================================================================

SAMPLE_RICH_FILTER = {
    "richFilter": {
        "status": "active",
        "name": "RHIDP Operational",
        "jiraFilter": {
            "id": "27716",
            "name": "RHIDP Operational",
            "jql": "project in (rhidp, rhdhplan, rhdhsupp, rhdhbugs) and (resolutiondate >= -365d or status != Closed) ORDER BY priority DESC",
        },
        "staticFilters": [
            {
                "key": "k1",
                "name": "CVE",
                "jql": 'summary ~ "CVE-*"',
            },
            {
                "key": "k2",
                "name": "Feature Freeze",
                "jql": 'resolution is EMPTY AND component not in ("AEM Migration", AI) AND Type not in (Bug, Vulnerability, sub-task) AND status not in ("Dev Complete", "Release Pending", Done, Closed)',
            },
            {
                "key": "k3",
                "name": "Code Freeze",
                "jql": 'issuetype in (bug, Story, task, Vulnerability) AND status not in ("Release Pending", Closed) AND component not in ("AEM Migration", AI)',
            },
            {
                "key": "k4",
                "name": "demo",
                "jql": "labels in (demo)",
            },
        ],
        "smartFilters": [
            {
                "key": "sf1",
                "name": "Scrum Team",
                "andEnabled": False,
                "clauses": [
                    {
                        "key": "c1",
                        "name": "AI",
                        "jql": '"Team[Team]" = ec74d716-af36-4b3c-950f-f79213d08f71-1087',
                    },
                    {
                        "key": "c2",
                        "name": "Cope",
                        "jql": '"Team[Team]" = ec74d716-af36-4b3c-950f-f79213d08f71-4403',
                    },
                ],
            },
            {
                "key": "sf2",
                "name": "Delivery Team",
                "andEnabled": False,
                "clauses": [
                    {
                        "key": "c3",
                        "name": "Engineering",
                        "jql": "Team in (ec74d716-af36-4b3c-950f-f79213d08f71-1087)",
                    },
                ],
            },
        ],
        "richQueues": [
            {
                "key": "rq1",
                "name": "RNs Unclassified",
                "jql": '("Release Note Type" not in ("Release Note Not Required") OR "release note type" is EMPTY) AND summary !~ "CVE-*"',
            },
            {
                "key": "rq2",
                "name": "RNs Proposed",
                "jql": '"Release Note Status" in (Proposed)',
            },
        ],
    }
}


def _write_sample_rf(tmpdir: Path) -> Path:
    """Write sample Rich Filter JSON and return the file path."""
    rf_path = tmpdir / "rf.json"
    rf_path.write_text(json.dumps(SAMPLE_RICH_FILTER))
    return rf_path


class TestRichFilterParser:
    def setup_method(self):
        rich_filter.reset_cache()

    def test_load_returns_rich_filter_dict(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        rf = rich_filter.load(rf_path)
        assert rf is not None
        assert rf["name"] == "RHIDP Operational"

    def test_load_missing_file_returns_none(self, tmp_path):
        rf = rich_filter.load(tmp_path / "nonexistent.json")
        assert rf is None

    def test_load_bad_structure_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text('{"not_richFilter": {}}')
        try:
            rich_filter.load(bad)
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "richFilter" in str(e)

    def test_base_jql_strips_order_by(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        base = rich_filter.base_jql(rf_path)
        assert base is not None
        assert "ORDER BY" not in base
        assert "project in" in base.lower()

    def test_static_filter_by_name(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        ff = rich_filter.static_filter("Feature Freeze", rf_path)
        assert ff is not None
        assert "resolution is EMPTY" in ff

    def test_static_filter_case_insensitive(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        ff = rich_filter.static_filter("feature freeze", rf_path)
        assert ff is not None

    def test_static_filter_not_found(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        result = rich_filter.static_filter("Nonexistent", rf_path)
        assert result is None

    def test_smart_filter_clause(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql_str = rich_filter.smart_filter_clause("Scrum Team", "AI", rf_path)
        assert jql_str is not None
        assert "ec74d716" in jql_str

    def test_smart_filter_clause_not_found(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        result = rich_filter.smart_filter_clause("Scrum Team", "Missing", rf_path)
        assert result is None

    def test_rich_queue(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        rn = rich_filter.rich_queue("RNs Unclassified", rf_path)
        assert rn is not None
        assert "Release Note Type" in rn

    def test_rich_queue_not_found(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        result = rich_filter.rich_queue("Missing Queue", rf_path)
        assert result is None

    def test_scrum_teams(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        teams = rich_filter.scrum_teams(rf_path)
        assert teams is not None
        assert len(teams) == 2
        assert teams[0]["name"] == "AI"
        assert "ec74d716" in teams[0]["cloud_id"]
        assert teams[1]["name"] == "Cope"

    def test_list_static_filters(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        names = rich_filter.list_static_filters(rf_path)
        assert names is not None
        assert "Feature Freeze" in names
        assert "CVE" in names

    def test_list_smart_filters(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        names = rich_filter.list_smart_filters(rf_path)
        assert names is not None
        assert "Scrum Team" in names
        assert "Delivery Team" in names

    def test_list_rich_queues(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        names = rich_filter.list_rich_queues(rf_path)
        assert names is not None
        assert "RNs Unclassified" in names

    def test_caching(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        rf1 = rich_filter.load(rf_path)
        rf2 = rich_filter.load(rf_path)
        assert rf1 is rf2

    def test_reset_cache(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        rf1 = rich_filter.load(rf_path)
        rich_filter.reset_cache()
        rf2 = rich_filter.load(rf_path)
        assert rf1 is not rf2

    def test_load_none_without_file_returns_none(self):
        result = rich_filter.load()
        # Will return None if no file is discoverable in the default paths
        assert result is None or isinstance(result, dict)


# =========================================================================
# jql.py — Rich Filter integration
# =========================================================================


class TestJqlRichFilterIntegration:
    def setup_method(self):
        jql._TEMPLATE_CACHE = None
        rich_filter.reset_cache()

    def teardown_method(self):
        jql._TEMPLATE_CACHE = None
        jql._RICH_FILTER_PATH = None
        rich_filter.reset_cache()

    def test_adds_feature_freeze_from_rich_filter(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        templates = jql.load_templates()
        ff = templates["feature_freeze_issues"]
        assert "resolution is EMPTY" in ff
        assert "fixVersion" in ff
        assert "project in" in ff.lower()

    def test_adds_code_freeze_from_rich_filter(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        templates = jql.load_templates()
        cf = templates["code_freeze_issues"]
        assert "issuetype in (bug, Story, task, Vulnerability)" in cf
        assert "fixVersion" in cf

    def test_adds_release_notes_from_rich_filter(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        templates = jql.load_templates()
        rn = templates["release_notes"]
        assert "Release Note Type" in rn
        assert "fixVersion" in rn

    def test_adds_team_filter_from_rich_filter(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        templates = jql.load_templates()
        ff_team = templates["feature_freeze_issues_by_team"]
        assert "{{CLOUD_ID}}" in ff_team
        assert "Team[Team]" in ff_team

    def test_preserves_markdown_templates(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        templates = jql.load_templates()
        assert "active_release" in templates
        assert "blockers" in templates
        assert "epics" in templates
        assert "rhdhplan" in templates["active_release"].lower()

    def test_total_16_with_rich_filter(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        templates = jql.load_templates()
        assert len(templates) == 16

    def test_render_with_rich_filter(self, tmp_path):
        rf_path = _write_sample_rf(tmp_path)
        jql.set_rich_filter_path(rf_path)
        rendered = jql.render("feature_freeze_issues", version="2.1.0")
        assert '"2.1.0"' in rendered
        assert "{{RELEASE_VERSION}}" not in rendered


class TestJqlWithoutRichFilter:
    def setup_method(self):
        jql._TEMPLATE_CACHE = None
        jql._RICH_FILTER_PATH = None
        rich_filter.reset_cache()

    def teardown_method(self):
        jql._TEMPLATE_CACHE = None
        jql._RICH_FILTER_PATH = None
        rich_filter.reset_cache()

    def test_only_11_templates_without_rich_filter(self):
        jql.set_rich_filter_path(None)
        templates = jql.load_templates()
        assert len(templates) == 11

    def test_only_11_when_path_missing(self, tmp_path):
        jql.set_rich_filter_path(tmp_path / "nonexistent.json")
        templates = jql.load_templates()
        assert len(templates) == 11

    def test_freeze_templates_missing_without_rich_filter(self):
        jql.set_rich_filter_path(None)
        templates = jql.load_templates()
        assert "feature_freeze_issues" not in templates
        assert "code_freeze_issues" not in templates
        assert "release_notes" not in templates

    def test_freeze_template_raises_keyerror(self):
        jql.set_rich_filter_path(None)
        try:
            jql.get_template("feature_freeze_issues")
            assert False, "Expected KeyError"
        except KeyError as e:
            assert "feature_freeze_issues" in str(e)
