# Biomni Machine Stability Analysis
**Date:** 2026-04-07  
**Machine:** alan (64 CPU, 251GB RAM)  
**Evidence collected:** read-only observation, no processes touched

---

## Executive Summary

The machine "deaths" are caused by **memory exhaustion + OOM**, not I/O overload directly. The burst of concurrent experiment runs pushes memory over the edge (only 22GB headroom, 2GB swap fully exhausted). I/O is a secondary amplifier — the key contributing factors are:

1. **Memory headroom critically thin**: 229/251GB RAM used (91%), swap 2/2GB full
2. **Active API ports balloon to 10–24GB RSS each** under load
3. **74 of 75 vLLM connections stuck in CLOSE-WAIT** — socket leak per keepalive ping
4. **139,091 local_output dirs** causing VSCode fileWatcher to burn 99% CPU
5. **Idle ports**: 56 ports × ~130MB = 6.9GB of baseline "cold" overhead

---

## Evidence: Memory

```
Total RAM:     251 GB
Used RAM:      229 GB  (91%)
Free RAM:       22 GB
Swap total:      2 GB  (FULL — 2/2 GB consumed)
```

**Active port memory:**
| Port | RSS |
|------|-----|
| 6034 | 24 GB |
| 6023 | 21 GB |
| 6124 | 21 GB |
| 6050 | 21 GB |
| 6070 | 17 GB |

- **19 active ports** total = 203 GB RSS combined (avg 10.7 GB each)
- **56 idle ports** total = 6.9 GB RSS combined (avg ~130 MB each)

**OOM threshold:**
```
Free: 22 GB, Avg active port: 10.7 GB
→ Only ~2 new simultaneous query activations needed to trigger OOM
```

When OOM strikes, the kernel kills random processes, SSH daemon or sshd children may be killed, making the machine appear "dead" despite hardware being fine — which explains why the sister machine is still reachable.

---

## Evidence: CLOSE-WAIT Socket Leak

```
vLLM connections:  74 × CLOSE-WAIT + 1 × ESTAB
```

Every keepalive ping (every 300s per port) uses `_requests.get(url)` — a bare `requests` call with **no session/connection pool**. Each ping:
1. Opens a new TCP connection to vLLM
2. Sends GET /models
3. vLLM closes the connection (FIN from remote)
4. Local socket gets stuck in CLOSE-WAIT until the process explicitly closes the socket

Since 75 ports are running, 74 accumulated CLOSE-WAIT sockets are held open — one per port. Under heavy query load, the active query connections add on top. In a burst scenario these could exhaust the local ephemeral port range (typically 60K ports) and contribute to "connection refused" symptoms.

---

## Evidence: local_outputs Explosion

```
Directories in local_outputs/: 139,091
Total size: 26 GB
New dirs per day: ~10,903
Age: going back to Sep 2025
```

Each Biomni query creates a timestamped output directory under `local_outputs/`. This directory is never cleaned up. The accumulation causes:

1. **VSCode fileWatcher at 99% CPU** — inotify is watching the entire repo including `local_outputs/`. With 139K directories, each new query triggers filesystem events that the watcher must scan.
2. **`ls` / `find` commands slow** — any script or tool that traverses the directory takes significant time.
3. **Metadata I/O pressure** — directory entry reads/writes for 100K+ entries strain the filesystem metadata cache, explaining the I/O spikes during high-concurrency runs.

---

## Evidence: Current I/O (Baseline — Quiet State)

```
%iowait:  0.01%   (negligible right now)
vmstat bi/bo:  2097 / 131 kB/s read/write   (normal)
D-state processes: 0
```

I/O is **not the primary issue in isolation** — but becomes the trigger when combined with memory pressure. When many queries run simultaneously:
- Python code execution reads data lake files (parquet/tsv) from NVMe
- Log files are written in parallel (717MB of logs, actively growing)
- diskcache SQLite writes (37MB cache.db, 75 processes sharing it)
- 10K new output dirs/day = metadata write pressure

The NVMe is fast (low latency, high IOPS) but 75 processes simultaneously doing parquet reads + writes can queue up. With swap exhausted, any memory pressure triggers a page reclaim cycle that competes with data I/O on the same NVMe device — this is the "I/O overload" you're experiencing during burst runs.

---

## Evidence: Idle Port Overhead

56 idle ports × ~130MB RSS = **6.9GB baseline overhead** just for ports not serving any requests. This is not the primary killer, but:
- Each idle port has a keepalive thread pinging vLLM every 300s
- Each idle port holds one CLOSE-WAIT socket (contributing to the 74-socket leak)
- Under memory pressure, idle port pages get swapped out → when a request comes in and the process needs to warm up, it triggers swap reads at the worst possible time

---

## Root Cause Summary

| Factor | Impact | Status |
|---|---|---|
| Memory at 91% with swap full | **CRITICAL** — just 2 new queries trigger OOM | Active |
| Active port RSS 10–24 GB each | **CRITICAL** — amplifies memory problem | Active |
| CLOSE-WAIT socket leak | **HIGH** — 74 stale sockets, grows under load | Active |
| local_outputs 139K dirs | **HIGH** — 99% CPU on VSCode watcher, I/O metadata pressure | Active |
| Idle port count (56 ports) | **MEDIUM** — 6.9GB wasted, 56 CLOSE-WAITs | Active |
| Swap only 2GB | **MEDIUM** — no safety net | Infrastructure |
| Log file writes (75 parallel) | **LOW** — 717MB, manageable on NVMe | Active |
| diskcache SQLite contention | **LOW** — 0 processes holding it open at quiet time | Likely bursts |

---

## Proposed Solutions

### 1. ✅ Fix CLOSE-WAIT Leak in Keepalive Thread (Quick — Code Change)

**Problem:** `_requests.get()` creates a new TCP connection each ping; vLLM closes it; local socket gets stuck in CLOSE-WAIT.

**Fix:** Use a persistent `requests.Session` with connection pool, and explicitly close the response:

```python
def _start_vllm_keepalive(base_url: str, interval_seconds: int = 300):
    def _ping():
        session = _requests.Session()
        session.headers.update({"Connection": "close"})  # don't keep-alive to vLLM
        while True:
            try:
                resp = session.get(f"{base_url}/models", timeout=10)
                resp.close()
                print(f"[Keepalive] vLLM ping -> HTTP {resp.status_code}")
            except Exception as e:
                print(f"[Keepalive] vLLM ping failed: {e}")
            time.sleep(interval_seconds)
```

Adding `"Connection": "close"` header tells the server to close the connection cleanly after each response, which moves the socket through the full TCP teardown instead of getting stuck in CLOSE-WAIT.

---

### 2. ✅ Clean Up local_outputs (Quick — One-Time + Cron)

**Problem:** 139,091 dirs, 26GB, VSCode watching all of them at 99% CPU.

**Immediate cleanup (safe — output dirs are only needed for the duration of a query):**
```bash
# Archive dirs older than 7 days into a tar (or just delete if not needed)
find /alan-data/jinc/git_chen/Biomni/local_outputs/ -mindepth 1 -maxdepth 1 \
     -type d -mtime +7 -name "2026*" | head -1000 | xargs rm -rf
```

**Add to `.vscode/settings.json` (exclude from file watching):**
```json
{
  "files.watcherExclude": {
    "**/local_outputs/**": true,
    "**/logs/**": true,
    "**/.biomni/**": true
  },
  "files.exclude": {
    "**/local_outputs": true
  }
}
```

**Add cleanup to the API server** — after a query completes, schedule old dirs for deletion:
```python
# In biomni_api_server: auto-cleanup output dirs older than 24h
import shutil
from datetime import datetime, timedelta

def _cleanup_old_outputs(output_base: str, max_age_hours: int = 24):
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    for d in Path(output_base).iterdir():
        if d.is_dir() and d.stat().st_mtime < cutoff.timestamp():
            shutil.rmtree(d, ignore_errors=True)
```

---

### 3. 🔧 Add Memory Limits to systemd Scopes (Moderate — Prevents OOM Cascade)

**Problem:** One busy port can consume 24GB, starving others and triggering OOM.

**Fix:** Add `MemoryMax` to your `systemd-run` commands:
```bash
systemd-run --user --scope --unit=biomni-$port \
  -p MemoryHigh=8G \
  -p MemoryMax=12G \
  bash -c "exec uvicorn ..."
```

- `MemoryHigh`: soft limit — process gets throttled (slower but stable)
- `MemoryMax`: hard limit — process gets SIGKILL if exceeded, but only that one port dies, not the whole machine

This turns a machine-wide OOM crash into a single-port restart.

---

### 4. 🔧 Reduce Idle Port Count (Moderate — Operational Change)

**Your observation is correct:** You spin up 9-10 ports per SCP endpoint but use only 2-5. The idle ports waste:
- 6.9GB RAM (56 idle × 130MB)
- 56 CLOSE-WAIT sockets
- 56 keepalive threads pinging vLLM every 5 min

**Recommendation:** Reduce to 3-4 ports per SCP endpoint when running experiments. Scale back up when you need full parallelism. The per-endpoint reduction:

| Current | Suggested | RAM saved | Sockets freed |
|---|---|---|---|
| 10 ports × 8 SCP nodes = 80 | 4 ports × 8 nodes = 32 | ~6GB (idle) | ~48 CLOSE-WAIT |

The per-port overhead of an **idle** biomni server is small (~130MB), but the risk is that under memory pressure, even idle ports can become the straw that breaks the camel's back.

---

### 5. 🔧 Increase Swap or Add RAM Pressure Safety Net

**Problem:** 2GB swap is completely exhausted and provides no safety net.

**Options (requires sysadmin):**
```bash
# Create a larger swap file (e.g., 32GB on the NVMe)
fallocate -l 32G /swapfile2 && chmod 600 /swapfile2
mkswap /swapfile2 && swapon /swapfile2
```

Or configure **memory overcommit** and **OOM score**:
```bash
# Lower OOM score for critical processes (they die last)
echo -1000 > /proc/$(pgrep sshd)/oom_score_adj
# Give uvicorn ports a slightly higher OOM score (die before sshd)
echo 200 > /proc/$(pgrep -f "uvicorn.*:8010")/oom_score_adj
```

---

### 6. 🔧 Log Rotation (Low Priority — Prevents Runaway Logs)

717MB of logs currently. At current rate, these will grow to tens of GB over weeks. Add `logrotate` config:
```
/alan-data/jinc/git_chen/Biomni/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate  # doesn't require process restart
}
```

---

## Recommended Priority Order

| Priority | Action | Expected Impact |
|---|---|---|
| 🔴 **Immediate** | Fix CLOSE-WAIT: add `Connection: close` header to keepalive | Clear 74 stuck sockets |
| 🔴 **Immediate** | Clean up local_outputs (archive/delete dirs >7 days) | Free 20+GB, kill VSCode 99% CPU |
| 🔴 **Immediate** | Add VSCode file watcher exclusion for local_outputs | Kill 99% CPU on fileWatcher immediately |
| 🟡 **Short-term** | Add `MemoryMax=12G` to systemd-run in server.md | Prevent single-port OOM cascade |
| 🟡 **Short-term** | Reduce to 4 ports/SCP endpoint (from 10) | Save 6GB RAM + clean up idle sockets |
| 🟢 **Medium-term** | Add per-query output dir auto-cleanup to API server | Prevent future accumulation |
| 🟢 **Medium-term** | Add logrotate for Biomni logs | Prevent log runaway |
| 🟢 **Long-term** | Request 32GB swap from sysadmin | Better OOM safety net |
