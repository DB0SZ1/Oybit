import { BOTS, type BotId } from "./bot-config"

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean>
}

export class ApiClient {
  static async fetchBot<T>(botId: BotId, endpoint: string, options: FetchOptions = {}): Promise<T> {
    const bot = BOTS[botId]
    if (!bot) throw new Error(`Unknown bot: ${botId}`)

    let url = `${bot.apiUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
    
    if (options.params) {
      const searchParams = new URLSearchParams()
      for (const [key, value] of Object.entries(options.params)) {
        searchParams.append(key, String(value))
      }
      url += `?${searchParams.toString()}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      return await response.json() as T
    } catch (error) {
      console.error(`Failed to fetch from ${botId} (${url}):`, error)
      throw error
    }
  }

  static async getBotHealth(botId: BotId): Promise<boolean> {
    try {
      const res = await this.fetchBot<{ status: string }>(botId, "/", { 
        // Fast timeout for health checks
        signal: AbortSignal.timeout(3000) 
      })
      return res.status === "ok"
    } catch {
      return false
    }
  }
}
