import { AlertCircle, Bell, Info } from "lucide-react";
import { NotificationItemData } from "../data/mockData";

interface NotificationItemProps {
  item: NotificationItemData;
  onOpen: (id: string) => void;
}

export function NotificationItem({ item, onOpen }: NotificationItemProps) {
  const Icon = item.level === "critical" ? AlertCircle : item.level === "warning" ? Bell : Info;
  const tone = item.level === "critical" ? "text-red-300" : item.level === "warning" ? "text-yellow-300" : "text-blue-300";

  return (
    <button
      type="button"
      onClick={() => onOpen(item.id)}
      className="flex w-full items-start gap-3 rounded-lg border border-cyber-line bg-cyber-panel2 px-3 py-2 text-left transition hover:border-cyber-neonBlue/40"
    >
      <Icon size={18} className={tone} />
      <div className="min-w-0">
        <div className="truncate text-sm">{item.message}</div>
        <div className="mt-1 text-xs text-cyber-muted">{item.timestamp}</div>
      </div>
    </button>
  );
}
