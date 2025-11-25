export interface Position {
  id: number
  symbol: string
  quantity: number
  entry_price: number
  current_price: number
  entry_time: string
  stop_loss?: number
  take_profit?: number
  entry_reason?: string
  status: 'open' | 'closed'
}

export interface Trade {
  id: number
  symbol: string
  type: 'buy' | 'sell'
  entry_price: number
  exit_price?: number
  quantity: number
  entry_time: string
  exit_time?: string
  pnl?: number
  pnl_percent?: number
  exit_reason?: string
}

export interface Strategy {
  id: number
  name: string
  status: 'active' | 'paused' | 'error' | 'warming'
  consecutive_losses: number
  is_warming_up: boolean
  parameters: StrategyParameters
}

export interface StrategyParameters {
  ema_fast_period: number
  ema_slow_period: number
  rsi_period: number
  rsi_overbought: number
  rsi_oversold: number
  stop_loss_percent: number
  take_profit_percent: number
  max_consecutive_losses: number
  warmup_bars: number
}

export interface Signal {
  id: number
  symbol: string
  signal_type: 'buy' | 'sell'
  timestamp: string
  price: number
  indicators: {
    ema_fast?: number
    ema_slow?: number
    rsi?: number
  }
  executed: boolean
}

export interface Alert {
  id: number
  type: 'info' | 'warning' | 'error' | 'success'
  message: string
  timestamp: string
  details?: string
}

export interface OHLCVData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface IndicatorData {
  timestamp: string
  value: number
}

export interface PriceUpdate {
  symbol: string
  price: number
  timestamp: string
}

export interface WebSocketMessage {
  type: 'price' | 'trade' | 'signal' | 'alert' | 'position'
  data: PriceUpdate | Trade | Signal | Alert | Position
}
