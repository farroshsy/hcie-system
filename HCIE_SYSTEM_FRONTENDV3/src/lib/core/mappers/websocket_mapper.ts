/**
 * WebSocket Mapper Implementation
 * 
 * Note: WebSocket mapper is minimal as WebSocket messages are typically handled directly
 * by the WebSocket service without extensive mapping. This mapper provides basic
 * validation and conversion utilities if needed.
 */

import type {
  WebSocketMessage,
} from '../interfaces'

/**
 * WebSocket Mapper Implementation
 */
export class WebSocketMapper {
  /**
   * Parse raw WebSocket message
   */
  parseRawMessage(raw: string): WebSocketMessage<unknown> {
    try {
      return JSON.parse(raw) as WebSocketMessage<unknown>
    } catch (error) {
      throw new Error('Invalid WebSocket message format')
    }
  }

  /**
   * Serialize WebSocket message
   */
  serializeMessage(message: WebSocketMessage<unknown>): string {
    return JSON.stringify(message)
  }

  /**
   * Create WebSocket message
   */
  createMessage<T>(type: string, data: T, id?: string): WebSocketMessage<T> {
    return {
      type,
      data,
      timestamp: new Date().toISOString(),
      id,
    }
  }
}
