export default function SidePanel() {
  return (
    <div className="flex flex-col gap-4">
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Control</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Status</span>
            <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
              Paused
            </span>
          </div>
          <button className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            Activate
          </button>
          <button className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
            Configure
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4 flex-grow">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Open Positions</h2>
        <div className="flex items-center justify-center bg-gray-50 rounded h-64">
          <p className="text-gray-500">Positions will be implemented in Task 5</p>
        </div>
      </div>
    </div>
  )
}
