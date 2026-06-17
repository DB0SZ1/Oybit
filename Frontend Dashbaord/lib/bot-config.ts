import { Facebook, Instagram, Linkedin, MessageCircle, Send, type LucideIcon } from "lucide-react"

export type BotId = 
  | "facebook_page" 
  | "facebook_personal" 
  | "instagram_brand" 
  | "instagram_personal" 
  | "linkedin" 
  | "reddit" 
  | "telegram"

export interface BotConfig {
  id: BotId
  name: string
  icon: LucideIcon
  color: string
  apiUrl: string
}

export const BOTS: Record<BotId, BotConfig> = {
  facebook_page: {
    id: "facebook_page",
    name: "Facebook Page",
    icon: Facebook,
    color: "bg-blue-600",
    apiUrl: process.env.NEXT_PUBLIC_FB_PAGE_API_URL || "http://localhost:8001"
  },
  facebook_personal: {
    id: "facebook_personal",
    name: "Facebook Personal",
    icon: Facebook,
    color: "bg-blue-500",
    apiUrl: process.env.NEXT_PUBLIC_FB_PERSONAL_API_URL || "http://localhost:8002"
  },
  instagram_brand: {
    id: "instagram_brand",
    name: "Instagram Brand",
    icon: Instagram,
    color: "bg-pink-600",
    apiUrl: process.env.NEXT_PUBLIC_IG_BRAND_API_URL || "http://localhost:8003"
  },
  instagram_personal: {
    id: "instagram_personal",
    name: "Instagram Personal",
    icon: Instagram,
    color: "bg-pink-500",
    apiUrl: process.env.NEXT_PUBLIC_IG_PERSONAL_API_URL || "http://localhost:8004"
  },
  linkedin: {
    id: "linkedin",
    name: "LinkedIn",
    icon: Linkedin,
    color: "bg-blue-700",
    apiUrl: process.env.NEXT_PUBLIC_LINKEDIN_API_URL || "http://localhost:8005"
  },
  reddit: {
    id: "reddit",
    name: "Reddit",
    icon: MessageCircle,
    color: "bg-orange-500",
    apiUrl: process.env.NEXT_PUBLIC_REDDIT_API_URL || "http://localhost:8006"
  },
  telegram: {
    id: "telegram",
    name: "Telegram",
    icon: Send,
    color: "bg-sky-500",
    apiUrl: process.env.NEXT_PUBLIC_TELEGRAM_API_URL || "http://localhost:8007"
  }
}
