import { AlertItem } from "../data/mockData";

interface AlertTableProps {
  alerts: AlertItem[];
  onOpen: (alert: AlertItem) => void;
}

function severityStyle(severity: AlertItem["severity"]): string {
  if (severity === "Critical") return "bg-red-500/20 text-red-300 border-red-500/40";
  if (severity === "High") return "bg-orange-500/20 text-orange-300 border-orange-500/40";
  if (severity === "Medium") return "bg-yellow-500/20 text-yellow-300 border-yellow-500/40";
  return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
}

export function AlertTable({ alerts, onOpen }: AlertTableProps) {
  return (
    <section className="rounded-xl border border-cyber-line bg-cyber-panel p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-cyber-muted">Recent Alerts</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-cyber-line text-left text-cyber-muted">
              <th className="py-2 pr-3 font-medium">Time</th>
              <th className="py-2 pr-3 font-medium">Threat Type</th>
              <th className="py-2 pr-3 font-medium">Severity</th>
              <th className="py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr
                key={alert.id}
                className={`cursor-pointer border-b border-cyber-line/70 transition hover:bg-cyber-panel2 ${
                  alert.severity === "Critical" ? "glow-critical" : ""
                }`}
                onClick={() => onOpen(alert)}
              >
                <td className="py-2 pr-3 text-cyber-muted">{alert.time}</td>
                <td className="py-2 pr-3">{alert.threatType}</td>
                <td className="py-2 pr-3">
                  <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${severityStyle(alert.severity)}`}>
                    {alert.severity}
                  </span>
                </td>
                <td className="py-2">
                  <span className={alert.status === "Resolved" ? "text-emerald-300" : "text-cyber-neonAmber"}>{alert.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
