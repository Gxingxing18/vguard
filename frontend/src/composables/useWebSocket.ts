import { ref, onUnmounted } from 'vue'
import type { WsMessage } from '@/types'

export function useWebSocket(taskType: 'injection' | 'verification') {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const lastMessage = ref<WsMessage | null>(null)
  const error = ref<string | null>(null)

  let pollInterval: ReturnType<typeof setInterval> | null = null
  let pollCallback: (() => Promise<void>) | null = null
  let messageHandler: ((msg: WsMessage) => void) | null = null

  function connect(taskId: string, onMessage: (msg: WsMessage) => void) {
    messageHandler = onMessage
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/${taskType}/${taskId}`
    const socket = new WebSocket(url)

    socket.onopen = () => {
      connected.value = true
      error.value = null
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage
        lastMessage.value = msg
        onMessage(msg)
      } catch {
        // ignore parse errors
      }
    }

    socket.onerror = () => {
      error.value = 'WebSocket connection error'
    }

    socket.onclose = () => {
      connected.value = false
    }

    ws.value = socket

    // Polling fallback after 5 seconds if WS fails
    setTimeout(() => {
      if (!connected.value && pollCallback) {
        startPolling(pollCallback)
      }
    }, 5000)
  }

  function startPolling(callback: () => Promise<void>) {
    pollCallback = callback
    pollInterval = setInterval(callback, 2000)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  function sendPing() {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send('ping')
    }
  }

  function disconnect() {
    stopPolling()
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connected,
    lastMessage,
    error,
    connect,
    disconnect,
    sendPing,
    startPolling,
    stopPolling,
  }
}
