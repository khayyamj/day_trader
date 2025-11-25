import { useState } from 'react'
import TradesTable from '../tables/TradesTable'
import AlertPanel from '../alerts/AlertPanel'

export default function BottomPanel() {
  const [activeTab, setActiveTab] = useState<'trades' | 'alerts'>('trades')

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('trades')}
            className={`text-lg font-semibold pb-2 border-b-2 transition-colors ${
              activeTab === 'trades'
                ? 'text-gray-900 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            Recent Trades
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`text-lg font-semibold pb-2 border-b-2 transition-colors ${
              activeTab === 'alerts'
                ? 'text-gray-900 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            Alerts
          </button>
        </div>
      </div>

      {activeTab === 'trades' ? <TradesTable /> : <AlertPanel />}
    </div>
  )
}
