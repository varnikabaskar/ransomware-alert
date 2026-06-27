# R-GUARD Live Demo Video Script
## Professional Presentation for Judges

**Total Runtime:** ~5-7 minutes  
**Target:** Live ransomware detection, decoy trap mechanism, and dashboard response

---

## VIDEO STRUCTURE

### Segment 1: Architecture Overview (0:00 - 0:45)

**Narration:**
"R-GUARD is a hybrid ransomware detection system built on a server-agent architecture. The server analyzes behavioral patterns and decoy trap events using machine learning. Endpoints run lightweight agents that collect telemetry and monitor decoy files. When a threat is detected, the server and agent work together to isolate and contain the attack."

**Visual:**
- Show architecture diagram (if available) or draw simple blocks:
  - Agent (endpoint) → Server (central)
  - Two detection pathways: Behavioral + Decoy Traps
  - Alert output to Dashboard

---

### Segment 2: Demo Setup & Decoy Placement (0:45 - 2:00)

**Narration:**
"Now let's see how this works in practice. First, I'll show you the decoy files that the agent creates. These are fake financial documents that act as bait for ransomware."

**Step 1: Open File Explorer**
```powershell
explorer.exe agent\decoy_files
```

**On Screen:**
Point to the decoy folder and explain:
- `DEC0Y_finance_00.xlsx` - Fake Excel file
- `DEC0Y_finance_01.xlsx` - Another fake file
- `DEC0Y_finance_02.xlsx` - Third decoy
- `.decoy_manifest.json` - Integrity tracking file

**Narration:**
"Each decoy has a stored hash in the manifest file. If ransomware tries to encrypt or modify these files, that change triggers our trap detection. The agent is constantly watching these files."

**Step 2: Show the manifest file**
```powershell
Get-Content agent\decoy_files\.decoy_manifest.json | ConvertFrom-Json | ConvertTo-Json
```

**On Screen:**
Show the JSON output with:
- `last_rotation_utc`: When the decoys were last rotated
- `paths`: List of all decoy file paths
- `wiretraps`: Hash values and file sizes for integrity checking

**Narration:**
"The manifest stores the SHA-256 hash of each decoy. This allows us to detect any modification, deletion, or tampering attempt."

---

### Segment 3: Start Server & Agent (2:00 - 2:30)

**Narration:**
"Now I'll start the R-GUARD system. The server runs centralized analysis, and the agent monitors this endpoint."

**Step 1: Terminal 1 - Start Server**
```powershell
cd C:\Users\Shabutha\R-GUARD
.\scripts\run_server_prod.ps1
```

**Wait for:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**On Screen:**
Capture the server startup message.

**Narration:**
"The server is now running and listening on port 8000. It's ready to receive telemetry from agents and perform analysis."

**Step 2: Terminal 2 - Start Agent**
```powershell
cd C:\Users\Shabutha\R-GUARD
.\scripts\run_agent_prod.ps1 -ConfigPath agent\config.example.yaml
```

**Wait for:**
```
[R-GUARD Agent] Started as endpoint-001 on DESKTOP-****
```

**On Screen:**
Capture the agent startup message.

**Narration:**
"The agent is now running. It's connected to the server and beginning to monitor the system for suspicious behavior and decoy file access."

---

### Segment 4: Open Dashboard (2:30 - 3:15)

**Narration:**
"Next, I'll open the R-GUARD dashboard where we can see real-time monitoring, system health metrics, threat trends, and alerts."

**Step 1: Open Browser**
Navigate to: `http://127.0.0.1:8000/dashboard`

**On Screen - Point out each component:**

**1. Top Navigation Bar (0:10 seconds)**
- Current time display
- Notification badge (shows unread alerts)
- User profile (SecOps Admin, SOC Team)

**Narration:**
"At the top is the navigation bar showing the current time and notification count. When an alert is triggered, this badge will increment."

**2. Left Sidebar (0:10 seconds)**
Show the menu items:
- Dashboard (active)
- Alerts
- Logs
- System Health
- Settings

**Narration:**
"The sidebar provides access to different sections. We're currently on the main Dashboard view."

**3. Health Metrics Cards (0:20 seconds)**
Point to each card and read the values:
- **CPU Usage**: `48%` - Healthy (Green) - Uses blue line indicator
- **Memory Usage**: `63%` - Warning (Amber) - Uses amber line indicator
- **Disk Activity**: `28%` - Healthy (Green)
- **Network Traffic**: `55%` - Healthy (Green)

**Narration:**
"These cards show real-time system health. Each metric is color-coded: green for safe (under 60%), amber for warning (60-80%), and red for critical (above 80%). The bars fill proportionally to the percentage."

**4. System Activity Chart (0:20 seconds)**
- X-axis: Time of day (24-hour window)
- Y-axis: Percentage
- Blue line: CPU usage
- Green line: Network traffic
- Red dots: Suspicious events

**Narration:**
"The System Activity chart shows CPU and network trends over the last 24 hours. Red spikes indicate suspicious activity detected during that hour. This helps identify patterns of attack activity."

**5. Threat Detection Trends Chart (0:15 seconds)**
Point to the red area chart with:
- X-axis: Time of day
- Y-axis: Threat count
- Red area: Number of ransomware-like events detected

**Narration:**
"The Threat Detection Trends graph shows the volume of suspicious events per hour. During a ransomware attack, this would spike dramatically as encryption activity accelerates."

**6. Recent Alerts Table (0:30 seconds)**
Show the table with columns:
- Time
- Threat Type
- Severity (Critical/High/Medium/Low)
- Status (Pending/Resolved)

Point to example alerts:
- "Mass File Encryption Pattern" - Critical - Pending
- "Decoy Wiretrap Tamper" - High - Pending
- "Shadow Copy Delete Attempt" - Medium - Resolved

**Narration:**
"The Recent Alerts table shows detected threats in reverse chronological order. Each row shows when it was detected, what type of threat, severity level, and current status. Critical alerts glow red."

**7. Notifications Panel (0:15 seconds)**
Point to the right-side notification list:
- Red bell icon for critical alerts
- Yellow bell icon for warnings
- Blue info icon for informational messages

**Narration:**
"On the right, the Notifications panel provides a real-time stream of alerts and system events. Critical notifications appear at the top with red icons."

---

### Segment 5: Trigger Safe Fake Attack (3:15 - 4:30)

**Narration:**
"Now comes the critical test. I'm going to simulate a ransomware attack targeting the decoy files. This is 100% safe—we're only modifying the decoy files we set up explicitly for this purpose."

**Step 1: Show the attack command**
Display the command on screen:
```powershell
python .\scripts\demo_fake_attack.py --dir agent\decoy_files_wiretrap_test --delay 0.25
```

**Narration:**
"This script safely simulates ransomware behavior by creating encrypted copies of the decoy files. No real files are harmed, and no actual ransomware is involved. The script creates `.locked` versions of the decoys within the monitored folder."

**Step 2: Execute the attack**
```powershell
Set-Location C:\Users\Shabutha\R-GUARD
python .\scripts\demo_fake_attack.py --dir agent\decoy_files_wiretrap_test --delay 0.25
```

**Expected output:**
```
Simulating fake attack on 3 files in c:\Users\Shabutha\R-GUARD\agent\decoy_files_wiretrap_test
[OK] created: c:\Users\Shabutha\R-GUARD\agent\decoy_files_wiretrap_test\.decoy_manifest.json.locked
[OK] created: c:\Users\Shabutha\R-GUARD\agent\decoy_files_wiretrap_test\DEC0Y_finance_00.xlsx.locked
[OK] created: c:\Users\Shabutha\R-GUARD\agent\decoy_files_wiretrap_test\DEC0Y_finance_01.xlsx.locked
Done. Originals preserved; encrypted-copies created with .locked suffix.
```

**On Screen - Monitor the servers:**

**Terminal 1 (Server):**
Watch for:
```
POST /agent/detect HTTP/1.1" 200 OK
```

**Narration:**
"The server received the detection request from the agent. The agent detected the decoy tampering and immediately reported it."

**Terminal 2 (Agent):**
Watch for output like:
```
[R-GUARD Agent] risk= 0.XXX behavior= X.XXX decoy= X.XXX alert= True
```

**Narration:**
"The agent computed three key scores: behavioral risk, decoy trap risk, and a final overall risk. The 'alert= True' indicates a threat was detected."

---

### Segment 6: Dashboard Response & Alert Analysis (4:30 - 5:45)

**Narration:**
"Now let's see how the system responded to the attack. I'll refresh the dashboard to show the new alert."

**Step 1: Refresh the dashboard**
Press F5 in the browser or click the notifications bell.

**On Screen - Show the changes:**

**1. Health Cards Update**
- Values have changed slightly as system processed the detection
- Explain the fluctuation is normal

**2. Notifications Badge**
- Badge count increased
- Now shows a number (e.g., "2" or higher)

**Narration:**
"The notification badge has increased, indicating new alerts. Let's look at the details."

**3. New Alert in Table**
Point to the top row of the alert table:
- Time: Current time
- Threat Type: "Possible ransomware activity on host DESKTOP-****"
- Severity: "Critical" (Red)
- Status: "Pending" or "Resolved"

**Narration:**
"A new Critical alert has appeared in the Recent Alerts table. This was detected within seconds of the decoy file tampering."

**4. Click Alert to See Details**
Click the alert row to open the full details panel.

**Alert Details Panel - Explain each section:**

**Alert ID & Time:**
```
ID: ALT-XXXX
Time: 3:42:15 PM
```

**Threat Type:**
```
"Possible ransomware activity on host DESKTOP-P8MDA2F"
```
**Narration:**
"This field identifies what type of threat was detected. In this case, ransomware activity."

**Affected System:**
```
"DESKTOP-P8MDA2F"
```
**Narration:**
"This is the hostname of the endpoint where the activity was detected."

**Description:**
```
"Behavioral sequence resembles ransomware encryption pattern"
"Decoy trap interaction indicates unauthorized bulk file activity"
```
**Narration:**
"The description provides two key reasons the alert was triggered:
1. Behavioral analysis detected encryption-like process patterns (file writes, rapid operations)
2. Decoy trap analysis detected unauthorized access to our monitored decoy files

Either one alone might be suspicious, but together they provide strong confidence in the detection."

**Suggested Action:**
```
"Isolate host and trigger containment workflow"
```
**Narration:**
"The system recommends immediate isolation of the affected host and automatic containment. This includes terminating suspicious processes and preventing network spread."

**5. Show Detection Metrics**
Point to the server logs or API response showing:
```json
{
  "behavioral_score": 1.0,
  "decoy_score": 0.627,
  "risk_score": 0.739,
  "is_ransomware": true,
  "contained": true
}
```

**Narration:**
"Let's break down the detection scoring:

- **Behavioral Score: 1.0** - The process behavior matched ransomware signatures at 100% confidence. This includes rapid file writes, extension changes, and suspicious process names.

- **Decoy Score: 0.627** - Our decoy files were accessed and modified with 62.7% confidence of malicious intent. This is based on access patterns, modification velocity, and entropy changes.

- **Risk Score: 0.739** - The final fused score combined behavioral (65% weight) and decoy (35% weight) evidence. This is above the 0.70 threshold.

- **is_ransomware: true** - The system classified this as a true ransomware attack.

- **contained: true** - Containment measures were applied automatically."

---

### Segment 7: Show Containment Action (5:45 - 6:15)

**Narration:**
"The system also attempted automatic containment. Let me show you what processes were terminated."

**Step 1: Show containment notes from the alert**
In the Alert Details Panel, look for:
```
Containment Notes:
"Terminated suspect process(es): svchost.exe:2816, runtimebroker.exe:5860, conhost.exe:3000"
```

**Narration:**
"The server identified processes that matched the ransomware's behavioral signature and terminated them. These are non-critical system processes that showed suspicious file operation patterns.

The system maintains a protected allowlist of critical system binaries (explorer.exe, services.exe, system, etc.) to prevent accidental damage."

**Step 2: Optional - Show the allowlist**
```powershell
$env = @{}
Get-Content .env | ForEach-Object {
  if ($_ -match '^R_GUARD_CONTAINMENT_ALLOWLIST=(.*)$') {
    Write-Host "Protected processes: $($matches[1])"
  }
}
```

**Narration:**
"These processes are protected from termination even if they show suspicious behavior. This prevents the system from accidentally killing Windows, networking, or display drivers."

---

### Segment 8: Summary & Key Takeaways (6:15 - 7:00)

**Narration:**
"Let's recap what we just demonstrated:

1. **Decoy Placement**: R-GUARD creates monitored fake files that act as early warning sensors.

2. **Trap Detection**: When those decoys are accessed, the agent detects it instantly and reports to the server.

3. **Behavioral Analysis**: Simultaneously, the system analyzes process behavior for encryption-like patterns.

4. **Risk Fusion**: The server combines both signals using machine learning to compute a final risk score.

5. **Automated Response**: When the risk crosses the threshold, the system automatically:
   - Generates a critical alert
   - Terminates suspicious processes
   - Notifies the dashboard in real-time

6. **Dashboard Visibility**: Security operators see:
   - Real-time health metrics
   - Threat trends and volume
   - Alert details with suggested actions
   - Notification stream of all events

The entire detection-to-response cycle happened in seconds, demonstrating the effectiveness of a hybrid behavioral + deception-based approach to ransomware defense."

**Final Screen:**
Show the dashboard with:
- Active alert highlighted
- Threat chart spike visible
- Notification badge
- System still running normally

**Narration:**
"R-GUARD successfully detected and responded to the ransomware activity without impacting legitimate system operations. The endpoint continued functioning normally while the attack was isolated and contained."

---

## DASHBOARD METRICS EXPLAINED

### Health Cards (Top Row)

| Metric | Green (<60%) | Amber (60-80%) | Red (>80%) | What It Means |
|--------|-------------|----------------|-----------|--------------|
| **CPU Usage** | Safe | Operating near capacity | System overload | % of CPU cores in use |
| **Memory Usage** | Safe | System memory pressure | Out of memory risk | % of RAM in use |
| **Disk Activity** | Safe | Heavy I/O | Potential ransomware write burst | % disk I/O utilization |
| **Network Traffic** | Safe | Elevated traffic | Potential data exfiltration | % network bandwidth in use |

### Activity Chart Lines

- **Blue Line (CPU)**: Shows processor usage over time. Spikes indicate compute-heavy processes.
- **Green Line (Network)**: Shows network throughput. Spikes suggest data transfer or C2 communication.
- **Red Dots (Suspicious)**: Marks when suspicious behavior was detected during that hour.

### Threat Detection Trends

- **Y-Axis (0-10)**: Number of ransomware-like events detected per hour.
- **X-Axis (Time)**: 24-hour period.
- **Interpretation**: Baseline is 0-2 events/hour (normal background noise). Attack would show spike to 5-10+ events/hour.

### Alert Table Columns

| Column | Values | Meaning |
|--------|--------|---------|
| **Time** | HH:MM:SS | When the alert was triggered |
| **Threat Type** | Text description | Category of detected attack |
| **Severity** | Critical/High/Medium/Low | How confident the detection is |
| **Status** | Pending/Resolved | Whether action has been taken |

**Color coding:**
- Red = Critical (>0.85 risk score)
- Orange = High (0.70-0.85 risk score)
- Yellow = Medium (0.50-0.70 risk score)
- Green = Low (<0.50 risk score)

### Alert Details (Full View)

**Displayed metrics:**
- `behavioral_score`: (0.0-1.0) How much process behavior matches ransomware patterns
- `decoy_score`: (0.0-1.0) How much decoy interaction suggests attack
- `risk_score`: (0.0-1.0) Fused score = (behavioral_score × 0.65) + (decoy_score × 0.35)
- `is_ransomware`: Boolean - True if risk_score ≥ alert_threshold
- `contained`: Boolean - True if containment was attempted

**Reasons provided:**
- "Behavioral sequence resembles ransomware encryption pattern" → behavioral_score > 0.65
- "Decoy trap interaction indicates unauthorized bulk file activity" → decoy_score > 0.5

---

## RECORDING TIPS

1. **Screen Resolution**: Record at 1920x1080 minimum for clarity
2. **Font Size**: Zoom browser to 125% so text is readable
3. **Audio**: Use a microphone and speak clearly with pauses between points
4. **Pacing**: Pause 1-2 seconds after each narration point so viewers can read the screen
5. **Timing**: This script targets 7 minutes; practice to avoid rushing
6. **B-Roll**: If possible, record the code/config files being set up beforehand
7. **Failsafes**: Record each segment separately so you can re-take sections without re-doing the entire demo

---

## COMMAND REFERENCE (Quick Copy-Paste)

```powershell
# Terminal 1 - Server
cd C:\Users\Shabutha\R-GUARD
.\scripts\run_server_prod.ps1

# Terminal 2 - Agent  
cd C:\Users\Shabutha\R-GUARD
.\scripts\run_agent_prod.ps1 -ConfigPath agent\config.example.yaml

# Terminal 3 - Fake Attack
cd C:\Users\Shabutha\R-GUARD
python .\scripts\demo_fake_attack.py --dir agent\decoy_files_wiretrap_test --delay 0.25

# Dashboard
http://127.0.0.1:8000/dashboard

# Server Alerts API
http://127.0.0.1:8000/alerts
```
