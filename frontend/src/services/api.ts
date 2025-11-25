import axios from 'axios'
import type { OHLCVData, Position, Trade, Strategy, Signal, IndicatorData } from '@types/index'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const marketDataAPI = {
  getOHLCV: async (symbol: string, interval: string = '1d', limit: number = 100): Promise<OHLCVData[]> => {
    const response = await api.get(`/api/market-data/ohlcv`, {
      params: { symbol, interval, limit },
    })
    return response.data
  },
}

export const positionsAPI = {
  getAll: async (): Promise<Position[]> => {
    const response = await api.get('/api/positions')
    return response.data
  },
}

export const tradesAPI = {
  getRecent: async (limit: number = 20): Promise<Trade[]> => {
    const response = await api.get('/api/trades', {
      params: { limit, sort: 'timestamp:desc' },
    })
    return response.data
  },
}

export const strategyAPI = {
  getAll: async (): Promise<Strategy[]> => {
    const response = await api.get('/api/strategies')
    return response.data
  },

  activate: async (id: number): Promise<Strategy> => {
    const response = await api.post(`/api/strategies/${id}/activate`)
    return response.data
  },

  pause: async (id: number): Promise<Strategy> => {
    const response = await api.post(`/api/strategies/${id}/pause`)
    return response.data
  },

  updateParameters: async (id: number, parameters: Record<string, unknown>): Promise<Strategy> => {
    const response = await api.put(`/api/strategies/${id}/parameters`, parameters)
    return response.data
  },
}

export const indicatorsAPI = {
  calculate: async (
    symbol: string,
    indicators: string[],
    params?: Record<string, unknown>
  ): Promise<Record<string, IndicatorData[]>> => {
    const response = await api.get('/api/indicators/calculate', {
      params: { symbol, indicators: indicators.join(','), ...params },
    })
    return response.data
  },
}

export default api
