// src/services/websocket.js
/**
 * WebSocket connection manager for real-time agent communication.
 * 
 * This class handles:
 * - Establishing and maintaining WebSocket connection
 * - Reconnection logic if connection drops
 * - Message parsing and routing to handlers
 * - Sending messages to backend
 * 
 * The key insight here is that we want the rest of our app to not
 * worry about connection details. Components just register handlers
 * for message types they care about.
 */

class AgentWebSocket {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.ws = null;
    this.messageHandlers = new Map();
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  /**
   * Connect to the WebSocket server.
   * 
   * This establishes the connection and sets up event handlers.
   * If the connection drops, we'll automatically try to reconnect.
   */
  connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return; // Already connected or connecting
    }

    this.isConnecting = true;
    const wsUrl = `ws://localhost:8000/ws/${this.sessionId}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      
      // Notify handlers about connection
      this.notifyHandlers('connected', { sessionId: this.sessionId });
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.notifyHandlers('error', { error });
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.isConnecting = false;
      
      // Try to reconnect if we haven't exceeded max attempts
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
      } else {
        this.notifyHandlers('connection_failed', {
          message: 'Failed to connect after multiple attempts'
        });
      }
    };
  }

  /**
   * Handle an incoming message by routing it to registered handlers.
   * 
   * Each message has a 'type' field that tells us what kind of message it is.
   * We call all handlers that are registered for that type.
   */
  handleMessage(message) {
    const type = message.type;
    console.log('Received message:', type, message);

    // Call all handlers registered for this message type
    const handlers = this.messageHandlers.get(type) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error(`Error in handler for ${type}:`, error);
      }
    });
  }

  /**
   * Register a handler for a specific message type.
   * 
   * Components use this to say "when you receive a message of type X,
   * call my function". This is how the WorkflowPanel knows when
   * approval is required, for example.
   */
  on(messageType, handler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType).push(handler);

    // Return a cleanup function that components can call to unregister
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    };
  }

  /**
   * Send a message to the backend.
   * 
   * This is how we send approval decisions, start analysis, etc.
   */
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected, cannot send message');
    }
  }

  /**
   * Notify handlers of an event.
   * 
   * This is used internally to broadcast connection events.
   */
  notifyHandlers(type, data) {
    const handlers = this.messageHandlers.get(type) || [];
    handlers.forEach(handler => handler(data));
  }

  /**
   * Close the connection.
   */
  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default AgentWebSocket;
