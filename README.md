# Speed Test Agent

A background agent that logs internet speed test and traceroute results every 15 minutes to a SQLite database, using Windows Task Scheduler.

## What It Logs

All data is stored in `speedtest.db` (SQLite).

### `speed_tests` table
| Column | Description |
|--------|-------------|
| timestamp | ISO 8601 timestamp |
| download_mbps | Download speed in Mbps |
| upload_mbps | Upload speed in Mbps |
| ping_ms | Latency in ms |
| server_name | Ookla test server name |
| server_host | Ookla test server host |
| isp | Your ISP |
| error | Error message (NULL if successful) |

### `traceroutes` table
| Column | Description |
|--------|-------------|
| timestamp | ISO 8601 timestamp |
| target | Traceroute destination IP |
| hop_number | Hop sequence number |
| hop_ip | IP address of the hop |
| rtt_ms | Round-trip time in ms |
| error | Error message (NULL if successful) |

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

## Viewing Results in Excel (Power Query)

1. Install the **SQLite ODBC driver**: download from http://www.ch-werner.de/sqliteodbc/ and install `sqliteodbc_w64.exe`
2. Open Excel → **Data** tab → **Get Data** → **From Other Sources** → **From ODBC**
3. Choose the SQLite3 ODBC driver and set the **Database** to:
   ```
   C:\Users\patri\SpeedTestAgent\speedtest.db
   ```
4. Select the `speed_tests` or `traceroutes` table → **Load**
5. To refresh data later: **Data** tab → **Refresh All**

Because SQLite uses WAL mode, Excel can read the database even while the agent is writing to it — no file locking issues.
