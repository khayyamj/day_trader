import { useEffect, useState } from 'react'
import { websocketClient } from '@services/websocket'
import type { WebSocketMessage, PriceUpdate } from '@types/index'

export function useRealTimeData() {
  const [latestPrices, setLatestPrices] = useState<Map<string, PriceUpdate>>(new Map())

  useEffect(() => {
    const handleMessage = (message: WebSocketMessage) => {
      switch (message.type) {
        case 'price':
          const priceUpdate = message.data as PriceUpdate
          setLatestPrices((prev) => {
            const newPrices = new Map(prev)
            newPrices.set(priceUpdate.symbol, priceUpdate)
            return newPrices
          })
          break

        case 'trade':
          // Trade messages will trigger refetch in tables
          console.log('New trade received:', message.data)
          break

        case 'signal':
          // Signal messages for chart markers
          console.log('New signal received:', message.data)
          break

        case 'alert':
          // Alert messages for notifications
          console.log('New alert received:', message.data)
          break

        case 'position':
          // Position updates
          console.log('Position update received:', message.data)
          break

        default:
          console.log('Unknown message type:', message.type)
      }
    }

    const unsubscribe = websocketClient.onMessage(handleMessage)

    return () => {
      unsubscribe()
    }
  }, [])

  const getPrice = (symbol: string): number | null => {
    const priceUpdate = latestPrices.get(symbol)
    return priceUpdate ? priceUpdate.price : null
  }

  return {
    latestPrices,
    getPrice,
  }
}
