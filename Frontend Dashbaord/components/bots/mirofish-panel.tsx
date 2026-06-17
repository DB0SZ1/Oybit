"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { Activity } from "lucide-react"

export function MirofishPanel({ botId }: { botId: BotId }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <CardTitle>MiroFish Swarm</CardTitle>
        </div>
        <CardDescription>Multi-agent simulation gates and confidence scores</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Simulation run history pending data structure finalization.
        </div>
      </CardContent>
    </Card>
  )
}
