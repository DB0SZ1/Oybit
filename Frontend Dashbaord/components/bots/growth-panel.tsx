"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { TrendingUp } from "lucide-react"

export function GrowthPanel({ botId }: { botId: BotId }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <CardTitle>Growth & Community</CardTitle>
        </div>
        <CardDescription>Follower tracking and engagement campaigns</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Community metrics and follower charts will render here.
        </div>
      </CardContent>
    </Card>
  )
}
