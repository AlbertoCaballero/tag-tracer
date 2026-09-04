# tag-tracer

<div align="center">

<!-- Simple modern SVG logo -->

<img src="assets/tagtracer_logo.png" alt="TagTracer Logo" width="100%" />

</div>

A lightweight, automated tool designed to validate marketing, analytics, and tracking tags using an automated browser, with configuration-driven rules powered by Excel.

---

## Overview

TagTracer accelerates the QA workflow for digital analytics implementations. It launches a real browser, captures all network requests a page makes, compares them against an Excel-based validation rule set, and produces clear reports identifying valid tags, missing tags, and incorrect parameter values.

TagTracer is particularly useful for:

* Analytics audits
* Marketing tag verification
* Pre-release QA for new features
* Regression testing for tracking
* Ongoing compliance monitoring

---

## Key Features

* **Real-browser scanning** using Playwright, with stealth configuration to avoid bot detection (headed by default, optional `--headless`).
* **Network interception** for every request — URLs, query params, body payloads (form-encoded and JSON), and headers.
* **Excel-driven configuration** for vendors, domains, fields, and expected values.
* **Location-aware validation** — each expected field is looked up in the location the vendor sheet declares (query / body / header), with automatic fallback.
* **Flexible matching** supporting exact, regex, contains, and "present" rules.
* **Rich console report** for readable terminal output.
* **Multiple report formats:** interactive HTML, JSON, and Excel.
* **CI/CD friendly** — non-zero exit code when any page fails.
* **Command-line interface:** `tag-tracer` for rapid testing.
* **Modular architecture** for long-term maintainability.

---

## How It Works

1. **Configure** — define vendors and pages in an Excel workbook (see [Configuration](#configuration)).
2. **Scan** — `tag-tracer scan` opens a page in a browser, waits for the page to settle, and captures every network request.
3. **Validate** — captured requests are filtered to the configured vendor domains, matched against expected tags, and compared field-by-field.
4. **Report** — results are printed to the console and exported to HTML / JSON / Excel.

---

## Use Cases

### 1. Digital Analytics QA

Ensure that Adobe Analytics, GA4, Meta Pixel, TikTok, LinkedIn, or any custom tag fires correctly with all required parameters.

### 2. Marketing Tag Compliance

Validate tracking pixels, conversion tags, and remarketing parameters prior to publishing campaigns.

### 3. Continuous Monitoring

Schedule scans to detect when tags break due to deployments or platform changes.

### 4. Automated Regression Testing

Integrate into CI/CD pipelines to verify instrumentation stability. The non-zero exit code on failure lets a pipeline fail when a tag is missing or wrong.

### 5. Vendor Migration Support

When migrating from one analytics platform to another, TagTracer helps validate parity across implementations.

---

## Installation

Requires Python 3.10+.

```
git clone https://github.com/AlbertoCaballero/tag-tracer
cd tag-tracer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m playwright install chromium
```

Verify the install:

```
tag-tracer version
```

---

## Configuration

Configuration is an Excel workbook with one **pages** sheet and one sheet **per vendor** (the sheet name is the vendor name).

### Pages sheet

Each row is a page to scan. The `vendors` column lists the vendor sheet names for the page. Every other column is an **expected tag** named `<vendor>-<field>` with the expected value in the cell — e.g. `meta-ev` means "vendor `meta`, field `ev`".

| id | target-url | vendors | meta-ev | meta-cd | meta-id | google-ad | floodlight-flo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| auto | `https://www.example.com/auto` | `[meta, google, floodlight]` | ViewContent | aut-ins | 1244998375585961 | something | aefl |

### Vendor sheets

Each vendor sheet declares where its fields live. `domain` is the host the requests go to; `query-fields`, `body-fields`, and `header-fields` tell TagTracer where to look for each field.

`meta` sheet:

| vendor | meta |
| --- | --- |
| domain | www.facebook.com |
| query-fields | [ev, cd, id] |
| body-fields | [data.field, data.something] |
| header-fields | [] |

`google` sheet:

| vendor | google |
| --- | --- |
| domain | www.googletagmanager.com |
| query-fields | [ad] |

`floodlight` sheet:

| vendor | floodlight |
| --- | --- |
| domain | fls.doubleclick.net |
| body-field | [flo] |

**How a tag is validated:** `meta-ev` with expected value `ViewContent` maps to vendor `meta`, field `ev`. Because `ev` is listed under `query-fields`, TagTracer looks for `ev` in the query string of Meta requests and compares its value to `ViewContent`. Fields are resolved against the declared location first and fall back to the other sources if not found there.

A copy of this example is available at `assets/sample-config.xlsx`.

---

## Quick Start

### Scan a page

```
tag-tracer scan \
  --url "https://www.example.com/auto" \
  --config assets/sample-config.xlsx \
  --output reports
```

This launches the browser, captures the page's network requests, validates them, prints a report, and writes `validation_report_<timestamp>.json` and `.html` into `reports/`.

### Validate a previous capture

```
tag-tracer validate \
  --input reports/captured_filtered_requests.json \
  --config assets/sample-config.xlsx \
  --output reports
```

---

## Commands

### `scan`

| Flag | Default | Description |
| --- | --- | --- |
| `--url` | `all` | URL to scan. |
| `--config` | — | Path to the Excel configuration file (required). |
| `--output` | `output` | Directory for captured requests and reports. |
| `--report-formats` | `json,html` | Comma-separated list of report formats: `json`, `html`, `excel`. |
| `--headless` | off | Run the browser in headless mode. |
| `--wait` | `5` | Seconds to wait after page load for tags to fire. |

### `validate`

| Flag | Default | Description |
| --- | --- | --- |
| `--input` | — | Path to a previously captured network log (JSON) (required). |
| `--config` | — | Path to the Excel configuration file (required). |
| `--output` | `output` | Directory for generated reports. |
| `--report-formats` | `json,html` | Comma-separated list of report formats: `json`, `html`, `excel`. |

### `version`

Prints the TagTracer version.

---

## Example Output

```
╔══════════════════════════════════════════════╗
║ TagTracer Validation Report                  ║
║ Generated on 2026-09-04 04:05:31            ║
╚══════════════════════════════════════════════╝

  Metric                Value
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Pages Scanned       3
  Pages Passed              3
  Pages Failed              0

┌──────────────────────────────────────────────────────────────┐
│ Page: auto — https://www.example.com/auto  PASSED           │
└──────────────────────────────────────────────────────────────┘
Expected Tags: 5 | Matched Requests: 3

  Tag          Vendor     Field  Location  Expected   Actual    Status
 ─────────────────────────────────────────────────────────────────────
  meta-ev      meta       ev     query     ViewConten ViewConte FOUND
  meta-cd      meta       cd     query     aut-ins    aut-ins   FOUND
  google-ad    google     ad     query     something  something FOUND
  floodlight-flo floodlight flo  body      aefl       aefl      FOUND

PASSED — all 3 pages passed validation.
```

Each request is listed below its page with its query/body/header parameters and per-tag validations.

---

## Reports

* **Console** — rich, color-coded terminal output (shown above).
* **HTML** — an interactive report with live filters (by name, URL, parameter, and page status), collapsible sections, expected vs found tags, and full per-request parameters.
* **JSON** — machine-readable validation results, ideal for downstream tooling.
* **Excel** — a summary sheet plus a detailed sheet with one row per validated tag.

---

## Stealth & bot detection

By default TagTracer launches a **headed** (visible) Chromium browser with stealth tweaks — `--disable-blink-features=AutomationControlled`, `navigator.webdriver` masking, and a realistic user agent — so that scans are less likely to be detected and blocked by websites. Headed mode is the default because headless browsers are easier for anti-bot systems to fingerprint. If stealth is not a concern, pass `--headless` to run without a visible window.

## Capturing late-firing tags

Analytics and marketing tags often fire on the `load` event or after a delay, not at DOMContentLoaded. TagTracer therefore waits for the page to settle before collecting the captured requests. The default wait is 5 seconds; adjust it with `--wait` (pass `--wait 0` to disable):

```
tag-tracer scan \
  --url "https://www.example.com/auto" \
  --config assets/sample-config.xlsx \
  --output reports \
  --wait 8
```

## Exit codes

`tag-tracer scan` and `tag-tracer validate` exit with status `0` when every page passes validation and `1` when any page fails (or an error occurs). This makes TagTracer easy to gate on in CI/CD pipelines:

```
tag-tracer validate --input captured.json --config config.xlsx
# $? == 0 when all pages passed, 1 when any failed
```

---

## Roadmap

The full roadmap is available in the `OUTLINE.md` file. Upcoming enhancements include:

* GTM container inspection
* Session video recording
* Dashboard UI
* PyPI distribution

---

## License

[MIT](LICENSE)

---

## Maintainers

TagTracer is designed for long-term accuracy and maintainability in digital analytics workflows.