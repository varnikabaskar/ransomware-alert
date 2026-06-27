import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ThreatPoint } from "../data/mockData";

interface ThreatChartProps {
  data: ThreatPoint[];
}

export function ThreatChart({ data }: ThreatChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="threatFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#FF4D6D" stopOpacity={0.55} />
            <stop offset="95%" stopColor="#FF4D6D" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" />
        <XAxis dataKey="hour" tick={{ fill: "#9FB2D9", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
        <YAxis tick={{ fill: "#9FB2D9", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "#111622", border: "1px solid #1F2937", borderRadius: 8 }}
          labelStyle={{ color: "#E5ECFF" }}
        />
        <Area type="monotone" dataKey="threats" stroke="#FF4D6D" fill="url(#threatFill)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
