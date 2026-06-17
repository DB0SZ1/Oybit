import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { notFound } from "next/navigation"
import { BOTS, type BotId } from "@/lib/bot-config"
import { BotOverviewCard } from "@/components/bots/bot-overview-card"
import { ManualTriggerBar } from "@/components/bots/manual-trigger-bar"
import { PipelineProcessBoard } from "@/components/bots/pipeline-process-board"
import { MirofishDebatePanel } from "@/components/bots/mirofish-debate-panel"
import { ContentPipeline } from "@/components/bots/content-pipeline"
import { IntelligencePanel } from "@/components/bots/intelligence-panel"

export default async function OpsDashboardPage({ params }: { params: Promise<{ botId: string }> }) {
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
          title={`${bot.name} - Ops Dashboard`}
          description={`Manage ops dashboard for ${bot.name}`}
          actions={null}
        />

        <div className="mt-6">
          <ManualTriggerBar botId={botId} />
          <div className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1"><BotOverviewCard botId={botId} botName={bot.name} /></div>
              <div className="lg:col-span-2"><PipelineProcessBoard botId={botId} /></div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <MirofishDebatePanel botId={botId} />
              <IntelligencePanel botId={botId} />
            </div>
            <ContentPipeline botId={botId} />
          </div>
        </div>
      </main>
    </div>
  )
}
