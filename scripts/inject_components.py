import os

base_dir = r"Frontend Dashbaord\app\[botId]"

pages = {
    "": {
        "title": "Ops Dashboard",
        "import": "import { BotOverviewCard } from \"@/components/bots/bot-overview-card\"\nimport { ManualTriggerBar } from \"@/components/bots/manual-trigger-bar\"\nimport { PipelineProcessBoard } from \"@/components/bots/pipeline-process-board\"\nimport { MirofishDebatePanel } from \"@/components/bots/mirofish-debate-panel\"\nimport { ContentPipeline } from \"@/components/bots/content-pipeline\"\nimport { IntelligencePanel } from \"@/components/bots/intelligence-panel\"",
        "component": "<ManualTriggerBar botId={botId} />\n          <div className=\"mt-6 space-y-6\">\n            <div className=\"grid grid-cols-1 lg:grid-cols-3 gap-6\">\n              <div className=\"lg:col-span-1\"><BotOverviewCard botId={botId} botName={bot.name} /></div>\n              <div className=\"lg:col-span-2\"><PipelineProcessBoard botId={botId} /></div>\n            </div>\n            <div className=\"grid grid-cols-1 lg:grid-cols-2 gap-6\">\n              <MirofishDebatePanel botId={botId} />\n              <IntelligencePanel botId={botId} />\n            </div>\n            <ContentPipeline botId={botId} />\n          </div>"
    },
    "intelligence": {
        "title": "Intelligence",
        "import": "import { IntelligencePanel } from \"@/components/bots/intelligence-panel\"",
        "component": "<IntelligencePanel botId={botId} />"
    },
    "personas": {
        "title": "Personas",
        "import": "import { PersonaManager } from \"@/components/bots/persona-manager\"",
        "component": "<PersonaManager botId={botId} />"
    },
    "content": {
        "title": "Content Pipeline",
        "import": "import { ContentPipeline } from \"@/components/bots/content-pipeline\"\nimport { ManualTriggerBar } from \"@/components/bots/manual-trigger-bar\"",
        "component": "<ManualTriggerBar botId={botId} />\n          <div className=\"mt-4\">\n            <ContentPipeline botId={botId} />\n          </div>"
    },
    "media": {
        "title": "Media Library",
        "import": "import { MediaLibrary } from \"@/components/bots/media-library\"",
        "component": "<MediaLibrary botId={botId} />"
    },
    "analytics": {
        "title": "Analytics",
        "import": "import { AnalyticsDashboard } from \"@/components/bots/analytics-dashboard\"",
        "component": "<AnalyticsDashboard botId={botId} />"
    },
    "growth": {
        "title": "Growth",
        "import": "import { GrowthPanel } from \"@/components/bots/growth-panel\"",
        "component": "<GrowthPanel botId={botId} />"
    },
    "mirofish": {
        "title": "MiroFish Simulation",
        "import": "import { MirofishDebatePanel } from \"@/components/bots/mirofish-debate-panel\"",
        "component": "<MirofishDebatePanel botId={botId} />"
    },
    "guardian": {
        "title": "Guardian & Safety",
        "import": "import { GuardianPanel } from \"@/components/bots/guardian-panel\"",
        "component": "<GuardianPanel botId={botId} />"
    },
    "workers": {
        "title": "Worker Management",
        "import": "import { WorkersPanel } from \"@/components/bots/workers-panel\"",
        "component": "<WorkersPanel botId={botId} />"
    },
    "settings": {
        "title": "Bot Settings",
        "import": "",
        "component": "<div className=\"text-muted-foreground\">Settings form coming soon.</div>"
    },
}

TEMPLATE = """import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { notFound } from "next/navigation"
import { BOTS, type BotId } from "@/lib/bot-config"
__IMPORTS__

export default async function __COMP_NAME__Page({ params }: { params: Promise<{ botId: string }> }) {
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
          title={`${bot.name} - __TITLE__`}
          description={`Manage __TITLE_LOWER__ for ${bot.name}`}
          actions={null}
        />

        <div className="mt-6">
          __COMPONENT__
        </div>
      </main>
    </div>
  )
}
"""

def generate():
    for route, config in pages.items():
        dir_path = os.path.join(base_dir, route) if route else base_dir
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = os.path.join(dir_path, "page.tsx")
        component_name = config["title"].replace(" ", "").replace("&", "And")
        
        content = TEMPLATE.replace("__COMP_NAME__", component_name)
        content = content.replace("__TITLE__", config["title"])
        content = content.replace("__TITLE_LOWER__", config["title"].lower())
        content = content.replace("__IMPORTS__", config["import"])
        content = content.replace("__COMPONENT__", config["component"])
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    generate()
    print("Frontend routes updated with components.")
