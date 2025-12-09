import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, Play, AlertCircle, CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/common/EmptyState';
import { LoadingState } from '@/components/common/LoadingState';
import { getQueryHistory } from '@/lib/api';
import { QueryHistoryItem } from '@/lib/types';
import { toast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

export default function HistoryPage() {
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [runningId, setRunningId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getQueryHistory();
      setHistory(data);
    } catch {
      toast({
        title: 'Failed to load history',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusIcon = (status: QueryHistoryItem['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-success" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-destructive" />;
      case 'pending':
        return <RefreshCw className="w-4 h-4 text-warning animate-spin" />;
    }
  };

  return (
    <AppLayout>
      <div className="p-6 lg:p-8 max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-foreground">Query History</h1>
          <p className="text-muted-foreground">
            View and re-run your recent queries
          </p>
        </div>

        {/* Content */}
        {isLoading ? (
          <LoadingState message="Loading history..." />
        ) : history.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <EmptyState
              icon={<History className="w-6 h-6" />}
              title="No query history"
              description="Your executed queries will appear here"
              action={
                <Button onClick={() => navigate('/')}>
                  Start Querying
                </Button>
              }
            />
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <div
                key={item.id}
                className={cn(
                  "bg-card border border-border rounded-xl p-5 shadow-soft",
                  "hover:border-primary/20 transition-all duration-200"
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-start gap-2">
                      {getStatusIcon(item.status)}
                      <p className="text-sm text-foreground flex-1">
                        {item.query}
                      </p>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(item.createdAt)}
                      </div>
                      
                      {item.status === 'success' && (
                        <>
                          {item.rowCount !== undefined && (
                            <span>{item.rowCount} rows</span>
                          )}
                          {item.executionTime !== undefined && (
                            <span>{item.executionTime.toFixed(0)}ms</span>
                          )}
                        </>
                      )}
                      
                      {item.status === 'error' && item.error && (
                        <span className="text-destructive">{item.error}</span>
                      )}
                    </div>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={runningId === item.id}
                    onClick={() => {
                      setRunningId(item.id);
                      navigate('/', { state: { query: item.query } });
                      // Reset running state after navigation
                      setTimeout(() => setRunningId(null), 100);
                    }}
                  >
                    <Play className="w-4 h-4" />
                    <span className="hidden sm:inline">Re-run</span>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
