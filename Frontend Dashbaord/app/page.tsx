import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { BOTS } from "@/lib/bot-config"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, Server, Zap, ShieldCheck } from "lucide-react"
import { BotOverviewCard } from "@/components/bots/bot-overview-card"

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header
          title="Command Center"
          description="Global overview of all Oybit social media agents."
          actions={null}
        />

        <div className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">System Status</CardTitle>
                <Activity className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">Operational</div>
                <p className="text-xs text-muted-foreground mt-1">All pipelines routing normally</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Active Agents</CardTitle>
                <Server className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">7 / 7</div>
                <p className="text-xs text-muted-foreground mt-1">Across 4 platforms</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Ops Handled Today</CardTitle>
                <Zap className="h-4 w-4 text-accent" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">142</div>
                <p className="text-xs text-muted-foreground mt-1">Scans, Generations, Posts</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Guardian Blocks</CardTitle>
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">0</div>
                <p className="text-xs text-muted-foreground mt-1">Safety checks passed</p>
              </CardContent>
            </Card>
          </div>

          <h3 className="text-lg font-medium tracking-tight mb-4 text-foreground/90">Platform Deployments</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.values(BOTS).map((bot) => (
              <div key={bot.id} className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/30 to-accent/30 rounded-xl blur opacity-0 group-hover:opacity-100 transition duration-500"></div>
                <div className="relative">
                  <BotOverviewCard botId={bot.id} botName={bot.name} />
                  <div className="absolute top-4 right-4 z-10">
                    <Link 
                      href={`/${bot.id}`}
                      className="inline-flex items-center text-xs font-mono bg-secondary hover:bg-secondary/80 text-secondary-foreground px-2 py-1 rounded transition-colors"
                    >
                      ENTER &gt;
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}

