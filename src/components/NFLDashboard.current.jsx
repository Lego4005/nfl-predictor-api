import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getTeam, NFL_TEAMS } from "../data/nflTeams";
import TeamCard from "./TeamCard";
import GameCard from "./game/GameCard";
import GameDetailModal from "./GameDetailModal";
import SmartInsights from "./SmartInsights";
import NewsFeed from "./NewsFeed";
import PowerRankings from "./PowerRankings";
import ModelPerformance from "./ModelPerformance";
import Leaderboard from "./Leaderboard";

// Extracted components
import LiveTicker from "./dashboard/LiveTicker";
import AnalyticsCharts from "./dashboard/AnalyticsCharts";
import WsBadge from "./dashboard/WsBadge";
import {
  OddsComparisonTable,
  ValueBetsTable,
  OddsMovementChart,
} from "./dashboard/BettingComponents";
import { InjuriesPanel, SystemHealthPanel } from "./dashboard/SystemComponents";
import {
  MiniStat,
  PredictionAccuracyChart,
  ModelLeaderboard,
  TeamComparator,
} from "./dashboard/ChartComponents";
import { DashboardHeader, LiveGamesBar } from "./dashboard/HeaderComponents";
import { DesktopTabsList, MobileTabsList } from "./dashboard/TabsComponents";

// Extracted hooks
import useTheme from "../hooks/useTheme";
import useLiveFeed from "../hooks/useLiveFeed";
import useApi from "../hooks/useApi";
// Recharts imports moved to extracted chart components
import { Activity, AlertTriangle, RefreshCw } from "lucide-react";

// shadcn/ui components
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

// NFL Prediction Dashboard - Refactored with extracted components

// Utility functions and constants moved to extracted components

// Helper function for betting tab
function makeStatusMap(games) {
  const map = {};
  (games || []).forEach((g) => {
    map[g.id] = {
      status: g.status,
      quarter: g.quarter,
      clock: g.clock,
      startTime: g.startTime,
      home: g.homeTeam,
      away: g.awayTeam,
    };
  });
  return map;
}

// ----------------------------
// Error Boundary
// ----------------------------
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("Dashboard crashed:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] grid place-items-center p-8">
          <Card className="max-w-2xl w-full">
            <CardHeader className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="font-semibold">Something went sideways</span>
              </div>
              <Badge variant="destructive">Error</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm opacity-80">
                The dashboard hit an error. Try refreshing. If this persists,
                check your data endpoints.
              </p>
              <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-48">
                {String(this.state.error)}
              </pre>
            </CardContent>
            <CardFooter>
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload
              </Button>
            </CardFooter>
          </Card>
        </div>
      );
    }
    // @ts-ignore
    return this.props.children;
  }
}

// Live feed hook extracted to ../hooks/useLiveFeed.js

// API hook extracted to ../hooks/useApi.js

// All components and hooks extracted to separate files

// ----------------------------
// Main Component
// ----------------------------
export default function NFLPredictionDashboard() {
  const { dark, setDark } = useTheme();
  const { connected, events } = useLiveFeed();
  const [wide, setWide] = useState(true);
  const [selectedGame, setSelectedGame] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [expandedView, setExpandedView] = useState(false);
  const [demoMode, setDemoMode] = useState(false); // Default to real data from Supabase

  // Data domains - live ESPN API integration with demo fallback
  const games = useApi("/games", { demo: demoMode });
  const analytics = useApi("/teams/analytics", { demo: demoMode });
  const accuracy = useApi("/predictions/accuracy", {
    refreshMs: 60000,
    demo: demoMode,
  });
  const odds = useApi("/odds", { demo: demoMode });
  const oddsMovements = useApi("/odds/movements", { demo: demoMode });
  const injuries = useApi("/injuries", { refreshMs: 60000, demo: demoMode });
  const models = useApi("/models/leaderboard", {
    refreshMs: 120000,
    demo: demoMode,
  });
  const health = useApi("/system/health", { refreshMs: 45000, demo: demoMode });

  const isLoading =
    games.loading ||
    analytics.loading ||
    accuracy.loading ||
    odds.loading ||
    injuries.loading;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-neutral-900">
        <div
          className={`min-h-screen text-foreground ${wide ? "max-w-screen-2xl" : "max-w-7xl"} mx-auto p-4`}
        >
          {/* Header */}
          <DashboardHeader
            dark={dark}
            setDark={setDark}
            wide={wide}
            setWide={setWide}
            connected={connected}
            isLoading={isLoading}
            demoMode={demoMode}
            setDemoMode={setDemoMode}
          />

          {/* Live Games & Expert Predictions Bar - Always visible */}
          <LiveGamesBar games={games.data} connected={connected} />

          {/* Live Ticker - Only show during live games */}
          {games.data?.filter((g) => g.status === "live").length > 0 && (
            <LiveTicker events={events} />
          )}

          {/* Smart Insights Section */}
          {games.data && <SmartInsights games={games.data} />}

          {/* Main Content - Mobile Responsive */}
          <div className="mt-4 sm:mt-6">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              {/* Desktop Tabs - Hidden on Mobile */}
              <DesktopTabsList />

              {/* Mobile Tabs - Horizontal Scroll */}
              <MobileTabsList />

              <TabsContent value="overview" className="space-y-4 sm:space-y-6">
                {isLoading ? (
                  <div className="mobile-grid">
                    {[...Array(6)].map((_, i) => (
                      <Skeleton key={i} className="h-48 sm:h-64" />
                    ))}
                  </div>
                ) : (
                  <>
                    {/* Live Games Priority Section */}
                    {games.data?.filter((g) => g.status === "live").length >
                      0 && (
                      <div className="mb-6">
                        <div className="flex items-center gap-2 mb-3">
                          <Badge className="bg-red-600 text-white animate-pulse">
                            <Activity className="w-3 h-3 mr-1" />
                            LIVE NOW
                          </Badge>
                          <span className="text-sm font-semibold">
                            {
                              games.data.filter((g) => g.status === "live")
                                .length
                            }{" "}
                            Games In Progress
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {games.data
                            .filter((g) => g.status === "live")
                            .map((g) => (
                              <GameCard key={g.id} game={g} />
                            ))}
                        </div>
                      </div>
                    )}

                    {/* All Games Grid - Dynamic sizing */}
                    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                      {games.data
                        ?.filter((g) => g.status !== "live") // Don't duplicate live games
                        .sort((a, b) => {
                          // Sort: scheduled first (by time), then final
                          if (
                            a.status === "scheduled" &&
                            b.status === "scheduled"
                          ) {
                            return new Date(a.gameTime) - new Date(b.gameTime);
                          }
                          if (a.status === "scheduled") return -1;
                          if (b.status === "scheduled") return 1;
                          return 0;
                        })
                        .map((g) => (
                          <div
                            key={g.id}
                            onClick={() => {
                              if (g.status === "scheduled") {
                                setSelectedGame(g);
                                setModalOpen(true);
                              }
                            }}
                            className={
                              g.status === "scheduled" ? "cursor-pointer" : ""
                            }
                          >
                            <GameCard game={g} />
                          </div>
                        ))}
                    </div>

                    {/* Show more/less for many games */}
                    {games.data?.length > 12 && (
                      <div className="mt-4 text-center">
                        <Button
                          variant="outline"
                          onClick={() => setExpandedView(!expandedView)}
                        >
                          {expandedView
                            ? "Show Less"
                            : `Show All ${games.data.length} Games`}
                        </Button>
                      </div>
                    )}

                    {/* Phase 3 & 4 Components - Mobile Responsive */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
                      {/* Power Rankings */}
                      <PowerRankings analytics={analytics.data} />

                      {/* Model Performance */}
                      <div>
                        <ModelPerformance />
                      </div>
                    </div>

                    {/* News Feed */}
                    <NewsFeed games={games.data} />

                    {accuracy.data && (
                      <PredictionAccuracyChart rows={accuracy.data} />
                    )}
                  </>
                )}
              </TabsContent>

              <TabsContent value="live" className="space-y-4 sm:space-y-6">
                <div className="mobile-grid">
                  {games.data
                    ?.filter((g) => g.status === "live")
                    .map((g) => (
                      <GameCard key={g.id} game={g} />
                    ))}
                </div>
              </TabsContent>

              <TabsContent value="analytics" className="space-y-4 sm:space-y-6">
                {analytics.data && (
                  <AnalyticsCharts analytics={analytics.data} />
                )}
                {analytics.data && (
                  <TeamComparator analytics={analytics.data} />
                )}
              </TabsContent>

              <TabsContent
                value="predictions"
                className="space-y-4 sm:space-y-6"
              >
                {models.data && <ModelLeaderboard rows={models.data} />}
                {accuracy.data && (
                  <PredictionAccuracyChart rows={accuracy.data} />
                )}
              </TabsContent>

              <TabsContent value="players" className="space-y-4 sm:space-y-6">
                {injuries.data && <InjuriesPanel items={injuries.data} />}
              </TabsContent>

              <TabsContent value="betting" className="space-y-4 sm:space-y-6">
                {odds.data && games.data && (
                  <>
                    <OddsComparisonTable
                      rows={odds.data}
                      statusMap={makeStatusMap(games.data)}
                      smartDefault={true}
                    />
                    <ValueBetsTable games={games.data} oddsRows={odds.data} />
                    {oddsMovements.data && (
                      <OddsMovementChart
                        movements={oddsMovements.data}
                        oddsRows={odds.data}
                      />
                    )}
                  </>
                )}
              </TabsContent>

              <TabsContent
                value="leaderboard"
                className="space-y-4 sm:space-y-6"
              >
                {/* Create placeholder for leaderboard since the component might not exist */}
                <div className="text-center py-8">
                  <h3 className="responsive-text-lg font-semibold mb-2">
                    Leaderboard Coming Soon
                  </h3>
                  <p className="responsive-text-sm text-muted-foreground">
                    Player and team leaderboards will be available here.
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="health" className="space-y-4 sm:space-y-6">
                {health.data && (
                  <SystemHealthPanel
                    health={health.data}
                    wsConnected={connected}
                  />
                )}
              </TabsContent>
            </Tabs>
          </div>

          {/* Game Detail Modal */}
          <GameDetailModal
            game={selectedGame}
            isOpen={modalOpen}
            onClose={() => {
              setModalOpen(false);
              setSelectedGame(null);
            }}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}
