"use client"

import { useBotData } from "@/hooks/use-bot-data"
import { type BotId } from "@/lib/bot-config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, CheckCircle2, Clock, Zap, Search, Lightbulb, PenLine, FlaskConical, Send, AlertCircle } from "lucide-react"

const PIPELINE_STEPS = [
  { key: "init",       label: "Pipeline Init",        icon: Zap,          color: "text-violet-500",  bg: "bg-violet-50 border-violet-200" },
  { key: "trending",   label: "Trend Aggregation",    icon: Search,       color: "text-blue-500",    bg: "bg-blue-50 border-blue-200" },
  { key: "opportunity",label: "Opportunity Detection",icon: Lightbulb,    color: "text-amber-500",   bg: "bg-amber-50 border-amber-200" },
  { key: "generation", label: "Content Generation",   icon: PenLine,      color: "text-indigo-500",  bg: "bg-indigo-50 border-indigo-200" },
  { key: "simulation", label: "MiroFish Gate",        icon: FlaskConical, color: "text-emerald-500", bg: "bg-emerald-50 border-emerald-200" },
  { key: "publish",    label: "Publish / Schedule",   icon: Send,         color: "text-primary",     bg: "bg-primary/5 border-primary/20" },
]

function extractStep(log: any): string {
  return log?.details?.step || ""
}

function getLatestRunLogs(logs: any[]): any[] {
  if (!logs || logs.length === 0) return []
  // Find the most recent "init" to mark the start of the last pipeline run
  const reversed = [...logs].reverse()
  const lastInitIdx = reversed.findIndex(l => extractStep(l) === "init")
  if (lastInitIdx === -1) return reversed.slice(0, 10)
  return reversed.slice(lastInitIdx)
}

export function PipelineProcessBoard({ botId }: { botId: BotId }) {
  const { data, loading } = useBotData<{ logs: any[] }>(botId, "api/system/logs", { refreshIntervalMs: 2000 })

  const latestRunLogs = getLatestRunLogs(data?.logs || [])

  // Map each step key → its log entry (if present in latest run)
  const stepMap: Record<string, any> = {}
  for (const log of latestRunLogs) {
    const step = extractStep(log)
    if (step && !stepMap[step]) stepMap[step] = log
  }

  // Determine which step is currently "running" (last done step + 1)
  const doneKeys = PIPELINE_STEPS.map(s => s.key).filter(k => stepMap[k])
  const lastDoneIdx = doneKeys.length > 0
    ? PIPELINE_STEPS.findIndex(s => s.key === doneKeys[doneKeys.length - 1])
    : -1
  const runningIdx = lastDoneIdx < PIPELINE_STEPS.length - 1 && latestRunLogs.length > 0
    ? lastDoneIdx + 1
    : -1

  const hasActiveRun = latestRunLogs.length > 0 && !stepMap["publish"]

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            <CardTitle>Content Pipeline</CardTitle>
          </div>
          {hasActiveRun ? (
            <Badge className="bg-primary/10 text-primary border-primary/30 gap-1">
              <Loader2 className="h-3 w-3 animate-spin" /> Running
            </Badge>
          ) : latestRunLogs.length > 0 ? (
            <Badge className="bg-emerald-50 text-emerald-600 border-emerald-200 gap-1">
              <CheckCircle2 className="h-3 w-3" /> Complete
            </Badge>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {loading && !data ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : latestRunLogs.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-8">
            No pipeline runs yet. Click <strong>Generate</strong> above to start.
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {PIPELINE_STEPS.map((step, idx) => {
              const log = stepMap[step.key]
              const isRunning = idx === runningIdx && hasActiveRun
              const isDone = !!log
              const isPending = !isDone && !isRunning

              const Icon = step.icon

              return (
                <div
                  key={step.key}
                  className={`
                    relative rounded-xl border p-4 transition-all duration-500
                    ${isDone ? step.bg : isRunning ? "bg-primary/5 border-primary/30 shadow-md shadow-primary/10" : "bg-muted/40 border-border"}
                  `}
                >
                  {/* Status badge top-right */}
                  <div className="absolute top-2 right-2">
                    {isDone ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    ) : isRunning ? (
                      <Loader2 className="h-4 w-4 text-primary animate-spin" />
                    ) : (
                      <Clock className="h-4 w-4 text-muted-foreground/40" />
                    )}
                  </div>

                  {/* Icon */}
                  <div className={`mb-2 ${isDone ? step.color : isRunning ? "text-primary" : "text-muted-foreground/40"}`}>
                    <Icon className="h-5 w-5" />
                  </div>

                  {/* Label */}
                  <p className={`text-xs font-semibold mb-1 ${isDone || isRunning ? "text-foreground" : "text-muted-foreground/50"}`}>
                    {step.label}
                  </p>

                  {/* Detail */}
                  {isDone && log?.details?.reason && (
                    <p className="text-[10px] text-muted-foreground leading-tight mt-1 line-clamp-2">
                      {log.details.reason}
                    </p>
                  )}
                  {isDone && log?.details?.confidence && (
                    <p className="text-[11px] font-bold mt-1 text-emerald-600">
                      {(log.details.confidence * 100).toFixed(1)}% confidence
                    </p>
                  )}
                  {isRunning && (
                    <p className="text-[10px] text-primary/70 mt-1 animate-pulse">Processing...</p>
                  )}
                  {isDone && log?.created_at && (
                    <p className="text-[9px] text-muted-foreground mt-1">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
