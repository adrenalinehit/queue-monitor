import time
import random
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.console import Console

console = Console()

QUEUES = [
    {"vhost": "/", "name": "Production-Orders"},
    {"vhost": "/", "name": "Production-Notifications"},
    {"vhost": "/", "name": "Production-Analytics"},
    {"vhost": "staging", "name": "Staging-Orders"},
]


def simulate_metrics(state: dict, queue: dict) -> dict:
    key = f"{queue['vhost']}:{queue['name']}"
    ready = state.get(key, random.randint(5, 60))
    incoming = random.randint(3, 18)
    processed = random.randint(4, 16)
    ready = max(0, ready + incoming - processed)
    state[key] = ready

    consumers = random.randint(1, 5) if random.random() > 0.05 else 0
    return {
        "vhost": queue["vhost"],
        "name": queue["name"],
        "ready": ready,
        "unacked": random.randint(1, 10),
        "total": ready + random.randint(1, 10),
        "consumers": consumers,
        "publish_rate": round(random.uniform(0.5, 25.0), 1),
        "deliver_rate": round(random.uniform(0.3, 22.0), 1),
    }


def status_for(ready, consumers):
    if consumers == 0 and ready > 0:
        return "NO CONSUMERS", "bold red"
    if ready >= 500:
        return "CRITICAL", "bold red"
    if ready >= 100:
        return "WARNING", "yellow"
    return "HEALTHY", "green"


def run_demo():
    state: dict = {}

    with Live(refresh_per_second=1) as live:
        while True:
            table = Table(title="RabbitMQ Queue Monitor (Demo Mode)")
            table.add_column("VHost", style="dim")
            table.add_column("Queue", style="cyan", no_wrap=True)
            table.add_column("Ready", justify="right")
            table.add_column("Unacked", justify="right")
            table.add_column("Total", justify="right")
            table.add_column("Consumers", justify="right")
            table.add_column("Pub/s", justify="right")
            table.add_column("Del/s", justify="right")
            table.add_column("Status", justify="center")

            for q in QUEUES:
                m = simulate_metrics(state, q)
                label, style = status_for(m["ready"], m["consumers"])
                table.add_row(
                    m["vhost"],
                    m["name"],
                    str(m["ready"]),
                    str(m["unacked"]),
                    str(m["total"]),
                    str(m["consumers"]),
                    f"{m['publish_rate']:.1f}",
                    f"{m['deliver_rate']:.1f}",
                    Text(label, style=style),
                )

            live.update(table)
            time.sleep(2)


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        console.print("\n[bold red]Monitoring stopped.[/bold red]")
