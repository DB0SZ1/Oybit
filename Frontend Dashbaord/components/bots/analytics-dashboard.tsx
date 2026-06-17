"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { useBotData } from "@/hooks/use-bot-data"
import { BarChart3, Loader2 } from "lucide-react"

export function AnalyticsDashboard({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<any>(botId, "api/analytics/overview")

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <CardTitle>Analytics Overview</CardTitle>
        </div>
        <CardDescription>Aggregated engagement and performance metrics</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center p-6"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
        ) : error ? (
          <div className="text-destructive text-sm">Failed to load analytics: {error.message}</div>
        ) : data?.overview ? (
          <div className="grid grid-cols-2 gap-4">
             <div className="p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Total Posts</div>
                <div className="text-2xl font-bold">{data.overview.total_posts || 0}</div>
             </div>
             <div className="p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Avg Engagement</div>
                <div className="text-2xl font-bold">{data.overview.avg_engagement || 0}</div>
             </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground py-4 text-center">No analytics data available.</div>
        )}
      </CardContent>
    </Card>
  )
}
