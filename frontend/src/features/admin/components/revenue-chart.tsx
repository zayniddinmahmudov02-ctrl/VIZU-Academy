"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ChartPoint } from "../types/dashboard";

interface Props {
  data: ChartPoint[];
}

export default function RevenueChart({ data }: Props) {
  return (
    <div className="admin-glass rounded-2xl p-5 shadow-[var(--admin-shadow-card)] sm:p-6">
      <p className="text-sm font-bold text-white">Revenue</p>
      <p className="text-xs text-[var(--admin-text-muted)]">Approved payments by month</p>

      <div className="mt-4 h-64">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--admin-text-muted)]">
            No revenue data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
              <defs>
                <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#5b5bf8" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="#5b5bf8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis
                dataKey="label"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} width={48} />
              <Tooltip
                contentStyle={{
                  background: "#111827",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: 12,
                  color: "#f8fafc",
                  fontSize: 12,
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#5b5bf8"
                strokeWidth={2}
                fill="url(#revenueFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
