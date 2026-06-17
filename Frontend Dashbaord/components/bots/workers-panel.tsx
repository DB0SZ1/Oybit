"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { useBotData } from "@/hooks/use-bot-data"
import { ServerCog, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export function WorkersPanel({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<{ heartbeats: any[] }>(botId, "api/workers/heartbeats")

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ServerCog className="h-5 w-5 text-primary" />
          <CardTitle>Worker Management</CardTitle>
        </div>
        <CardDescription>Background task workers and scheduler statuses</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
           <div className="flex items-center justify-center p-6"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
        ) : error ? (
           <div className="text-destructive text-sm">Failed to load workers: {error.message}</div>
        ) : data?.heartbeats && data.heartbeats.length > 0 ? (
           <div className="space-y-4">
             {data.heartbeats.map((worker: any, i: number) => (
               <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="font-medium text-sm">{worker.worker_name}</div>
                  <Badge variant={worker.status === "running" ? "default" : "destructive"}>
                     {worker.status || "unknown"}
                  </Badge>
               </div>
             ))}
           </div>
        ) : (
           <div className="text-sm text-muted-foreground py-4 text-center">No workers currently registered.</div>
        )}
      </CardContent>
    </Card>
  )
}
