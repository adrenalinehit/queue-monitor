#!/usr/bin/env python3
"""AWS SQS Queue Monitor — real-time terminal dashboard for SQS queue metrics."""

import argparse
import logging
import signal
import sys
import time
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class Thresholds:
    warn: int
    critical: int


@dataclass
class QueueMetrics:
    url: str
    name: str
    visible: int = 0
    in_flight: int = 0
    delayed: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# AWS helpers
# ---------------------------------------------------------------------------


def create_sqs_client(region: str | None, profile: str | None):
    kwargs: dict = {}
    if profile:
        kwargs["profile_name"] = profile
    if region:
        kwargs["region_name"] = region
    return boto3.Session(**kwargs).client("sqs")


def discover_queues(sqs, prefix: str) -> list[str]:
    """Return all queue URLs whose name starts with *prefix*."""
    urls: list[str] = []
    params: dict = {"QueueNamePrefix": prefix}
    while True:
        resp = sqs.list_queues(**params)
        urls.extend(resp.get("QueueUrls", []))
        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token
    return urls


def fetch_metrics(sqs, queue_url: str) -> QueueMetrics:
    name = queue_url.rstrip("/").rsplit("/", 1)[-1]
    try:
        resp = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=[
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
                "ApproximateNumberOfMessagesDelayed",
            ],
        )
        attrs = resp["Attributes"]
        return QueueMetrics(
            url=queue_url,
            name=name,
            visible=int(attrs.get("ApproximateNumberOfMessages", 0)),
            in_flight=int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0)),
            delayed=int(attrs.get("ApproximateNumberOfMessagesDelayed", 0)),
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("Failed to fetch metrics for %s: %s", name, exc)
        return QueueMetrics(url=queue_url, name=name, error=str(exc))


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def status_for(visible: int, t: Thresholds) -> tuple[str, str]:
    if visible >= t.critical:
        return "CRITICAL", "bold red"
    if visible >= t.warn:
        return "WARNING", "yellow"
    return "HEALTHY", "green"


def build_table(metrics: list[QueueMetrics], t: Thresholds) -> Table:
    table = Table(title="SQS Queue Monitor")
    table.add_column("Queue", style="cyan", no_wrap=True)
    table.add_column("Visible", justify="right")
    table.add_column("In-Flight", justify="right")
    table.add_column("Delayed", justify="right")
    table.add_column("Status", justify="center")

    for m in metrics:
        if m.error:
            table.add_row(m.name, "—", "—", "—", Text("ERROR", style="bold red"))
        else:
            label, style = status_for(m.visible, t)
            table.add_row(
                m.name,
                str(m.visible),
                str(m.in_flight),
                str(m.delayed),
                Text(label, style=style),
            )
    return table


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def resolve_queue_urls(sqs, args) -> list[str]:
    urls: list[str] = list(args.queue_urls or [])
    if args.prefix:
        discovered = discover_queues(sqs, args.prefix)
        if not discovered:
            console.print(f"[bold red]No queues found with prefix '{args.prefix}'[/bold red]")
            sys.exit(1)
        urls.extend(discovered)
    return sorted(set(urls))


def run(args):
    sqs = create_sqs_client(args.region, args.profile)
    thresholds = Thresholds(warn=args.warn, critical=args.critical)
    queue_urls = resolve_queue_urls(sqs, args)

    console.print(
        f"[bold]Monitoring {len(queue_urls)} queue(s) every {args.interval}s[/bold]\n"
    )

    with Live(refresh_per_second=1, console=console) as live:
        while True:
            metrics = [fetch_metrics(sqs, url) for url in queue_urls]
            live.update(build_table(metrics, thresholds))
            time.sleep(args.interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Real-time SQS queue monitor")

    p.add_argument("queue_urls", nargs="*", metavar="QUEUE_URL", help="SQS queue URL(s) to monitor")
    p.add_argument("--prefix", help="Monitor all queues whose name starts with PREFIX")
    p.add_argument("--region", default=None, help="AWS region (default: from env/config)")
    p.add_argument("--profile", default=None, help="AWS named profile")
    p.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    p.add_argument("--warn", type=int, default=100, help="Visible-message count for WARNING status (default: 100)")
    p.add_argument("--critical", type=int, default=500, help="Visible-message count for CRITICAL status (default: 500)")
    p.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: WARNING)",
    )

    args = p.parse_args(argv)

    if not args.queue_urls and not args.prefix:
        p.error("provide at least one QUEUE_URL or use --prefix")

    return args


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    try:
        run(args)
    except KeyboardInterrupt:
        console.print("\n[bold red]Monitoring stopped.[/bold red]")
        sys.exit(0)


if __name__ == "__main__":
    main()
