# R-GUARD

R-GUARD is a server-agent ransomware detection platform with two detection pathways:
- Behavioral pattern detection using sliding-window telemetry, LSTM-assisted feature extraction, and uncertainty-aware early-stopping deep model logic.
- Decoy file trap detection using Random Forest (R-Trap style) and DBSCAN-based strategic decoy placement.

## Architecture

- Server: hosts ML models, receives telemetry, computes risk, stores alerts, and attempts containment.
- Agent: runs on endpoints, collects process telemetry, monitors decoy files, reads Sysmon-style logs, and reports continuously.
- Dashboard: browser UI for live alert visibility.

## Project Structure

- server/app: FastAPI APIs, inference, containment, dashboard static files.
- agent: endpoint collector, decoy monitor, Sysmon parser.
- ml/behavioral: sliding window dataset prep, LSTM feature extraction, uncertainty-aware model training.
- ml/decoy: Random Forest training and DBSCAN decoy placement strategy.
- data/behavioral and data/decoy: training dataset location.
- models: saved trained models for deployment.

## Required Dataset Format

Behavioral CSV columns:
- file_ops_per_min
- entropy_delta
- extension_change_rate
- failed_decrypt_ops
- shadow_copy_delete_attempt
- privilege_escalation_flag
- label

Decoy CSV columns:
- access_freq
- rename_burst
- entropy_jump
- unknown_process_touch
- label

## Setup (Windows PowerShell)

1. Create a virtual environment:
   python -m venv .venv
2. Activate it:
   .\.venv\Scripts\Activate.ps1
3. Install dependencies:
   pip install -r requirements.txt

## Run Server

python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8000 --reload

Open dashboard:
http://127.0.0.1:8000/dashboard

## Train Models

Start the server and call training endpoint:

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/train" -Body (@{
  behavioral_csv_path = "data/behavioral/sample_behavioral.csv"
  decoy_csv_path = "data/decoy/sample_decoy.csv"
  sequence_length = 2
   epochs = 60
  test_size = 0.5
  random_state = 42
} | ConvertTo-Json) -ContentType "application/json"

Trained artifacts are written to:
- models/behavioral_uades.joblib
- models/decoy_rf.joblib

## Tune Final Alert Threshold

After training, tune the combined runtime alert threshold and apply it to `.env`:

python scripts/tune_final_alert.py --apply

To search for better fusion weights and threshold together:

python scripts/tune_final_alert.py --search-weights --apply

This evaluates three runtime scenarios (`behavioral_only`, `decoy_only`, `both_present`) using the trained models,
then writes these values to `.env`:
- `R_GUARD_ALERT_THRESHOLD`
- `R_GUARD_BEHAVIORAL_WEIGHT`
- `R_GUARD_DECOY_WEIGHT`

Restart the server after applying so the new threshold is used.

## Run Agent

python -m agent.agent --config agent/config.example.yaml

The agent sends heartbeat and detection requests repeatedly.

## Production Security Hardening

To enforce authenticated server-agent traffic, configure `.env`:

- `R_GUARD_REQUIRE_API_TOKEN=true`
- `R_GUARD_API_TOKEN=<strong-random-token>`
- `R_GUARD_REQUIRE_DASHBOARD_TOKEN=true` (optional, to protect `/alerts` API consumed by dashboard)

In your agent config set the same token:

- `api_token: "<strong-random-token>"`

When enabled, `/agent/*` and `/train` require header `X-R-Guard-Token`.
When dashboard token mode is enabled, `/alerts` also requires this header.

Containment safety allowlist is configurable with:

- `R_GUARD_CONTAINMENT_ALLOWLIST`

Default allowlist protects system/admin binaries from accidental termination.

## Production Run Scripts

- Server: `scripts/run_server_prod.ps1`
- Agent: `scripts/run_agent_prod.ps1`

## Windows Service Deployment

Run PowerShell as Administrator:

`powershell -ExecutionPolicy Bypass -File scripts/install_windows_services.ps1`

Then start services:

- `Start-Service RGuardServer`
- `Start-Service RGuardAgent`

## Production Handoff Checklist

See `docs/PRODUCTION_CHECKLIST.md` for final deployment and operational validation.

## Demo and Deployment Guide

For a safe live demo and a two-laptop production deployment, see `docs/DEMO_AND_DEPLOYMENT_GUIDE.md`.

## Sysmon Integration Notes

- Set sysmon_xml_path in agent/config.example.yaml to a generated XML export path.
- For production, replace the XML parser with direct Windows Event Log channel reading.

## Containment Notes

If risk is above threshold, server attempts to terminate suspicious process names from telemetry using psutil. This is a first response mechanism and should be paired with:
- host network isolation
- endpoint policy lockdown
- forensic preservation procedures

## What You Need To Upload Next

1. Real behavioral training dataset CSV in data/behavioral.
2. Real decoy trap training dataset CSV in data/decoy.
3. Optional Sysmon exported event XML samples for parser tuning.

After you upload these, I can tune feature engineering, thresholds, class balancing, and validation strategy for your environment.
