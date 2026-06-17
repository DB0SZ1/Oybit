"use client"

import { 
  LayoutDashboard, 
  Settings, 
  HelpCircle, 
  LogOut, 
  ChevronDown,
  ChevronRight,
  BrainCircuit,
  UserCircle,
  Megaphone,
  Image as ImageIcon,
  BarChart3,
  TrendingUp,
  Activity,
  ShieldCheck,
  ServerCog
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { BOTS } from "@/lib/bot-config"

const globalItems = [
  { icon: LayoutDashboard, label: "Overview", href: "/" },
  { icon: Settings, label: "Global Settings", href: "/settings" },
  { icon: ShieldCheck, label: "Audit Log", href: "/audit" },
]

const botSubItems = [
  { icon: BrainCircuit, label: "Intelligence", path: "/intelligence" },
  { icon: UserCircle, label: "Personas", path: "/personas" },
  { icon: Megaphone, label: "Content Pipeline", path: "/content" },
  { icon: ImageIcon, label: "Media Library", path: "/media" },
  { icon: BarChart3, label: "Analytics", path: "/analytics" },
  { icon: TrendingUp, label: "Growth", path: "/growth" },
  { icon: Activity, label: "MiroFish", path: "/mirofish" },
  { icon: ShieldCheck, label: "Guardian", path: "/guardian" },
  { icon: ServerCog, label: "Workers", path: "/workers" },
  { icon: Settings, label: "Settings", path: "/settings" },
]

export function Sidebar() {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)
  const pathname = usePathname()
  const [openBots, setOpenBots] = useState<Record<string, boolean>>({})

  const toggleBot = (botId: string) => {
    setOpenBots(prev => ({ ...prev, [botId]: !prev[botId] }))
  }

  return (
    <aside className="fixed top-0 left-0 w-64 bg-card border-r border-border p-4 h-screen overflow-y-auto lg:block">
      <div className="flex items-center gap-2 mb-6 group cursor-pointer">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center transition-transform group-hover:scale-110 duration-300 relative">
            <div
              className="w-1.5 h-1.5 rounded-full bg-primary-foreground absolute"
              style={{ top: "30%", left: "30%" }}
            />
            <div
              className="w-1.5 h-1.5 rounded-full bg-primary-foreground absolute"
              style={{ top: "30%", right: "30%" }}
            />
            <div className="w-3 h-1.5 border-b-2 border-primary-foreground rounded-full absolute bottom-2.5" />
          </div>
          <span className="text-lg font-semibold text-foreground">Oybit</span>
        </Link>
      </div>

      <div className="space-y-6">
        <div>
          <p className="text-[10px] font-medium text-muted-foreground mb-2 uppercase tracking-wider">System</p>
          <nav className="space-y-0.5">
            {globalItems.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onMouseEnter={() => setHoveredItem(item.label)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={cn(
                    "w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-300",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                    hoveredItem === item.label && !isActive && "translate-x-1",
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="text-sm">{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        <div>
          <p className="text-[10px] font-medium text-muted-foreground mb-2 uppercase tracking-wider">Platforms</p>
          <nav className="space-y-1">
            {Object.values(BOTS).map((bot) => {
              const isOpen = openBots[bot.id]
              const isBotActive = pathname.startsWith(`/${bot.id}`)
              
              return (
                <div key={bot.id} className="space-y-1">
                  <button
                    onClick={() => toggleBot(bot.id)}
                    className={cn(
                      "w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-300",
                      isBotActive && !isOpen
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                    )}
                  >
                    <bot.icon className={cn("w-4 h-4", bot.color.replace('bg-', 'text-'))} />
                    <span className="text-sm flex-1 text-left">{bot.name}</span>
                    {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  
                  {isOpen && (
                    <div className="ml-4 pl-2 border-l border-border space-y-0.5">
                      {botSubItems.map((subItem) => {
                        const href = `/${bot.id}${subItem.path}`
                        const isActive = pathname === href
                        
                        return (
                          <Link
                            key={subItem.label}
                            href={href}
                            className={cn(
                              "w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-300",
                              isActive
                                ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                            )}
                          >
                            <subItem.icon className="w-3.5 h-3.5" />
                            <span className="text-xs">{subItem.label}</span>
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </nav>
        </div>
      </div>
    </aside>
  )
}
