import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '@/components/query/QueryInput';
import { ExecutionStats } from '@/components/query/ExecutionStats';
import { ViewToggle } from '@/components/query/ViewToggle';
import { ResultsView } from '@/components/query/ResultsView';
import { ResultsChart } from '@/components/query/ResultsChart';
import { SqlPreview } from '@/components/query/SqlPreview';
import { ExportActions } from '@/components/query/ExportActions';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoadingState, TableSkeleton } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';
import { executeQuery, addToHistory } from '@/lib/api';
import { QueryResult, ViewMode } from '@/lib/types';
import { BarChart3, BookmarkPlus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { saveQuery } from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function QueryPage() {
  const location = useLocation();
  const [result, setResult] = useState<QueryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [lastQuery, setLastQuery] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [queryName, setQueryName] = useState('');
  const [activeTab, setActiveTab] = useState('data');
  const [initialQuery, setInitialQuery] = useState('');

  // Handle initial query from navigation state
  useEffect(() => {
    if (location.state?.query) {
      setInitialQuery(location.state.query);
      // Clear the state to avoid re-running on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleSubmit = async (query: string) => {
    setIsLoading(true);
    setError(null);
    setLastQuery(query);

    try {
      const data = await executeQuery(query);
      console.log('Query result received:', data);
      console.log('Columns:', data.columns);
      console.log('Rows:', data.rows);
      console.log('Row count:', data.rowCount);
      setResult(data);
      addToHistory({
        query,
        status: 'success',
        rowCount: data.rowCount,
        executionTime: data.executionTime,
      });
    } catch (err) {
      console.error('Query error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to execute query';
      setError(errorMessage);
      addToHistory({
        query,
        status: 'error',
        error: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastQuery) {
      handleSubmit(lastQuery);
    }
  };

  const handleSaveQuery = async () => {
    if (!queryName.trim()) return;
    
    try {
      await saveQuery(queryName.trim(), lastQuery);
      toast({
        title: 'Query saved',
        description: `"${queryName}" has been saved to your collection.`,
      });
      setShowSaveDialog(false);
      setQueryName('');
    } catch {
      toast({
        title: 'Failed to save query',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  return (
    <AppLayout>
      <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-foreground">Query</h1>
          <p className="text-muted-foreground">
            Ask questions about your data in natural language
          </p>
        </div>

        {/* Query Input */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
          <QueryInput 
            onSubmit={handleSubmit} 
            isLoading={isLoading}
            initialValue={initialQuery}
          />
        </div>

        {/* Results */}
        {isLoading && (
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <LoadingState message="Analyzing your question..." />
          </div>
        )}

        {error && !isLoading && (
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <ErrorState 
              title="Query failed"
              message={error}
              onRetry={handleRetry}
            />
          </div>
        )}

        {result && !isLoading && !error && (
          <div className="bg-card border border-border rounded-xl shadow-soft animate-fade-in">
            {/* Results header */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 border-b border-border">
              <ExecutionStats
                executionTime={result.executionTime}
                rowCount={result.rowCount}
                cached={result.cached}
              />
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSaveDialog(true)}
                >
                  <BookmarkPlus className="w-4 h-4" />
                  <span className="hidden sm:inline">Save</span>
                </Button>
                <ExportActions 
                  columns={result.columns} 
                  rows={result.rows}
                  queryId={result.queryId}
                />
              </div>
            </div>

            {/* Tabs for data and chart */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <div className="flex items-center justify-between px-5 pt-4 gap-4 flex-wrap">
                <TabsList className="bg-muted">
                  <TabsTrigger value="data" className="gap-2">
                    <Search className="w-4 h-4" />
                    Data
                  </TabsTrigger>
                  <TabsTrigger value="chart" className="gap-2">
                    <BarChart3 className="w-4 h-4" />
                    Chart
                  </TabsTrigger>
                </TabsList>
                {activeTab === 'data' && (
                  <ViewToggle mode={viewMode} onChange={setViewMode} />
                )}
              </div>

              <TabsContent value="data" className="p-5 pt-4">
                {result.rows.length === 0 && result.emptyResultMessage ? (
                  <div className="bg-muted/50 border border-border rounded-lg p-8 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <Search className="w-12 h-12 text-muted-foreground" />
                      <div className="space-y-1">
                        <h3 className="font-medium text-foreground">No Results Found</h3>
                        <p className="text-sm text-muted-foreground max-w-md">
                          {result.emptyResultMessage}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <ResultsView 
                    mode={viewMode} 
                    columns={result.columns} 
                    rows={result.rows} 
                  />
                )}
              </TabsContent>

              <TabsContent value="chart" className="p-5 pt-4">
                <ResultsChart columns={result.columns} rows={result.rows} />
              </TabsContent>
            </Tabs>

            {/* SQL Preview */}
            <div className="p-5 pt-0">
              <SqlPreview sql={result.sql} />
            </div>
          </div>
        )}

        {!result && !isLoading && !error && (
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <EmptyState
              icon={<Search className="w-6 h-6" />}
              title="No results yet"
              description="Enter a question above to query your database"
            />
          </div>
        )}
      </div>

      {/* Save Query Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Query</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Query name</Label>
              <Input
                id="name"
                value={queryName}
                onChange={(e) => setQueryName(e.target.value)}
                placeholder="e.g., Top Customers"
              />
            </div>
            <div className="space-y-2">
              <Label>Query</Label>
              <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
                {lastQuery}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveQuery} disabled={!queryName.trim()}>
              Save Query
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
