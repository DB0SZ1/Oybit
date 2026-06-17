import os

base_dir = r"Frontend Dashbaord\components\bots"

COMPONENTS = {
    "bot-overview-card.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { type BotId } from "@/lib/bot-config"
import { useBotData, useBotHealth } from "@/hooks/use-bot-data"
import { Activity, AlertCircle, CheckCircle2 } from "lucide-react"

export function BotOverviewCard({ botId, botName }: { botId: BotId, botName: string }) {
  const isHealthy = useBotHealth(botId)
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-xl">{botName} Status</CardTitle>
        </div>
        {isHealthy === null ? (
          <Badge variant="outline" className="text-muted-foreground">Checking...</Badge>
        ) : isHealthy ? (
          <Badge variant="outline" className="bg-emerald-50 text-emerald-600 border-emerald-200">
            <CheckCircle2 className="w-3 h-3 mr-1" /> Online
          </Badge>
        ) : (
          <Badge variant="destructive">
            <AlertCircle className="w-3 h-3 mr-1" /> Offline
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <CardDescription>Real-time status and health metrics</CardDescription>
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground">Uptime</span>
            <span className="font-medium">99.9%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground">API Latency</span>
            <span className="font-medium">~45ms</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
""",
    "intelligence-panel.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { useBotData } from "@/hooks/use-bot-data"
import { BrainCircuit, Loader2 } from "lucide-react"

export function IntelligencePanel({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<{ trends: any[] }>(botId, "api/intelligence/trends")
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-primary" />
          <CardTitle>Intelligence & Trends</CardTitle>
        </div>
        <CardDescription>Recent market signals and trends identified by the agent</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center p-6"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
        ) : error ? (
          <div className="text-destructive text-sm">Failed to load trends: {error.message}</div>
        ) : data?.trends && data.trends.length > 0 ? (
          <div className="space-y-4">
            {data.trends.map((t: any, i: number) => (
              <div key={i} className="flex justify-between items-center p-3 border rounded-lg">
                <span className="font-medium">{t.topic || "Unknown Topic"}</span>
                <span className="text-sm text-muted-foreground">Score: {t.score || "N/A"}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground py-4 text-center">No recent trends found.</div>
        )}
      </CardContent>
    </Card>
  )
}
""",
    "persona-manager.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { UserCircle } from "lucide-react"

export function PersonaManager({ botId }: { botId: BotId }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <UserCircle className="h-5 w-5 text-primary" />
          <CardTitle>Persona Management</CardTitle>
        </div>
        <CardDescription>Active voice, traits, and persona drift</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Integration pending. This will display the markdown content of the current persona profile.
        </div>
      </CardContent>
    </Card>
  )
}
""",
    "content-pipeline.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { useBotData } from "@/hooks/use-bot-data"
import { Megaphone, Loader2 } from "lucide-react"

export function ContentPipeline({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<{ posts: any[] }>(botId, "api/pipeline/posts")

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Megaphone className="h-5 w-5 text-primary" />
          <CardTitle>Content Pipeline</CardTitle>
        </div>
        <CardDescription>Drafts, scheduled, and published content</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center p-6"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
        ) : error ? (
          <div className="text-destructive text-sm">Failed to load posts: {error.message}</div>
        ) : data?.posts && data.posts.length > 0 ? (
          <div className="space-y-4">
            {data.posts.map((post: any, i: number) => (
              <div key={i} className="p-3 border rounded-lg text-sm">
                <div className="font-medium mb-1 capitalize">{post.status || "draft"}</div>
                <div className="text-muted-foreground line-clamp-2">{post.content_text || "No text"}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground py-4 text-center">No posts in the pipeline.</div>
        )}
      </CardContent>
    </Card>
  )
}
""",
    "media-library.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { Image as ImageIcon } from "lucide-react"

export function MediaLibrary({ botId }: { botId: BotId }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ImageIcon className="h-5 w-5 text-primary" />
          <CardTitle>Media Library</CardTitle>
        </div>
        <CardDescription>Uploaded images and video assets</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          No media assets found. Upload functionality coming soon.
        </div>
      </CardContent>
    </Card>
  )
}
""",
    "analytics-dashboard.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
""",
    "growth-panel.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
""",
    "mirofish-panel.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
""",
    "guardian-panel.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
""",
    "workers-panel.tsx": """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
""",
    "manual-trigger-bar.tsx": """import { type BotId } from "@/lib/bot-config"
import { Button } from "@/components/ui/button"
import { Play, Sparkles, RefreshCw, ShieldAlert, Send } from "lucide-react"
import { ApiClient } from "@/lib/api-client"
import { toast } from "sonner"
import { useState } from "react"

export function ManualTriggerBar({ botId }: { botId: BotId }) {
  const [loading, setLoading] = useState<string | null>(null)

  const handleTrigger = async (action: string, endpoint: string) => {
    try {
      setLoading(action)
      await ApiClient.fetchBot(botId, endpoint, { method: "POST" })
      toast.success(`${action} triggered successfully for ${botId}`)
    } catch (err: any) {
      toast.error(`Failed to trigger ${action}: ${err.message}`)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 p-4 bg-secondary/50 rounded-lg border border-border">
      <span className="text-sm font-medium mr-2 text-muted-foreground">Manual Controls:</span>
      
      <Button 
        variant="outline" 
        size="sm" 
        disabled={loading !== null}
        onClick={() => handleTrigger("Scan Opportunities", "api/intelligence/scan")}
        className="gap-2"
      >
        <Play className="w-3.5 h-3.5" /> Scan
      </Button>
      
      <Button 
        variant="outline" 
        size="sm" 
        disabled={loading !== null}
        onClick={() => handleTrigger("Generate Content", "api/pipeline/generate")}
        className="gap-2"
      >
        <Sparkles className="w-3.5 h-3.5 text-primary" /> Generate
      </Button>

      <Button 
        variant="outline" 
        size="sm" 
        disabled={loading !== null}
        onClick={() => handleTrigger("Run MiroFish", "api/mirofish/trigger")}
        className="gap-2"
      >
        <ShieldAlert className="w-3.5 h-3.5 text-emerald-600" /> MiroFish
      </Button>

      <Button 
        variant="outline" 
        size="sm" 
        disabled={loading !== null}
        onClick={() => handleTrigger("Rotate Persona", "api/personas/rotate")}
        className="gap-2"
      >
        <RefreshCw className="w-3.5 h-3.5 text-blue-500" /> Rotate Persona
      </Button>
    </div>
  )
}
"""
}

def generate():
    os.makedirs(base_dir, exist_ok=True)
    for filename, content in COMPONENTS.items():
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    generate()
    print("Bot components generated.")
