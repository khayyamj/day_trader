import { useEffect, useState } from 'react'
import { tradesAPI } from '@services/api'
import type { Trade } from '@types/index'

export default function TradesTable() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [limit] = useState(20)

  useEffect(() => {
    fetchTrades()
  }, [])

  const fetchTrades = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await tradesAPI.getRecent(limit)
      setTrades(data)
    } catch (err) {
      console.error('Error fetching trades:', err)
      setError('Failed to load trades')
    } finally {
      setIsLoading(false)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading trades...</div>
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

  if (trades.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500">No trades yet</div>
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
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Entry
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Exit
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Time
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              P&L
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              P&L%
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {trades.map((trade) => {
            const pnlColor = (trade.pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
            const typeColor = trade.type === 'buy' ? 'text-green-600' : 'text-red-600'

            return (
              <tr key={trade.id} className="hover:bg-gray-50">
                <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                  {trade.symbol}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-center">
                  <span
                    className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      trade.type === 'buy' ? 'bg-green-100' : 'bg-red-100'
                    } ${typeColor}`}
                  >
                    {trade.type.toUpperCase()}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 text-right">
                  {formatCurrency(trade.entry_price)}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 text-right">
                  {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">
                  {formatDateTime(trade.entry_time)}
                </td>
                <td className={`px-3 py-2 whitespace-nowrap text-sm font-semibold text-right ${pnlColor}`}>
                  {trade.pnl !== undefined ? formatCurrency(trade.pnl) : '-'}
                </td>
                <td className={`px-3 py-2 whitespace-nowrap text-sm font-semibold text-right ${pnlColor}`}>
                  {trade.pnl_percent !== undefined
                    ? `${trade.pnl_percent >= 0 ? '+' : ''}${trade.pnl_percent.toFixed(2)}%`
                    : '-'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <div className="px-3 py-3 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
        <div className="text-sm text-gray-700">
          Showing {trades.length} of last {limit} trades
        </div>
        <button
          onClick={fetchTrades}
          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>
    </div>
  )
}
