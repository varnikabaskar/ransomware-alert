# R-GUARD Demo and Production Deployment Guide

This guide covers two things:

1. A safe live demo that shows how decoy files are created, trapped, and escalated without running real ransomware.
2. A production deployment where this laptop runs the server and your friend's laptop runs the agent.

## 1. Safe Live Demo for Presentation

### What the demo shows

- The agent creates decoy files in the watched folder.
- A fake attack modifies one decoy file only.
- The decoy monitor detects the tamper.
- The agent sends trap events to the server.
- The server fuses behavioral and decoy signals, creates an alert, and triggers containment if enabled.
- The dashboard shows the alert, notification, severity, and final status.

### Where decoy files are created

By default, the decoy files are created inside the agent watch directory:

- `agent/decoy_files/`

The agent uses `agent/decoy_monitor.py` to create files named like:

- `DEC0Y_finance_00.xlsx`
- `DEC0Y_finance_01.xlsx`
- `DEC0Y_finance_02.xlsx`

It also writes a manifest file:

- `agent/decoy_files/.decoy_manifest.json`

That manifest stores file hashes and is used to detect tamper or deletion.

### How the trap actually works

The trap has two layers:

1. File-system watch layer
   - The agent starts a watchdog observer on the decoy folder.
   - Any event on a file starting with `DEC0Y_` is captured as a trap event.

2. Integrity check layer
   - The manifest stores the original SHA-256 hash for each decoy file.
   - If a decoy is modified or deleted, the hash check fails or the file is missing.
   - That becomes a high-confidence wiretrap alert.

The agent then sends those trap events to the server in `POST /agent/detect`.

### How the attack is fake and safe

Do not use real ransomware.

Use the included safe demo script:

```powershell
python .\scripts\demo_fake_attack.py --dir agent\decoy_files_wiretrap_test --delay 0.25
```

This script only creates `.locked` copies of the files in the decoy folder and preserves the originals. It simulates ransomware-like file activity without harming your laptop.

You can also simulate a trap by appending a small text line to one watched decoy file:

```powershell
Add-Content -Path 'agent\decoy_files\DEC0Y_finance_00.xlsx' -Value "FAKE_RANSOMWARE_WRITE_TEST"
```

### Exact demo steps for the panel

1. Start the server on your laptop.

```powershell
Set-Location C:\Users\Shabutha\R-GUARD
.\scripts\run_server_prod.ps1
```

2. Start the agent on the same laptop for rehearsal or on your friend's laptop for real deployment.

```powershell
Set-Location C:\Users\Shabutha\R-GUARD
.\scripts\run_agent_prod.ps1 -ConfigPath agent\config.example.yaml
```

3. Open the dashboard.

```text
http://127.0.0.1:8000/dashboard
```

4. Show the initial dashboard state.
   - Health cards show current CPU, memory, disk, and network load.
   - Activity chart shows recent system movement.
   - Threat chart shows threat volume over time.
   - Alert table shows recent alerts.
   - Notification panel shows recent warnings and critical items.

5. Show the decoy folder in File Explorer.
   - Open `agent/decoy_files/`.
   - Point out the `DEC0Y_*.xlsx` files and the `.decoy_manifest.json` file.

6. Trigger the fake attack.

```powershell
python .\scripts\demo_fake_attack.py --dir agent\decoy_files_wiretrap_test --delay 0.25
```

7. Refresh the dashboard and show the response.
   - New alert appears in the alert table.
   - Notification count increases in the top bar.
   - Alert details show the affected system, threat type, and suggested action.

8. Show the server alert API if needed.

```text
http://127.0.0.1:8000/alerts
```

### What the output means during the demo

- `heartbeat 200 OK` means the agent is connected and reporting telemetry.
- `detect 200 OK` means the server accepted telemetry and returned a verdict.
- `is_ransomware: true` means the fused score crossed the alert threshold.
- `contained: true` means containment ran on the machine that is executing the containment service.

### Important containment note

The server-side containment service terminates suspect processes on the machine where the server is running.

If the agent is on your friend's laptop, local endpoint termination happens on that laptop only if `enable_local_termination: true` is set in the agent config.

So there are two possible termination paths:

- Server containment: protects the server laptop.
- Agent local termination: protects the friend's laptop.

The current code does not remote-kill processes across machines.

## 2. Production Deployment

### Production layout

- Server laptop: runs FastAPI server, dashboard, alert storage, and central inference.
- Friend's laptop: runs the agent, decoy monitor, and local telemetry collection.

### Server laptop setup

1. Install Python dependencies.

```powershell
Set-Location C:\Users\Shabutha\R-GUARD
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure `.env` on the server laptop.

Recommended production values:

```env
R_GUARD_SERVER_HOST=0.0.0.0
R_GUARD_SERVER_PORT=8000
R_GUARD_ALERT_THRESHOLD=0.70
R_GUARD_ENABLE_CONTAINMENT=true
R_GUARD_REQUIRE_API_TOKEN=true
R_GUARD_REQUIRE_DASHBOARD_TOKEN=false
R_GUARD_API_TOKEN=<strong-random-token>
```

3. Start the server.

```powershell
.\scripts\run_server_prod.ps1
```

4. Find the server laptop LAN IP.

```powershell
ipconfig
```

Use that LAN IP in the agent config on your friend's laptop.

5. If Windows Firewall blocks the agent, open port 8000 inbound on the server laptop.

### Friend's laptop setup

1. Copy the repository to the friend's laptop or copy only the `agent/`, `models/`, and required runtime files.

2. Install Python dependencies.

```powershell
Set-Location C:\Users\Shabutha\R-GUARD
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Create a production agent config from the template.

- Use `agent/config.remote.example.yaml` as the base.
- Set `server_url` to the server laptop LAN IP, for example `http://192.168.1.25:8000`.
- Set `api_token` to the same token used on the server if token auth is enabled.

4. Start the agent.

```powershell
.\scripts\run_agent_prod.ps1 -ConfigPath agent\config.remote.example.yaml
```

### Real-time test procedure

1. Confirm the agent can reach the server.
   - On the server laptop, `/agent/heartbeat` and `/agent/detect` should start logging 200 responses.

2. Confirm the agent created decoys.
   - Check `agent/decoy_files/` on the friend's laptop.

3. Run a safe fake attack on the friend's laptop.

```powershell
python .\scripts\demo_fake_attack.py --dir agent\decoy_files --delay 0.25
```

4. Watch the dashboard on the server laptop.
   - Alerts should appear in the table.
   - Notifications should increment.
   - The alert detail panel should show the exact reason string and suggested action.

5. If you want to show containment, keep `enable_local_termination: true` on the friend's laptop and use a fake suspect process name that is already in telemetry.

### What to show the judges

- The server dashboard before the attack.
- The decoy files on the friend laptop.
- The fake attack command.
- The server response and alert creation.
- The alert details panel.
- The notifications badge changing.
- The containment note after detection.

## 3. Suggested Presentation Order

1. Show architecture slide.
2. Show server laptop dashboard.
3. Show friend's laptop decoy folder.
4. Run fake attack.
5. Show alert generation and containment note.
6. Explain that no real ransomware was used and only decoy files were touched.
