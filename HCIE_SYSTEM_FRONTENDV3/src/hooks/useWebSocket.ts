'use client'

import { useEffect, useState, useRef } from 'react'
import { createWebSocketClient, getWebSocketClient } from '@/lib/websocket/client'

interface WebSocketMessage {
  type: 'projection_update' | 'learning_event' | 'system_status' | 'progress_update' | 'mastery_change' | 'bandit_update' | 'notification'
  data: any
  timestamp: string
}

interface UseWebSocketOptions {
  enabled?: boolean
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const { enabled = true, onMessage, onError, onConnect, onDisconnect } = options
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsClientRef = useRef<ReturnType<typeof getWebSocketClient> | null>(null)

  useEffect(() => {
    if (!enabled) return

    // Initialize WebSocket client — auto-create with default config if not yet
    // initialized (e.g. on first render when createWebSocketClient hasn't been
    // called explicitly by the app bootstrap).
    if (!wsClientRef.current) {
      try {
        wsClientRef.current = getWebSocketClient()
      } catch {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/connections'
        wsClientRef.current = createWebSocketClient({
          url: wsUrl,
          reconnectInterval: 5000,
          maxReconnectAttempts: 3,
        })
      }
    }

    const client = wsClientRef.current

    // Set up message handler
    const unsubscribe = client.on('message', (data) => {
      const message: WebSocketMessage = {
        type: data.type || 'notification',
        data: data.data || data,
        timestamp: data.timestamp || new Date().toISOString(),
      }
      setLastMessage(message)
      onMessage?.(message)
    })

    // Set up status handler
    const handleStatusChange = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => {
      setIsConnected(status === 'connected')
      if (status === 'connected') onConnect?.()
      if (status === 'disconnected') onDisconnect?.()
    }

    // Connect
    client.connect()

    return () => {
      unsubscribe()
      client.disconnect()
    }
  }, [url, enabled, onMessage, onError, onConnect, onDisconnect])

  const sendMessage = (message: any) => {
    if (wsClientRef.current) {
      wsClientRef.current.send(message)
    }
  }

  return {
    isConnected,
    lastMessage,
    sendMessage
  }
}

// Hook for learning progress updates
export function useLearningProgress() {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/connections'
  
  const [masteryUpdates, setMasteryUpdates] = useState<Record<string, number>>({})
  const [banditScores, setBanditScores] = useState<Record<string, number>>({})
  const [notifications, setNotifications] = useState<string[]>([])

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'projection_update':
        if (message.data.mastery) {
          setMasteryUpdates(prev => ({
            ...prev,
            [message.data.concept]: message.data.mastery
          }))
        }
        break
      case 'learning_event':
        if (message.data.mastery_change) {
          setMasteryUpdates(prev => ({
            ...prev,
            [message.data.concept]: message.data.mastery_change
          }))
        }
        break
      case 'mastery_change':
        setMasteryUpdates(prev => ({
          ...prev,
          [message.data.conceptId]: message.data.mastery
        }))
        break
      case 'bandit_update':
        setBanditScores(prev => ({
          ...prev,
          [message.data.conceptId]: message.data.score
        }))
        break
      case 'notification':
        setNotifications(prev => [...prev, message.data.message])
        break
    }
  }

  const { isConnected } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onError: (error) => console.error('Learning progress WebSocket error:', error)
  })

  return {
    isConnected,
    masteryUpdates,
    banditScores,
    notifications
  }
}

// Hook for system status updates
export function useSystemStatus() {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/connections'
  
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'degraded' | 'unhealthy'>('healthy')
  const [activeUsers, setActiveUsers] = useState(0)
  const [processingRate, setProcessingRate] = useState(0)

  const handleMessage = (message: WebSocketMessage) => {
    if (message.type === 'system_status') {
      setSystemHealth(message.data.health || 'healthy')
      setActiveUsers(message.data.active_users || 0)
      setProcessingRate(message.data.processing_rate || 0)
    }
  }

  const { isConnected } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onError: (error) => console.error('System status WebSocket error:', error)
  })

  return {
    isConnected,
    systemHealth,
    activeUsers,
    processingRate
  }
}
