import { Clock, Database, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ExecutionStatsProps {
  executionTime: number;
  rowCount: number;
  cached: boolean;
}

export function ExecutionStats({ executionTime, rowCount, cached }: ExecutionStatsProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 text-sm">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Clock className="w-4 h-4" />
        <span>{executionTime.toFixed(0)}ms</span>
      </div>
      
      <div className="flex items-center gap-2 text-muted-foreground">
        <Database className="w-4 h-4" />
        <span>{rowCount.toLocaleString()} {rowCount === 1 ? 'row' : 'rows'}</span>
      </div>
      
      <div className={cn(
        "flex items-center gap-2 px-2 py-0.5 rounded-full text-xs font-medium",
        cached 
          ? "bg-success/10 text-success" 
          : "bg-muted text-muted-foreground"
      )}>
        <Zap className="w-3 h-3" />
        {cached ? 'Cached' : 'Fresh'}
      </div>
    </div>
  );
}
