import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, TrendingUp, Clock, Database, RefreshCw, Play, Pause } from 'lucide-react';
import { getPopularQueries, getUserStats, PopularQuery, UserStats } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';

const AUTO_REFRESH_INTERVAL = 30000; // 30 seconds

export default function AnalyticsPage() {
  const [popularQueries, setPopularQueries] = useState<PopularQuery[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    loadAnalytics();
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadAnalytics(true); // Silent refresh
    }, AUTO_REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadAnalytics = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);
      
      const [queriesData, statsData] = await Promise.all([
        getPopularQueries(10, 30),
        getUserStats(1, 30)
      ]);
      
      setPopularQueries(queriesData.queries);
      setUserStats(statsData);
      setLastRefresh(new Date());
      
      if (silent) {
        toast({
          title: 'Analytics Refreshed',
          description: 'Data updated successfully',
          duration: 2000,
        });
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load analytics';
      setError(errorMsg);
      if (!silent) {
        toast({
          title: 'Failed to Load Analytics',
          description: errorMsg,
          variant: 'destructive',
        });
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleManualRefresh = () => {
    loadAnalytics();
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
    toast({
      title: autoRefresh ? 'Auto-refresh Disabled' : 'Auto-refresh Enabled',
      description: autoRefresh 
        ? 'Analytics will no longer update automatically' 
        : `Analytics will update every ${AUTO_REFRESH_INTERVAL / 1000} seconds`,
    });
  };

  const getTimeAgo = () => {
    const seconds = Math.floor((new Date().getTime() - lastRefresh.getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <button onClick={() => loadAnalytics()} className="btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const successRate = userStats 
    ? ((userStats.successfulQueries / userStats.totalQueries) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Insights into your query usage and performance over the last 30 days
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">
            Updated {getTimeAgo()}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={toggleAutoRefresh}
            className="gap-2"
          >
            {autoRefresh ? (
              <>
                <Pause className="h-4 w-4" />
                Auto-refresh On
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Auto-refresh Off
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleManualRefresh}
            disabled={loading || refreshing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${(loading || refreshing) ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats?.totalQueries || 0}</div>
            <p className="text-xs text-muted-foreground">
              {userStats?.savedQueries || 0} saved queries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
            <p className="text-xs text-muted-foreground">
              {userStats?.successfulQueries || 0} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Execution Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {userStats?.avgExecutionTime ? `${userStats.avgExecutionTime.toFixed(0)}ms` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Per query average
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Rows</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {userStats?.totalRowsReturned?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Rows returned
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Activity Chart */}
      {userStats?.activityByDay && userStats.activityByDay.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Query Activity (Last 30 Days)</CardTitle>
            <CardDescription>Daily query execution count</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={userStats.activityByDay}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="date" 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="hsl(217, 91%, 50%)" 
                  strokeWidth={2}
                  name="Queries"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Popular Queries */}
      <Card>
        <CardHeader>
          <CardTitle>Most Popular Queries</CardTitle>
          <CardDescription>Top queries by execution count</CardDescription>
        </CardHeader>
        <CardContent>
          {popularQueries.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No popular queries found
            </p>
          ) : (
            <div className="space-y-4">
              {popularQueries.map((query, index) => (
                <div 
                  key={index} 
                  className="flex items-start justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{query.question}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        {query.executionCount} executions
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {query.avgExecutionTime.toFixed(0)}ms avg
                      </span>
                    </div>
                  </div>
                  <div className="ml-4 text-right flex-shrink-0">
                    <div className="text-2xl font-bold text-primary">
                      #{index + 1}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution Time Comparison */}
      {popularQueries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Execution Time Comparison</CardTitle>
            <CardDescription>Average execution time for popular queries</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart 
                data={popularQueries.map((q, i) => ({
                  name: `Query ${i + 1}`,
                  time: q.avgExecutionTime,
                  executions: q.executionCount
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="name" 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar 
                  dataKey="time" 
                  fill="hsl(217, 91%, 50%)" 
                  radius={[4, 4, 0, 0]}
                  name="Avg Time (ms)"
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
