# How to Use the SQS Queue Monitor

This guide walks you through setting up and using the SQS Queue Monitor to keep an eye on your message queues in real time.

---

## 1. Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or later** installed — check with `python --version`
- **AWS credentials** configured — the monitor needs permission to read your SQS queues

### AWS Permissions Required

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

If you'd like to see the dashboard before connecting to AWS, run the demo:

```bash
python queue-demo.py
```

This launches a simulated dashboard with randomised queue data. Press `Ctrl+C` to stop.

---

## 4. Monitor Your Queues

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
