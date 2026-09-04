"""Console reporting for TagTracer.

Renders validation summaries as readable rich output, mirroring the HTML report
structure (overall summary, per-page expected/found tags, per-request details)
without the interactive search and filter features.
"""

from datetime import datetime
from typing import Any, Dict

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config.loader import ExcelConfig
from src.models import NetworkRequest
from src.validation.validation import ValidationSummary

console = Console()


def _status(status: str) -> str:
    return "[green]PASSED[/green]" if status == "passed" else "[red]FAILED[/red]"


def _found(status: str) -> str:
    return "[green]FOUND[/green]" if status == "passed" else "[red]MISSING[/red]"


def _location(location: str) -> str:
    styles = {"query": "cyan", "body": "magenta", "header": "yellow", "N/A": "dim"}
    return f"[{styles.get(location, 'white')}]{location}[/{styles.get(location, 'white')}]"


def _display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(value.get("value", ""))
    return str(value)


def _param_table(title: str, params: Dict[str, Any]) -> Table:
    table = Table(title=title, box=box.SIMPLE, expand=False)
    table.add_column("Key", style="bold", overflow="fold")
    table.add_column("Value", overflow="fold")
    for key, value in params.items():
        table.add_row(key, str(value))
    return table


def print_header(title: str, subtitle: str = "") -> None:
    panel_text = f"[bold blue]{title}[/bold blue]"
    if subtitle:
        panel_text += f"\n[dim]{subtitle}[/dim]"
    console.print()
    console.print(Panel(panel_text, box=box.DOUBLE, expand=False))


def print_captured_requests(requests: list[NetworkRequest]) -> None:
    console.print()
    table = Table(
        title=f"Captured Network Requests ({len(requests)})",
        box=box.SIMPLE,
        header_style="bold",
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("Method", style="bold")
    table.add_column("URL", overflow="fold")
    for i, req in enumerate(requests, start=1):
        table.add_row(str(i), req.method or "GET", req.url)
    console.print(table)


def print_config_summary(config: ExcelConfig) -> None:
    console.print("\n[bold]Configuration[/bold]")

    vendors_table = Table(box=box.SIMPLE, header_style="bold")
    vendors_table.add_column("Vendor", style="bold")
    vendors_table.add_column("Domains", overflow="fold")
    vendors_table.add_column("Query Fields", overflow="fold")
    vendors_table.add_column("Body Fields", overflow="fold")
    vendors_table.add_column("Header Fields", overflow="fold")
    for name, vendor in config.vendors.items():
        vendors_table.add_row(
            name,
            ", ".join(vendor.domains) or "-",
            ", ".join(vendor.query_fields) or "-",
            ", ".join(vendor.body_fields) or "-",
            ", ".join(vendor.header_fields) or "-",
        )
    console.print(vendors_table)

    pages_table = Table(box=box.SIMPLE, header_style="bold")
    pages_table.add_column("ID", style="bold")
    pages_table.add_column("URL", overflow="fold")
    pages_table.add_column("Vendors", overflow="fold")
    pages_table.add_column("Expected Tags", overflow="fold")
    for page in config.pages:
        expected = ", ".join(page.expected_tags.keys()) or "-"
        pages_table.add_row(
            page.id, page.target_url, ", ".join(page.page_vendors), expected
        )
    console.print(pages_table)


def print_validation_summary(summary: ValidationSummary) -> None:
    console.print()
    console.print(
        Panel(
            "[bold blue]TagTracer Validation Report[/bold blue]\n"
            f"[dim]Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            box=box.DOUBLE,
            expand=False,
        )
    )

    summary_table = Table(box=box.SIMPLE_HEAVY, header_style="bold")
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    summary_table.add_row("Total Pages Scanned", str(summary.total_pages_scanned))
    summary_table.add_row("Pages Passed", f"[green]{summary.pages_passed}[/green]")
    summary_table.add_row("Pages Failed", f"[red]{summary.pages_failed}[/red]")
    console.print(summary_table)

    for page in summary.page_results:
        _print_page(page)


def _print_page(page) -> None:
    border = "green" if page.overall_status == "passed" else "red"
    console.print()
    console.print(
        Panel(
            f"[bold]Page: {page.page_id}[/bold] — {page.page_url} {_status(page.overall_status)}",
            box=box.SQUARE,
            border_style=border,
        )
    )
    console.print(
        f"Expected Tags: {page.expected_tags_count} | "
        f"Matched Requests: {page.matched_requests_count}"
    )

    # Expected tags
    expected_table = Table(box=box.SIMPLE, header_style="bold", expand=False)
    expected_table.add_column("Tag", style="bold", overflow="fold")
    expected_table.add_column("Vendor")
    expected_table.add_column("Field", style="dim")
    expected_table.add_column("Location")
    expected_table.add_column("Expected", overflow="fold")
    expected_table.add_column("Actual", overflow="fold")
    expected_table.add_column("Status", justify="center")
    for tag in page.expected_tag_status:
        expected_table.add_row(
            tag["key"],
            tag.get("vendor") or "-",
            tag["field"],
            _location(tag["location"]),
            _display_value(tag["expected_value"]),
            _display_value(tag["actual_value"]),
            _found("passed" if tag["found"] else "failed"),
        )
    expected_table.title = "Expected Tags"
    console.print(expected_table)

    # Found tags
    if page.found_tags:
        console.print(_param_table("Found Tags", page.found_tags))

    # Requests
    for request in page.request_results:
        _print_request(request)


def _print_request(request) -> None:
    border = "green" if request.overall_status == "passed" else "red"
    console.print()
    console.print(
        Panel(
            f"[bold]{request.method or 'GET'}[/bold] {request.request_url} "
            f"{_status(request.overall_status)}",
            box=box.SQUARE,
            border_style=border,
        )
    )
    console.print(
        f"Vendor: {request.vendor_name} | "
        f"Matched Domains: {', '.join(request.matched_domains) or '-'}"
    )

    for label, params in (
        ("Query Parameters", request.query_params),
        ("Body Parameters", request.body_params),
        ("Headers", request.header_params),
    ):
        if params:
            console.print(_param_table(label, params))

    if request.tags_validated:
        tags_table = Table(box=box.SIMPLE, header_style="bold", expand=False)
        tags_table.add_column("Tag", style="bold", overflow="fold")
        tags_table.add_column("Field", style="dim")
        tags_table.add_column("Location")
        tags_table.add_column("Expected", overflow="fold")
        tags_table.add_column("Actual", overflow="fold")
        tags_table.add_column("Rule")
        tags_table.add_column("Status", justify="center")
        tags_table.add_column("Message", overflow="fold")
        for tag in request.tags_validated:
            tags_table.add_row(
                tag.key,
                tag.field,
                _location(tag.location),
                _display_value(tag.expected_value),
                _display_value(tag.actual_value),
                tag.rule_type,
                _status(tag.status),
                tag.message,
            )
        tags_table.title = "Tag Validations"
        console.print(tags_table)