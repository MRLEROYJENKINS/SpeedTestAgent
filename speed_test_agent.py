"""
Speed Test & Traceroute Agent
Runs speed tests and traceroutes, logging results to a SQLite database.
Designed to be triggered by Windows Task Scheduler every 15 minutes.
"""

import datetime
import json
import os
import sqlite3
import subprocess
import sys

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "speedtest.db")

# Traceroute targets (add/remove as desired)
TRACEROUTE_TARGETS = [
    "8.8.8.8",         # Google DNS
]

# Max hops for traceroute
TRACEROUTE_MAX_HOPS = 30
# Timeout per hop in milliseconds
TRACEROUTE_TIMEOUT_MS = 3000


def get_db():
    """Open (and initialize) the SQLite database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")  # allows concurrent reads while writing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS speed_tests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            download_mbps REAL,
            upload_mbps   REAL,
            ping_ms       REAL,
            server_name   TEXT,
            server_host   TEXT,
            isp           TEXT,
            error         TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traceroutes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            target      TEXT NOT NULL,
            hop_number  INTEGER,
            hop_ip      TEXT,
            rtt_ms      TEXT,
            error       TEXT
        )
    """)
    conn.commit()
    return conn


def run_speed_test(conn):
    """Run a speed test using Ookla's official CLI and save results."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Running speed test...")

    try:
        result = subprocess.run(
            ["speedtest", "--format=json", "--accept-license", "--accept-gdpr"],
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"Exit code {result.returncode}")

        data = json.loads(result.stdout)

        download_mbps = round(data["download"]["bandwidth"] * 8 / 1_000_000, 2)
        upload_mbps = round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2)
        ping_ms = round(data["ping"]["latency"], 2)
        server_name = data["server"]["name"]
        server_host = data["server"]["host"]
        isp = data["isp"]

        conn.execute(
            "INSERT INTO speed_tests (timestamp, download_mbps, upload_mbps, ping_ms, server_name, server_host, isp) VALUES (?,?,?,?,?,?,?)",
            (timestamp, download_mbps, upload_mbps, ping_ms, server_name, server_host, isp),
        )
        conn.commit()

        print(f"  Download: {download_mbps} Mbps | Upload: {upload_mbps} Mbps | Ping: {ping_ms} ms")

    except Exception as e:
        print(f"  Speed test failed: {e}", file=sys.stderr)
        conn.execute(
            "INSERT INTO speed_tests (timestamp, error) VALUES (?,?)",
            (timestamp, str(e)),
        )
        conn.commit()


def run_traceroute(conn, target):
    """Run tracert to a target and save hop-by-hop results."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Running traceroute to {target}...")

    try:
        result = subprocess.run(
            ["tracert", "-h", str(TRACEROUTE_MAX_HOPS), "-w", str(TRACEROUTE_TIMEOUT_MS), target],
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        output = result.stdout

        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith("Tracing") or line.startswith("Trace complete") or line.startswith("over a maximum"):
                continue

            parts = line.split()
            if not parts:
                continue

            try:
                hop_num = int(parts[0])
            except (ValueError, IndexError):
                continue

            hop_ip = parts[-1] if parts[-1] != "out." else "* (timeout)"
            hop_ip = hop_ip.strip("[]")

            rtt = None
            for part in parts[1:]:
                if part == "*" or part == "ms":
                    continue
                if part.startswith("<"):
                    rtt = part
                    break
                try:
                    rtt = str(float(part))
                    break
                except ValueError:
                    continue

            if rtt is None:
                rtt = "*"

            conn.execute(
                "INSERT INTO traceroutes (timestamp, target, hop_number, hop_ip, rtt_ms) VALUES (?,?,?,?,?)",
                (timestamp, target, hop_num, hop_ip, rtt),
            )

        conn.commit()
        print(f"  Traceroute to {target} complete.")

    except subprocess.TimeoutExpired:
        print(f"  Traceroute to {target} timed out.", file=sys.stderr)
        conn.execute(
            "INSERT INTO traceroutes (timestamp, target, error) VALUES (?,?,?)",
            (timestamp, target, "TIMEOUT"),
        )
        conn.commit()
    except Exception as e:
        print(f"  Traceroute to {target} failed: {e}", file=sys.stderr)
        conn.execute(
            "INSERT INTO traceroutes (timestamp, target, error) VALUES (?,?,?)",
            (timestamp, target, str(e)),
        )
        conn.commit()


def main():
    conn = get_db()
    try:
        run_speed_test(conn)
        for target in TRACEROUTE_TARGETS:
            run_traceroute(conn, target)
    finally:
        conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
