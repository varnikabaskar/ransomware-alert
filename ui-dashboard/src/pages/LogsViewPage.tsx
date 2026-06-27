import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";
import { fetchAlerts } from "../services/api";
import { AlertItem, initialAlerts } from "../data/mockData";

function toCsv(rows: Array<Record<string, string | number | boolean | null | undefined>>): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]);
  const escapeCell = (value: string | number | boolean | null | undefined) => {
    const raw = value === null || value === undefined ? "" : String(value);
    return `"${raw.replace(/"/g, '""')}"`;
  };
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escapeCell(row[header])).join(","))].join("\n");
}

function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function LogsViewPage() {
  const [logs, setLogs] = useState<AlertItem[]>(initialAlerts);
  const [selectedHost, setSelectedHost] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const host = new URLSearchParams(window.location.search).get("host") || undefined;

  const loadLogs = async () => {
    setLoading(true);
    try {
      const alerts = await fetchAlerts(host);
      setLogs(alerts);
      setSelectedHost(host ?? null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadLogs();
  }, []);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (statusFilter !== "all" && log.status !== statusFilter) return false;
      if (severityFilter !== "all" && log.severity !== severityFilter) return false;
      if (dateFrom) {
        const from = new Date(dateFrom);
        const logDate = new Date(log.time);
        if (logDate < from) return false;
      }
      if (dateTo) {
        const to = new Date(dateTo);
        const logDate = new Date(log.time);
        // include entire day
        to.setHours(23, 59, 59, 999);
        if (logDate > to) return false;
      }
      return true;
    });
  }, [logs, statusFilter, severityFilter, dateFrom, dateTo]);

  const csv = useMemo(
    () =>
      toCsv(
        filteredLogs.map((log) => ({
          id: log.id,
          time: log.time,
          severity: log.severity,
          status: log.status,
          threatType: log.threatType,
          affectedSystem: log.affectedSystem,
          description: log.description,
          suggestedAction: log.suggestedAction,
        })),
      ),
    [filteredLogs],
  );

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(57,160,255,0.15)_0%,_rgba(9,11,16,1)_38%)] p-4 lg:p-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <div className="rounded-xl border border-cyber-line bg-cyber-panel p-5 shadow-neonBlue/30">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-cyber-muted">Ransomware Shield</p>
              <h1 className="mt-2 text-2xl font-bold text-cyber-text">Fleet Registered Logs</h1>
              <p className="mt-2 text-sm text-cyber-muted">
                This tab shows the registered log history for {selectedHost ?? "all agents"} and can be exported as CSV.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void loadLogs()}
                className="inline-flex items-center gap-2 rounded-lg border border-cyber-line px-4 py-2 text-sm text-cyber-text transition hover:border-cyber-neonBlue/60"
              >
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                type="button"
                onClick={() => downloadCsv(`rguard-logs-${new Date().toISOString().slice(0, 19)}.csv`, csv)}
                className="inline-flex items-center gap-2 rounded-lg bg-cyber-neonBlue px-4 py-2 text-sm font-semibold text-black transition hover:brightness-110"
              >
                <Download size={16} />
                Download CSV
              </button>
              <div className="flex items-center gap-2">
                <label className="text-xs text-cyber-muted">Status</label>
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded px-2 py-1">
                  <option value="all">All</option>
                  <option value="Pending">Pending</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-cyber-muted">Severity</label>
                <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="rounded px-2 py-1">
                  <option value="all">All</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-cyber-muted">From</label>
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="rounded px-2 py-1" />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-cyber-muted">To</label>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="rounded px-2 py-1" />
              </div>
              <button
                type="button"
                onClick={() => window.location.assign("/dashboard/")}
                className="inline-flex items-center gap-2 rounded-lg border border-cyber-line px-4 py-2 text-sm text-cyber-text transition hover:border-cyber-neonBlue/60"
              >
                <ArrowLeft size={16} />
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>

        <section className="rounded-xl border border-cyber-line bg-cyber-panel p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-cyber-muted">Fleet Log History</h2>
            <span className="text-xs text-cyber-muted">{filteredLogs.length} records</span>
          </div>

          {loading ? (
            <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-4 text-sm text-cyber-muted">Loading logs...</div>
          ) : logs.length === 0 ? (
            <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-4 text-sm text-cyber-muted">No logs available yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-cyber-muted">
                  <tr className="border-b border-cyber-line">
                    <th className="py-2 pr-3 font-medium">Time</th>
                    <th className="py-2 pr-3 font-medium">Severity</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Threat Type</th>
                    <th className="py-2 pr-3 font-medium">System</th>
                    <th className="py-2 font-medium">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="border-b border-cyber-line/60 align-top transition hover:bg-cyber-panel2">
                      <td className="py-3 pr-3 text-cyber-muted">{log.time}</td>
                      <td className="py-3 pr-3">
                        <span className="rounded-full border border-cyber-line px-2 py-0.5 text-xs uppercase tracking-wide text-cyber-text">
                          {log.severity}
                        </span>
                      </td>
                      <td className="py-3 pr-3">
                        <span className={log.status === "Resolved" ? "text-emerald-300" : "text-cyber-neonAmber"}>{log.status}</span>
                      </td>
                      <td className="py-3 pr-3 font-medium text-cyber-text">{log.threatType}</td>
                      <td className="py-3 pr-3 text-cyber-text">{log.affectedSystem}</td>
                      <td className="py-3 text-cyber-muted">{log.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}