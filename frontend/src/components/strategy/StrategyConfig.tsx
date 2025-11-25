import { useState } from 'react'
import type { Strategy, StrategyParameters } from '@types/index'

interface StrategyConfigProps {
  strategy: Strategy
  onClose: () => void
  onSave: (parameters: Record<string, unknown>) => Promise<void>
}

export default function StrategyConfig({ strategy, onClose, onSave }: StrategyConfigProps) {
  const [parameters, setParameters] = useState<StrategyParameters>(strategy.parameters)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSaving, setIsSaving] = useState(false)

  const validateParameters = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (parameters.ema_fast_period < 2 || parameters.ema_fast_period > 200) {
      newErrors.ema_fast_period = 'EMA Fast period must be between 2 and 200'
    }

    if (parameters.ema_slow_period < 2 || parameters.ema_slow_period > 200) {
      newErrors.ema_slow_period = 'EMA Slow period must be between 2 and 200'
    }

    if (parameters.ema_fast_period >= parameters.ema_slow_period) {
      newErrors.ema_fast_period = 'EMA Fast must be less than EMA Slow'
    }

    if (parameters.rsi_period < 2 || parameters.rsi_period > 50) {
      newErrors.rsi_period = 'RSI period must be between 2 and 50'
    }

    if (parameters.rsi_overbought < 50 || parameters.rsi_overbought > 100) {
      newErrors.rsi_overbought = 'RSI overbought must be between 50 and 100'
    }

    if (parameters.rsi_oversold < 0 || parameters.rsi_oversold > 50) {
      newErrors.rsi_oversold = 'RSI oversold must be between 0 and 50'
    }

    if (parameters.stop_loss_percent < 0 || parameters.stop_loss_percent > 100) {
      newErrors.stop_loss_percent = 'Stop loss must be between 0 and 100%'
    }

    if (parameters.take_profit_percent < 0 || parameters.take_profit_percent > 100) {
      newErrors.take_profit_percent = 'Take profit must be between 0 and 100%'
    }

    if (parameters.max_consecutive_losses < 1 || parameters.max_consecutive_losses > 10) {
      newErrors.max_consecutive_losses = 'Max consecutive losses must be between 1 and 10'
    }

    if (parameters.warmup_bars < 0 || parameters.warmup_bars > 200) {
      newErrors.warmup_bars = 'Warmup bars must be between 0 and 200'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateParameters()) {
      return
    }

    setIsSaving(true)
    try {
      await onSave(parameters)
    } catch (err) {
      setErrors({ _general: 'Failed to update strategy parameters' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleChange = (field: keyof StrategyParameters, value: number) => {
    setParameters((prev) => ({ ...prev, [field]: value }))
    setErrors((prev) => {
      const newErrors = { ...prev }
      delete newErrors[field]
      delete newErrors._general
      return newErrors
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Strategy Configuration</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isSaving}
            >
              <span className="text-2xl">&times;</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {errors._general && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {errors._general}
            </div>
          )}

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">EMA Indicators</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  EMA Fast Period
                </label>
                <input
                  type="number"
                  value={parameters.ema_fast_period}
                  onChange={(e) => handleChange('ema_fast_period', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.ema_fast_period ? 'border-red-500' : 'border-gray-300'}`}
                  min="2"
                  max="200"
                  disabled={isSaving}
                />
                {errors.ema_fast_period && (
                  <p className="text-xs text-red-600 mt-1">{errors.ema_fast_period}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  EMA Slow Period
                </label>
                <input
                  type="number"
                  value={parameters.ema_slow_period}
                  onChange={(e) => handleChange('ema_slow_period', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.ema_slow_period ? 'border-red-500' : 'border-gray-300'}`}
                  min="2"
                  max="200"
                  disabled={isSaving}
                />
                {errors.ema_slow_period && (
                  <p className="text-xs text-red-600 mt-1">{errors.ema_slow_period}</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">RSI Indicator</h3>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">RSI Period</label>
                <input
                  type="number"
                  value={parameters.rsi_period}
                  onChange={(e) => handleChange('rsi_period', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.rsi_period ? 'border-red-500' : 'border-gray-300'}`}
                  min="2"
                  max="50"
                  disabled={isSaving}
                />
                {errors.rsi_period && (
                  <p className="text-xs text-red-600 mt-1">{errors.rsi_period}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Overbought
                </label>
                <input
                  type="number"
                  value={parameters.rsi_overbought}
                  onChange={(e) => handleChange('rsi_overbought', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.rsi_overbought ? 'border-red-500' : 'border-gray-300'}`}
                  min="50"
                  max="100"
                  disabled={isSaving}
                />
                {errors.rsi_overbought && (
                  <p className="text-xs text-red-600 mt-1">{errors.rsi_overbought}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Oversold</label>
                <input
                  type="number"
                  value={parameters.rsi_oversold}
                  onChange={(e) => handleChange('rsi_oversold', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.rsi_oversold ? 'border-red-500' : 'border-gray-300'}`}
                  min="0"
                  max="50"
                  disabled={isSaving}
                />
                {errors.rsi_oversold && (
                  <p className="text-xs text-red-600 mt-1">{errors.rsi_oversold}</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Risk Management</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stop Loss %
                </label>
                <input
                  type="number"
                  value={parameters.stop_loss_percent}
                  onChange={(e) => handleChange('stop_loss_percent', parseFloat(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.stop_loss_percent ? 'border-red-500' : 'border-gray-300'}`}
                  min="0"
                  max="100"
                  step="0.1"
                  disabled={isSaving}
                />
                {errors.stop_loss_percent && (
                  <p className="text-xs text-red-600 mt-1">{errors.stop_loss_percent}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Take Profit %
                </label>
                <input
                  type="number"
                  value={parameters.take_profit_percent}
                  onChange={(e) => handleChange('take_profit_percent', parseFloat(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.take_profit_percent ? 'border-red-500' : 'border-gray-300'}`}
                  min="0"
                  max="100"
                  step="0.1"
                  disabled={isSaving}
                />
                {errors.take_profit_percent && (
                  <p className="text-xs text-red-600 mt-1">{errors.take_profit_percent}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Consecutive Losses
                </label>
                <input
                  type="number"
                  value={parameters.max_consecutive_losses}
                  onChange={(e) =>
                    handleChange('max_consecutive_losses', parseInt(e.target.value))
                  }
                  className={`w-full px-3 py-2 border rounded-md ${errors.max_consecutive_losses ? 'border-red-500' : 'border-gray-300'}`}
                  min="1"
                  max="10"
                  disabled={isSaving}
                />
                {errors.max_consecutive_losses && (
                  <p className="text-xs text-red-600 mt-1">{errors.max_consecutive_losses}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Warmup Bars
                </label>
                <input
                  type="number"
                  value={parameters.warmup_bars}
                  onChange={(e) => handleChange('warmup_bars', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md ${errors.warmup_bars ? 'border-red-500' : 'border-gray-300'}`}
                  min="0"
                  max="200"
                  disabled={isSaving}
                />
                {errors.warmup_bars && (
                  <p className="text-xs text-red-600 mt-1">{errors.warmup_bars}</p>
                )}
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
