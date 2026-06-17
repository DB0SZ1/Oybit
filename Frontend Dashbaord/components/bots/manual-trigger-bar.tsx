"use client"

import { type BotId } from "@/lib/bot-config"
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
