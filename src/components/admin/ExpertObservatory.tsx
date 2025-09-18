/**
 * Expert Observatory - Multi-Mode Admin Dashboard
 * Provides comprehensive analysis of expert predictions, reasoning, and performance
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  createColumnHelper,
  flexRender,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Eye,
  Compare,
  Brain,
  Target,
  Clock,
  AlertTriangle
} from 'lucide-react';

// Types
interface Expert {
  expert_id: string;
  display_name: string;
  personality: string;
  brand_color: string;
  avatar_emoji: string;
  performance_tier: 'gold' | 'silver' | 'bronze';
  accuracy_rate: number;
  confidence_avg: number;
  predictions_count: number;
  recent_trend: 'up' | 'down' | 'stable';
}

interface GamePrediction {
  game_id: string;
  date: string;
  home_team: string;
  away_team: string;
  consensus_winner: string;
  consensus_confidence: number;
  accuracy_rate: number;
  outlier_count: number;
  status: 'completed' | 'in_progress' | 'upcoming';
  expert_predictions: ExpertPrediction[];
}

interface ExpertPrediction {
  expert_id: string;
  expert_name: string;
  prediction: {
    winner: string;
    home_score: number;
    away_score: number;
    confidence: number;
  };
  reasoning_chain: ReasoningStep[];
  is_outlier: boolean;
}

interface ReasoningStep {
  factor: string;
  value: string;
  weight: number;
  confidence: number;
  source: string;
}

// Dashboard Mode Types
type DashboardMode = 'game-analysis' | 'expert-comparison' | 'performance-dashboard';

const ExpertObservatory: React.FC = () => {
  const [mode, setMode] = useState<DashboardMode>('game-analysis');
  const [selectedExperts, setSelectedExperts] = useState<string[]>([]);
  const [selectedGame, setSelectedGame] = useState<GamePrediction | null>(null);
  const [selectedExpert, setSelectedExpert] = useState<ExpertPrediction | null>(null);
  const [dateRange, setDateRange] = useState<string>('7d');
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  // Data fetching
  const { data: gamesData, isLoading: gamesLoading } = useQuery({
    queryKey: ['admin-games', dateRange],
    queryFn: () => fetchGamesData(dateRange),
  });

  const { data: expertsData, isLoading: expertsLoading } = useQuery({
    queryKey: ['admin-experts'],
    queryFn: () => fetchExpertsData(),
  });

  const { data: performanceData } = useQuery({
    queryKey: ['expert-performance', dateRange],
    queryFn: () => fetchPerformanceData(dateRange),
  });

  // Column definitions for games table
  const columnHelper = createColumnHelper<GamePrediction>();
  const gameColumns = useMemo(() => [
    columnHelper.accessor('date', {
      header: 'Date',
      cell: info => new Date(info.getValue()).toLocaleDateString(),
      sortingFn: 'datetime',
    }),
    columnHelper.accessor('home_team', {
      header: 'Matchup',
      cell: info => (
        <div className="font-medium">
          {info.row.original.away_team} @ {info.getValue()}
        </div>
      ),
    }),
    columnHelper.accessor('consensus_winner', {
      header: 'Consensus',
      cell: info => (
        <div className="flex items-center gap-2">
          <Badge variant="outline">{info.getValue()}</Badge>
          <span className="text-sm text-muted-foreground">
            {(info.row.original.consensus_confidence * 100).toFixed(0)}%
          </span>
        </div>
      ),
    }),
    columnHelper.accessor('accuracy_rate', {
      header: 'Accuracy',
      cell: info => {
        const rate = info.getValue();
        return (
          <div className="flex items-center gap-2">
            <Badge
              variant={rate > 0.8 ? 'default' : rate > 0.6 ? 'secondary' : 'destructive'}
            >
              {(rate * 100).toFixed(0)}%
            </Badge>
            {info.row.original.outlier_count > 0 && (
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            )}
          </div>
        );
      },
    }),
    columnHelper.accessor('status', {
      header: 'Status',
      cell: info => (
        <Badge
          variant={
            info.getValue() === 'completed' ? 'default' :
            info.getValue() === 'in_progress' ? 'secondary' :
            'outline'
          }
        >
          {info.getValue()}
        </Badge>
      ),
    }),
    columnHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedGame(row.original)}
        >
          <Eye className="h-4 w-4" />
          Analyze
        </Button>
      ),
    }),
  ], []);

  // Table setup
  const table = useReactTable({
    data: gamesData || [],
    columns: gameColumns,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  // Handlers
  const handleExpertToggle = useCallback((expertId: string) => {
    setSelectedExperts(prev =>
      prev.includes(expertId)
        ? prev.filter(id => id !== expertId)
        : [...prev, expertId]
    );
  }, []);

  const handleModeChange = useCallback((newMode: DashboardMode) => {
    setMode(newMode);
    setSelectedGame(null);
    setSelectedExpert(null);
  }, []);

  if (gamesLoading || expertsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Expert Observatory</h1>
          <p className="text-muted-foreground">
            Comprehensive expert analysis and performance monitoring
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last Week</SelectItem>
              <SelectItem value="30d">Last Month</SelectItem>
              <SelectItem value="season">Full Season</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Mode Tabs */}
      <Tabs value={mode} onValueChange={(value) => handleModeChange(value as DashboardMode)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="game-analysis" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Game Analysis
          </TabsTrigger>
          <TabsTrigger value="expert-comparison" className="flex items-center gap-2">
            <Compare className="h-4 w-4" />
            Expert Comparison
          </TabsTrigger>
          <TabsTrigger value="performance-dashboard" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Performance Dashboard
          </TabsTrigger>
        </TabsList>

        {/* Game Analysis Mode */}
        <TabsContent value="game-analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Games</CardTitle>
              <CardDescription>
                Click on any game to see expert predictions and reasoning
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex items-center gap-4 mb-4">
                <Input
                  placeholder="Filter games..."
                  value={(table.getColumn('home_team')?.getFilterValue() as string) ?? ''}
                  onChange={(event) =>
                    table.getColumn('home_team')?.setFilterValue(event.target.value)
                  }
                  className="max-w-sm"
                />
              </div>

              {/* Games Table */}
              <div className="rounded-md border">
                <table className="w-full">
                  <thead>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <tr key={headerGroup.id} className="border-b">
                        {headerGroup.headers.map((header) => (
                          <th
                            key={header.id}
                            className="h-12 px-4 text-left align-middle font-medium"
                          >
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </th>
                        ))}
                      </tr>
                    ))}
                  </thead>
                  <tbody>
                    {table.getRowModel().rows?.length ? (
                      table.getRowModel().rows.map((row) => (
                        <tr
                          key={row.id}
                          className="border-b hover:bg-muted/50 cursor-pointer"
                          onClick={() => setSelectedGame(row.original)}
                        >
                          {row.getVisibleCells().map((cell) => (
                            <td key={cell.id} className="p-4 align-middle">
                              {flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext()
                              )}
                            </td>
                          ))}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={gameColumns.length}
                          className="h-24 text-center"
                        >
                          No results.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between space-x-2 py-4">
                <div className="text-sm text-muted-foreground">
                  {table.getFilteredSelectedRowModel().rows.length} of{" "}
                  {table.getFilteredRowModel().rows.length} row(s) selected.
                </div>
                <div className="space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Expert Comparison Mode */}
        <TabsContent value="expert-comparison" className="space-y-6">
          <ExpertComparisonView
            experts={expertsData || []}
            selectedExperts={selectedExperts}
            onExpertToggle={handleExpertToggle}
          />
        </TabsContent>

        {/* Performance Dashboard Mode */}
        <TabsContent value="performance-dashboard" className="space-y-6">
          <PerformanceDashboardView
            experts={expertsData || []}
            performanceData={performanceData}
          />
        </TabsContent>
      </Tabs>

      {/* Game Detail Dialog */}
      {selectedGame && (
        <GameDetailDialog
          game={selectedGame}
          onClose={() => setSelectedGame(null)}
          onExpertClick={setSelectedExpert}
        />
      )}

      {/* Expert Reasoning Dialog */}
      {selectedExpert && (
        <ExpertReasoningDialog
          expert={selectedExpert}
          onClose={() => setSelectedExpert(null)}
        />
      )}
    </div>
  );
};

// Additional component implementations would go here...
// ExpertComparisonView, PerformanceDashboardView, GameDetailDialog, ExpertReasoningDialog

// Placeholder data fetching functions
async function fetchGamesData(dateRange: string): Promise<GamePrediction[]> {
  // Implementation would connect to your API
  return [];
}

async function fetchExpertsData(): Promise<Expert[]> {
  // Implementation would connect to your API
  return [];
}

async function fetchPerformanceData(dateRange: string) {
  // Implementation would connect to your API
  return {};
}

export default ExpertObservatory;