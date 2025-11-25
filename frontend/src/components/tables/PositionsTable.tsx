import { useEffect, useState } from 'react'
import { positionsAPI } from '@services/api'
import { useRealTimeData } from '@hooks/useRealTimeData'
import type { Position } from '@types/index'

export default function PositionsTable() {
  const [positions, setPositions] = useState<Position[]>([])
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { getPrice } = useRealTimeData()

  useEffect(() => {
    fetchPositions()
  }, [])

  const fetchPositions = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await positionsAPI.getAll()
      setPositions(data.filter((p) => p.status === 'open'))
    } catch (err) {
      console.error('Error fetching positions:', err)
      setError('Failed to load positions')
    } finally {
      setIsLoading(false)
    }
  }

  const calculatePnL = (position: Position) => {
    const currentPrice = getPrice(position.symbol) ?? position.current_price
    const pnl = (currentPrice - position.entry_price) * position.quantity
    const pnlPercent = ((currentPrice - position.entry_price) / position.entry_price) * 100
    return { pnl, pnlPercent, currentPrice }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading positions...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500">No open positions</div>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Symbol
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Qty
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Entry
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Current
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              P&L
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              P&L%
            </th>
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {positions.map((position) => {
            const { pnl, pnlPercent, currentPrice } = calculatePnL(position)
            const isExpanded = expandedId === position.id
            const pnlColor = pnl >= 0 ? 'text-green-600' : 'text-red-600'

            return (
              <>
                <tr key={position.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                    {position.symbol}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 text-right">
                    {position.quantity}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 text-right">
                    {formatCurrency(position.entry_price)}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 text-right">
                    {formatCurrency(currentPrice)}
                  </td>
                  <td className={`px-3 py-2 whitespace-nowrap text-sm font-semibold text-right ${pnlColor}`}>
                    {formatCurrency(pnl)}
                  </td>
                  <td className={`px-3 py-2 whitespace-nowrap text-sm font-semibold text-right ${pnlColor}`}>
                    {formatPercent(pnlPercent)}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-center">
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : position.id)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      {isExpanded ? '▲' : '▼'}
                    </button>
                  </td>
                </tr>
                {isExpanded && (
                  <tr key={`${position.id}-details`}>
                    <td colSpan={7} className="px-3 py-3 bg-gray-50">
                      <div className="text-sm space-y-2">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="font-medium text-gray-700">Entry Time:</span>
                            <span className="ml-2 text-gray-900">
                              {new Date(position.entry_time).toLocaleString()}
                            </span>
                          </div>
                          {position.stop_loss && (
                            <div>
                              <span className="font-medium text-gray-700">Stop Loss:</span>
                              <span className="ml-2 text-gray-900">
                                {formatCurrency(position.stop_loss)}
                              </span>
                            </div>
                          )}
                          {position.take_profit && (
                            <div>
                              <span className="font-medium text-gray-700">Take Profit:</span>
                              <span className="ml-2 text-gray-900">
                                {formatCurrency(position.take_profit)}
                              </span>
                            </div>
                          )}
                          {position.entry_reason && (
                            <div className="col-span-2">
                              <span className="font-medium text-gray-700">Entry Reason:</span>
                              <span className="ml-2 text-gray-900">{position.entry_reason}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
