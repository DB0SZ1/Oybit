import os

base_dir = r"Frontend Dashbaord\app\[botId]"

pages = {
    "": "Overview",
    "intelligence": "Intelligence",
    "personas": "Personas",
    "content": "Content Pipeline",
    "media": "Media Library",
    "analytics": "Analytics",
    "growth": "Growth",
    "mirofish": "MiroFish Simulation",
    "guardian": "Guardian & Safety",
    "workers": "Worker Management",
    "settings": "Bot Settings",
}

TEMPLATE = """import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { notFound } from "next/navigation"
import { BOTS, type BotId } from "@/lib/bot-config"

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
          <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
            <h2 className="text-xl font-semibold mb-4">__TITLE__</h2>
            <p className="text-muted-foreground">
              This panel displays data from the <code>{bot.apiUrl}</code> endpoint.
              Components for this section are being built in Phase 5.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
"""

def generate():
    for route, title in pages.items():
        dir_path = os.path.join(base_dir, route) if route else base_dir
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = os.path.join(dir_path, "page.tsx")
        component_name = title.replace(" ", "").replace("&", "And")
        
        content = TEMPLATE.replace("__COMP_NAME__", component_name)
        content = content.replace("__TITLE__", title)
        content = content.replace("__TITLE_LOWER__", title.lower())
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    generate()
    print("Frontend routes generated.")
