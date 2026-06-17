"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
