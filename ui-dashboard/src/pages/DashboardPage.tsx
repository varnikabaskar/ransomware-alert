import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Cpu, HardDrive, Network, MemoryStick } from "lucide-react";
import { Sidebar, type SidebarSection } from "../components/Sidebar";
import { TopNavbar } from "../components/TopNavbar";
import { Card } from "../components/Card";
import { ChartContainer } from "../components/ChartContainer";
import { ActivityChart } from "../components/ActivityChart";
import { ThreatChart } from "../components/ThreatChart";
import { AlertTable } from "../components/AlertTable";
import { NotificationItem } from "../components/NotificationItem";
import { AlertDetailsPanel } from "../components/AlertDetailsPanel";
import {
  AlertItem,
  initialActivity,
  initialHealth,
  initialThreats,
} from "../data/mockData";
import { acknowledgeAlert, fetchAgents, fetchAlerts, generateRegistrationCode, deleteAgent, fetchNotifications, type AgentNode, type Notification } from "../services/api";

const metricIcons = {
  cpu: Cpu,
  memory: MemoryStick,
  disk: HardDrive,
  network: Network,
} as const;

export function DashboardPage() {
  const [activeSection, setActiveSection] = useState<SidebarSection>("dashboard");
  const [health, setHealth] = useState(initialHealth);
  const [activityData, setActivityData] = useState(initialActivity);
  const [threatData, setThreatData] = useState(initialThreats);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [agents, setAgents] = useState<AgentNode[]>([]);
  const [selectedHost, setSelectedHost] = useState<string>("all");
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [regCode, setRegCode] = useState<string | null>(null);
  const [now, setNow] = useState(new Date().toLocaleString());

  const navigateToSection = (section: SidebarSection) => {
    setActiveSection(section);
    const element = document.getElementById(section);
    element?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const refreshAgents = useCallback(async () => {
    try {
      const remote = await fetchAgents();
      setAgents(remote);
      setSelectedHost((current) => {
        if (current !== "all" && remote.some((agent) => agent.host === current)) {
          return current;
        }
        return remote[0]?.host ?? "all";
      });
    } catch {
      // Keep the existing selector if the server agent registry is unavailable.
    }
  }, []);

  const refreshAlerts = useCallback(async (host?: string) => {
    try {
      const remote = await fetchAlerts(host);
      // Only show threat activity (warning/critical) in Recent Logs. Consider result severity OR original alert level.
      const threats = remote.filter((a) => {
        const sev = (a.severity || "").toLowerCase();
        const src = (a as any).sourceLevel || "";
        return sev !== "normal" || src === "critical" || src === "warning";
      });
      if (threats.length > 0) {
        setAlerts(threats.slice(0, 30));
      } else {
        setAlerts([]);
      }
    } catch {
      // Keep simulation mode if backend alerts are unavailable.
    }
  }, []);

  const refreshNotifications = useCallback(async () => {
    try {
      const hostParam = selectedHost === "all" ? undefined : selectedHost;
      const remote = await fetchNotifications(hostParam);
      setNotifications(remote.slice(0, 10));
    } catch {
      // Keep existing notifications if backend is unavailable
    }
  }, []);

  useEffect(() => {
    const clock = setInterval(() => {
      setNow(new Date().toLocaleString());
    }, 1000);

    const simulation = setInterval(() => {
      setHealth((prev) =>
        prev.map((item) => {
          const delta = Math.floor(Math.random() * 13) - 6;
          return { ...item, value: Math.max(8, Math.min(99, item.value + delta)) };
        }),
      );

      setActivityData((prev) => {
        const nextCpu = Math.max(10, Math.min(98, prev[prev.length - 1].cpu + (Math.floor(Math.random() * 15) - 7)));
        const nextNetwork = Math.max(5, Math.min(99, prev[prev.length - 1].network + (Math.floor(Math.random() * 17) - 8)));
        const point = {
          hour: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          cpu: nextCpu,
          network: nextNetwork,
          suspicious: Math.random() > 0.9 ? 1 : 0,
        };
        return [...prev.slice(1), point];
      });

      setThreatData((prev) => {
        const spike = Math.random() > 0.85;
        const point = {
          hour: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          threats: spike ? Math.floor(Math.random() * 10 + 5) : Math.floor(Math.random() * 4),
        };
        return [...prev.slice(1), point];
      });

    }, 3000);

    return () => {
      clearInterval(clock);
      clearInterval(simulation);
    };
  }, []);

  useEffect(() => {
    let active = true;

    const syncAlerts = async () => {
      if (active) {
        await refreshAlerts(selectedHost === "all" ? undefined : selectedHost);
      }
    };

    syncAlerts();
    const intervalId = setInterval(syncAlerts, 10000);
    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, [refreshAlerts, selectedHost]);

  useEffect(() => {
    let active = true;

    const syncNotifications = async () => {
      if (active) {
        await refreshNotifications();
      }
    };

    syncNotifications();
    const intervalId = setInterval(syncNotifications, 10000);
    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, [refreshNotifications]);

  useEffect(() => {
    void refreshAgents();
  }, [refreshAgents]);

  const notificationItems = useMemo(() =>
    notifications.map((notif) => ({
      id: notif.id,
      level: notif.level as "critical",
      message: notif.message,
      timestamp: notif.timestamp,
      alertId: notif.id,
    })),
    [notifications],
  );

  const notificationCount = useMemo(() => notificationItems.length, [notificationItems]);

  const openFromNotification = (notificationId: string) => {
    const target = notificationItems.find((n) => n.id === notificationId);
    if (!target?.alertId) return;
    const alert = alerts.find((a) => a.id === target.alertId);
    if (alert) {
      setSelectedAlert(alert);
    }
  };

  const openLogsTab = () => {
    const logsUrl = selectedHost === "all"
      ? `${window.location.pathname}?view=logs`
      : `${window.location.pathname}?view=logs&host=${encodeURIComponent(selectedHost)}`;
    window.open(logsUrl, "_blank", "noopener,noreferrer");
  };

  const markAlertAsRead = (id: string) => {
    void acknowledgeAlert(id).catch(() => {
      // Keep the local state update even if the backend sync is momentarily unavailable.
    });
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "Resolved" } : a)),
    );
    setSelectedAlert((prev) =>
      prev && prev.id === id ? { ...prev, status: "Resolved" } : prev,
    );
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(57,160,255,0.15)_0%,_rgba(9,11,16,1)_38%)]">
      <div className="flex min-h-screen">
        <Sidebar activeSection={activeSection} onNavigate={navigateToSection} />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopNavbar notificationCount={notificationCount} now={now} />

          <main className="flex-1 space-y-4 p-4 lg:p-5">
            <section id="dashboard" className="grid grid-cols-1 gap-4 scroll-mt-24 sm:grid-cols-2 2xl:grid-cols-4">
              {health.map((metric) => {
                const Icon = metricIcons[metric.key as keyof typeof metricIcons] ?? Activity;
                return <Card key={metric.key} title={metric.title} value={metric.value} icon={Icon} />;
              })}
            </section>

            <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
              <div className="rounded-xl border border-cyber-line bg-cyber-panel p-4 xl:col-span-2">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-cyber-muted">Fleet Scope</h3>
                <p className="mt-2 text-sm text-cyber-muted">
                  Choose the agent node whose logs, alerts, and unread notifications you want to review.
                </p>
              </div>
              <div className="rounded-xl border border-cyber-line bg-cyber-panel p-4">
                <label className="text-sm font-semibold uppercase tracking-wider text-cyber-muted" htmlFor="agent-scope">
                  Agent Node
                </label>
                <select
                  id="agent-scope"
                  value={selectedHost}
                  onChange={(event) => setSelectedHost(event.target.value)}
                  className="mt-2 w-full rounded-lg border border-cyber-line bg-cyber-panel2 px-3 py-2 text-sm text-cyber-text outline-none transition focus:border-cyber-neonBlue"
                >
                  <option value="all">All agents</option>
                  {agents.map((agent) => (
                    <option key={agent.agent_id} value={agent.host}>
                      {agent.host} ({agent.agent_id})
                    </option>
                  ))}
                </select>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const code = await generateRegistrationCode();
                        setRegCode(code);
                      } catch {
                        setRegCode("ERROR");
                      }
                    }}
                    className="rounded-lg bg-cyber-neonBlue px-3 py-1 text-sm font-semibold text-black transition hover:brightness-110"
                  >
                    Generate Code
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      const currentAgent = agents.find(a => a.host === selectedHost);
                      if (!currentAgent) return;
                      try {
                        await deleteAgent(currentAgent.agent_id);
                        await refreshAgents();
                        await refreshAlerts();
                      } catch {
                        // ignore
                      }
                    }}
                    className="rounded-lg border border-cyber-line px-3 py-1 text-sm text-cyber-muted transition hover:text-cyber-text"
                  >
                    Remove Agent
                  </button>
                </div>
                {regCode ? <div className="mt-2 text-xs text-cyber-muted">Code: {regCode}</div> : null}
              </div>
            </section>

            <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <ChartContainer title="Fleet Activity (Last 24 Hours)">
                <ActivityChart data={activityData} />
              </ChartContainer>
              <ChartContainer title="Threat Detection Trends Across Agents">
                <ThreatChart data={threatData} />
              </ChartContainer>
            </section>

            <section id="alerts" className="grid grid-cols-1 gap-4 scroll-mt-24 xl:grid-cols-3">
              <div className="xl:col-span-2 rounded-xl border border-cyber-line bg-cyber-panel p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-cyber-muted">Recent Logs</h3>
                    <p className="mt-1 text-xs text-cyber-muted">
                      Recent alerts received from the selected agent node.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={openLogsTab}
                    className="rounded-lg bg-cyber-neonBlue px-3 py-1 text-sm font-semibold text-black transition hover:brightness-110"
                  >
                    View Logs
                  </button>
                </div>
                <AlertTable alerts={alerts.slice(0, 10)} onOpen={setSelectedAlert} />
              </div>

              <section className="rounded-xl border border-cyber-line bg-cyber-panel p-4">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-cyber-muted">Notification Logs</h3>
                <p className="mb-3 text-xs text-cyber-muted">
                  Active unread alerts for the selected agent node. This is the actionable queue.
                </p>
                <div className="max-h-[310px] space-y-2 overflow-y-auto pr-1">
                  {notificationItems.length > 0 ? notificationItems.map((item) => (
                    <NotificationItem key={item.id} item={item} onOpen={openFromNotification} />
                  )) : (
                    <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3 text-sm text-cyber-muted">
                      No unread notifications for this agent.
                    </div>
                  )}
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <p className="text-xs text-cyber-muted">Preview only. Open the selected agent&apos;s full logs in a new tab.</p>
                </div>
              </section>
            </section>

            <section id="settings" className="scroll-mt-24">
              <div className="rounded-xl border border-cyber-line bg-cyber-panel p-4">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-cyber-muted">Settings</h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3">
                    <div className="text-xs uppercase tracking-wider text-cyber-muted">Alert Threshold</div>
                    <div className="mt-1 text-lg font-semibold text-cyber-neonGreen">0.70</div>
                  </div>
                  <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3">
                    <div className="text-xs uppercase tracking-wider text-cyber-muted">Fusion Weights</div>
                    <div className="mt-1 text-sm font-medium text-cyber-text">65% behavioral / 35% decoy</div>
                  </div>
                  <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3">
                    <div className="text-xs uppercase tracking-wider text-cyber-muted">Containment</div>
                    <div className="mt-1 text-sm font-medium text-cyber-text">Enabled</div>
                  </div>
                  <div className="rounded-lg border border-cyber-line bg-cyber-panel2 p-3">
                    <div className="text-xs uppercase tracking-wider text-cyber-muted">Alert Store</div>
                    <div className="mt-1 text-sm font-medium text-cyber-text">JSON rolling window</div>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => void refreshAlerts(selectedHost === "all" ? undefined : selectedHost)}
                    className="rounded-lg bg-cyber-neonBlue px-4 py-2 text-sm font-semibold text-black transition hover:brightness-110"
                  >
                    Refresh Alerts
                  </button>
                  <button
                    type="button"
                    onClick={() => navigateToSection("dashboard")}
                    className="rounded-lg border border-cyber-line px-4 py-2 text-sm text-cyber-muted transition hover:text-cyber-text"
                  >
                    Back to Dashboard
                  </button>
                </div>
              </div>
            </section>
          </main>
        </div>
      </div>

      <AlertDetailsPanel alert={selectedAlert} onClose={() => setSelectedAlert(null)} onMarkAsRead={markAlertAsRead} />
    </div>
  );
}
