"use client"

import { useBotData } from "@/hooks/use-bot-data"
import { type BotId } from "@/lib/bot-config"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Megaphone, Loader2, CheckCircle2, Clock, XCircle, FlaskConical } from "lucide-react"

function ScorePill({ label, value }: { label: string; value: number | null }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? "bg-emerald-100 text-emerald-700" : pct >= 60 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
  return (
    <span className={`inline-flex items-center gap-1 text-[9px] font-semibold px-1.5 py-0.5 rounded ${color}`}>
      {label} {pct}%
    </span>
  )
}

function PostCard({ post }: { post: any }) {
  const status = post.status || "draft"

  const statusConfig: Record<string, { label: string; icon: any; cls: string }> = {
    draft:     { label: "Draft",     icon: Clock,       cls: "bg-muted text-muted-foreground border-border" },
    published: { label: "Published", icon: CheckCircle2, cls: "bg-emerald-50 text-emerald-600 border-emerald-200" },
    scheduled: { label: "Scheduled", icon: Clock,       cls: "bg-blue-50 text-blue-600 border-blue-200" },
    blocked:   { label: "Blocked",   icon: XCircle,     cls: "bg-red-50 text-red-600 border-red-200" },
  }
  const cfg = statusConfig[status] || statusConfig.draft
  const Icon = cfg.icon

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-snug line-clamp-2 flex-1">
          {post.content_text || "No content"}
        </p>
        <Badge className={`shrink-0 text-[10px] gap-1 border ${cfg.cls}`}>
          <Icon className="h-2.5 w-2.5" />
          {cfg.label}
        </Badge>
      </div>

      {/* Meta tags */}
      <div className="flex flex-wrap gap-1.5">
        {post.hook_type && (
          <span className="text-[9px] bg-violet-50 text-violet-700 border border-violet-200 px-1.5 py-0.5 rounded">
            {post.hook_type}
          </span>
        )}
        {post.topic_pillar && (
          <span className="text-[9px] bg-blue-50 text-blue-700 border border-blue-200 px-1.5 py-0.5 rounded">
            {post.topic_pillar}
          </span>
        )}
        {post.emotional_tone && (
          <span className="text-[9px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded capitalize">
            {post.emotional_tone}
          </span>
        )}
        {post.format && (
          <span className="text-[9px] bg-indigo-50 text-indigo-700 border border-indigo-200 px-1.5 py-0.5 rounded capitalize">
            {post.format}
          </span>
        )}
      </div>

      {/* Media Preview */}
      {post.media_urls && post.media_urls.length > 0 && (
        <div className="mt-2 rounded-lg overflow-hidden border bg-muted/30">
          {post.format === "carousel" ? (
            <div className="flex gap-2 overflow-x-auto p-2 pb-3 snap-x scrollbar-thin">
              {post.media_urls.map((url: string, i: number) => (
                <img 
                  key={i} 
                  src={`http://localhost:8005${url}`} 
                  alt={`Slide ${i + 1}`} 
                  className="h-32 w-32 object-cover rounded shadow-sm shrink-0 snap-center border border-border" 
                />
              ))}
            </div>
          ) : (
            <div className="p-2">
              <img 
                src={`http://localhost:8005${post.media_urls[0]}`} 
                alt="Post Media" 
                className="max-h-48 rounded object-contain mx-auto border border-border" 
              />
            </div>
          )}
        </div>
      )}

      {/* Scores */}
      <div className="flex flex-wrap gap-1">
        <ScorePill label="Hook" value={post.score_hook} />
        <ScorePill label="Persona" value={post.score_persona} />
        <ScorePill label="Overall" value={post.score_total} />
        {post.mirofish_confidence != null && (
          <span className={`inline-flex items-center gap-1 text-[9px] font-semibold px-1.5 py-0.5 rounded
            ${post.mirofish_gate_result === "pass" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}
          `}>
            <FlaskConical className="h-2.5 w-2.5" />
            MiroFish {Math.round(post.mirofish_confidence * 100)}%
          </span>
        )}
      </div>

      {/* Timestamp */}
      {post.created_at && (
        <p className="text-[9px] text-muted-foreground">
          {new Date(post.created_at).toLocaleString()}
        </p>
      )}
    </div>
  )
}

export function ContentPipeline({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<{ posts: any[] }>(botId, "api/pipeline/posts", { refreshIntervalMs: 3000 })
  const posts = data?.posts || []
  const drafts = posts.filter(p => p.status === "draft").length
  const published = posts.filter(p => p.status === "published").length
  const scheduled = posts.filter(p => p.status === "scheduled").length

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Megaphone className="h-5 w-5 text-primary" />
            <div>
              <CardTitle>Post Queue</CardTitle>
              <CardDescription className="mt-0.5">All generated drafts, scheduled and published posts</CardDescription>
            </div>
          </div>
          <div className="flex gap-2 text-xs">
            {drafts > 0 && <Badge className="bg-muted text-muted-foreground">{drafts} Draft</Badge>}
            {scheduled > 0 && <Badge className="bg-blue-50 text-blue-600 border-blue-200">{scheduled} Scheduled</Badge>}
            {published > 0 && <Badge className="bg-emerald-50 text-emerald-600 border-emerald-200">{published} Published</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading && !data ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="text-destructive text-sm">{error.message}</div>
        ) : posts.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-8">
            No posts generated yet. Click <strong>Generate</strong> to run the pipeline.
          </div>
        ) : (
          <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
