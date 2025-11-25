import TradesTable from '../tables/TradesTable'

export default function BottomPanel() {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Trades</h2>
      <TradesTable />
    </div>
  )
}
