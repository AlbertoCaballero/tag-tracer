# TagTracer

<div align="center">

<!-- Simple modern SVG logo -->

<img src="assets/tagtracer_logo.png" alt="TagTracer Logo" width="100%" />

</div>

A lightweight, automated tool designed to validate marketing, analytics, and tracking tags using a headless browser, with configuration-driven rules powered by Excel.

---

## Overview

TagTracer accelerates the QA workflow for digital analytics implementations. It programmatically loads a webpage, captures all network calls, compares them against an Excel-based validation rule set, and produces clear reports identifying valid tags, missing tags, and incorrect parameter values.

TagTracer is particularly useful for:

* Analytics audits
* Marketing tag verification
* Pre-release QA for new features
* Regression testing for tracking
* Ongoing compliance monitoring

---

## Key Features

* **Headless browser scanning** using Playwright.
* **Network interception** for all requests.
* **Excel-driven configuration** for domains, rules, and expected values.
* **Flexible validation engine** supporting exact, partial, and regex matching.
* **Multiple report formats:** HTML, JSON, and optional Excel.
* **Command-line interface:** `tag-tracer` for rapid testing.
* **Modular architecture** for long-term maintainability.

---

## Use Cases

### 1. Digital Analytics QA

Ensure that Adobe Analytics, GA4, Meta Pixel, TikTok, LinkedIn, or any custom tag fires correctly with all required parameters.

### 2. Marketing Tag Compliance

Validate tracking pixels, conversion tags, and remarketing parameters prior to publishing campaigns.

### 3. Continuous Monitoring

Schedule scans to detect when tags break due to deployments or platform changes.

### 4. Automated Regression Testing

Integrate into CI/CD pipelines to verify instrumentation stability.

### 5. Vendor Migration Support

When migrating from one analytics platform to another, TagTracer helps validate parity across implementations.

---

## Installation (coming soon)

```
pip install tag-tracer
```

Or local development:

```
git clone https://github.com/your-repo/tag-tracer
cd tag-tracer
pip install -r requirements.txt
```

---

## Quick Start

```
tag-tracer --url "https://example.com" \
           --config config/tag-tracer-config.xlsx \
           --output reports/
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

MIT License (pending)

---

## Maintainers

TagTracer is designed for long-term accuracy and maintainability in digital analytics workflows.
