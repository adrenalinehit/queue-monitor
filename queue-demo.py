import time
import random
from rich.live import Live
from rich.table import Table
from rich.console import Console

console = Console()

def generate_queue_data(current_len):
    # Simulate some randomness: 
    # Account for 5-15 new messages and 4-12 processed messages
    incoming = random.randint(5, 15)
    processed = random.randint(4, 12)
    
    new_len = max(0, current_len + incoming - processed)
    
    return {
        "url": "https://sqs.us-east-1.amazonaws.com/123456789012/Production-Order-Queue",
        "visible": new_len,
        "in_flight": random.randint(2, 8),
        "delayed": random.randint(0, 2),
        "status": "HEALTHY" if new_len < 150 else "DEGRADED"
    }

def run_demo():
    queue_length = 42  # Starting point
    
    with Live(refresh_per_second=1) as live:
        while True:
            data = generate_queue_data(queue_length)
            queue_length = data["visible"]
            
            table = Table(title="AWS SQS Real-Time Monitor (Demo Mode)")
            table.add_column("Attribute", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Queue Name", "Production-Order-Queue")
            table.add_row("Queue URL", data["url"])
            table.add_row("ApproximateNumberOfMessages", str(data["visible"]))
            table.add_row("Messages In-Flight", str(data["in_flight"]))
            table.add_row("Messages Delayed", str(data["delayed"]))
            table.add_row("System Status", data["status"], style="green" if data["status"] == "HEALTHY" else "red")
            
            live.update(table)
            time.sleep(2)

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        console.print("\n[bold red]Monitoring stopped.[/bold red]")

        