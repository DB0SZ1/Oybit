"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { ShieldCheck } from "lucide-react"

export function GuardianPanel({ botId }: { botId: BotId }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-primary" />
          <CardTitle>Guardian Safety Checks</CardTitle>
        </div>
        <CardDescription>Brand safety rules, blocklists, and audit logs</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          No recent guardian flags or interventions.
        </div>
      </CardContent>
    </Card>
  )
}
