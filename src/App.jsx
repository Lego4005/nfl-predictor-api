import React, { useState } from 'react';
import NFLDashboard from './components/NFLDashboard.current.jsx';
import ExpertObservatorySimple from './components/admin/ExpertObservatorySimple';
import { Brain } from 'lucide-react';
import './index.css';

function App() {
  const [showAdmin, setShowAdmin] = useState(false);

  // Check URL for admin mode
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('admin') === 'true') {
      setShowAdmin(true);
    }
  }, []);

  return (
    <div className="App">
      {/* Admin Brain Icon */}
      <div className="fixed top-4 right-4 z-50">
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
      ) : (
        <NFLDashboard />
      )}
    </div>
  );
}

export default App;
