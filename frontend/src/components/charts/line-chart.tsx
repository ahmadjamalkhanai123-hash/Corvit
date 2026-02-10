"use client"

import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface LineChartProps {
  title: string
  data: Record<string, unknown>[]
  xKey: string
  yKey: string
  color?: string
}

export function LineChart({ title, data, xKey, yKey, color = "hsl(var(--primary))" }: LineChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey={xKey} className="text-xs" tick={{ fontSize: 12 }} />
              <YAxis className="text-xs" tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={false} />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
