import PositionsTable from '../tables/PositionsTable'
import StrategyPanel from '../strategy/StrategyPanel'

export default function SidePanel() {
  return (
    <div className="flex flex-col gap-4">
      <StrategyPanel />

      <div className="bg-white rounded-lg shadow p-4 flex-grow overflow-hidden">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Open Positions</h2>
        <div className="overflow-y-auto max-h-96">
          <PositionsTable />
        </div>
      </div>
    </div>
  )
}
