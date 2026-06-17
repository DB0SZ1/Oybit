"use client"

import { useState, useEffect, useCallback } from "react"
import { ApiClient } from "@/lib/api-client"
import { type BotId } from "@/lib/bot-config"

interface UseBotDataOptions {
  refreshIntervalMs?: number
  enabled?: boolean
}

export function useBotData<T>(botId: BotId, endpoint: string, options: UseBotDataOptions = {}) {
  const { refreshIntervalMs = 0, enabled = true } = options
  
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchData = useCallback(async () => {
    if (!enabled) return
    
    try {
      setLoading(true)
      const result = await ApiClient.fetchBot<T>(botId, endpoint)
      setData(result)
      setError(null)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setLoading(false)
    }
  }, [botId, endpoint, enabled])

  useEffect(() => {
    fetchData()

    if (refreshIntervalMs > 0 && enabled) {
      const intervalId = setInterval(fetchData, refreshIntervalMs)
      return () => clearInterval(intervalId)
    }
  }, [fetchData, refreshIntervalMs, enabled])

  return { data, loading, error, lastUpdated, mutate: fetchData }
}

export function useBotHealth(botId: BotId, refreshIntervalMs = 15000) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)

  const checkHealth = useCallback(async () => {
    const health = await ApiClient.getBotHealth(botId)
    setIsHealthy(health)
  }, [botId])

  useEffect(() => {
    checkHealth()
    const intervalId = setInterval(checkHealth, refreshIntervalMs)
    return () => clearInterval(intervalId)
  }, [checkHealth, refreshIntervalMs])

  return isHealthy
}
