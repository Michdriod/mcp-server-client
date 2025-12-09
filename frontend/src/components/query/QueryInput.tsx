import React, { useState, KeyboardEvent, useEffect } from 'react';
import { Send, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  initialValue?: string;
}

const exampleQueries = [
  "Which customers ordered keyboards?",
  "Show me customers with the most orders",
  "What orders are still pending?",
  "Total revenue by customer",
];

export function QueryInput({ onSubmit, isLoading, initialValue }: QueryInputProps) {
  const [query, setQuery] = useState(initialValue || '');

  // Update query when initialValue changes
  useEffect(() => {
    if (initialValue) {
      setQuery(initialValue);
    }
  }, [initialValue]);

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-4">
      {/* Query input */}
      <div className="relative">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data..."
          className="query-input pr-24"
          rows={3}
          disabled={isLoading}
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          <span className="text-xs text-muted-foreground hidden sm:inline">
            {navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}+Enter
          </span>
          <Button 
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading}
            size="sm"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Run</span>
          </Button>
        </div>
      </div>

      {/* Example queries or pre-filled indicator */}
      {initialValue ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-success">
            <Sparkles className="w-4 h-4" />
            <span>Query loaded from {initialValue.trim().length > 50 ? 'history' : 'saved queries'}</span>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="w-4 h-4" />
            <span>Try an example:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className={cn(
                  "example-chip",
                  query === example && "bg-primary/10 text-primary"
                )}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
