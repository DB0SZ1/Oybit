import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { notFound } from "next/navigation"
import { BOTS, type BotId } from "@/lib/bot-config"
import { ContentPipeline } from "@/components/bots/content-pipeline"
import { ManualTriggerBar } from "@/components/bots/manual-trigger-bar"

export default async function ContentPipelinePage({ params }: { params: Promise<{ botId: string }> }) {
  const resolvedParams = await params
  const botId = resolvedParams.botId as BotId
  const bot = BOTS[botId]
  
  if (!bot) {
    notFound()
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header
          title={`${bot.name} - Content Pipeline`}
          description={`Manage content pipeline for ${bot.name}`}
          actions={null}
        />

        <div className="mt-6">
          <ManualTriggerBar botId={botId} />
          <div className="mt-4">
            <ContentPipeline botId={botId} />
          </div>
        </div>
      </main>
    </div>
  )
}
