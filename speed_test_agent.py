"""
Speed Test & Traceroute Agent
Runs speed tests and traceroutes, logging results to CSV files.
Designed to be triggered by Windows Task Scheduler every 15 minutes.
"""

import csv
import datetime
import json
import os
import subprocess
import sys

# --- Configuration ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
SPEED_LOG = os.path.join(LOG_DIR, "speed_tests.csv")
TRACEROUTE_LOG = os.path.join(LOG_DIR, "traceroutes.csv")

# Traceroute targets (add/remove as desired)
TRACEROUTE_TARGETS = [
    "8.8.8.8",         # Google DNS
]

# Max hops for traceroute
TRACEROUTE_MAX_HOPS = 30
# Timeout per hop in milliseconds
TRACEROUTE_TIMEOUT_MS = 3000


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def init_speed_csv():
    """Create the speed test CSV with headers if it doesn't exist."""
    if not os.path.exists(SPEED_LOG):
        with open(SPEED_LOG, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "download_mbps",
                "upload_mbps",
                "ping_ms",
                "server_name",
                "server_host",
                "isp",
            ])


def init_traceroute_csv():
    """Create the traceroute CSV with headers if it doesn't exist."""
    if not os.path.exists(TRACEROUTE_LOG):
        with open(TRACEROUTE_LOG, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "target",
                "hop_number",
                "hop_ip",
                "rtt_ms",
            ])


def run_speed_test():
    """Run a speed test using Ookla's official CLI and append results to CSV."""
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] Running speed test...")

    try:
        result = subprocess.run(
            ["speedtest", "--format=json", "--accept-license", "--accept-gdpr"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"Exit code {result.returncode}")

        data = json.loads(result.stdout)

        # Ookla CLI reports bytes per second; convert to Mbps
        download_mbps = round(data["download"]["bandwidth"] * 8 / 1_000_000, 2)
        upload_mbps = round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2)
        ping_ms = round(data["ping"]["latency"], 2)
        server_name = data["server"]["name"]
        server_host = data["server"]["host"]
        isp = data["isp"]

        with open(SPEED_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                download_mbps,
                upload_mbps,
                ping_ms,
                server_name,
                server_host,
                isp,
            ])

        print(f"  Download: {download_mbps} Mbps | Upload: {upload_mbps} Mbps | Ping: {ping_ms} ms")

    except Exception as e:
        print(f"  Speed test failed: {e}", file=sys.stderr)
        with open(SPEED_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, "ERROR", "ERROR", "ERROR", str(e), "", ""])


def run_traceroute(target):
    """Run tracert to a target and append hop-by-hop results to CSV."""
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] Running traceroute to {target}...")

    try:
        result = subprocess.run(
            ["tracert", "-h", str(TRACEROUTE_MAX_HOPS), "-w", str(TRACEROUTE_TIMEOUT_MS), target],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout

        with open(TRACEROUTE_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            for line in output.splitlines():
                line = line.strip()
                # Skip header/blank lines
                if not line or line.startswith("Tracing") or line.startswith("Trace complete") or line.startswith("over a maximum"):
                    continue

                # Parse lines like: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
                #                   "  2     *        *        *     Request timed out."
                parts = line.split()
                if not parts:
                    continue

                try:
                    hop_num = int(parts[0])
                except (ValueError, IndexError):
                    continue

                # Extract the IP (last part that looks like an IP or hostname)
                hop_ip = parts[-1] if parts[-1] != "out." else "* (timeout)"
                # Remove brackets if present, e.g. [192.168.1.1]
                hop_ip = hop_ip.strip("[]")

                # Try to extract RTT - take the first non-* timing
                rtt = None
                for part in parts[1:]:
                    if part == "*" or part == "ms":
                        continue
                    if part.startswith("<"):
                        rtt = part  # e.g. "<1"
                        break
                    try:
                        rtt = str(float(part))
                        break
                    except ValueError:
                        continue

                if rtt is None:
                    rtt = "*"

                writer.writerow([timestamp, target, hop_num, hop_ip, rtt])

        print(f"  Traceroute to {target} complete.")

    except subprocess.TimeoutExpired:
        print(f"  Traceroute to {target} timed out.", file=sys.stderr)
        with open(TRACEROUTE_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, target, "TIMEOUT", "", ""])
    except Exception as e:
        print(f"  Traceroute to {target} failed: {e}", file=sys.stderr)
        with open(TRACEROUTE_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, target, "ERROR", str(e), ""])


def main():
    ensure_log_dir()
    init_speed_csv()
    init_traceroute_csv()

    run_speed_test()

    for target in TRACEROUTE_TARGETS:
        run_traceroute(target)

    print("Done.")


if __name__ == "__main__":
    main()
