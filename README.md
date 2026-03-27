# Speed Test Agent

A background agent that logs internet speed test and traceroute results every 15 minutes using Windows Task Scheduler.

## What It Logs

### Speed Tests (`logs/speed_tests.csv`)
- Timestamp, download Mbps, upload Mbps, ping ms, server info, ISP

### Traceroutes (`logs/traceroutes.csv`)
- Timestamp, target, hop number, hop IP, round-trip time
- Default targets: Google DNS (8.8.8.8), Cloudflare DNS (1.1.1.1)

## Setup

### 1. Install Ookla Speedtest CLI

```powershell
winget install Ookla.Speedtest.CLI --accept-package-agreements
```

Then restart your terminal so `speedtest` is on your PATH.

### 2. Create Python virtual environment

```powershell
cd C:\Users\patri\SpeedTestAgent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Test it manually first

```powershell
python speed_test_agent.py
```

Check the `logs/` folder for output CSV files.

### 4. Install as a scheduled task (runs every 15 minutes)

Open an **elevated (Administrator)** PowerShell prompt:

```powershell
cd C:\Users\patri\SpeedTestAgent
.\Install-Task.ps1
```

### Uninstall

```powershell
.\Install-Task.ps1 -Uninstall
```

## Configuration

Edit the top of `speed_test_agent.py` to customize:

- `TRACEROUTE_TARGETS` — list of IPs/hostnames to traceroute
- `TRACEROUTE_MAX_HOPS` — max hops (default 30)
- `TRACEROUTE_TIMEOUT_MS` — timeout per hop (default 3000ms)

## Viewing Results

The CSV files in `logs/` can be opened directly in Excel for analysis and charting.
