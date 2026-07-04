/**
 * WebSocket Service Implementation
 * 
 * Implements the IWebSocketService protocol for WebSocket-related operations.
 * This service handles real-time communication, event handling, and connection management.
 */

import type {
  IWebSocketService,
  WebSocketConfig,
  ConnectionState,
  WebSocketMessage,
  WebSocketEvent,
  EventHandler,
  ConnectionStatistics,
  ConnectionEvent,
} from '../interfaces'

/**
 * WebSocket Service Implementation
 */
export class WebSocketService implements IWebSocketService {
  private url: string
  private authToken: string
  private reconnectInterval: number
  private maxReconnectAttempts: number
  private debug: boolean
  
  private socket: WebSocket | null = null
  private connectionState: ConnectionState = 'disconnected'
  private reconnectAttempts: number = 0
  private reconnectTimer: NodeJS.Timeout | null = null
  
  private eventHandlers: Map<string, Set<EventHandler>> = new Map()
  private allEventHandlers: Set<EventHandler<WebSocketEvent>> = new Set()
  
  private messagesReceived: number = 0
  private messagesSent: number = 0
  private connectionStartTime: number = 0
  private lastConnectionTime: number = 0

  constructor(config: WebSocketConfig) {
    this.url = config.url
    this.authToken = config.authToken
    this.reconnectInterval = config.reconnectInterval || 5000 // 5 seconds default
    this.maxReconnectAttempts = config.maxReconnectAttempts || 10
    this.debug = config.debug || false
  }

  /**
   * Connect to WebSocket server
   */
  async connect(userId: string): Promise<void> {
    this.log('Connecting to WebSocket server for user:', userId)
    
    if (this.socket && this.connectionState === 'connected') {
      this.log('Already connected')
      return
    }

    return new Promise((resolve, reject) => {
      try {
        // Construct WebSocket URL with auth token
        const wsUrl = `${this.url}?token=${this.authToken}&user_id=${userId}`
        this.socket = new WebSocket(wsUrl)
        this.connectionState = 'connecting'
        this.connectionStartTime = Date.now()

        this.socket.onopen = () => {
          this.log('WebSocket connected')
          this.connectionState = 'connected'
          this.reconnectAttempts = 0
          this.lastConnectionTime = Date.now()
          this.emitConnectionEvent('connected', userId)
          resolve()
        }

        this.socket.onmessage = (event) => {
          this.handleMessage(event)
        }

        this.socket.onerror = (error) => {
          this.log('WebSocket error:', error)
          this.connectionState = 'error'
          this.emitConnectionEvent('error', userId)
          reject(new Error('WebSocket connection error'))
        }

        this.socket.onclose = (event) => {
          this.log('WebSocket closed:', event.code, event.reason)
          this.connectionState = 'disconnected'
          this.emitConnectionEvent('disconnected', userId)
          
          // Attempt reconnection if not intentionally closed
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(userId)
          }
        }
      } catch (error) {
        this.log('Error creating WebSocket connection:', error)
        this.connectionState = 'error'
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  async disconnect(): Promise<void> {
    this.log('Disconnecting from WebSocket server')
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.socket) {
      this.socket.close(1000, 'Intentional disconnect')
      this.socket = null
    }

    this.connectionState = 'disconnected'
    this.clearSubscriptions()
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return this.connectionState
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState === 'connected' && this.socket?.readyState === WebSocket.OPEN
  }

  /**
   * Send a message to the server
   */
  async send<T = unknown>(message: WebSocketMessage<T>): Promise<void> {
    if (!this.isConnected()) {
      throw new Error('WebSocket is not connected')
    }

    this.log('Sending message:', message.type)
    
    try {
      this.socket!.send(JSON.stringify(message))
      this.messagesSent++
    } catch (error) {
      this.log('Error sending message:', error)
      throw new Error(`Failed to send message: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Subscribe to an event type
   */
  subscribe<T = unknown>(eventType: string, handler: EventHandler<T>): () => void {
    this.log('Subscribing to event:', eventType)
    
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set())
    }
    
    this.eventHandlers.get(eventType)!.add(handler as EventHandler)
    
    // Return unsubscribe function
    return () => {
      this.unsubscribe(eventType, handler as EventHandler)
    }
  }

  /**
   * Subscribe to all events
   */
  subscribeAll(handler: EventHandler<WebSocketEvent>): () => void {
    this.log('Subscribing to all events')
    this.allEventHandlers.add(handler)
    
    // Return unsubscribe function
    return () => {
      this.allEventHandlers.delete(handler)
    }
  }

  /**
   * Unsubscribe from an event type
   */
  unsubscribe(eventType: string, handler: EventHandler): void {
    this.log('Unsubscribing from event:', eventType)
    
    const handlers = this.eventHandlers.get(eventType)
    if (handlers) {
      handlers.delete(handler)
      
      if (handlers.size === 0) {
        this.eventHandlers.delete(eventType)
      }
    }
  }

  /**
   * Clear all event subscriptions
   */
  clearSubscriptions(): void {
    this.log('Clearing all subscriptions')
    this.eventHandlers.clear()
    this.allEventHandlers.clear()
  }

  /**
   * Get connection statistics
   */
  getStatistics(): ConnectionStatistics {
    return {
      state: this.connectionState,
      reconnectAttempts: this.reconnectAttempts,
      timeSinceLastConnection: this.lastConnectionTime ? Date.now() - this.lastConnectionTime : 0,
      messagesReceived: this.messagesReceived,
      messagesSent: this.messagesSent,
      connectionDuration: this.connectionStartTime ? Date.now() - this.connectionStartTime : 0,
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(event: MessageEvent): void {
    this.messagesReceived++
    
    try {
      const message = JSON.parse(event.data) as WebSocketMessage
      this.log('Received message:', message.type)
      
      // Emit to specific event handlers
      const handlers = this.eventHandlers.get(message.type)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message.data)
          } catch (error) {
            this.log('Error in event handler:', error)
          }
        })
      }
      
      // Emit to all event handlers
      this.allEventHandlers.forEach(handler => {
        try {
          handler(message as unknown as WebSocketEvent)
        } catch (error) {
          this.log('Error in all-event handler:', error)
        }
      })
    } catch (error) {
      this.log('Error parsing message:', error)
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(userId: string): void {
    this.reconnectAttempts++
    this.log(`Scheduling reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
    
    this.reconnectTimer = setTimeout(() => {
      this.log('Attempting to reconnect...')
      this.connect(userId).catch((error) => {
        this.log('Reconnection failed:', error)
      })
    }, this.reconnectInterval)
  }

  /**
   * Emit connection event
   */
  private emitConnectionEvent(state: ConnectionState, userId?: string): void {
    const event: ConnectionEvent = {
      state,
      user_id: userId,
      timestamp: new Date().toISOString(),
    }
    
    // Emit to all event handlers as unknown first, then as WebSocketEvent
    this.allEventHandlers.forEach(handler => {
      try {
        handler(event as unknown as WebSocketEvent)
      } catch (error) {
        this.log('Error in connection event handler:', error)
      }
    })
  }

  /**
   * Debug logging
   */
  private log(...args: unknown[]): void {
    if (this.debug) {
      console.log('[WebSocketService]', ...args)
    }
  }
}
