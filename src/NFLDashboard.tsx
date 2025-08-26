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
import apiService, { WeeklyPredictions } from "./services/apiService";
import NotificationBanner from "./components/NotificationBanner";
import LoadingIndicator from "./components/LoadingIndicator";
import DataFreshness from "./components/DataFreshness";
import RetryButton from "./components/RetryButton";
import ErrorBoundary from "./components/ErrorBoundary";

type TabType = "main" | "props" | "fantasy" | "lineup";

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
  const [tab, setTab] = useState<TabType>("main");
  const [data, setData] = useState<APIResponse<WeeklyPredictions> | null>(null);
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
      const response = await apiService.getWeeklyPredictions(w);
      setData(response);
      setLastRefresh(new Date().toISOString());
      
      // Set notifications from API response
      if (response.notifications && response.notifications.length > 0) {
        setNotifications(response.notifications);
      }
      
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Failed to fetch data";
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
              ["main", "Main Predictions"],
              ["props", "Prop Bets"],
              ["fantasy", "Fantasy Picks"],
              ["lineup", "Classic Lineup"],
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
              {/* MAIN TAB */}
              {tab === "main" && (
                <>
                  <Section title="Top 5 Straight-Up Picks">
                    <Table
                      cols={["Home", "Away", "Su Pick", "Su Confidence"]}
                      rows={(data?.data?.best_picks || []).slice(0, 5).map((r, i) => (
                        <tr key={i}>
                          <td style={td}>{r.home}</td>
                          <td style={td}>{r.away}</td>
                          <td style={td}>{r.su_pick}</td>
                          <td style={td}>{pct(r.su_confidence)}</td>
                        </tr>
                      ))}
                    />
                  </Section>

                  <Section title="Top 5 Against the Spread (ATS)">
                    <Table
                      cols={["Matchup", "ATS Pick", "Spread", "ATS Confidence"]}
                      rows={(data?.data?.ats_picks || []).slice(0, 5).map((r, i) => (
                        <tr key={i}>
                          <td style={td}>{r.matchup || "—"}</td>
                          <td style={td}>{r.ats_pick}</td>
                          <td style={td}>{typeof r.spread === "number" ? r.spread : "—"}</td>
                          <td style={td}>{pct(r.ats_confidence)}</td>
                        </tr>
                      ))}
                    />
                  </Section>

                  <Section title="Top 5 Totals (O/U)">
                    <Table
                      cols={["Matchup", "Pick", "Line", "Confidence"]}
                      rows={(data?.data?.totals_picks || []).slice(0, 5).map((r, i) => (
                        <tr key={i}>
                          <td style={td}>{r.matchup || "—"}</td>
                          <td style={td}>{r.tot_pick || "—"}</td>
                          <td style={td}>{typeof r.total_line === "number" ? r.total_line : "—"}</td>
                          <td style={td}>{pct(r.tot_confidence)}</td>
                        </tr>
                      ))}
                    />
                  </Section>
                </>
              )}

              {/* PROPS TAB */}
              {tab === "props" && (
                <Section title="Top 5 Player Prop Bets">
                  <Table
                    cols={["Player", "Market", "Pick", "Line", "Confidence", "Book", "Game"]}
                    rows={(data?.data?.prop_bets || []).slice(0, 5).map((p, i) => {
                      const game = (p.team && p.opponent ? `${p.opponent} @ ${p.team}` : "—");
                      const line = typeof p.line === "number" ? `${p.line}${p.units ? " " + p.units : ""}` : "—";
                      return (
                        <tr key={i}>
                          <td style={td}>{p.player}</td>
                          <td style={td}>{p.prop_type}</td>
                          <td style={td}>{p.pick || "—"}</td>
                          <td style={td}>{line}</td>
                          <td style={td}>{pct(p.confidence)}</td>
                          <td style={td}>{p.bookmaker || "—"}</td>
                          <td style={td}>{game}</td>
                        </tr>
                      );
                    })}
                  />
                </Section>
              )}

              {/* FANTASY TAB */}
              {tab === "fantasy" && (
                <Section title="Top 5 Fantasy Value Picks">
                  <Table
                    cols={["Player", "Position", "Salary", "Projected Points", "Value Score"]}
                    rows={(data?.data?.fantasy_picks || []).slice(0, 5).map((f, i) => (
                      <tr key={i}>
                        <td style={td}>{f.player}</td>
                        <td style={td}>{f.position}</td>
                        <td style={td}>{money(f.salary)}</td>
                        <td style={td}>{f.projected_points ?? "—"}</td>
                        <td style={td}>{f.value_score ?? "—"}</td>
                      </tr>
                    ))}
                  />
                </Section>
              )}

              {/* LINEUP TAB */}
              {tab === "lineup" && (
                <Section title="Classic Lineup">
                  {data?.data?.classic_lineup && data.data.classic_lineup.length > 0 ? (
                    <Table
                      cols={["Position", "Player", "Salary", "Projected Points", "Value Score"]}
                      rows={data.data.classic_lineup.map((f, i) => (
                        <tr key={i}>
                          <td style={td}>{f.position}</td>
                          <td style={td}>{f.player}</td>
                          <td style={td}>{money(f.salary)}</td>
                          <td style={td}>{f.projected_points ?? "—"}</td>
                          <td style={td}>{f.value_score ?? "—"}</td>
                        </tr>
                      ))}
                    />
                  ) : (
                    <div style={{ color: "#777", textAlign: "center", padding: "24px" }}>
                      Classic lineup data not available for this week.
                    </div>
                  )}
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