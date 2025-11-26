type MessageHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private subscriptions: Set<string> = new Set();

  connect(url = 'ws://localhost:8000/ws') {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;

      // 기존 구독 복구
      this.subscriptions.forEach((stockCode) => {
        this.subscribe(stockCode);
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(url);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private attemptReconnect(url: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(url), this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private handleMessage(data: any) {
    const { type, stock_code } = data;

    // 타입별 핸들러 실행
    if (type && this.handlers.has(type)) {
      this.handlers.get(type)?.forEach((handler) => handler(data));
    }

    // 종목별 핸들러 실행
    if (stock_code && this.handlers.has(`stock:${stock_code}`)) {
      this.handlers.get(`stock:${stock_code}`)?.forEach((handler) => handler(data));
    }

    // 전체 핸들러 실행
    if (this.handlers.has('*')) {
      this.handlers.get('*')?.forEach((handler) => handler(data));
    }
  }

  subscribe(stockCode: string) {
    this.subscriptions.add(stockCode);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        stock_code: stockCode,
      }));
    }
  }

  unsubscribe(stockCode: string) {
    this.subscriptions.delete(stockCode);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'unsubscribe',
        stock_code: stockCode,
      }));
    }
  }

  on(event: string, handler: MessageHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)?.add(handler);

    // cleanup 함수 반환
    return () => {
      this.handlers.get(event)?.delete(handler);
    };
  }

  off(event: string, handler: MessageHandler) {
    this.handlers.get(event)?.delete(handler);
  }

  ping() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'ping' }));
    }
  }

  disconnect() {
    this.subscriptions.clear();
    this.handlers.clear();
    this.ws?.close();
    this.ws = null;
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
export default wsService;
