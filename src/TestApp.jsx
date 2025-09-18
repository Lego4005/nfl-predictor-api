import React from 'react';

function TestApp() {
  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: '#333', fontSize: '2rem' }}>Test App is Working!</h1>
      <p style={{ color: '#666' }}>If you can see this, React is rendering properly.</p>
      <button style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
        Click Me
      </button>
    </div>
  );
}

export default TestApp;