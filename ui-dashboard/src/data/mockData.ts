export type Severity = "Low" | "Medium" | "High" | "Critical";
export type AlertStatus = "Resolved" | "Pending";

export interface HealthMetric {
  key: string;
  title: string;
  value: number;
}

export interface ActivityPoint {
  hour: string;
  cpu: number;
  network: number;
  suspicious: number;
}

export interface ThreatPoint {
  hour: string;
  threats: number;
}

export interface AlertItem {
  id: string;
  time: string;
  threatType: string;
  severity: Severity;
  status: AlertStatus;
  affectedSystem: string;
  description: string;
  suggestedAction: string;
}

export interface NotificationItemData {
  id: string;
  level: "info" | "warning" | "critical";
  message: string;
  timestamp: string;
  alertId?: string;
}

const now = new Date();

function backMinutes(minutes: number): string {
  return new Date(now.getTime() - minutes * 60_000).toLocaleTimeString();
}

export const initialHealth: HealthMetric[] = [
  { key: "cpu", title: "CPU Usage", value: 48 },
  { key: "memory", title: "Memory Usage", value: 63 },
  { key: "disk", title: "Disk Activity", value: 28 },
  { key: "network", title: "Network Traffic", value: 55 },
];

export const initialActivity: ActivityPoint[] = Array.from({ length: 24 }).map((_, i) => ({
  hour: `${i.toString().padStart(2, "0")}:00`,
  cpu: 20 + Math.floor(Math.random() * 65),
  network: 10 + Math.floor(Math.random() * 80),
  suspicious: Math.random() > 0.84 ? 1 : 0,
}));

export const initialThreats: ThreatPoint[] = Array.from({ length: 24 }).map((_, i) => ({
  hour: `${i.toString().padStart(2, "0")}:00`,
  threats: Math.random() > 0.82 ? Math.floor(Math.random() * 8 + 4) : Math.floor(Math.random() * 3),
}));

export const initialAlerts: AlertItem[] = [
  {
    id: "ALT-1042",
    time: backMinutes(2),
    threatType: "Mass File Encryption Pattern",
    severity: "Critical",
    status: "Pending",
    affectedSystem: "FINANCE-WS-22",
    description: "Rapid write burst and extension mutation detected across protected directories.",
    suggestedAction: "Isolate system and terminate suspicious process tree.",
  },
  {
    id: "ALT-1038",
    time: backMinutes(8),
    threatType: "Decoy Wiretrap Tamper",
    severity: "High",
    status: "Pending",
    affectedSystem: "HR-LAP-07",
    description: "Decoy canary hash mismatch indicates unauthorized modification attempt.",
    suggestedAction: "Collect forensic snapshot and quarantine endpoint.",
  },
  {
    id: "ALT-1029",
    time: backMinutes(20),
    threatType: "Shadow Copy Delete Attempt",
    severity: "Medium",
    status: "Resolved",
    affectedSystem: "OPS-VM-03",
    description: "Command-line telemetry matched backup deletion behavior.",
    suggestedAction: "Keep elevated monitoring for 24 hours.",
  },
  {
    id: "ALT-1017",
    time: backMinutes(33),
    threatType: "Privilege Escalation Sequence",
    severity: "Low",
    status: "Resolved",
    affectedSystem: "ENG-DESKTOP-11",
    description: "Transient token elevation observed with no follow-up encryption indicators.",
    suggestedAction: "No immediate action required.",
  },
];

export const initialNotifications: NotificationItemData[] = [
  {
    id: "NTF-9001",
    level: "critical",
    message: "Suspicious encryption activity detected on FINANCE-WS-22",
    timestamp: backMinutes(1),
    alertId: "ALT-1042",
  },
  {
    id: "NTF-8997",
    level: "warning",
    message: "Decoy wiretrap integrity changed on HR-LAP-07",
    timestamp: backMinutes(6),
    alertId: "ALT-1038",
  },
  {
    id: "NTF-8991",
    level: "info",
    message: "Threat model threshold synchronized across all agents",
    timestamp: backMinutes(18),
  },
];
