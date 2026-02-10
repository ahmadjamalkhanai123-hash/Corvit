"use client"

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface BarChartProps {
  title: string
  data: Record<string, unknown>[]
  xKey: string
  yKey: string
  color?: string
}

export function BarChart({ title, data, xKey, yKey, color = "hsl(var(--primary))" }: BarChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsBarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey={xKey} className="text-xs" tick={{ fontSize: 12 }} />
              <YAxis className="text-xs" tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
            </RechartsBarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
