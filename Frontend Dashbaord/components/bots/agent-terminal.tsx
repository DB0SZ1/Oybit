"use client"

import { useEffect, useRef, useState } from "react"
import { type BotId } from "@/lib/bot-config"
import { useBotData } from "@/hooks/use-bot-data"
import { Terminal, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function AgentTerminal({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<{ logs: any[] }>(botId, "api/system/logs", { refreshIntervalMs: 2000 })
  const terminalEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isAutoScroll, setIsAutoScroll] = useState(true)

  const handleScroll = () => {
    if (!containerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    // If we are within 50px of the bottom, enable auto-scroll
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 50
    setIsAutoScroll(isNearBottom)
  }

  useEffect(() => {
    // Auto scroll to bottom when new logs come in, but only if user hasn't scrolled up
    if (isAutoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [data, isAutoScroll])

  return (
    <Card className="border-ring/50 shadow-lg shadow-ring/10 overflow-hidden flex flex-col h-[400px]">
      <CardHeader className="bg-muted/50 border-b pb-3 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-mono tracking-tight uppercase text-primary">Live Agent Stream</CardTitle>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            LISTENING
          </div>
        </div>
      </CardHeader>
      <CardContent 
        className="p-0 flex-1 bg-black text-green-400 font-mono text-xs relative overflow-hidden"
      >
        <div 
          ref={containerRef}
          onScroll={handleScroll}
          className="h-full w-full overflow-y-auto absolute inset-0"
        >
          {loading && !data ? (
             <div className="p-4 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                Initializing connection...
             </div>
          ) : error ? (
             <div className="p-4 text-destructive">
                CONNECTION FAILED: {error.message}
             </div>
          ) : data?.logs && data.logs.length > 0 ? (
          <div className="p-4 space-y-2">
            {data.logs.slice().reverse().map((log: any, i: number) => (
              <div key={i} className="border-l-2 border-primary/30 pl-3 py-1">
                <div className="flex items-center justify-between opacity-50 mb-1">
                  <span>[{new Date(log.created_at).toLocaleTimeString()}]</span>
                  <span className="uppercase text-[10px] bg-primary/20 text-primary px-1 rounded">{log.action}</span>
                </div>
                <div className="text-white whitespace-pre-wrap">
                  {log.details?.reason || log.details?.status || JSON.stringify(log.details)}
                </div>
                {log.details?.step && (
                  <div className="mt-1 text-[10px] opacity-60">
                    &gt; step: {log.details.step}
                    {log.details.confidence && ` | conf: ${(log.details.confidence * 100).toFixed(1)}%`}
                  </div>
                )}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>
          ) : (
            <div className="p-4 opacity-50">
              Awaiting instructions...
              <div ref={terminalEndRef} />
            </div>
          )}
        </div>
        
        {!isAutoScroll && (
          <div className="absolute bottom-4 right-4 z-10">
            <button 
              onClick={() => {
                setIsAutoScroll(true)
                if (containerRef.current) {
                  containerRef.current.scrollTop = containerRef.current.scrollHeight
                }
              }}
              className="bg-primary/20 text-primary border border-primary hover:bg-primary/40 px-3 py-1 rounded text-xs backdrop-blur-sm"
            >
              Resume Auto-scroll
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
