# TagTracer – Project Outline

## 1. Overview

TagTracer is an automated tag validation tool designed to run an automated browser, capture all network requests, compare them against an Excel‑based configuration, and output validation results in multiple formats. It aims to simplify and speed up QA and compliance for marketing, analytics, and tracking implementations.

---

## 2. Core Requirements

* **Python-based** for long-term maintainability and strong Excel + automation support.
* **Browser automation** using Playwright (headed + stealth by default, optional headless).
* **Excel configuration input** for domains, expected parameters, and validation rules.
* **Network request capture** with full URL, method, query params, body payload, and headers.
* **Config-driven validation engine** to compare expected vs actual.
* **Flexible reporting** (HTML, JSON, Excel, and rich console output).
* **CLI tool** for simple execution.
* **Modular architecture** for expansion.
* **Automated testing** for stability.

---

## 3. Project Architecture

```
tag-tracer/
│
├── OUTLINE.md                  # Project outline (this file)
├── README.md                   # Documentation
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Python project file
│
├── assets/
│   ├── sample-config.xlsx      # Example Excel config
│   └── tagtracer_logo.png
│
├── src/
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point (argparse)
│   ├── models.py               # Pydantic data models (NetworkRequest)
│   │
│   ├── browser/
│   │   └── browser.py          # Playwright launcher + network capture
│   │
│   ├── commands/
│   │   ├── scan.py             # scan command
│   │   ├── validate.py         # validate command
│   │   └── version.py          # version command
│   │
│   ├── config/
│   │   └── loader.py           # Configuration loader from Excel to Pydantic models
│   │
│   ├── network_capture/
│   │   └── network_capture.py  # Request filtering + JSON persistence
│   │
│   ├── reporting/
│   │   ├── reporting.py        # Report format router
│   │   ├── console_report.py   # Rich console report
│   │   ├── html_report.py      # HTML report generator (Jinja2)
│   │   ├── json_report.py      # JSON report generator
│   │   ├── excel_report.py     # Excel report generator
│   │   └── templates/
│   │       └── report_template.html
│   │
│   ├── validation/
│   │   ├── validation.py       # Validation engine + result models
│   │   ├── rules.py            # Validation rule models
│   │   └── matcher.py          # Rule matcher (exact, regex, contains, present)
│   │
│   └── utils/
│       ├── utils.py            # Shared helpers
│       └── inspect_excel.py    # Excel inspection script
│
└── tests/
    ├── test_config_loader.py
    ├── test_validation.py
    └── test_browser_mock.py
```

---

## 4. Module Descriptions

### **4.1 config**

* Reads Excel file input (vendor sheets + pages sheet).
* Converts rows into structured Pydantic config objects (`ExcelConfig`, `VendorConfig`, `PageConfig`).
* Validates configuration integrity.

### **4.2 browser**

* Launches a Playwright browser with stealth configuration (anti-bot).
* Intercepts all network requests (query params, body, headers).
* Waits for late-firing tags (`--wait` settle time).
* Normalizes requests for processing.

### **4.3 validation**

* Matches captured requests against vendor domains.
* Extracts query, body (incl. JSON flattening), and header parameters.
* Resolves fields by declared location (query/body/header) with fallback.
* Validates parameters and expected values (exact, regex, contains, present).
* Scopes expected tags per vendor (`meta-ev` → vendor `meta`, field `ev`).
* Produces structured pass/fail outcomes.

### **4.4 reporting**

* Takes validation output and generates:

  * HTML report (Jinja2 template, filters, collapsible sections, expected/found tags)
  * JSON output
  * Excel summary
  * Rich console report

### **4.5 CLI**

* Provides `tag-tracer` command (argparse).
* Subcommands: `scan`, `validate`, `version`.
* Flags: `--url`, `--config`, `--output`, `--report-formats`, `--headless`, `--wait`.

### **4.6 utils**

* Shared helpers and small utilities.

### **4.7 tests**

* Automated unit tests (config loader, validator) and mock browser tests.

---

## 5. Requirements

### **5.1 Python Packages**

* `playwright`
* `pandas`
* `openpyxl`
* `rich` (console reporting)
* `pydantic` (config and result models)
* `jinja2` (HTML report templates)
* CLI built with `argparse` (standard library)
* Testing: `pytest`, `pytest-asyncio`, `pytest-mock`

### **5.2 Compatibility Constraints**

* Python 3.10+ recommended
* Should run on macOS, Windows, and Linux
* Headed + stealth mode by default (anti-bot), optional `--headless` flag
* Config file must follow TagTracer template format

---

## 6. Development Roadmap

### **Phase 1 — Setup**

* [x] Initialize repository and project structure
* [x] Add requirements.txt
* [x] Add pyproject.toml
* [x] Project scaffolding
* [x] Create sample Excel config structure

### **Phase 2 — Configuration Parsing**

* [x] Implement Excel parsing module
* [x] Validate configuration format
* [x] Build config object models

### **Phase 3 — Browser Automation**

* [x] Implement Playwright launcher
* [x] Implement network request capture
* [x] Normalize URLs, parameters, payload
* [x] Stealth / anti-bot configuration (headed by default, `--headless` opt-out)
* [x] Settle wait for late-firing tags (`--wait`)
* [x] HTTP/2 workaround (`--disable-http2`)
* [x] Store network calls in json report for reference
* [x] Enhanced HTML report: show all captured requests with all found parameters

#### **3.1 Enhanced HTML Report Plan**

Goal: make the HTML report a browsable view of every request captured during a
scan, not just the validated tags. Implemented.

* **Show all requests** — list every captured request (URL, method, vendor,
  status) grouped by page, each with an expandable detail view.
* **All parameters found** — the detail view exposes every query, body, and
  header parameter captured for the request, not only the expected-tag keys.
* **Show / hide** — per-request expand/collapse toggle plus global
  "Expand all" / "Collapse all" controls; Found Tags and Requests sections are
  also collapsible (closed by default).
* **Filters** (client-side, applied live):
  * by name (vendor and/or page ID)
  * by URL (substring on request URL)
  * by parameter (substring on any parameter key)
  * by page status (passed / failed)
* **Data flow** — `RequestValidationResult` carries the full `query_params`,
  `body_params`, and `header_params` dicts so the template can render them
  without re-parsing.

### **Phase 4 — Tag Matching & Validation**

* [x] Match requests to vendor domains
* [x] Extract query, body, and header parameters (incl. JSON body flattening)
* [x] Location-aware field lookup (query/body/header) with fallback
* [x] Vendor-scoped expected tags (e.g. `meta-ev` → vendor `meta`, field `ev`)
* [x] Compare actual vs expected values
* [x] Define validation rule types (exact, regex, contains, present)

### **Phase 5 — Reporting System**

* [x] Create JSON report generator
* [x] Create HTML report (templated) — filters, collapsible sections,
      expected/found tags, per-request params
* [x] Optional Excel export
* [x] Rich console report (readable terminal output)

### **Phase 6 — CLI Tool**

* [x] Implement CLI with argparse (subcommands: scan, validate, version)
* [x] Provide flags (url, config, output, report-formats, headless, wait)
* [x] Integrate modules together

### **Phase 7 — Testing**

* [x] Unit tests: config loader
* [x] Unit tests: validator
* [x] Browser tests with mock URLs
* [ ] Add CI workflow (optional)

### **Phase 8 — Polish & Release**

* [x] Add documentation (README + OUTLINE)
* [x] Add versioning (0.1.0)
* [ ] Package for PyPI (optional)

### **Current Status**

Phases 1–6 are complete. Phase 7 is essentially complete (only the optional CI
workflow remains). The project is in **Phase 8 — Polish & Release**: remaining
work is packaging for PyPI, single-source versioning, a LICENSE file, and a CI
workflow.

---

## 7. Naming Conventions

* **Project name:** TagTracer
* **CLI command:** `tag-tracer`
* **Package folder:** `src` (flat layout)
* **Config file template:** `tag-tracer-config.xlsx`

---

## 8. Future Enhancements (optional)

* Support for GTM container inspection
* Browser session video recording
* Real-time dashboard UI
* Scheduled runs with alerts
* YAML configuration support
* User-interaction simulation (clicks / scrolls) to trigger late-firing tags
* Non-zero exit codes for CI/CD gating
* Hostname-based domain matching (avoid substring false positives)
