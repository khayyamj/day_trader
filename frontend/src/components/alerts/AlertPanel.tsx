import { useState, useEffect } from 'react'
import type { Alert } from '@types/index'

export default function AlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([])

  const addAlert = (alert: Alert) => {
    setAlerts((prev) => [alert, ...prev].slice(0, 20))
  }

  useEffect(() => {
    // Expose addAlert function globally for use by WebSocket handler
    ;(window as any).addDashboardAlert = addAlert

    return () => {
      delete (window as any).addDashboardAlert
    }
  }, [])

  const getAlertIcon = (type: Alert['type']) => {
    const icons = {
      info: 'ℹ️',
      warning: '⚠️',
      error: '❌',
      success: '✅',
    }
    return icons[type]
  }

  const getAlertColor = (type: Alert['type']) => {
    const colors = {
      info: 'bg-blue-50 border-blue-200 text-blue-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      success: 'bg-green-50 border-green-200 text-green-800',
    }
    return colors[type]
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  if (alerts.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        No alerts yet
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`p-3 rounded-lg border ${getAlertColor(alert.type)}`}
        >
          <div className="flex items-start gap-2">
            <span className="text-lg">{getAlertIcon(alert.type)}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium truncate">{alert.message}</p>
                <span className="text-xs whitespace-nowrap">{formatTime(alert.timestamp)}</span>
              </div>
              {alert.details && (
                <p className="text-xs mt-1 opacity-80">{alert.details}</p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
