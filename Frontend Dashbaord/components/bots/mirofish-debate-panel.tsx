"use client"

import { useBotData } from "@/hooks/use-bot-data"
import { type BotId } from "@/lib/bot-config"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, FlaskConical, CheckCircle2, XCircle, ThumbsUp, ThumbsDown, Minus, TrendingUp } from "lucide-react"

const DEBATE_PERSONAS = [
  { id: "hawk",     label: "The Hawk",     role: "Risk Detector",    color: "text-red-500",     bg: "bg-red-50 border-red-200",     icon: ThumbsDown },
  { id: "dove",     label: "The Dove",     role: "Audience Advocate", color: "text-blue-500",    bg: "bg-blue-50 border-blue-200",   icon: ThumbsUp },
  { id: "neutral",  label: "The Analyst",  role: "Data Realist",     color: "text-amber-500",   bg: "bg-amber-50 border-amber-200", icon: Minus },
  { id: "growth",   label: "Growth Lead",  role: "Opportunity Scout", color: "text-emerald-500", bg: "bg-emerald-50 border-emerald-200", icon: TrendingUp },
]

function ConfidenceArc({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const radius = 40
  const circumference = Math.PI * radius // half circle
  const dash = (pct / 100) * circumference

  const color = pct >= 75 ? "#10b981" : pct >= 55 ? "#f59e0b" : "#ef4444"

  return (
    <div className="flex flex-col items-center">
      <svg width="100" height="58" viewBox="0 0 100 58">
        {/* Background arc */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
      </svg>
      <div className="-mt-4 text-center">
        <p className="text-2xl font-bold" style={{ color }}>{pct}%</p>
        <p className="text-[10px] text-muted-foreground">Confidence</p>
      </div>
    </div>
  )
}

export function MirofishDebatePanel({ botId }: { botId: BotId }) {
  const { data: runsData, loading } = useBotData<{ runs: any[] }>(botId, "api/mirofish/runs", { refreshIntervalMs: 3000 })
  const { data: simsData } = useBotData<{ simulations: any[] }>(botId, "api/mirofish/simulations", { refreshIntervalMs: 3000 })

  const latestRun = runsData?.runs?.[0] || null
  const confidence = latestRun?.confidence_score || 0
  const passed = confidence >= 0.6
  const simEntries = simsData?.simulations || []
  const latestSims = simEntries.slice(0, 4)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-primary" />
            <div>
              <CardTitle>MiroFish Swarm Debate</CardTitle>
              <CardDescription className="mt-0.5">Multi-agent audience simulation & pre-publish gate</CardDescription>
            </div>
          </div>
          {latestRun && (
            <Badge className={passed
              ? "bg-emerald-50 text-emerald-600 border-emerald-200 gap-1"
              : "bg-red-50 text-red-600 border-red-200 gap-1"
            }>
              {passed
                ? <><CheckCircle2 className="h-3 w-3" /> Gate Passed</>
                : <><XCircle className="h-3 w-3" /> Gate Failed</>
              }
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading && !runsData ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !latestRun ? (
          <div className="text-sm text-muted-foreground text-center py-8">
            No simulations run yet. Click <strong>MiroFish</strong> or <strong>Generate</strong> to trigger.
          </div>
        ) : (
          <div className="space-y-5">
            {/* Score + verdict row */}
            <div className="flex items-start gap-6 p-4 rounded-xl bg-muted/30 border">
              <ConfidenceArc score={confidence} />
              <div className="flex-1 space-y-2 pt-1">
                <p className="text-sm font-semibold">
                  {passed ? "Content cleared to publish" : "Content blocked — revisions needed"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Run type: <span className="font-medium capitalize">{latestRun.run_type || "ad_hoc"}</span>
                  {latestRun.created_at && (
                    <span className="ml-2 text-muted-foreground/60">
                      · {new Date(latestRun.created_at).toLocaleTimeString()}
                    </span>
                  )}
                </p>
                {latestRun.narrative_output?.verdict && (
                  <p className="text-xs italic text-muted-foreground border-l-2 border-primary/40 pl-2">
                    "{latestRun.narrative_output.verdict}"
                  </p>
                )}
              </div>
            </div>

            {/* Debate agents */}
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Agent Opinions</p>
              <div className="grid grid-cols-2 gap-2">
                {DEBATE_PERSONAS.map((persona, i) => {
                  const sim = latestSims[i]
                  const Icon = persona.icon
                  return (
                    <div key={persona.id} className={`rounded-xl border p-3 ${persona.bg}`}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Icon className={`h-3.5 w-3.5 ${persona.color}`} />
                        <span className={`text-xs font-bold ${persona.color}`}>{persona.label}</span>
                      </div>
                      <p className="text-[9px] text-muted-foreground mb-1">{persona.role}</p>
                      {sim ? (
                        <>
                          <p className="text-[10px] font-medium text-foreground line-clamp-2">
                            {sim.user_reaction || "Simulating reaction..."}
                          </p>
                          {sim.ai_learned && (
                            <p className="text-[9px] text-muted-foreground mt-1 italic line-clamp-1">
                              Learned: {sim.ai_learned}
                            </p>
                          )}
                          <Badge className={`mt-1.5 text-[8px] px-1.5 py-0 h-4 ${
                            sim.user_decision === "engage" ? "bg-emerald-100 text-emerald-700 border-emerald-300" :
                            sim.user_decision === "scroll" ? "bg-amber-100 text-amber-700 border-amber-300" :
                            "bg-red-100 text-red-700 border-red-300"
                          }`}>
                            {sim.user_decision || "pending"}
                          </Badge>
                        </>
                      ) : (
                        <p className="text-[10px] text-muted-foreground/50 italic">Awaiting data...</p>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Timing recommendation */}
            {latestRun.timing_recommendations && (
              <div className="rounded-lg border bg-primary/5 border-primary/20 p-3">
                <p className="text-xs font-semibold text-primary mb-1">Optimal Publish Window</p>
                <p className="text-xs text-muted-foreground">
                  {typeof latestRun.timing_recommendations === "string"
                    ? latestRun.timing_recommendations
                    : JSON.stringify(latestRun.timing_recommendations)}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
