import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { websocketClient } from '@services/websocket'
import type { WebSocketMessage, PriceUpdate, Alert, Trade, Signal } from '@types/index'

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
          const trade = message.data as Trade
          toast.success(`Trade executed: ${trade.type.toUpperCase()} ${trade.symbol} @ ${trade.entry_price}`)
          if ((window as any).addDashboardAlert) {
            ;(window as any).addDashboardAlert({
              id: Date.now(),
              type: 'success',
              message: `Trade executed: ${trade.type.toUpperCase()} ${trade.symbol}`,
              timestamp: new Date().toISOString(),
              details: `Price: $${trade.entry_price}`,
            })
          }
          break

        case 'signal':
          const signal = message.data as Signal
          toast(`Signal: ${signal.signal_type.toUpperCase()} ${signal.symbol}`, {
            icon: signal.signal_type === 'buy' ? '📈' : '📉',
          })
          if ((window as any).addDashboardAlert) {
            ;(window as any).addDashboardAlert({
              id: Date.now(),
              type: 'info',
              message: `Signal generated: ${signal.signal_type.toUpperCase()} ${signal.symbol}`,
              timestamp: new Date().toISOString(),
              details: `Price: $${signal.price}`,
            })
          }
          break

        case 'alert':
          const alert = message.data as Alert
          const toastFn = alert.type === 'error' ? toast.error :
                         alert.type === 'warning' ? toast :
                         alert.type === 'success' ? toast.success :
                         toast
          toastFn(alert.message)

          if ((window as any).addDashboardAlert) {
            ;(window as any).addDashboardAlert(alert)
          }
          break

        case 'position':
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
