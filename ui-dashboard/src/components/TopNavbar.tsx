import { Bell, ShieldCheck } from "lucide-react";

interface TopNavbarProps {
  notificationCount: number;
  now: string;
}

export function TopNavbar({ notificationCount, now }: TopNavbarProps) {
  return (
    <header className="flex h-20 items-center justify-between border-b border-cyber-line bg-cyber-panel/40 px-5 backdrop-blur">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-cyber-muted">Enterprise ransomware detection and response view</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="rounded-lg border border-cyber-line bg-cyber-panel2 px-3 py-2 text-sm text-cyber-muted">{now}</div>

        <button type="button" className="relative rounded-lg border border-cyber-line bg-cyber-panel2 p-2 text-cyber-neonBlue">
          <Bell size={18} />
          {notificationCount > 0 ? (
            <span className="absolute -right-1 -top-1 rounded-full bg-cyber-neonRed px-1.5 text-[10px] font-semibold text-white">
              {notificationCount}
            </span>
          ) : null}
        </button>

        <div className="flex items-center gap-2 rounded-lg border border-cyber-line bg-cyber-panel2 px-2 py-1">
          <div className="grid h-8 w-8 place-items-center rounded-full bg-cyber-neonBlue/20 text-cyber-neonBlue">
            <ShieldCheck size={16} />
          </div>
          <div className="text-sm">
            <div className="font-medium">SecOps Admin</div>
            <div className="text-cyber-muted">SOC Team</div>
          </div>
        </div>
      </div>
    </header>
  );
}
