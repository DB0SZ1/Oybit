"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { type BotId } from "@/lib/bot-config"
import { useBotData } from "@/hooks/use-bot-data"
import { BrainCircuit, Loader2, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export function IntelligencePanel({ botId }: { botId: BotId }) {
  const { data, loading, error } = useBotData<{ trends: any[] }>(botId, "api/intelligence/trends")
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5
  
  // Sort trends: recent to outdated (descending)
  const sortedTrends = data?.trends ? [...data.trends].sort((a, b) => {
    const timeA = a.collected_at ? new Date(a.collected_at).getTime() : a.id;
    const timeB = b.collected_at ? new Date(b.collected_at).getTime() : b.id;
    return timeB - timeA;
  }) : []

  const totalPages = Math.ceil(sortedTrends.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const currentTrends = sortedTrends.slice(startIndex, startIndex + itemsPerPage)

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
        ) : sortedTrends.length > 0 ? (
          <div className="space-y-4">
            <div className="space-y-2">
              {currentTrends.map((t: any, i: number) => (
                <div key={i} className="flex justify-between items-center p-3 border rounded-lg bg-card/50">
                  <div className="flex flex-col truncate pr-4">
                    <span className="font-medium text-sm truncate">{t.topic || "Unknown Topic"}</span>
                    {t.collected_at && (
                      <span className="text-[10px] text-muted-foreground">
                        {new Date(t.collected_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">Score: {t.score || "N/A"}</span>
                  </div>
                </div>
              ))}
            </div>
            
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-2 border-t mt-4">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" /> Prev
                </Button>
                <span className="text-xs text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </span>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground py-4 text-center">No recent trends found.</div>
        )}
      </CardContent>
    </Card>
  )
}

