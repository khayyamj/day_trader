import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from '@components/layout/Dashboard'
import AlertToast from '@components/alerts/AlertToast'

function App() {
  return (
    <Router>
      <AlertToast />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  )
}

export default App
