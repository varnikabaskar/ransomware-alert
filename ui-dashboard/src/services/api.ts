import { AlertItem } from "../data/mockData";

export interface AgentNode {
  agent_id: string;
  host: string;
  ip_address: string;
  sysmon_enabled: boolean;
  last_seen: string;
  event_count: number;
  trap_event_count: number;
}

export interface Notification {
  id: string;
  level: "critical" | "warning" | "info";
  message: string;
  timestamp: string;
  affectedSystem?: string;
}

function getDashboardToken(): string {
  const envToken = (import.meta.env.VITE_RGUARD_API_TOKEN as string | undefined) ?? "";
  if (envToken.trim()) {
    return envToken.trim();
  }
  try {
    const local = window.localStorage.getItem("rguard_token") ?? "";
    return local.trim();
  } catch {
    return "";
  }
}

export async function fetchAgents(): Promise<AgentNode[]> {
  const token = getDashboardToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["X-R-Guard-Token"] = token;
  }

  const response = await fetch("/agent/agents", { headers });
  if (!response.ok) {
    throw new Error(`agents request failed: ${response.status}`);
  }

  return (await response.json()) as AgentNode[];
}

export async function generateRegistrationCode(): Promise<string> {
  const token = getDashboardToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["X-R-Guard-Token"] = token;
  }

  const response = await fetch(`/agent/register/generate`, { method: "POST", headers });
  if (!response.ok) {
    throw new Error(`generate code failed: ${response.status}`);
  }
  const body = await response.json();
  return body.code as string;
}

export async function deleteAgent(agentId: string): Promise<void> {
  const token = getDashboardToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["X-R-Guard-Token"] = token;
  }

  const response = await fetch(`/agent/agents/${encodeURIComponent(agentId)}`, { method: "DELETE", headers });
  if (!response.ok) {
    throw new Error(`delete agent failed: ${response.status}`);
  }
}

export async function fetchAlerts(host?: string): Promise<AlertItem[]> {
  const token = getDashboardToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["X-R-Guard-Token"] = token;
  }

  const url = host ? `/alerts?host=${encodeURIComponent(host)}` : "/alerts";
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`alerts request failed: ${response.status}`);
  }

  const raw = (await response.json()) as Array<{
    id: string;
    created_at: string;
    level: string;
    message: string;
    result: { host: string; reasons: string[]; severity?: string };
    contained?: boolean;
    acknowledged?: boolean;
  }>;

  return raw.map((item) => ({
    id: item.id,
    time: new Date(item.created_at).toLocaleTimeString(),
    threatType: item.message,
    severity: ((item.result?.severity ?? item.level) || "Low").replace(/^./, (s) => s.toUpperCase()) as AlertItem["severity"],
    sourceLevel: (item.level || "").toLowerCase(),
    status: item.contained || item.acknowledged ? "Resolved" : "Pending",
    affectedSystem: item.result?.host ?? "unknown",
    description: (item.result?.reasons || []).join("; ") || "No detail available",
    suggestedAction: item.contained ? "Containment completed. Verify host integrity." : "Review telemetry and isolate host if required.",
  }));
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  const token = getDashboardToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["X-R-Guard-Token"] = token;
  }

  const response = await fetch(`/alerts/${encodeURIComponent(alertId)}/acknowledge`, {
    method: "POST",
    headers,
  });

  if (!response.ok) {
    throw new Error(`acknowledge request failed: ${response.status}`);
  }
}

export async function fetchNotifications(host?: string): Promise<Notification[]> {
  const token = getDashboardToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["X-R-Guard-Token"] = token;
  }

  const query = host ? `/alerts?unread_critical_only=true&host=${encodeURIComponent(host)}` : `/alerts?unread_critical_only=true`;
  const response = await fetch(query, { headers });
  if (!response.ok) {
    throw new Error(`notifications request failed: ${response.status}`);
  }

  const raw = (await response.json()) as Array<{
    id: string;
    level: string;
    message: string;
    timestamp: string;
    affectedSystem?: string;
  }>;

  return raw.map((item) => ({
    id: item.id,
    level: (item.level || "info") as "critical" | "warning" | "info",
    message: item.message,
    timestamp: item.timestamp,
    affectedSystem: item.affectedSystem,
  }));
}
