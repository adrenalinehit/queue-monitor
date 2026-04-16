#!/usr/bin/env python3
"""Amazon MQ (RabbitMQ) Queue Monitor — real-time terminal dashboard for RabbitMQ queue metrics."""

import argparse
import logging
import signal
import sys
import time
from dataclasses import dataclass
from urllib.parse import quote

import requests
from requests.exceptions import RequestException
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
    vhost: str
    name: str
    ready: int = 0
    unacked: int = 0
    total: int = 0
    consumers: int = 0
    publish_rate: float = 0.0
    deliver_rate: float = 0.0
    error: str | None = None


# ---------------------------------------------------------------------------
# RabbitMQ Management API helpers
# ---------------------------------------------------------------------------


def build_base_url(host: str, port: int, tls: bool) -> str:
    scheme = "https" if tls else "http"
    return f"{scheme}://{host}:{port}/api"


def list_queues(base_url: str, auth: tuple[str, str], vhost: str | None, verify: bool) -> list[dict]:
    """Fetch all queues, optionally filtered to a single vhost."""
    if vhost:
        url = f"{base_url}/queues/{quote(vhost, safe='')}"
    else:
        url = f"{base_url}/queues"
    resp = requests.get(url, auth=auth, timeout=15, verify=verify)
    resp.raise_for_status()
    return resp.json()


def filter_queues(queues: list[dict], prefix: str | None, names: list[str] | None) -> list[dict]:
    """Return queues matching the given prefix and/or explicit names."""
    result = queues
    if prefix:
        result = [q for q in result if q["name"].startswith(prefix)]
    if names:
        name_set = set(names)
        by_name = [q for q in queues if q["name"] in name_set]
        # merge, dedup by (vhost, name)
        seen = {(q["vhost"], q["name"]) for q in result}
        for q in by_name:
            if (q["vhost"], q["name"]) not in seen:
                result.append(q)
    return result


def parse_queue_metrics(q: dict) -> QueueMetrics:
    """Extract a QueueMetrics from a RabbitMQ management API queue object."""
    msg_stats = q.get("message_stats", {})
    publish_details = msg_stats.get("publish_details", {})
    deliver_details = msg_stats.get("deliver_get_details", {})
    return QueueMetrics(
        vhost=q.get("vhost", "/"),
        name=q["name"],
        ready=q.get("messages_ready", 0),
        unacked=q.get("messages_unacknowledged", 0),
        total=q.get("messages", 0),
        consumers=q.get("consumers", 0),
        publish_rate=publish_details.get("rate", 0.0),
        deliver_rate=deliver_details.get("rate", 0.0),
    )


def fetch_all_metrics(
    base_url: str, auth: tuple[str, str], vhost: str | None,
    prefix: str | None, names: list[str] | None, verify: bool,
) -> list[QueueMetrics]:
    try:
        raw = list_queues(base_url, auth, vhost, verify)
        filtered = filter_queues(raw, prefix, names)
        return [parse_queue_metrics(q) for q in filtered]
    except RequestException as exc:
        logger.error("Failed to fetch queues: %s", exc)
        return [QueueMetrics(vhost="?", name="<connection error>", error=str(exc))]


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def status_for(ready: int, consumers: int, t: Thresholds) -> tuple[str, str]:
    if consumers == 0 and ready > 0:
        return "NO CONSUMERS", "bold red"
    if ready >= t.critical:
        return "CRITICAL", "bold red"
    if ready >= t.warn:
        return "WARNING", "yellow"
    return "HEALTHY", "green"


def build_table(metrics: list[QueueMetrics], t: Thresholds, show_vhost: bool) -> Table:
    table = Table(title="RabbitMQ Queue Monitor")
    if show_vhost:
        table.add_column("VHost", style="dim")
    table.add_column("Queue", style="cyan", no_wrap=True)
    table.add_column("Ready", justify="right")
    table.add_column("Unacked", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Consumers", justify="right")
    table.add_column("Pub/s", justify="right")
    table.add_column("Del/s", justify="right")
    table.add_column("Status", justify="center")

    for m in metrics:
        if m.error:
            cols = ["—"] * (7 if show_vhost else 6) + [Text("ERROR", style="bold red")]
            if show_vhost:
                cols = [m.vhost] + cols
            else:
                cols = [m.name] + ["—"] * 6 + [Text("ERROR", style="bold red")]
            table.add_row(*cols)
        else:
            label, style = status_for(m.ready, m.consumers, t)
            row: list = []
            if show_vhost:
                row.append(m.vhost)
            row.extend([
                m.name,
                str(m.ready),
                str(m.unacked),
                str(m.total),
                str(m.consumers),
                f"{m.publish_rate:.1f}",
                f"{m.deliver_rate:.1f}",
                Text(label, style=style),
            ])
            table.add_row(*row)
    return table


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run(args):
    auth = (args.user, args.password)
    base_url = build_base_url(args.host, args.port, not args.no_tls)
    thresholds = Thresholds(warn=args.warn, critical=args.critical)
    vhost = args.vhost
    prefix = args.prefix
    names = args.queues or None
    verify = not args.no_verify
    show_vhost = vhost is None  # show vhost column when monitoring all vhosts

    # initial fetch to confirm connectivity and count queues
    initial = fetch_all_metrics(base_url, auth, vhost, prefix, names, verify)
    if not initial or (len(initial) == 1 and initial[0].error):
        console.print("[bold red]Could not connect to RabbitMQ Management API[/bold red]")
        sys.exit(1)

    console.print(
        f"[bold]Monitoring {len(initial)} queue(s) at {args.host}:{args.port} "
        f"every {args.interval}s[/bold]\n"
    )

    with Live(refresh_per_second=1, console=console) as live:
        while True:
            metrics = fetch_all_metrics(base_url, auth, vhost, prefix, names, verify)
            metrics.sort(key=lambda m: (m.vhost, m.name))
            live.update(build_table(metrics, thresholds, show_vhost))
            time.sleep(args.interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Real-time RabbitMQ queue monitor (via Management API)"
    )

    conn = p.add_argument_group("connection")
    conn.add_argument("--host", required=True, help="RabbitMQ host (Amazon MQ endpoint or IP)")
    conn.add_argument("--port", type=int, default=443, help="Management API port (default: 443 for Amazon MQ)")
    conn.add_argument("--user", required=True, help="RabbitMQ management username")
    conn.add_argument("--password", required=True, help="RabbitMQ management password")
    conn.add_argument("--no-tls", action="store_true", help="Use HTTP instead of HTTPS")
    conn.add_argument("--no-verify", action="store_true", help="Skip TLS certificate verification")

    filt = p.add_argument_group("filtering")
    filt.add_argument("--vhost", default=None, help="Limit to a specific vhost (default: all)")
    filt.add_argument("--prefix", default=None, help="Monitor queues whose name starts with PREFIX")
    filt.add_argument("--queues", nargs="*", metavar="NAME", help="Specific queue name(s) to monitor")

    p.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    p.add_argument("--warn", type=int, default=100, help="Ready-message count for WARNING status (default: 100)")
    p.add_argument("--critical", type=int, default=500, help="Ready-message count for CRITICAL status (default: 500)")
    p.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: WARNING)",
    )

    args = p.parse_args(argv)

    if not args.queues and not args.prefix and not args.vhost:
        # monitor everything — that's fine, but warn
        logger.info("No --queues, --prefix, or --vhost specified; monitoring all queues")

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
