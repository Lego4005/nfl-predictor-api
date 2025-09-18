import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Globe,
  Server,
  Wifi,
  Zap,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
} from 'lucide-react';

interface MetricSnapshot {
  timestamp: string;
  api_response_time: number;
  prediction_accuracy: number;
  cache_hit_rate: number;
  websocket_connections: number;
  system_cpu: number;
  system_memory: number;
  database_connections: number;
  error_rate: number;
  data_source_availability: Record<string, boolean>;
}

interface SystemStatus {
  timestamp: string;
  health_score: number;
  status: 'healthy' | 'degraded' | 'unhealthy';
  metrics: {
    api_response_time: number;
    prediction_accuracy: number;
    cache_hit_rate: number;
    websocket_connections: number;
    system_cpu: number;
    system_memory: number;
    error_rate: number;
  };
  data_sources: Record<string, boolean>;
  recent_alerts: number;
  sla_compliance: Record<string, number>;
}

interface Alert {
  id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  metric: string;
  message: string;
  resolved: boolean;
}

interface BottleneckDetection {
  timestamp: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_component: string;
  root_cause: string;
  impact_score: number;
  confidence_score: number;
}

const SystemHealth: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [historicalData, setHistoricalData] = useState<MetricSnapshot[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [bottlenecks, setBottlenecks] = useState<BottleneckDetection[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/monitoring/status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  // Fetch historical metrics
  const fetchHistoricalData = async () => {
    try {
      const response = await fetch('/api/monitoring/metrics/history?hours=24');
      const data = await response.json();
      setHistoricalData(data);
    } catch (error) {
      console.error('Failed to fetch historical data:', error);
    }
  };

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/monitoring/alerts?hours=24');
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  // Fetch bottlenecks
  const fetchBottlenecks = async () => {
    try {
      const response = await fetch('/api/monitoring/bottlenecks?hours=24');
      const data = await response.json();
      setBottlenecks(data);
    } catch (error) {
      console.error('Failed to fetch bottlenecks:', error);
    }
  };

  // Load all data
  const loadData = async () => {
    setLoading(true);
    await Promise.all([
      fetchSystemStatus(),
      fetchHistoricalData(),
      fetchAlerts(),
      fetchBottlenecks(),
    ]);
    setLoading(false);
  };

  // Auto-refresh effect
  useEffect(() => {
    loadData();

    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  // Get status color and icon
  const getStatusDisplay = (status: string, score: number) => {
    switch (status) {
      case 'healthy':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          icon: CheckCircle,
          text: 'Healthy'
        };
      case 'degraded':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          icon: AlertTriangle,
          text: 'Degraded'
        };
      case 'unhealthy':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          icon: AlertTriangle,
          text: 'Unhealthy'
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          icon: Minus,
          text: 'Unknown'
        };
    }
  };

  // Get trend icon
  const getTrendIcon = (data: MetricSnapshot[], metric: keyof MetricSnapshot) => {
    if (data.length < 2) return Minus;

    const recent = data.slice(-10);
    const older = data.slice(-20, -10);

    if (recent.length === 0 || older.length === 0) return Minus;

    const recentAvg = recent.reduce((sum, item) => sum + (item[metric] as number), 0) / recent.length;
    const olderAvg = older.reduce((sum, item) => sum + (item[metric] as number), 0) / older.length;

    const change = ((recentAvg - olderAvg) / olderAvg) * 100;

    if (Math.abs(change) < 5) return Minus;
    return change > 0 ? TrendingUp : TrendingDown;
  };

  // Format metric value
  const formatMetricValue = (value: number, metric: string) => {
    switch (metric) {
      case 'api_response_time':
        return `${value.toFixed(0)}ms`;
      case 'prediction_accuracy':
      case 'cache_hit_rate':
        return `${(value * 100).toFixed(1)}%`;
      case 'system_cpu':
      case 'system_memory':
        return `${value.toFixed(1)}%`;
      case 'error_rate':
        return `${(value * 100).toFixed(2)}%`;
      default:
        return value.toFixed(0);
    }
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'bg-blue-100 text-blue-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'critical':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Prepare chart data
  const prepareChartData = (data: MetricSnapshot[]) => {
    return data.map(item => ({
      ...item,
      timestamp: new Date(item.timestamp).toLocaleTimeString(),
      prediction_accuracy_percent: item.prediction_accuracy * 100,
      cache_hit_rate_percent: item.cache_hit_rate * 100,
      error_rate_percent: item.error_rate * 100,
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading system health data...</span>
      </div>
    );
  }

  if (!systemStatus) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold">Unable to load system status</h3>
            <p className="text-gray-600">Please check your connection and try again</p>
            <Button onClick={loadData} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const statusDisplay = getStatusDisplay(systemStatus.status, systemStatus.health_score);
  const chartData = prepareChartData(historicalData);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">System Health Dashboard</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          <Button onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Now
          </Button>
        </div>
      </div>

      {/* System Status Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            System Status Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-full ${statusDisplay.bgColor}`}>
                <statusDisplay.icon className={`h-6 w-6 ${statusDisplay.color}`} />
              </div>
              <div>
                <p className="text-sm text-gray-600">Overall Status</p>
                <p className="text-lg font-semibold">{statusDisplay.text}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-full bg-blue-100">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Health Score</p>
                <p className="text-lg font-semibold">{(systemStatus.health_score * 100).toFixed(1)}%</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-full bg-red-100">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Recent Alerts</p>
                <p className="text-lg font-semibold">{systemStatus.recent_alerts}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-full bg-green-100">
                <Clock className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Last Updated</p>
                <p className="text-lg font-semibold">
                  {new Date(systemStatus.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">API Response Time</p>
                <p className="text-2xl font-bold">
                  {formatMetricValue(systemStatus.metrics.api_response_time, 'api_response_time')}
                </p>
              </div>
              {React.createElement(getTrendIcon(historicalData, 'api_response_time'), {
                className: 'h-5 w-5 text-gray-500'
              })}
            </div>
            <Progress
              value={Math.min(systemStatus.metrics.api_response_time / 10, 100)}
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Prediction Accuracy</p>
                <p className="text-2xl font-bold">
                  {formatMetricValue(systemStatus.metrics.prediction_accuracy, 'prediction_accuracy')}
                </p>
              </div>
              {React.createElement(getTrendIcon(historicalData, 'prediction_accuracy'), {
                className: 'h-5 w-5 text-gray-500'
              })}
            </div>
            <Progress
              value={systemStatus.metrics.prediction_accuracy * 100}
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Cache Hit Rate</p>
                <p className="text-2xl font-bold">
                  {formatMetricValue(systemStatus.metrics.cache_hit_rate, 'cache_hit_rate')}
                </p>
              </div>
              {React.createElement(getTrendIcon(historicalData, 'cache_hit_rate'), {
                className: 'h-5 w-5 text-gray-500'
              })}
            </div>
            <Progress
              value={systemStatus.metrics.cache_hit_rate * 100}
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Error Rate</p>
                <p className="text-2xl font-bold">
                  {formatMetricValue(systemStatus.metrics.error_rate, 'error_rate')}
                </p>
              </div>
              {React.createElement(getTrendIcon(historicalData, 'error_rate'), {
                className: 'h-5 w-5 text-gray-500'
              })}
            </div>
            <Progress
              value={systemStatus.metrics.error_rate * 1000}
              className="mt-2"
            />
          </CardContent>
        </Card>
      </div>

      {/* Data Sources Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Globe className="h-5 w-5 mr-2" />
            Data Sources Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(systemStatus.data_sources).map(([source, available]) => (
              <div key={source} className="flex items-center space-x-3 p-3 rounded-lg bg-gray-50">
                <div className={`w-3 h-3 rounded-full ${available ? 'bg-green-500' : 'bg-red-500'}`} />
                <div>
                  <p className="font-medium capitalize">{source.replace('_', ' ')}</p>
                  <p className={`text-sm ${available ? 'text-green-600' : 'text-red-600'}`}>
                    {available ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Charts */}
      <Tabs defaultValue="performance" className="w-full">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="sla">SLA Compliance</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="bottlenecks">Bottlenecks</TabsTrigger>
        </TabsList>

        <TabsContent value="performance">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>API Response Time (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="api_response_time"
                      stroke="#8884d8"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Prediction Accuracy (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="prediction_accuracy_percent"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>System Resources (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="system_cpu"
                      stroke="#ff7300"
                      name="CPU %"
                    />
                    <Line
                      type="monotone"
                      dataKey="system_memory"
                      stroke="#00ff7f"
                      name="Memory %"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache Performance (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="cache_hit_rate_percent"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sla">
          <Card>
            <CardHeader>
              <CardTitle>SLA Compliance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(systemStatus.sla_compliance).map(([metric, compliance]) => (
                  <div key={metric} className="space-y-2">
                    <div className="flex justify-between">
                      <span className="font-medium capitalize">
                        {metric.replace('_', ' ')}
                      </span>
                      <span className="font-bold">
                        {(compliance * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={compliance * 100} />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Target: 95%+</span>
                      <Badge variant={compliance >= 0.95 ? "default" : "destructive"}>
                        {compliance >= 0.95 ? "Meeting SLA" : "Below SLA"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold">No Recent Alerts</h3>
                  <p className="text-gray-600">System is running smoothly</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.slice(0, 10).map((alert) => (
                    <div key={alert.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Badge className={getSeverityColor(alert.severity)}>
                          {alert.severity}
                        </Badge>
                        <div>
                          <p className="font-medium">{alert.metric}</p>
                          <p className="text-sm text-gray-600">{alert.message}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </p>
                        {alert.resolved && (
                          <Badge variant="outline" className="mt-1">
                            Resolved
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bottlenecks">
          <Card>
            <CardHeader>
              <CardTitle>Performance Bottlenecks (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              {bottlenecks.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold">No Bottlenecks Detected</h3>
                  <p className="text-gray-600">System performance is optimal</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {bottlenecks.slice(0, 5).map((bottleneck, index) => (
                    <div key={index} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge className={getSeverityColor(bottleneck.severity)}>
                            {bottleneck.severity}
                          </Badge>
                          <span className="font-medium">{bottleneck.type.replace('_', ' ')}</span>
                        </div>
                        <Badge variant="outline">
                          {bottleneck.affected_component}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{bottleneck.root_cause}</p>
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>Impact: {(bottleneck.impact_score * 100).toFixed(0)}%</span>
                        <span>Confidence: {(bottleneck.confidence_score * 100).toFixed(0)}%</span>
                        <span>{new Date(bottleneck.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemHealth;