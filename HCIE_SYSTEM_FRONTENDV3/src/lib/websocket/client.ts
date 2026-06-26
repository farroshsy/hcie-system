/**
 * WebSocket Client for Real-Time Updates
 * 
 * Provides real-time connection to HCIE backend for:
 * - Projection updates
 * - Learning events
 * - System status
 * 
 * Uses WebSocket protocol with automatic reconnection
 */

type WebSocketMessageHandler = (data: any) => void;
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketClientConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: WebSocketMessageHandler;
  onStatusChange?: (status: ConnectionStatus) => void;
}

/**
 * Resolve any configured WS URL to a SAME-ORIGIN ws/wss URL in the browser,
 * preserving the path. This makes WebSockets work through any tunnel/proxy and
 * be secure under HTTPS (wss), instead of the broken build-time ws://localhost.
 * The gateway proxies /ws (Upgrade) to the stream service.
 */
function resolveSameOriginWs(configUrl: string): string {
  if (typeof window === 'undefined' || !window.location?.host) return configUrl;
  let path = '/ws/connections';
  try {
    const u = new URL(configUrl, window.location.origin);
    if (u.pathname && u.pathname !== '/') path = u.pathname + (u.search || '');
  } catch {
    /* keep default path */
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${path}`;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketClientConfig;
  private reconnectAttempts: number = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private status: ConnectionStatus = 'disconnected';
  private messageHandlers: Map<string, Set<WebSocketMessageHandler>> = new Map();

  constructor(config: WebSocketClientConfig) {
    this.config = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      ...config,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.setStatus('connecting');

    try {
      this.ws = new WebSocket(resolveSameOriginWs(this.config.url));

      this.ws.onopen = () => {
        this.setStatus('connected');
        this.reconnectAttempts = 0;
        console.log('[WebSocket] Connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
          
          if (this.config.onMessage) {
            this.config.onMessage(message);
          }
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      this.ws.onclose = (event) => {
        this.setStatus('disconnected');
        console.log('[WebSocket] Disconnected:', event.code, event.reason);
        
        // Attempt reconnection
        if (this.reconnectAttempts < this.config.maxReconnectAttempts!) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        this.setStatus('error');
        console.error('[WebSocket] Error:', error);
      };
    } catch (error) {
      this.setStatus('error');
      console.error('[WebSocket] Connection failed:', error);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.setStatus('disconnected');
    this.reconnectAttempts = 0;
  }

  /**
   * Send message to WebSocket server
   */
  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WebSocket] Cannot send message: not connected');
    }
  }

  /**
   * Register message handler for specific message type
   */
  on(messageType: string, handler: WebSocketMessageHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    this.messageHandlers.get(messageType)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.messageHandlers.get(messageType)?.delete(handler);
    };
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(message: any): void {
    const { type, data } = message;
    
    if (type && this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type)!;
      handlers.forEach(handler => handler(data));
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval! * Math.min(this.reconnectAttempts, 5);
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  /**
   * Update connection status
   */
  private setStatus(status: ConnectionStatus): void {
    if (this.status !== status) {
      this.status = status;
      if (this.config.onStatusChange) {
        this.config.onStatusChange(status);
      }
    }
  }
}

// Create singleton instance
let wsClientInstance: WebSocketClient | null = null;

export function createWebSocketClient(config: WebSocketClientConfig): WebSocketClient {
  if (!wsClientInstance) {
    wsClientInstance = new WebSocketClient(config);
  }
  return wsClientInstance;
}

export function getWebSocketClient(): WebSocketClient {
  if (!wsClientInstance) {
    throw new Error('WebSocket client not initialized. Call createWebSocketClient first.');
  }
  return wsClientInstance;
}
