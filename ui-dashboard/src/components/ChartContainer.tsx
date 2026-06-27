import { ReactNode } from "react";

interface ChartContainerProps {
  title: string;
  children: ReactNode;
}

export function ChartContainer({ title, children }: ChartContainerProps) {
  return (
    <section className="rounded-xl border border-cyber-line bg-cyber-panel p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-cyber-muted">{title}</h3>
      <div className="h-72">{children}</div>
    </section>
  );
}
