import Header from './Header'
import SidePanel from './SidePanel'
import BottomPanel from './BottomPanel'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-screen p-4">
        <div className="lg:col-span-4">
          <Header />
        </div>

        <div className="lg:col-span-3 flex flex-col gap-4">
          <div className="bg-white rounded-lg shadow p-4 flex-grow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Price Chart</h2>
            <div className="h-96 flex items-center justify-center bg-gray-50 rounded">
              <p className="text-gray-500">Chart will be implemented in Task 3</p>
            </div>
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
