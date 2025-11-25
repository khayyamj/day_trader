export default function Header() {
  return (
    <header className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Trading Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-600">Portfolio Value</p>
            <p className="text-xl font-bold text-gray-900">$0.00</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              Paused
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
