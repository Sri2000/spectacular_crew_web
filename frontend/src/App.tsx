import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Layout from './components/Layout';
import AnalystDashboard from './pages/AnalystDashboard';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import DataUpload from './pages/DataUpload';
import SimulateDashboard from './pages/SimulateDashboard';
import ScenarioDetails from './pages/ScenarioDetails';
import StoreTransfer from './pages/StoreTransfer';
import FleetDashboard from './pages/FleetDashboard';
import StoreDashboard from './pages/StoreDashboard';
import { setAuthToken } from './services/api';

function App() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      setAuthToken(storedToken);
      // Set timer to logout after 30 minutes
      const timer = setTimeout(() => {
        logout();
      }, 30 * 60 * 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleLogin = (newToken: string) => {
    setToken(newToken);
    setAuthToken(newToken);
    localStorage.setItem('token', newToken);
    // Set timer to logout after 30 minutes
    setTimeout(() => {
      logout();
    }, 30 * 60 * 1000);
  };

  const logout = () => {
    setToken(null);
    setAuthToken(null);
    localStorage.removeItem('token');
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <Layout onLogout={logout}>
        <Routes>
          <Route path="/" element={<AnalystDashboard />} />
          <Route path="/executive" element={<ExecutiveDashboard />} />
          <Route path="/upload" element={<DataUpload />} />
          <Route path="/simulate" element={<SimulateDashboard />} />
          <Route path="/scenario/:id" element={<ScenarioDetails />} />
          <Route path="/transfers" element={<StoreTransfer />} />
          <Route path="/dashboard" element={<FleetDashboard />} />
          <Route path="/store/:storeId" element={<StoreDashboard />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
