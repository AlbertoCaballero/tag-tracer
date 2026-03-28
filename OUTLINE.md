# TagTracer – Project Outline

## 1. Overview

TagTracer is an automated tag validation tool designed to run a headless browser, capture all network requests, compare them against an Excel‑based configuration, and output validation results in multiple formats. It aims to simplify and speed up QA and compliance for marketing, analytics, and tracking implementations.

---

## 2. Core Requirements

* **Python-based** for long-term maintainability and strong Excel + automation support.
* **Headless browser automation** using Playwright.
* **Excel configuration input** for domains, expected parameters, and validation rules.
* **Network request capture** with full URL, method, query params, and payload.
* **Config-driven validation engine** to compare expected vs actual.
* **Flexible reporting** (HTML, JSON, Excel).
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
├── config/
│   └── sample_config.xlsx      # Example Excel config
│
├── src/
│   ├── tag_tracer
│   │   ├── __init__.py
│   │   └── cli.py              # CLI entry point
│   │
│   ├── browser/
│   │   └── browser.py          # Browser session initialicer
│   │
│   ├── config/
│   │   └── loader.py           # Configuration loader from Excel to Pydantic models
│   │
│   ├── network_capture/
│   │   └── network_capture.py  # Network capture engine
│   │
│   ├── reporting/
│   │   ├── reporting.py        # Reporting, agregation and format engine
│   │   ├── html_report.py
│   │   ├── json_report.py
│   │   └── excel_report.py
│   │
│   ├── validation/
│   │   ├── validation.py       # Validation engine
│   │   ├── rules.py
│   │   └── matcher.py
│   │
│   └── utils/
│       └── utils.py
│
└── tests/
    ├── test_config_loader.py
    ├── test_validation.py
    └── test_browser_mock.py
```

---

## 4. Module Descriptions

### **4.1 config**

* Reads Excel file input.
* Converts rows into structured Pydantic config objects.
* Validates configuration integrity.

### **4.2 browser**

* Launches a headless browser instance.
* Intercepts all network requests.
* Normalizes requests for processing.

### **4.3 validation**

* Matches captured requests against vendor rules.
* Validates parameters and expected values.
* Produces structured pass/fail outcomes.

### **4.4 reporting**

* Takes validation output and generates:

  * HTML report
  * JSON output
  * Excel summary

### **4.5 CLI**

* Provides `tag-tracer` command.
* Allows specifying URL, config file, output type.

### **4.6 utils**

* Shared helpers and small utilities.

### **4.7 tests**

* Automated unit tests and mock browser tests.

---

## 5. Requirements

### **5.1 Python Packages**

* `playwright`
* `pandas`
* `openpyxl`
* `typer` (or Click) for CLI
* `jinja2` for HTML report templates
* `pytest` for testing

### **5.2 Compatibility Constraints**

* Python 3.10+ recommended
* Should run on macOS, Windows, and Linux
* Must support headless mode by default but allow non-headless for debugging
* Config file must follow TagTracer template format

---

## 6. Development Roadmap

### **Phase 1 — Setup**

* [✅] Initialize repository and project structure
* [✅] Add requirements.txt
* [✅] Add pyproject.txt
* [✅] Project scaffolding
* [✅] Create sample Excel config structure

### **Phase 2 — Configuration Parsing**

* [✅] Implement Excel parsing module
* [✅] Validate configuration format
* [✅] Build config object models

### **Phase 3 — Browser Automation**

* [✅] Implement Playwright launcher
* [✅] Implement network request capture
* [✅] Normalize URLs, parameters, payload

### **Phase 4 — Tag Matching & Validation**

* [ ] Match requests to vendor domains
* [ ] Extract query and body parameters
* [ ] Compare actual vs expected values
* [ ] Define validation rule types (exact, regex, contains)

### **Phase 5 — Reporting System**

* [ ] Create JSON report generator
* [ ] Create HTML report (templated)
* [ ] Optional Excel export

### **Phase 6 — CLI Tool**

* [ ] Implement CLI with Typer
* [ ] Provide flags (url, config, output, headless)
* [ ] Integrate modules together

### **Phase 7 — Testing**

* [ ] Unit tests: config loader
* [ ] Unit tests: validator
* [ ] Browser tests with mock URLs
* [ ] Add CI workflow (optional)

### **Phase 8 — Polish & Release**

* [ ] Add documentation
* [ ] Add versioning
* [ ] Package for PyPI (optional)

---

## 7. Naming Conventions

* **Project name:** TagTracer
* **CLI command:** `tag-tracer`
* **Package folder:** `tag_tracer`
* **Config file template:** `tag-tracer-config.xlsx`

---

## 8. Future Enhancements (optional)

* Support for GTM container inspection
* Browser session video recording
* Real-time dashboard UI
* Scheduled runs with alerts
