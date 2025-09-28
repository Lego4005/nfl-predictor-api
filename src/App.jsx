import React, { useState } from 'react';
import NFLDashboard from './components/NFLDashboard.current.jsx';
import { NFEloDashboard } from "./components/nfelo-dashboard";
import ExpertObservatorySimple from './components/admin/ExpertObservatorySimple';
import { Brain, BarChart3, Grid } from "lucide-react";
import './index.css';

function App() {
  const [showAdmin, setShowAdmin] = useState(false);
  const [dashboardType, setDashboardType] = useState("default"); // 'default', 'nfelo', or 'grid'

  // Check URL for admin mode
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("admin") === "true") {
      setShowAdmin(true);
    }
    if (urlParams.get("dashboard") === "nfelo") {
      setDashboardType("nfelo");
    }
  }, []);

  const cycleDashboard = () => {
    if (dashboardType === "default") {
      setDashboardType("nfelo");
    } else if (dashboardType === "nfelo") {
      setDashboardType("grid");
    } else {
      setDashboardType("default");
    }
  };

  const getDashboardTitle = () => {
    if (dashboardType === "default") return "Switch to NFElo Dashboard";
    if (dashboardType === "nfelo") return "Switch to Grid Dashboard";
    return "Switch to Default Dashboard";
  };

  const getDashboardIcon = () => {
    if (dashboardType === "default") return <BarChart3 size={20} />;
    if (dashboardType === "nfelo") return <Grid size={20} />;
    return <BarChart3 size={20} />;
  };

  return (
    <div className="App">
      {/* Control Icons */}
      <div className="fixed top-4 right-4 z-50 flex gap-2">
        {/* Dashboard Toggle */}
        <button
          onClick={cycleDashboard}
          className="p-2 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg transition-all duration-200 hover:scale-110"
          title={getDashboardTitle()}
        >
          {getDashboardIcon()}
        </button>

        <button
          onClick={() => setShowAdmin(!showAdmin)}
          className="p-2 rounded-full bg-purple-600 hover:bg-purple-700 text-white shadow-lg transition-all duration-200 hover:scale-110"
          title={showAdmin ? "Back to Dashboard" : "Admin Mode"}
        >
          <Brain size={20} />
        </button>
      </div>

      {showAdmin ? (
        <ExpertObservatorySimple />
      ) : dashboardType === "nfelo" ? (
        <NFEloDashboard />
      ) : dashboardType === "grid" ? (
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-4">
            Grid Dashboard (Placeholder)
          </h1>
          <p>This would be a third dashboard style.</p>
        </div>
      ) : (
        <NFLDashboard />
      )}
    </div>
  );
}

export default App;