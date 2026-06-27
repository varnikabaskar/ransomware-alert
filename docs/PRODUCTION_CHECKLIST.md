# R-GUARD Production Checklist

## 1. Environment and Secrets

- [ ] Set `R_GUARD_REQUIRE_API_TOKEN=true` in `.env`
- [ ] Set `R_GUARD_REQUIRE_DASHBOARD_TOKEN=true` in `.env` (if dashboard API should be protected)
- [ ] Set `R_GUARD_API_TOKEN` to a strong random token
- [ ] Add matching `api_token` in agent config
- [ ] Restrict `.env` file permissions

## 2. Model and Threshold Validation

- [ ] Train models with production datasets
- [ ] Run tuner with constraints:
  - `python -m scripts.tune_final_alert --search-weights --max-fpr 0.03 --min-accuracy 0.95 --apply`
- [ ] Confirm metrics target:
  - FPR < 3%
  - Accuracy > 95%

## 3. Runtime Services

- [ ] Start server with `scripts/run_server_prod.ps1`
- [ ] Start agent with `scripts/run_agent_prod.ps1`
- [ ] (Optional) Install Windows services using `scripts/install_windows_services.ps1`
- [ ] Verify `/health` endpoint

## 4. Wiretrap and Containment

- [ ] Confirm decoy files are created and manifest is written
- [ ] Simulate decoy tamper and validate wiretrap alert generation
- [ ] Verify containment allowlist includes critical binaries
- [ ] Confirm only non-allowlisted suspect processes are terminated

## 5. Dashboard and Monitoring

- [ ] Build UI: `cd ui-dashboard && npm run build`
- [ ] Publish build to `server/app/static`
- [ ] Verify `http://127.0.0.1:8000/dashboard`
- [ ] If dashboard token is enabled, set browser local storage key `rguard_token`

## 6. Operational Readiness

- [ ] Configure backup and retention for `server/.alerts.json` or database backend
- [ ] Configure central log forwarding for agent and server logs
- [ ] Document escalation workflow for Critical alerts
- [ ] Schedule periodic retraining and threshold review
