# How to Use the Queue Monitor

This guide walks you through setting up and using the SQS Queue Monitor and the RabbitMQ Queue Monitor to keep an eye on your message queues in real time.

---

## 1. Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or later** installed — check with `python --version`
- **For the SQS monitor:** AWS credentials configured
- **For the RabbitMQ monitor:** Access to the RabbitMQ Management API (enabled by default on Amazon MQ)

### AWS Permissions Required (SQS only)

Your AWS user or role needs the following permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:ListQueues",
    "sqs:GetQueueAttributes"
  ],
  "Resource": "*"
}
```

> **Tip:** If you restrict the `Resource` to specific queue ARNs, you won't be able to use `--prefix` discovery — you'll need to provide queue URLs directly.

---

## 2. Installation

```bash
# 1. Clone or download the project
git clone <repo-url>
cd queue-monitor

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 3. Try the Demo First

If you'd like to see the dashboards before connecting to AWS, run a demo:

```bash
# SQS demo
python queue-demo.py

# RabbitMQ demo
python rabbit-demo.py
```

These launch simulated dashboards with randomised queue data. Press `Ctrl+C` to stop.

---

## 4. Monitor Your SQS Queues

### Option A: Monitor specific queues by URL

Find your queue URL in the AWS Console (Amazon SQS → Queues → select a queue → copy the URL) and pass it as an argument:

```bash
python queue_monitor.py https://sqs.eu-west-1.amazonaws.com/123456789012/my-queue
```

You can monitor multiple queues at once:

```bash
python queue_monitor.py \
  https://sqs.eu-west-1.amazonaws.com/123456789012/orders \
  https://sqs.eu-west-1.amazonaws.com/123456789012/notifications
```

### Option B: Discover queues by prefix

If your queues share a naming convention, use `--prefix` to find and monitor all of them automatically:

```bash
python queue_monitor.py --prefix Production-
```

This discovers every queue whose name starts with `Production-` and monitors them all.

### Option C: Combine both

```bash
python queue_monitor.py \
  https://sqs.eu-west-1.amazonaws.com/123456789012/legacy-queue \
  --prefix Production-
```

---

## 5. Configure the Refresh Interval

By default the dashboard refreshes every **10 seconds**. To change this:

```bash
# Refresh every 5 seconds
python queue_monitor.py --prefix MyApp- --interval 5
```

Lower intervals give you more up-to-date data but generate more API calls.

---

## 6. Set Alert Thresholds

The dashboard shows a colour-coded status for each queue based on how many visible (available) messages are waiting:

| Status | Default Threshold | Meaning |
|---|---|---|
| **HEALTHY** (green) | < 100 messages | Queue is processing normally |
| **WARNING** (yellow) | >= 100 messages | Messages are building up — investigate |
| **CRITICAL** (red) | >= 500 messages | Queue is significantly backed up — action required |

To customise these thresholds:

```bash
# Warn at 50 messages, critical at 200
python queue_monitor.py --prefix MyApp- --warn 50 --critical 200
```

---

## 7. Use AWS Profiles and Regions

If you use multiple AWS accounts or regions, specify them on the command line:

```bash
# Use a named profile
python queue_monitor.py --profile production --prefix MyApp-

# Target a specific region
python queue_monitor.py --region us-east-1 --prefix MyApp-

# Both together
python queue_monitor.py --profile production --region eu-west-1 --prefix MyApp-
```

The monitor respects standard AWS configuration (`AWS_PROFILE`, `AWS_DEFAULT_REGION`, `~/.aws/config`, etc.) when these flags are not provided.

---

## 8. Reading the Dashboard

Once running, the dashboard displays a table like this:

```
                    SQS Queue Monitor
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Queue                 ┃ Visible ┃ In-Flight ┃ Delayed ┃ Status   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ Production-Orders     │      12 │         3 │       0 │ HEALTHY  │
│ Production-Emails     │     142 │         8 │       1 │ WARNING  │
│ Production-Analytics  │     623 │        15 │       4 │ CRITICAL │
└───────────────────────┴─────────┴───────────┴─────────┴──────────┘
```

| Column | What It Means |
|---|---|
| **Queue** | The name of the SQS queue |
| **Visible** | Messages waiting to be picked up by a consumer |
| **In-Flight** | Messages currently being processed (received but not yet deleted) |
| **Delayed** | Messages that have been sent but are not yet visible (delay period) |
| **Status** | Health indicator based on the visible message count and your thresholds |

---

## 9. Enable Debug Logging

If something isn't working as expected, enable debug logging to see detailed output including API calls:

```bash
python queue_monitor.py --prefix MyApp- --log-level DEBUG
```

Log levels available: `DEBUG`, `INFO`, `WARNING` (default), `ERROR`.

---

## 10. Stopping the Monitor

Press **Ctrl+C** at any time to stop the monitor cleanly.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "No queues found with prefix …" | Check the prefix spelling, ensure the queues exist in the region you're targeting, and verify your credentials have `sqs:ListQueues` permission. |
| "Failed to fetch metrics for …" | Your credentials may lack `sqs:GetQueueAttributes` permission, or the queue may have been deleted. Enable `--log-level DEBUG` for details. |
| No output / hangs | Verify network connectivity to AWS. Check that your region is correct. |
| Import errors | Run `pip install -r requirements.txt` to ensure dependencies are installed. |

---

# RabbitMQ Monitor

The following sections cover the RabbitMQ monitor (`rabbit_monitor.py`), designed for Amazon MQ (RabbitMQ engine) or any self-hosted RabbitMQ with the Management plugin enabled.

---

## 11. Connect to Your RabbitMQ Broker

The RabbitMQ monitor connects to the **Management HTTP API** to fetch queue metrics. You need the broker hostname, a management username, and a password.

### Amazon MQ (RabbitMQ)

Find your broker endpoint in the AWS Console: **Amazon MQ → Brokers → select your broker → Connections → RabbitMQ web console URL**. The hostname looks like `b-xxxx-xxxx.mq.eu-west-1.amazonaws.com`.

```bash
python rabbit_monitor.py \
  --host b-xxxx-xxxx.mq.eu-west-1.amazonaws.com \
  --user admin --password secret
```

Amazon MQ exposes the Management API on port **443** over HTTPS — both are the default, so you don't need to specify them.

### Self-hosted RabbitMQ

For a self-hosted broker with the default management port:

```bash
python rabbit_monitor.py \
  --host rabbit.internal --port 15672 --no-tls \
  --user guest --password guest
```

---

## 12. Filter Queues

### By vhost

```bash
python rabbit_monitor.py --host ... --user admin --password secret --vhost /
```

### By prefix

```bash
python rabbit_monitor.py --host ... --user admin --password secret --prefix Production-
```

### By specific names

```bash
python rabbit_monitor.py --host ... --user admin --password secret \
  --queues orders notifications analytics
```

### Combine filters

```bash
python rabbit_monitor.py --host ... --user admin --password secret \
  --vhost / --prefix Production-
```

If you omit all filters, **every queue** on the broker is monitored.

---

## 13. RabbitMQ Alert Thresholds

The dashboard shows a colour-coded status for each queue based on the **ready** message count:

| Status | Default Threshold | Meaning |
|---|---|---|
| **HEALTHY** (green) | < 100 messages | Queue is processing normally |
| **WARNING** (yellow) | >= 100 messages | Messages are building up — investigate |
| **CRITICAL** (red) | >= 500 messages | Queue is significantly backed up — action required |
| **NO CONSUMERS** (red) | 0 consumers with messages | No consumers attached — messages are not being processed |

To customise thresholds:

```bash
python rabbit_monitor.py --host ... --user admin --password secret --warn 50 --critical 200
```

---

## 14. Reading the RabbitMQ Dashboard

```
                          RabbitMQ Queue Monitor
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━┓
┃ VHost  ┃ Queue               ┃ Ready ┃ Unacked ┃ Total ┃ Consumers ┃ Pub/s ┃ Del/s ┃ Status       ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━┩
│ /      │ Production-Orders   │    12 │       3 │    15 │         3 │  12.4 │  11.8 │ HEALTHY      │
│ /      │ Production-Emails   │   142 │       8 │   150 │         2 │   8.1 │   5.3 │ WARNING      │
│ /      │ Production-Deadltr  │    35 │       0 │    35 │         0 │   0.2 │   0.0 │ NO CONSUMERS │
└────────┴─────────────────────┴───────┴─────────┴───────┴───────────┴───────┴───────┴──────────────┘
```

| Column | What It Means |
|---|---|
| **VHost** | RabbitMQ virtual host (shown when monitoring all vhosts) |
| **Queue** | The queue name |
| **Ready** | Messages waiting to be consumed |
| **Unacked** | Messages delivered to a consumer but not yet acknowledged |
| **Total** | Ready + Unacked |
| **Consumers** | Number of active consumers on the queue |
| **Pub/s** | Publish rate — messages arriving per second |
| **Del/s** | Deliver/get rate — messages being consumed per second |
| **Status** | Health indicator based on ready count, consumer count, and your thresholds |

---

## 15. RabbitMQ Troubleshooting

| Problem | Solution |
|---|---|
| Connection refused / timeout | Verify the hostname, port, and that your network can reach the Management API. For Amazon MQ, check the broker's security group allows inbound on port 443. |
| 401 Unauthorized | Check your username and password. Amazon MQ credentials are set when the broker is created. |
| SSL certificate errors | For self-signed certs, use `--no-verify`. For Amazon MQ this should not be needed. |
| Empty dashboard | Ensure queues exist. Try without `--vhost`, `--prefix`, or `--queues` to see all queues. |
| Import errors | Run `pip install -r requirements.txt` to ensure `requests` and `rich` are installed. |
