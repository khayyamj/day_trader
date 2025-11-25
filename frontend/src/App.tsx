import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

function DashboardPlaceholder() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Trading Dashboard
        </h1>
        <p className="text-gray-600">
          Dashboard components will be built in upcoming tasks
        </p>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPlaceholder />} />
      </Routes>
    </Router>
  )
}

export default App
