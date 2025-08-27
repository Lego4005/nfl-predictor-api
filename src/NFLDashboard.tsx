import React, { useEffect, useState, useCallback } from "react";
import { 
  GamePrediction, 
  ATSPrediction, 
  TotalsPrediction, 
  PropBet, 
  FantasyPick,
  DataSource,
  APIResponse,
  Notification
} from "./types";
import apiService from "./services/apiService";
import NotificationBanner from "./components/NotificationBanner";
import LoadingIndicator from "./components/LoadingIndicator";
import DataFreshness from "./components/DataFreshness";
import RetryButton from "./components/RetryButton";
import ErrorBoundary from "./components/ErrorBoundary";

type TabType = "su" | "ats" | "totals" | "props" | "fantasy";

// New data structure matching the condensed schema
interface NewGameData {
  game_id: string;
  kickoff_utc: string;
  home: { team: string; abbr: string; logo?: string };
  away: { team: string; abbr: string; logo?: string };
  su: { pick: string; confidence: number };
  ats: { spread_team: string; spread: number; pick: string; confidence: number };
  totals: { line: number; pick: string; confidence: number };
}

interface NewPropData {
  prop_id: string;
  game_id: string;
  player: string;
  team: string;
  position: string;
  market: string;
  book: string;
  line: number;
  pick: string;
  confidence: number;
}

interface NewFantasyData {
  salary_cap: number;
  lineup: Array<{
    player: string;
    team: string;
    position: string;
    salary: number;
    projected_points: number;
    value: number;
    game_id: string;
  }>;
  alternates: Array<{
    player: string;
    team: string;
    position: string;
    salary: number;
    projected_points: number;
    value: number;
    game_id: string;
  }>;
}

interface NewWeeklyData {
  season: number;
  week: string;
  last_updated_utc: string;
  games: NewGameData[];
  props: NewPropData[];
  fantasy: NewFantasyData;
  exports: {
    csv: Record<string, string>;
    pdf_spec: {
      title: string;
      sections: string[];
      footer: string;
    };
  };
}

interface CardProps {
  children: React.ReactNode;
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

interface TableProps {
  cols?: string[];
  rows?: React.ReactNode[];
}

export default function NFLDashboard(): JSX.Element {
  const [week, setWeek] = useState<number>(1);
  const [tab, setTab] = useState<TabType>("su");
  const [data, setData] = useState<any>(null); // Simplified - use any for now
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);
  const [lastRefresh, setLastRefresh] = useState<string>("");

  const td: React.CSSProperties = { 
    padding: "8px 10px", 
    borderBottom: "1px solid #f2f2f2" 
  };
  
  const pct = (v: number | undefined | null): string => 
    (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—");
  
  const money = (v: number | undefined | null): string => 
    (typeof v === "number" ? `${v.toLocaleString()}` : "—");

  const fetchWeek = useCallback(async (w: number, isRetry: boolean = false): Promise<void> => {
    if (isRetry) {
      setIsRetrying(true);
    } else {
      setLoading(true);
    }
    
    setError("");
    setNotifications([]);

    try {
      // Direct fetch like the working HTML version
      const response = await fetch(`http://localhost:8080/v1/best-picks/2025/${w}?t=${Date.now()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const rawData = await response.json();
      console.log('React app received data:', rawData);
      
      setData(rawData);
      setLastRefresh(new Date().toISOString());
      
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Failed to fetch data";
      console.error('React app error:', errorMessage);
      setError(errorMessage);
      
      // Add error notification
      const errorNotification: Notification = {
        type: 'error',
        message: errorMessage,
        retryable: true
      };
      setNotifications([errorNotification]);
    } finally {
      setLoading(false);
      setIsRetrying(false);
    }
  }, []);

  // Transform old API format to new schema format
  const transformToNewFormat = (oldData: any, week: number): NewWeeklyData => {
    const games: NewGameData[] = [];
    const props: NewPropData[] = [];
    
    // Transform games data
    if (oldData.best_picks) {
      oldData.best_picks.forEach((pick: any, index: number) => {
        const gameId = `2025-W${week.toString().padStart(2, '0')}-${pick.away}-${pick.home}`;
        
        // Find corresponding ATS and totals data
        const atsData = oldData.ats_picks?.[index] || {};
        const totalsData = oldData.totals_picks?.[index] || {};
        
        games.push({
          game_id: gameId,
          kickoff_utc: new Date().toISOString(), // Default to now
          home: { 
            team: pick.home || 'HOME', 
            abbr: pick.home || 'HOME',
            logo: `https://a.espncdn.com/i/teamlogos/nfl/500/${pick.home}.png`
          },
          away: { 
            team: pick.away || 'AWAY', 
            abbr: pick.away || 'AWAY',
            logo: `https://a.espncdn.com/i/teamlogos/nfl/500/${pick.away}.png`
          },
          su: { 
            pick: pick.su_pick === pick.home ? 'HOME' : 'AWAY', 
            confidence: pick.su_confidence || 0.5 
          },
          ats: { 
            spread_team: atsData.spread > 0 ? 'AWAY' : 'HOME',
            spread: Math.abs(atsData.spread || 3.5), 
            pick: atsData.ats_pick?.includes(pick.home) ? 'HOME' : 'AWAY', 
            confidence: atsData.ats_confidence || 0.5 
          },
          totals: { 
            line: totalsData.total_line || 45.5, 
            pick: totalsData.tot_pick?.includes('Over') ? 'OVER' : 'UNDER', 
            confidence: totalsData.tot_confidence || 0.5 
          }
        });
      });
    }
    
    // Transform props data
    if (oldData.prop_bets) {
      oldData.prop_bets.forEach((prop: any, index: number) => {
        const gameId = `2025-W${week.toString().padStart(2, '0')}-${prop.opponent}-${prop.team}`;
        
        props.push({
          prop_id: `${gameId}-${prop.player.toLowerCase().replace(/\s+/g, '-')}-${prop.prop_type.toLowerCase().replace(/\s+/g, '')}`,
          game_id: gameId,
          player: prop.player || 'Unknown Player',
          team: prop.team || 'UNK',
          position: getPositionFromPropType(prop.prop_type),
          market: prop.prop_type || 'Unknown Market',
          book: prop.bookmaker || 'Unknown Book',
          line: prop.line || 0,
          pick: prop.pick || 'OVER',
          confidence: prop.confidence || 0.5
        });
      });
    }
    
    // Transform fantasy data
    const fantasy: NewFantasyData = {
      salary_cap: 50000,
      lineup: [],
      alternates: []
    };
    
    if (oldData.fantasy_picks) {
      fantasy.lineup = oldData.fantasy_picks.slice(0, 9).map((pick: any, index: number) => ({
        player: pick.player || `Player ${index + 1}`,
        team: pick.team || 'UNK',
        position: pick.position || 'FLEX',
        salary: pick.salary || 5000,
        projected_points: pick.projected_points || 10,
        value: pick.value_score || 2.0,
        game_id: `2025-W${week.toString().padStart(2, '0')}-GAME-${index + 1}`
      }));
      
      fantasy.alternates = oldData.fantasy_picks.slice(9, 14).map((pick: any, index: number) => ({
        player: pick.player || `Alt Player ${index + 1}`,
        team: pick.team || 'UNK',
        position: pick.position || 'FLEX',
        salary: pick.salary || 5000,
        projected_points: pick.projected_points || 10,
        value: pick.value_score || 2.0,
        game_id: `2025-W${week.toString().padStart(2, '0')}-ALT-${index + 1}`
      }));
    }
    
    return {
      season: 2025,
      week: week.toString(),
      last_updated_utc: new Date().toISOString(),
      games,
      props,
      fantasy,
      exports: {
        csv: {
          su: "Home,Away,Su Pick,Su Confidence,Game Id,Kickoff",
          ats: "Matchup,ATS Pick,Spread,ATS Confidence,Game Id,Kickoff",
          totals: "Matchup,Pick,Line,Confidence,Game Id,Kickoff",
          props: "Player,Market,Pick,Line,Confidence,Book,Game,Game Id,Kickoff",
          fantasy: "Player,Position,Team,Salary,Projected Points,Value,Game Id"
        },
        pdf_spec: {
          title: `NFL 2025 Predictions — Week ${week}`,
          sections: ["Straight-Up", "ATS", "Totals", "Props", "Fantasy"],
          footer: "API: https://nfl-predictor-api.onrender.com • Generated {local_time}"
        }
      }
    };
  };

  const getPositionFromPropType = (propType: string): string => {
    if (propType?.includes('Passing')) return 'QB';
    if (propType?.includes('Rushing')) return 'RB';
    if (propType?.includes('Receiving')) return 'WR';
    if (propType?.includes('Receptions')) return 'WR';
    return 'FLEX';
  };

  useEffect(() => { 
    fetchWeek(week); 
  }, [week, fetchWeek]);

  // Auto-refresh every 5 minutes for live data
  useEffect(() => {
    const interval = setInterval(() => {
      if (data && data.source !== DataSource.MOCK) {
        fetchWeek(week, false);
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [week, data, fetchWeek]);

  const download = async (fmt: 'json' | 'csv' | 'pdf'): Promise<void> => {
    try {
      const blob = await apiService.downloadData(week, fmt);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nfl-predictions-week-${week}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Download failed";
      const downloadError: Notification = {
        type: 'error',
        message: `Download failed: ${errorMessage}`,
        retryable: true
      };
      setNotifications(prev => [...prev, downloadError]);
    }
  };

  const handleRetry = (): void => {
    fetchWeek(week, true);
  };

  const handleDismissNotification = (index: number): void => {
    setNotifications(prev => prev.filter((_, i) => i !== index));
  };

  const handleRefresh = (): void => {
    fetchWeek(week, false);
  };

  const Card: React.FC<CardProps> = ({ children }) => (
    <div style={{ 
      background: "#fff", 
      borderRadius: 8, 
      padding: 16, 
      boxShadow: "0 1px 3px rgba(0,0,0,.08)" 
    }}>
      {children}
    </div>
  );

  const Section: React.FC<SectionProps> = ({ title, children }) => (
    <div style={{ marginTop: 16 }}>
      <Card>
        <h3 style={{ marginTop: 0 }}>{title}</h3>
        {children}
      </Card>
    </div>
  );

  const Table: React.FC<TableProps> = ({ cols = [], rows = [] }) => (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c} style={{ 
                textAlign: "left", 
                padding: "8px 10px", 
                borderBottom: "1px solid #eee" 
              }}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={cols.length} style={{ padding: 12, color: "#777" }}>
                No data.
              </td>
            </tr>
          ) : rows}
        </tbody>
      </table>
    </div>
  );

  return (
    <ErrorBoundary>
      <div style={{ 
        fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, Helvetica", 
        background: "#f7f7f9", 
        minHeight: "100vh" 
      }}>
        <div style={{ maxWidth: 980, margin: "0 auto", padding: 24 }}>
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "space-between",
            marginBottom: 16,
            flexWrap: "wrap",
            gap: 12
          }}>
            <h1 style={{ margin: 0 }}>NFL 2025 Predictions — Week {week}</h1>
            
            {data && (
              <DataFreshness
                timestamp={data.timestamp}
                source={data.source}
                cached={data.cached}
              />
            )}
          </div>

          {/* Notifications */}
          <NotificationBanner
            notifications={notifications}
            onDismiss={handleDismissNotification}
            maxVisible={3}
          />

          {/* Controls */}
          <Card>
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: 12, 
              flexWrap: "wrap" 
            }}>
              <label style={{ fontWeight: 600 }}>
                Week:&nbsp;
                <select 
                  value={week} 
                  onChange={(e) => setWeek(parseInt(e.target.value, 10))}
                  disabled={loading || isRetrying}
                >
                  {Array.from({ length: 18 }, (_, i) => (
                    <option key={i + 1} value={i + 1}>Week {i + 1}</option>
                  ))}
                </select>
              </label>

              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <button
                  onClick={handleRefresh}
                  disabled={loading || isRetrying}
                  style={{
                    padding: "6px 12px",
                    backgroundColor: "#f3f4f6",
                    border: "1px solid #d1d5db",
                    borderRadius: "4px",
                    cursor: loading || isRetrying ? "not-allowed" : "pointer",
                    fontSize: "14px"
                  }}
                >
                  🔄 Refresh
                </button>
                
                {error && (
                  <RetryButton
                    onRetry={handleRetry}
                    isRetrying={isRetrying}
                    variant="secondary"
                  />
                )}
              </div>

              <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                <button 
                  onClick={() => download("json")}
                  disabled={loading || !data}
                >
                  Download JSON
                </button>
                <button 
                  onClick={() => download("csv")}
                  disabled={loading || !data}
                >
                  Download CSV
                </button>
                <button 
                  onClick={() => download("pdf")}
                  disabled={loading || !data}
                >
                  Download PDF
                </button>
              </div>
            </div>
          </Card>  
      {/* Tabs */}
        <div style={{ 
          background: "#fff", 
          borderRadius: 8, 
          padding: 8, 
          marginTop: 16, 
          boxShadow: "0 1px 3px rgba(0,0,0,.08)" 
        }}>
          <nav style={{ 
            display: "flex", 
            gap: 16, 
            borderBottom: "1px solid #eee", 
            paddingBottom: 8, 
            marginBottom: 8, 
            flexWrap: "wrap" 
          }}>
            {[
              ["su", "Straight-Up"],
              ["ats", "ATS"],
              ["totals", "Totals"],
              ["props", "Props"],
              ["fantasy", "Fantasy"],
            ].map(([k, label]) => (
              <button 
                key={k} 
                onClick={() => setTab(k as TabType)}
                style={{ 
                  border: "none", 
                  background: "transparent", 
                  cursor: "pointer", 
                  fontWeight: tab === k ? 700 : 500, 
                  padding: "4px 6px" 
                }}
              >
                {label}
              </button>
            ))}
          </nav>

          {loading ? (
            <LoadingIndicator
              isLoading={true}
              message="Fetching NFL predictions..."
              size="medium"
            />
          ) : error ? (
            <div style={{ 
              color: "#dc2626", 
              fontWeight: 600,
              textAlign: "center",
              padding: "24px"
            }}>
              <div style={{ marginBottom: "16px" }}>⚠️ {error}</div>
              <RetryButton
                onRetry={handleRetry}
                isRetrying={isRetrying}
                variant="primary"
              />
            </div>
          ) : (
            <>
              {/* STRAIGHT-UP TAB */}
              {tab === "su" && (
                <Section title={`Straight-Up Picks (${data?.best_picks?.length || 0} Games)`}>
                  <Table
                    cols={["Home", "Away", "Su Pick", "Su Confidence"]}
                    rows={(data?.best_picks || []).map((pick: any, i: number) => (
                      <tr key={i}>
                        <td style={td}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            {pick.logo_home && (
                              <img 
                                src={pick.logo_home} 
                                alt={pick.home} 
                                style={{ width: 20, height: 20 }}
                                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                              />
                            )}
                            <strong>{pick.home}</strong>
                          </div>
                        </td>
                        <td style={td}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            {pick.logo_away && (
                              <img 
                                src={pick.logo_away} 
                                alt={pick.away} 
                                style={{ width: 20, height: 20 }}
                                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                              />
                            )}
                            {pick.away}
                          </div>
                        </td>
                        <td style={td}>
                          <span style={{ 
                            fontWeight: 600, 
                            color: pick.su_confidence > 0.7 ? "#22c55e" : pick.su_confidence > 0.6 ? "#f59e0b" : "#6b7280" 
                          }}>
                            {pick.su_pick}
                          </span>
                        </td>
                        <td style={td}>
                          <span style={{ 
                            fontWeight: 600,
                            color: pick.su_confidence > 0.7 ? "#22c55e" : pick.su_confidence > 0.6 ? "#f59e0b" : "#6b7280" 
                          }}>
                            {pct(pick.su_confidence)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  />
                </Section>
              )}

              {/* ATS TAB */}
              {tab === "ats" && (
                <Section title={`Against the Spread (${data?.ats_picks?.length || 0} Games)`}>
                  <Table
                    cols={["Matchup", "ATS Pick", "Spread", "ATS Confidence"]}
                    rows={(data?.ats_picks || []).map((pick: any, i: number) => (
                      <tr key={i}>
                        <td style={td}><strong>{pick.matchup}</strong></td>
                        <td style={td}>
                          <span style={{ 
                            fontWeight: 600, 
                            color: pick.ats_confidence > 0.7 ? "#22c55e" : pick.ats_confidence > 0.6 ? "#f59e0b" : "#6b7280" 
                          }}>
                            {pick.ats_pick}
                          </span>
                        </td>
                        <td style={td}>
                          <span style={{ 
                            fontWeight: 600,
                            color: Math.abs(pick.spread) > 6 ? "#dc2626" : Math.abs(pick.spread) > 3 ? "#f59e0b" : "#22c55e"
                          }}>
                            {pick.spread > 0 ? `+${pick.spread}` : pick.spread}
                          </span>
                        </td>
                        <td style={td}>
                          <span style={{ 
                            fontWeight: 600,
                            color: pick.ats_confidence > 0.7 ? "#22c55e" : pick.ats_confidence > 0.6 ? "#f59e0b" : "#6b7280" 
                          }}>
                            {pct(pick.ats_confidence)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  />
                </Section>
              )}

              {/* TOTALS TAB */}
              {tab === "totals" && (
                <Section title="Totals (Over/Under)">
                  <Table
                    cols={["Matchup", "Pick", "Line", "Confidence"]}
                    rows={(data?.totals_picks || []).map((pick: any, i: number) => (
                      <tr key={i}>
                        <td style={td}>{pick.matchup}</td>
                        <td style={td}>{pick.tot_pick}</td>
                        <td style={td}>{pick.total_line}</td>
                        <td style={td}>{pct(pick.tot_confidence)}</td>
                      </tr>
                    ))}
                  />
                </Section>
              )}

              {/* PROPS TAB */}
              {tab === "props" && (
                <Section title="Player Props">
                  <Table
                    cols={["Player", "Market", "Pick", "Line", "Confidence", "Book"]}
                    rows={(data?.prop_bets || []).map((prop: any, i: number) => (
                      <tr key={i}>
                        <td style={td}>{prop.player}</td>
                        <td style={td}>{prop.prop_type}</td>
                        <td style={td}>{prop.pick}</td>
                        <td style={td}>{prop.line}</td>
                        <td style={td}>{pct(prop.confidence)}</td>
                        <td style={td}>{prop.bookmaker}</td>
                      </tr>
                    ))}
                  />
                </Section>
              )}

              {/* FANTASY TAB */}
              {tab === "fantasy" && (
                <Section title="Fantasy Picks">
                  <Table
                    cols={["Player", "Position", "Salary", "Projected Points", "Value"]}
                    rows={(data?.fantasy_picks || []).map((pick: any, i: number) => (
                      <tr key={i}>
                        <td style={td}>{pick.player}</td>
                        <td style={td}>{pick.position}</td>
                        <td style={td}>${money(pick.salary)}</td>
                        <td style={td}>{pick.projected_points}</td>
                        <td style={td}>{pick.value_score}</td>
                      </tr>
                    ))}
                  />
                </Section>
              )}
            </>
          )}
        </div>

        <div style={{ 
          color: "#888", 
          marginTop: 12, 
          fontSize: "12px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 8
        }}>
          <div>
            API: <code>{apiService.getConfig().baseUrl}</code>
          </div>
          {lastRefresh && (
            <div>
              Last updated: {new Date(lastRefresh).toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}