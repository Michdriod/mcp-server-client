import { Table2, Code, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ViewMode } from '@/lib/types';
import { cn } from '@/lib/utils';

interface ViewToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

const views: { mode: ViewMode; icon: typeof Table2; label: string }[] = [
  { mode: 'table', icon: Table2, label: 'Table' },
  { mode: 'json', icon: Code, label: 'JSON' },
  { mode: 'csv', icon: FileText, label: 'CSV' },
];

export function ViewToggle({ mode, onChange }: ViewToggleProps) {
  return (
    <div className="inline-flex items-center bg-muted rounded-lg p-1">
      {views.map((view) => (
        <Button
          key={view.mode}
          variant="ghost"
          size="sm"
          onClick={() => onChange(view.mode)}
          className={cn(
            "gap-1.5 px-3 h-8",
            mode === view.mode 
              ? "bg-card shadow-sm text-foreground" 
              : "text-muted-foreground hover:text-foreground hover:bg-transparent"
          )}
        >
          <view.icon className="w-4 h-4" />
          <span className="hidden sm:inline">{view.label}</span>
        </Button>
      ))}
    </div>
  );
}
