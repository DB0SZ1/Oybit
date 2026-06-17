"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { type BotId } from "@/lib/bot-config"
import { useBotData, useBotHealth } from "@/hooks/use-bot-data"
import { CheckCircle2, AlertCircle, TrendingUp, FlaskConical, FileText, Send, Clock, ShieldCheck } from "lucide-react"

interface MetricTileProps {
  label: string
  value: string | number
  sub?: string
  icon: React.ElementType
  iconColor: string
  accent?: boolean
}

function MetricTile({ label, value, sub, icon: Icon, iconColor, accent }: MetricTileProps) {
  return (
    <div className={`rounded-xl border p-3 space-y-1 ${accent ? "bg-primary/5 border-primary/20" : "bg-card border-border"}`}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">{label}</span>
        <Icon className={`h-3.5 w-3.5 ${iconColor}`} />
      </div>
      <p className={`text-xl font-bold leading-none ${accent ? "text-primary" : "text-foreground"}`}>{value}</p>
      {sub && <p className="text-[10px] text-muted-foreground">{sub}</p>}
    </div>
  )
}

export function BotOverviewCard({ botId, botName }: { botId: BotId; botName: string }) {
  const isHealthy = useBotHealth(botId)
  const { data } = useBotData<any>(botId, "api/analytics/overview", { refreshIntervalMs: 4000 })

  const ov = data?.overview || {}

  const published    = ov.total_posts     ?? "—"
  const drafts       = ov.total_drafts    ?? "—"
  const scheduled    = ov.total_scheduled ?? "—"
  const blocked      = ov.total_blocked   ?? "—"
  const gatePassRate = ov.gate_pass_rate  != null ? `${ov.gate_pass_rate}%` : "—"
  const avgConf      = ov.avg_confidence  != null ? `${Math.round(ov.avg_confidence * 100)}%` : "—"
  const avgScore     = ov.avg_score       != null ? `${Math.round(ov.avg_score * 100)}%` : "—"
  const trends       = ov.trend_signals   ?? "—"

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-lg">{botName}</CardTitle>
        {isHealthy === null ? (
          <Badge variant="outline" className="text-muted-foreground text-[10px]">Checking...</Badge>
        ) : isHealthy ? (
          <Badge className="bg-emerald-50 text-emerald-600 border-emerald-200 gap-1 text-[10px]">
            <CheckCircle2 className="w-3 h-3" /> Online
          </Badge>
        ) : (
          <Badge variant="destructive" className="gap-1 text-[10px]">
            <AlertCircle className="w-3 h-3" /> Offline
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Primary metrics */}
        <div className="grid grid-cols-2 gap-2">
          <MetricTile label="Published"  value={published}    icon={Send}        iconColor="text-primary"      accent />
          <MetricTile label="Drafts"     value={drafts}       icon={FileText}    iconColor="text-muted-foreground" />
          <MetricTile label="Scheduled"  value={scheduled}    icon={Clock}       iconColor="text-blue-500" />
          <MetricTile label="Blocked"    value={blocked}      icon={AlertCircle} iconColor="text-red-400" />
        </div>

        {/* Divider */}
        <div className="border-t pt-2 mt-1">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground font-medium mb-2">Quality Signals</p>
          <div className="grid grid-cols-2 gap-2">
            <MetricTile label="Gate Pass Rate" value={gatePassRate} icon={ShieldCheck}   iconColor="text-emerald-500" />
            <MetricTile label="Avg MiroFish"   value={avgConf}      icon={FlaskConical}  iconColor="text-violet-500" />
            <MetricTile label="Avg Score"      value={avgScore}     icon={TrendingUp}    iconColor="text-amber-500" />
            <MetricTile label="Trend Signals"  value={trends}       icon={TrendingUp}    iconColor="text-blue-500" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
