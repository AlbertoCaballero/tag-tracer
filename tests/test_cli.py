import json
import os
import re
import sys
from types import SimpleNamespace

import pytest

from tag_tracer import commands
from tag_tracer.cli import main
from tag_tracer.commands.validate import validate
from tag_tracer.commands.version import get_version

CONFIG = os.path.join(os.path.dirname(__file__), "..", "assets", "sample-config.xlsx")

FAILING_CAPTURE = [
    {
        "url": "https://unrelated.example.com/x",
        "method": "GET",
        "headers": {},
        "post_data": None,
    },
]

PASSING_CAPTURE = [
    {
        "url": "https://www.facebook.com/tr/?ev=ViewContent&cd=aut-ins&id=1244998375585961",
        "method": "GET",
        "headers": {},
        "post_data": None,
    },
    {
        "url": "https://www.googletagmanager.com/gtag/js?ad=something",
        "method": "GET",
        "headers": {},
        "post_data": None,
    },
    {
        "url": "https://fls.doubleclick.net/activityi?src=1",
        "method": "POST",
        "headers": {},
        "post_data": "flo=aefl",
    },
]


def _write_capture(tmp_path, requests):
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(requests))
    return str(path)


def _args(input_path, tmp_path):
    return SimpleNamespace(
        input=input_path,
        config=CONFIG,
        output=str(tmp_path / "out"),
        report_formats="none",
    )


def test_validate_returns_1_when_pages_fail(tmp_path):
    capture = _write_capture(tmp_path, FAILING_CAPTURE)
    assert validate(_args(capture, tmp_path)) == 1


def test_validate_returns_0_when_all_pass(tmp_path):
    capture = _write_capture(tmp_path, PASSING_CAPTURE)
    assert validate(_args(capture, tmp_path)) == 0


def test_cli_exit_code_failed(tmp_path, monkeypatch):
    capture = _write_capture(tmp_path, FAILING_CAPTURE)
    monkeypatch.setattr(
        sys,
        "argv",
        ["tag-tracer", "validate", "--input", capture, "--config", CONFIG,
         "--output", str(tmp_path / "out"), "--report-formats", "none"],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_cli_exit_code_passed(tmp_path, monkeypatch):
    capture = _write_capture(tmp_path, PASSING_CAPTURE)
    monkeypatch.setattr(
        sys,
        "argv",
        ["tag-tracer", "validate", "--input", capture, "--config", CONFIG,
         "--output", str(tmp_path / "out"), "--report-formats", "none"],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_version_matches_metadata():
    assert re.fullmatch(r"\d+\.\d+\.\d+", get_version())


def test_version_matches_pyproject():
    pyproject = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(pyproject) as f:
        content = f.read()
    declared = re.search(r'^version\s*=\s*"([^"]+)"', content, re.M).group(1)
    assert get_version() == declared


def test_version_fallback_to_pyproject(monkeypatch):
    """When the package metadata is unavailable, fall back to pyproject.toml."""
    version_module = commands.version

    def raise_not_found(pkg):
        raise version_module.metadata.PackageNotFoundError(pkg)

    monkeypatch.setattr(version_module.metadata, "version", raise_not_found)
    assert get_version() == "0.1.0"


def test_cli_version_output(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tag-tracer", "version"])
    main()
    out = capsys.readouterr().out
    assert re.search(r"version \d+\.\d+\.\d+", out)