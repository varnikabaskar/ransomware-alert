from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse


STATUS_PATH = Path("agent/runtime_status.json")
app = FastAPI(title="R-GUARD Agent Dashboard", version="0.1.0")


@app.get("/status")
def status() -> dict:
    if not STATUS_PATH.exists():
        return {"status": "starting", "message": "Agent has not published status yet"}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "error", "message": "Failed to parse status"}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>R-GUARD Agent Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-slate-50 text-slate-900">
    <div class="mx-auto max-w-6xl p-6">
      <div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Endpoint View</div>
        <h1 class="mt-2 text-2xl font-semibold">R-GUARD Agent Dashboard</h1>
        <p class="mt-1 text-sm text-slate-600">Single-host telemetry for this computer only. The server dashboard is separate and shows the full agent fleet.</p>
      </div>

      <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div class="rounded-xl border bg-white p-4"><div class="text-xs uppercase text-slate-500">Host</div><div id="host" class="mt-1 text-lg font-semibold">-</div></div>
        <div class="rounded-xl border bg-white p-4"><div class="text-xs uppercase text-slate-500">Last Risk</div><div id="risk" class="mt-1 text-lg font-semibold">-</div></div>
        <div class="rounded-xl border bg-white p-4"><div class="text-xs uppercase text-slate-500">Severity</div><div id="severity" class="mt-1 text-lg font-semibold">-</div></div>
      </div>

      <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        <section class="rounded-xl border bg-white p-4"><h2 class="font-semibold">Local Event Logs</h2><div id="logs" class="mt-2 space-y-2 text-sm"></div></section>
        <section class="rounded-xl border bg-white p-4"><h2 class="font-semibold">Endpoint Notifications</h2><div id="notes" class="mt-2 space-y-2 text-sm"></div></section>
      </div>

      <div class="mt-6 rounded-xl border bg-white p-4">
        <h2 class="font-semibold">Register this agent with server</h2>
        <p class="text-sm text-slate-600 mt-1">Enter the registration code generated from the server to bind this agent as a node.</p>
        <div class="mt-3 flex flex-col gap-2 max-w-lg">
          <input id="serverUrl" placeholder="https://your-server:8000" class="rounded border px-3 py-2" />
          <input id="regCode" placeholder="Registration code" class="rounded border px-3 py-2" />
          <button id="registerBtn" class="rounded bg-slate-800 text-white px-4 py-2 w-40">Register Agent</button>
          <div id="regResult" class="text-sm text-slate-600"></div>
        </div>
      </div>
    </div>

    <script>
      async function refresh() {
        try {
          const res = await fetch('/status');
          const data = await res.json();
          const verdict = data.last_verdict || {};
          document.getElementById('host').textContent = data.host || '-';
          document.getElementById('risk').textContent = verdict.risk_score ? `${(verdict.risk_score * 100).toFixed(1)}%` : '-';
          document.getElementById('severity').textContent = verdict.severity || 'normal';

          const logs = (data.logs || []).slice(0, 12).map((x) => `<div class="rounded border p-2">risk ${(100 * (x.risk || 0)).toFixed(1)}% | ${x.severity || 'normal'} | events ${x.events || 0}</div>`).join('');
          document.getElementById('logs').innerHTML = logs || '<div>No logs yet</div>';

          const notes = (data.notifications || []).slice(0, 12).map((n) => `<div class="rounded border p-2">${n.level || 'info'}: ${n.message || ''}</div>`).join('');
          document.getElementById('notes').innerHTML = notes || '<div>No notifications yet</div>';
        } catch {
          document.getElementById('logs').innerHTML = '<div>Unable to load status</div>';
        }
      }
      refresh();
      setInterval(refresh, 5000);

      document.getElementById('registerBtn').addEventListener('click', async function () {
        const server = document.getElementById('serverUrl').value.trim();
        const code = document.getElementById('regCode').value.trim();
        const out = document.getElementById('regResult');
        out.textContent = '';
        if (!server || !code) {
          out.textContent = 'Server URL and code are required';
          return;
        }
        try {
          const statusRes = await fetch('/status');
          const status = await statusRes.json();
          const agentId = status.agent_id;
          if (!agentId) {
            out.textContent = 'Unable to determine agent_id from runtime status';
            return;
          }
          const resp = await fetch(`${server.replace(/\/$/, '')}/agent/register/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_id: agentId, code }),
          });
          const body = await resp.json();
          if (resp.ok) {
            out.textContent = `Registered as ${body.agent_id}`;
            if (body.pass_key) {
              try {
                await fetch('/apply_passkey', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ pass_key: body.pass_key })
                });
                out.textContent += ' (passkey saved locally)';
              } catch (e) {
                out.textContent += ' (failed to save passkey locally)';
              }
            }
          } else {
            out.textContent = body.detail || JSON.stringify(body);
          }
        } catch (e) {
          out.textContent = `Registration failed: ${e}`;
        }
      });
    </script>
  </body>
</html>
"""


@app.post('/apply_passkey')
def apply_passkey(payload: dict[str, Any]):
    pass_key = payload.get('pass_key')
    if not pass_key:
        raise HTTPException(status_code=400, detail='pass_key missing')

    # write a small runtime config that the agent process can pick up immediately
    try:
        Path('agent/runtime_config.json').write_text(json.dumps({'pass_key': pass_key}), encoding='utf-8')
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to write runtime config')

    # also persist into the agent YAML config if present
    cfg_path = Path('agent/config.example.yaml')
    if cfg_path.exists():
        try:
            import yaml

            cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8')) or {}
            cfg['pass_key'] = pass_key
            cfg_path.write_text(yaml.safe_dump(cfg), encoding='utf-8')
        except Exception:
            # non-fatal
            pass

    return {'status': 'ok'}
