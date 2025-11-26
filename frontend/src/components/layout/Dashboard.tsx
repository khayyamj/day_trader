import { useState } from 'react'
import Header from './Header'
import SidePanel from './SidePanel'
import BottomPanel from './BottomPanel'
import CandlestickChart from '../charts/CandlestickChart'
import StockSelector from '../charts/StockSelector'
import { useWebSocket } from '@hooks/useWebSocket'
import { useKeyboardShortcuts } from '@hooks/useKeyboardShortcuts'

export default function Dashboard() {
  const [selectedStock, setSelectedStock] = useState('AAPL')
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const { isConnected } = useWebSocket()

  useKeyboardShortcuts({
    onRefresh: () => {
      setRefreshTrigger((prev) => prev + 1)
      console.log('Dashboard refresh triggered')
    },
    onPauseToggle: () => {
      console.log('Pause toggle triggered (handled by StrategyPanel)')
    },
  })

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-screen p-4">
        <div className="lg:col-span-4">
          <Header />
        </div>

        <div className="lg:col-span-3 flex flex-col gap-4">
          <div className="bg-white rounded-lg shadow p-4 flex-grow">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Price Chart</h2>
              <StockSelector selectedStock={selectedStock} onStockChange={setSelectedStock} />
            </div>
            <CandlestickChart symbol={selectedStock} />
          </div>

          <BottomPanel />
        </div>

        <div className="lg:col-span-1">
          <SidePanel />
        </div>
      </div>
    </div>
  )
}
