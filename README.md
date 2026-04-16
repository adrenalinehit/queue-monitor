# Queue Monitor

Real-time terminal dashboards for monitoring **AWS SQS** and **RabbitMQ** (Amazon MQ) queue metrics. Displays message counts, consumer status, and health indicators with automatic colour-coded alerts.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

## Features

- **Live dashboard** — auto-refreshing Rich table rendered in your terminal
- **Two monitors** — SQS (`queue_monitor.py`) and RabbitMQ (`rabbit_monitor.py`)
- **Queue discovery** — monitor specific queues or discover by name prefix
- **Health status** — colour-coded HEALTHY / WARNING / CRITICAL indicators based on configurable thresholds
- **AWS profile & region support** — SQS monitor works with named profiles, environment variables, and IAM roles
- **Amazon MQ support** — RabbitMQ monitor connects to the Management API over HTTPS (Amazon MQ default)
- **Demo mode** — try either dashboard without credentials using the included demo scripts

## Prerequisites

- Python 3.10+
- **For SQS:** AWS credentials configured (via environment variables, `~/.aws/credentials`, IAM role, etc.) with `sqs:ListQueues` and `sqs:GetQueueAttributes` permissions
- **For RabbitMQ:** Access to the RabbitMQ Management API (enabled by default on Amazon MQ) with a valid username and password

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd queue-monitor

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### SQS

```bash
# Monitor a specific queue by URL
python queue_monitor.py https://sqs.eu-west-1.amazonaws.com/123456789012/my-queue

# Monitor all queues matching a prefix
python queue_monitor.py --prefix Production-

# Run the SQS demo (no AWS credentials required)
python queue-demo.py
```

### RabbitMQ (Amazon MQ)

```bash
# Monitor all queues on an Amazon MQ broker
python rabbit_monitor.py --host b-xxxx.mq.eu-west-1.amazonaws.com --user admin --password secret

# Monitor queues matching a prefix in a specific vhost
python rabbit_monitor.py --host b-xxxx.mq.eu-west-1.amazonaws.com \
  --user admin --password secret --vhost / --prefix Production-

# Run the RabbitMQ demo (no credentials required)
python rabbit-demo.py
```

---

## SQS Monitor

```
usage: queue_monitor.py [-h] [--prefix PREFIX] [--region REGION]
                        [--profile PROFILE] [--interval INTERVAL]
                        [--warn WARN] [--critical CRITICAL]
                        [--log-level {DEBUG,INFO,WARNING,ERROR}]
                        [QUEUE_URL ...]
```

### Arguments

| Argument | Description |
|---|---|
| `QUEUE_URL` | One or more SQS queue URLs to monitor |

### Options

| Option | Default | Description |
|---|---|---|
| `--prefix PREFIX` | — | Monitor all queues whose name starts with PREFIX |
| `--region REGION` | from env/config | AWS region |
| `--profile PROFILE` | — | AWS named profile |
| `--interval SECONDS` | `10` | Polling interval in seconds |
| `--warn N` | `100` | Visible-message count that triggers WARNING status |
| `--critical N` | `500` | Visible-message count that triggers CRITICAL status |
| `--log-level LEVEL` | `WARNING` | Log level: DEBUG, INFO, WARNING, ERROR |

You must provide at least one `QUEUE_URL` or use `--prefix`.

### Examples

```bash
# Monitor two queues with a 5-second refresh and custom thresholds
python queue_monitor.py \
  https://sqs.eu-west-1.amazonaws.com/123456789012/orders \
  https://sqs.eu-west-1.amazonaws.com/123456789012/notifications \
  --interval 5 --warn 50 --critical 200

# Use a named AWS profile and discover queues by prefix
python queue_monitor.py --profile production --region eu-west-1 --prefix MyApp-

# Enable debug logging
python queue_monitor.py --prefix staging- --log-level DEBUG
```

### Dashboard Columns

| Column | Description |
|---|---|
| **Queue** | Queue name (extracted from the URL) |
| **Visible** | Approximate number of messages available for retrieval |
| **In-Flight** | Messages currently being processed by consumers |
| **Delayed** | Messages in the delay period before becoming visible |
| **Status** | HEALTHY, WARNING, or CRITICAL based on thresholds |

### SQS Status Thresholds

| Status | Condition |
|---|---|
| HEALTHY (green) | Visible messages < `--warn` |
| WARNING (yellow) | Visible messages >= `--warn` and < `--critical` |
| CRITICAL (red) | Visible messages >= `--critical` |

---

## RabbitMQ Monitor

```
usage: rabbit_monitor.py [-h] --host HOST [--port PORT] --user USER
                         --password PASSWORD [--no-tls] [--no-verify]
                         [--vhost VHOST] [--prefix PREFIX]
                         [--queues [NAME ...]] [--interval INTERVAL]
                         [--warn WARN] [--critical CRITICAL]
                         [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

### Connection Options

| Option | Default | Description |
|---|---|---|
| `--host HOST` | *required* | RabbitMQ host (Amazon MQ endpoint or IP) |
| `--port PORT` | `443` | Management API port (443 for Amazon MQ) |
| `--user USER` | *required* | Management username |
| `--password PASSWORD` | *required* | Management password |
| `--no-tls` | — | Use HTTP instead of HTTPS |
| `--no-verify` | — | Skip TLS certificate verification |

### Filtering Options

| Option | Default | Description |
|---|---|---|
| `--vhost VHOST` | all | Limit to a specific vhost |
| `--prefix PREFIX` | — | Monitor queues whose name starts with PREFIX |
| `--queues NAME [...]` | — | Specific queue name(s) to monitor |

### General Options

| Option | Default | Description |
|---|---|---|
| `--interval SECONDS` | `10` | Polling interval in seconds |
| `--warn N` | `100` | Ready-message count that triggers WARNING status |
| `--critical N` | `500` | Ready-message count that triggers CRITICAL status |
| `--log-level LEVEL` | `WARNING` | Log level: DEBUG, INFO, WARNING, ERROR |

If none of `--queues`, `--prefix`, or `--vhost` are specified, all queues on the broker are monitored.

### RabbitMQ Examples

```bash
# Monitor all queues on an Amazon MQ broker
python rabbit_monitor.py --host b-xxxx.mq.eu-west-1.amazonaws.com \
  --user admin --password secret

# Monitor specific queues with custom thresholds
python rabbit_monitor.py --host b-xxxx.mq.eu-west-1.amazonaws.com \
  --user admin --password secret \
  --queues orders notifications --warn 50 --critical 200

# Self-hosted RabbitMQ on default port without TLS
python rabbit_monitor.py --host rabbit.internal --port 15672 --no-tls \
  --user guest --password guest --prefix MyApp-
```

### RabbitMQ Dashboard Columns

| Column | Description |
|---|---|
| **VHost** | Virtual host (shown when monitoring all vhosts) |
| **Queue** | Queue name |
| **Ready** | Messages waiting to be consumed |
| **Unacked** | Messages delivered but not yet acknowledged |
| **Total** | Total messages (ready + unacked) |
| **Consumers** | Number of active consumers |
| **Pub/s** | Publish rate (messages/second) |
| **Del/s** | Deliver/get rate (messages/second) |
| **Status** | HEALTHY, WARNING, CRITICAL, or NO CONSUMERS |

### RabbitMQ Status Thresholds

| Status | Condition |
|---|---|
| HEALTHY (green) | Ready messages < `--warn` |
| WARNING (yellow) | Ready messages >= `--warn` and < `--critical` |
| CRITICAL (red) | Ready messages >= `--critical` |
| NO CONSUMERS (red) | Queue has messages but zero consumers |

---

## Demo Mode

Run `python queue-demo.py` (SQS) or `python rabbit-demo.py` (RabbitMQ) to launch a simulated dashboard with randomised data — useful for testing or demonstrating the tool without credentials.

## Stopping the Monitor

Press `Ctrl+C` to stop. The monitor also responds to `SIGTERM`.

## Project Structure

```
queue-monitor/
├── queue_monitor.py    # SQS monitor
├── queue-demo.py       # SQS demo with simulated data
├── rabbit_monitor.py   # RabbitMQ monitor (Amazon MQ)
├── rabbit-demo.py      # RabbitMQ demo with simulated data
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── HOW-TO.md           # Customer usage guide
```

## Dependencies

- [boto3](https://pypi.org/project/boto3/) — AWS SDK for Python (SQS monitor)
- [requests](https://pypi.org/project/requests/) — HTTP client (RabbitMQ monitor)
- [rich](https://pypi.org/project/rich/) — Terminal formatting and live display
