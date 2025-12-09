import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bookmark, Search, Play, Trash2, Clock } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { EmptyState } from '@/components/common/EmptyState';
import { LoadingState } from '@/components/common/LoadingState';
import { getSavedQueries, deleteQuery } from '@/lib/api';
import { SavedQuery } from '@/lib/types';
import { toast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

export default function SavedQueriesPage() {
  const [queries, setQueries] = useState<SavedQuery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadQueries();
  }, []);

  const loadQueries = async () => {
    try {
      const data = await getSavedQueries();
      setQueries(data);
    } catch {
      toast({
        title: 'Failed to load saved queries',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    
    try {
      await deleteQuery(deleteId);
      setQueries(queries.filter(q => q.id !== deleteId));
      toast({
        title: 'Query deleted',
        description: 'The saved query has been removed.',
      });
    } catch {
      toast({
        title: 'Failed to delete query',
        variant: 'destructive',
      });
    } finally {
      setDeleteId(null);
    }
  };

  const filteredQueries = queries.filter(q =>
    q.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    q.query.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <AppLayout>
      <div className="p-6 lg:p-8 max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-foreground">Saved Queries</h1>
            <p className="text-muted-foreground">
              Your collection of saved queries for quick access
            </p>
          </div>
        </div>

        {/* Search */}
        {queries.length > 0 && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search saved queries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        )}

        {/* Content */}
        {isLoading ? (
          <LoadingState message="Loading saved queries..." />
        ) : queries.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <EmptyState
              icon={<Bookmark className="w-6 h-6" />}
              title="No saved queries"
              description="Save queries from the Query page to access them quickly"
              action={
                <Button onClick={() => navigate('/')}>
                  Go to Query
                </Button>
              }
            />
          </div>
        ) : filteredQueries.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <EmptyState
              icon={<Search className="w-6 h-6" />}
              title="No matching queries"
              description="Try adjusting your search term"
            />
          </div>
        ) : (
          <div className="space-y-3">
            {filteredQueries.map((query) => (
              <div
                key={query.id}
                className={cn(
                  "bg-card border border-border rounded-xl p-5 shadow-soft",
                  "hover:border-primary/20 transition-all duration-200"
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0 space-y-2">
                    <h3 className="font-medium text-foreground truncate">
                      {query.name}
                    </h3>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {query.query}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      <span>Created {formatDate(query.createdAt)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={runningId === query.id}
                      onClick={() => {
                        setRunningId(query.id);
                        // Navigate to query page with the query
                        navigate('/', { state: { query: query.query } });
                        // Reset running state after navigation
                        setTimeout(() => setRunningId(null), 100);
                      }}
                    >
                      <Play className="w-4 h-4" />
                      <span className="hidden sm:inline">Run</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setDeleteId(query.id)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete saved query?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The query will be permanently removed from your collection.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
}
