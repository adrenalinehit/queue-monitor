# SQS Queue Monitor

A real-time terminal dashboard for monitoring AWS SQS queue metrics. Displays message counts, in-flight status, and health indicators with automatic colour-coded alerts.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

## Features

- **Live dashboard** — auto-refreshing Rich table rendered in your terminal
- **Queue discovery** — monitor specific queue URLs or discover queues by name prefix
- **Health status** — colour-coded HEALTHY / WARNING / CRITICAL indicators based on configurable thresholds
- **AWS profile & region support** — works with named profiles, environment variables, and IAM roles
- **Demo mode** — try the dashboard without AWS credentials using the included demo script

## Prerequisites

- Python 3.10+
- AWS credentials configured (via environment variables, `~/.aws/credentials`, IAM role, etc.)
- Permissions: `sqs:ListQueues`, `sqs:GetQueueAttributes`

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd queue-monitor

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Monitor a specific queue by URL
python queue_monitor.py https://sqs.eu-west-1.amazonaws.com/123456789012/my-queue

# Monitor all queues matching a prefix
python queue_monitor.py --prefix Production-

# Run the demo (no AWS credentials required)
python queue-demo.py
```

## Usage

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

### Status Thresholds

| Status | Condition |
|---|---|
| HEALTHY (green) | Visible messages < `--warn` |
| WARNING (yellow) | Visible messages >= `--warn` and < `--critical` |
| CRITICAL (red) | Visible messages >= `--critical` |

## Demo Mode

Run `python queue-demo.py` to launch a simulated dashboard with randomised data — useful for testing or demonstrating the tool without AWS credentials.

## Stopping the Monitor

Press `Ctrl+C` to stop. The monitor also responds to `SIGTERM`.

## Project Structure

```
queue-monitor/
├── queue_monitor.py   # Main monitor script
├── queue-demo.py      # Demo with simulated data
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── HOW-TO.md          # Customer usage guide
```

## Dependencies

- [boto3](https://pypi.org/project/boto3/) — AWS SDK for Python
- [rich](https://pypi.org/project/rich/) — Terminal formatting and live display
