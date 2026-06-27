import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ActivityPoint } from "../data/mockData";

interface ActivityChartProps {
  data: ActivityPoint[];
}

export function ActivityChart({ data }: ActivityChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <XAxis dataKey="hour" tick={{ fill: "#9FB2D9", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
        <YAxis tick={{ fill: "#9FB2D9", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "#111622", border: "1px solid #1F2937", borderRadius: 8 }}
          labelStyle={{ color: "#E5ECFF" }}
        />
        <Line type="monotone" dataKey="cpu" stroke="#39A0FF" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="network" stroke="#36F9A2" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="suspicious" stroke="#FF4D6D" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
