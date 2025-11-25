import { useEffect, useState } from 'react'
import { websocketClient } from '@services/websocket'

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Event | null>(null)

  useEffect(() => {
    const handleConnect = () => {
      setIsConnected(true)
      setError(null)
    }

    const handleDisconnect = () => {
      setIsConnected(false)
    }

    const handleError = (err: Event) => {
      setError(err)
    }

    const unsubConnect = websocketClient.onConnect(handleConnect)
    const unsubDisconnect = websocketClient.onDisconnect(handleDisconnect)
    const unsubError = websocketClient.onError(handleError)

    websocketClient.connect()

    return () => {
      unsubConnect()
      unsubDisconnect()
      unsubError()
    }
  }, [])

  return { isConnected, error, client: websocketClient }
}
