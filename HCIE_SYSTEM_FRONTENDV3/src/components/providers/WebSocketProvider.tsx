'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage } from '@/types'

interface WebSocketContextType {
  socket: Socket | null
  connected: boolean
  connect: (userId: string) => void
  disconnect: () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)

  const connect = (userId: string) => {
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8011'
    const token = localStorage.getItem('access_token')

    const newSocket = io(`${WS_URL}/learning/${userId}`, {
      auth: { token },
      transports: ['websocket'],
    })

    newSocket.on('connect', () => {
      setConnected(true)
      console.log('WebSocket connected')
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
      console.log('WebSocket disconnected')
    })

    newSocket.on('message', (data: WebSocketMessage) => {
      console.log('WebSocket message:', data)
      // Handle different message types
      switch (data.type) {
        case 'projection_update':
          // Handle projection updates
          break
        case 'learning_event':
          // Handle learning events
          break
        case 'system_status':
          // Handle system status
          break
      }
    })

    newSocket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })

    setSocket(newSocket)
  }

  const disconnect = () => {
    if (socket) {
      socket.disconnect()
      setSocket(null)
      setConnected(false)
    }
  }

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [])

  const value = {
    socket,
    connected,
    connect,
    disconnect,
  }

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}
