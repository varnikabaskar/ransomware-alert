import { AlertTriangle, Activity, Bell, LayoutDashboard, ScrollText, Settings } from "lucide-react";

const items: Array<{ key: string; icon: typeof LayoutDashboard; target: SidebarSection } | { key: string; icon: typeof AlertTriangle; target: SidebarSection } | { key: string; icon: typeof ScrollText; target: SidebarSection } | { key: string; icon: typeof Activity; target: SidebarSection } | { key: string; icon: typeof Settings; target: SidebarSection }> = [
  { key: "Dashboard", icon: LayoutDashboard, target: "dashboard" },
  { key: "Alerts", icon: AlertTriangle, target: "alerts" },
  { key: "Logs", icon: ScrollText, target: "logs" },
  { key: "System Health", icon: Activity, target: "dashboard" },
  { key: "Settings", icon: Settings, target: "settings" },
];

export type SidebarSection = "dashboard" | "alerts" | "logs" | "settings";

interface SidebarProps {
  activeSection: SidebarSection;
  onNavigate: (section: SidebarSection) => void;
}

export function Sidebar({ activeSection, onNavigate }: SidebarProps) {
  return (
    <aside className="w-full shrink-0 border-b border-cyber-line bg-cyber-panel/70 p-5 backdrop-blur lg:w-72 lg:border-b-0 lg:border-r">
      <div className="mb-7 rounded-xl border border-cyber-line bg-cyber-panel2 p-4">
        <div className="text-xs uppercase tracking-[0.16em] text-cyber-muted">Ransomware Alert System</div>
        <div className="mt-2 flex items-center gap-2 text-xl font-semibold text-cyber-neonGreen">
          <Bell size={20} />
          Ransomware Shield
        </div>
      </div>

      <nav className="space-y-2">
        {items.map((item, idx) => {
          const Icon = item.icon;
          const active = activeSection === item.target || (idx === 0 && activeSection === "dashboard");
          return (
            <button
              type="button"
              key={item.key}
              onClick={() => onNavigate(item.target)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition ${
                active
                  ? "glow-active bg-cyber-panel2 text-cyber-neonGreen"
                  : "text-cyber-muted hover:bg-cyber-panel2 hover:text-cyber-text"
              }`}
            >
              <Icon size={18} />
              <span className="font-medium">{item.key}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
