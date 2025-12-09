import { ViewMode } from '@/lib/types';
import { ResultsTable } from './ResultsTable';

interface ResultsViewProps {
  mode: ViewMode;
  columns: string[];
  rows: Record<string, unknown>[];
}

export function ResultsView({ mode, columns, rows }: ResultsViewProps) {
  if (mode === 'table') {
    return <ResultsTable columns={columns} rows={rows} />;
  }

  if (mode === 'json') {
    return (
      <pre className="code-block overflow-auto max-h-[400px]">
        <code>{JSON.stringify(rows, null, 2)}</code>
      </pre>
    );
  }

  if (mode === 'csv') {
    const csv = [
      columns.join(','),
      ...rows.map(row => 
        columns.map(col => {
          const val = row[col];
          if (val === null || val === undefined) return '';
          const str = String(val);
          return str.includes(',') || str.includes('"') 
            ? `"${str.replace(/"/g, '""')}"` 
            : str;
        }).join(',')
      )
    ].join('\n');

    return (
      <pre className="code-block overflow-auto max-h-[400px]">
        <code>{csv}</code>
      </pre>
    );
  }

  return null;
}
