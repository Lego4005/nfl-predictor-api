import React, { useState } from 'react';

const NFEloDashboard = () => {
  const [week, setWeek] = useState(4);
  
  // Simplified structure matching real nfeloapp.com
  const columns = [
    {
      title: "Thursday, Sep 25",
      evCount: 0,
      games: [{ id: "sea-ari", time: "08:15 PM", away: "SEA (2-1)", home: "ARI (2-1)", score: "23-20", final: true }]
    },
    {
      title: "Sunday, Sep 28", subtitle: "early", evCount: 1,
      games: [
        { id: "min-pit", time: "09:30 AM", away: "MIN (2-1)", home: "PIT (2-1)" },
        { id: "cle-det", time: "01:00 PM", away: "CLE (1-2)", home: "DET (2-1)", hasEV: true }
      ]
    },
    {
      title: "Sunday, Sep 28", subtitle: "late", evCount: 1,
      games: [{ id: "gb-dal", time: "08:20 PM", away: "GB (2-1)", home: "DAL (1-2)", hasEV: true }]
    },
    {
      title: "Monday, Sep 29", evCount: 0,
      games: [{ id: "nyj-mia", time: "07:15 PM", away: "NYJ (0-3)", home: "MIA (0-3)" }]
    }
  ];

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#000',
      color: '#fff',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#111',
        borderBottom: '1px solid #333',
        padding: '16px 24px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>NFL Model Projections</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ color: '#aaa' }}>Week</span>
            <select value={week} onChange={(e) => setWeek(e.target.value)} style={{
              background: '#222', border: '1px solid #444', color: '#fff',
              padding: '6px 12px', borderRadius: '4px'
            }}>
              {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18].map(w => (
                <option key={w} value={w}>{w}</option>
              ))}
            </select>
            <button onClick={() => setWeek(Math.max(1, week-1))} style={{
              background: 'transparent', border: '1px solid #444', color: '#fff',
              width: '32px', height: '32px', borderRadius: '4px', cursor: 'pointer'
            }}>‹</button>
            <button onClick={() => setWeek(Math.min(18, week+1))} style={{
              background: 'transparent', border: '1px solid #444', color: '#fff',
              width: '32px', height: '32px', borderRadius: '4px', cursor: 'pointer'
            }}>›</button>
          </div>
        </div>
      </div>

      {/* 4-Column Layout */}
      <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
          {columns.map((column, idx) => (
            <div key={idx} style={{ background: '#111', borderRadius: '8px', overflow: 'hidden' }}>
              {/* Column Header */}
              <div style={{
                background: '#222', padding: '16px 20px', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333'
              }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>{column.title}</h2>
                  {column.subtitle && (
                    <span style={{ fontSize: '12px', color: '#888', display: 'block', marginTop: '2px' }}>
                      {column.subtitle}
                    </span>
                  )}
                </div>
                {column.evCount > 0 && (
                  <div style={{
                    background: '#10b981', color: '#000', padding: '4px 10px',
                    borderRadius: '12px', fontSize: '11px', fontWeight: 600
                  }}>
                    {column.evCount} +EV
                  </div>
                )}
              </div>
              
              {/* Games */}
              <div style={{ padding: '16px' }}>
                {column.games.map(game => (
                  <div key={game.id} style={{
                    marginBottom: '16px', padding: '16px',
                    border: game.hasEV ? '1px solid #10b981' : '1px solid #333',
                    borderRadius: '6px', background: '#1a1a1a'
                  }}>
                    <div style={{ fontSize: '12px', color: '#888', marginBottom: '12px' }}>
                      {game.time} {game.final && <span style={{ color: '#f87171' }}>FINAL</span>}
                    </div>
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{game.away}</span>
                        {game.score && <span style={{ fontWeight: 600 }}>{game.score.split('-')[0]}</span>}
                      </div>
                    </div>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{game.home}</span>
                        {game.score && <span style={{ fontWeight: 600 }}>{game.score.split('-')[1]}</span>}
                      </div>
                    </div>
                    {game.hasEV && (
                      <div style={{
                        marginTop: '8px', padding: '6px', background: 'rgba(16,185,129,0.1)',
                        borderRadius: '4px', fontSize: '11px', color: '#10b981'
                      }}>
                        +EV Opportunity
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NFEloDashboard;