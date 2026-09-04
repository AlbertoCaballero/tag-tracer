import json
import os
import sys
from types import SimpleNamespace

import pytest

from src.cli import main
from src.commands.validate import validate

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