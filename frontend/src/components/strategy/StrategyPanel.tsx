import { useEffect, useState } from 'react'
import { strategyAPI } from '@services/api'
import type { Strategy } from '@types/index'
import StrategyConfig from './StrategyConfig'

export default function StrategyPanel() {
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConfigOpen, setIsConfigOpen] = useState(false)
  const [actionLoading, setActionLoading] = useState<'activate' | 'pause' | null>(null)

  useEffect(() => {
    fetchStrategy()
  }, [])

  const fetchStrategy = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const strategies = await strategyAPI.getAll()
      if (strategies.length > 0) {
        setStrategy(strategies[0])
      }
    } catch (err) {
      console.error('Error fetching strategy:', err)
      setError('Failed to load strategy')
    } finally {
      setIsLoading(false)
    }
  }

  const handleActivate = async () => {
    if (!strategy) return
    setActionLoading('activate')
    try {
      const updated = await strategyAPI.activate(strategy.id)
      setStrategy(updated)
    } catch (err) {
      console.error('Error activating strategy:', err)
      setError('Failed to activate strategy')
    } finally {
      setActionLoading(null)
    }
  }

  const handlePause = async () => {
    if (!strategy) return
    setActionLoading('pause')
    try {
      const updated = await strategyAPI.pause(strategy.id)
      setStrategy(updated)
    } catch (err) {
      console.error('Error pausing strategy:', err)
      setError('Failed to pause strategy')
    } finally {
      setActionLoading(null)
    }
  }

  const handleConfigSave = async (parameters: Record<string, unknown>) => {
    if (!strategy) return
    try {
      const updated = await strategyAPI.updateParameters(strategy.id, parameters)
      setStrategy(updated)
      setIsConfigOpen(false)
    } catch (err) {
      console.error('Error updating strategy parameters:', err)
      throw err
    }
  }

  const getStatusBadge = (status: Strategy['status']) => {
    const badges = {
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      warming: 'bg-blue-100 text-blue-800',
    }
    const labels = {
      active: 'Active',
      paused: 'Paused',
      error: 'Error',
      warming: 'Warming Up',
    }
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${badges[status]}`}>
        {labels[status]}
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Control</h2>
        <div className="text-center text-gray-600 py-4">Loading strategy...</div>
      </div>
    )
  }

  if (error || !strategy) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Control</h2>
        <div className="text-center text-red-600 py-4">{error || 'No strategy found'}</div>
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Control</h2>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Strategy</span>
              {getStatusBadge(strategy.status)}
            </div>
            <p className="text-xs text-gray-500">{strategy.name}</p>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Consecutive Losses</span>
            <span className={`text-sm font-semibold ${strategy.consecutive_losses > 0 ? 'text-red-600' : 'text-gray-900'}`}>
              {strategy.consecutive_losses} / {strategy.parameters.max_consecutive_losses}
            </span>
          </div>

          {strategy.is_warming_up && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Warm-up Status</span>
              <span className="text-sm font-medium text-blue-600">In Progress</span>
            </div>
          )}

          <div className="pt-2 space-y-2">
            {strategy.status === 'paused' || strategy.status === 'error' ? (
              <button
                onClick={handleActivate}
                disabled={actionLoading === 'activate'}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'activate' ? 'Activating...' : 'Activate'}
              </button>
            ) : (
              <button
                onClick={handlePause}
                disabled={actionLoading === 'pause'}
                className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'pause' ? 'Pausing...' : 'Pause'}
              </button>
            )}

            <button
              onClick={() => setIsConfigOpen(true)}
              className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Configure
            </button>
          </div>
        </div>
      </div>

      {isConfigOpen && (
        <StrategyConfig
          strategy={strategy}
          onClose={() => setIsConfigOpen(false)}
          onSave={handleConfigSave}
        />
      )}
    </>
  )
}
