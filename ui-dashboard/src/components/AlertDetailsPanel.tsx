import { X } from "lucide-react";
import { AlertItem } from "../data/mockData";

interface AlertDetailsPanelProps {
  alert: AlertItem | null;
  onClose: () => void;
  onMarkAsRead: (id: string) => void;
}

export function AlertDetailsPanel({ alert, onClose, onMarkAsRead }: AlertDetailsPanelProps) {
  if (!alert) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/55 p-4">
      <div className="w-full max-w-2xl rounded-xl border border-cyber-line bg-cyber-panel p-5 shadow-neonBlue">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-semibold">Alert Details</h3>
            <p className="text-sm text-cyber-muted">{alert.id} • {alert.time}</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg border border-cyber-line p-2 text-cyber-muted hover:text-cyber-text">
            <X size={18} />
          </button>
        </div>

        <div className="grid gap-4 text-sm md:grid-cols-2">
          <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3">
            <div className="text-cyber-muted">Threat Type</div>
            <div className="mt-1 font-medium">{alert.threatType}</div>
          </div>
          <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3">
            <div className="text-cyber-muted">Affected System</div>
            <div className="mt-1 font-medium">{alert.affectedSystem}</div>
          </div>
          <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3 md:col-span-2">
            <div className="text-cyber-muted">Description</div>
            <div className="mt-1">{alert.description}</div>
          </div>
          <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3 md:col-span-2">
            <div className="text-cyber-muted">Suggested Action</div>
            <div className="mt-1 font-medium text-cyber-neonGreen">{alert.suggestedAction}</div>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => onMarkAsRead(alert.id)}
            disabled={alert.status === "Resolved"}
            className="rounded-lg bg-cyber-neonBlue px-4 py-2 text-sm font-semibold text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {alert.status === "Resolved" ? "Marked as Read" : "Mark as Read"}
          </button>
        </div>
      </div>
    </div>
  );
}
