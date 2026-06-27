import { LucideIcon } from "lucide-react";

interface CardProps {
  title: string;
  value: number;
  icon: LucideIcon;
}

function getTone(value: number) {
  if (value >= 80) {
    return {
      bar: "bg-cyber-neonRed",
      text: "text-cyber-neonRed",
      label: "Critical",
    };
  }
  if (value >= 60) {
    return {
      bar: "bg-cyber-neonAmber",
      text: "text-cyber-neonAmber",
      label: "Warning",
    };
  }
  return {
    bar: "bg-cyber-neonGreen",
    text: "text-cyber-neonGreen",
    label: "Safe",
  };
}

export function Card({ title, value, icon: Icon }: CardProps) {
  const tone = getTone(value);

  return (
    <article className="rounded-xl border border-cyber-line bg-cyber-panel p-4 transition hover:shadow-neonBlue">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm text-cyber-muted">{title}</div>
        <Icon size={18} className={tone.text} />
      </div>
      <div className={`text-2xl font-semibold ${tone.text}`}>{value}%</div>
      <div className="mt-2 h-2 w-full rounded-full bg-cyber-panel2">
        <div className={`h-2 rounded-full ${tone.bar}`} style={{ width: `${Math.min(100, value)}%` }} />
      </div>
      <div className="mt-2 text-xs text-cyber-muted">Status: {tone.label}</div>
    </article>
  );
}
