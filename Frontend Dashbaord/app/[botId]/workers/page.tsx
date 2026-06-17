import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { notFound } from "next/navigation"
import { BOTS, type BotId } from "@/lib/bot-config"
import { WorkersPanel } from "@/components/bots/workers-panel"

export default async function WorkerManagementPage({ params }: { params: Promise<{ botId: string }> }) {
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
          title={`${bot.name} - Worker Management`}
          description={`Manage worker management for ${bot.name}`}
          actions={null}
        />

        <div className="mt-6">
          <WorkersPanel botId={botId} />
        </div>
      </main>
    </div>
  )
}
