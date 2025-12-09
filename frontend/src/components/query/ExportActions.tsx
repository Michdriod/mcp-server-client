import { Download, Copy, Check, Server, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { exportQueryResults } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

interface ExportActionsProps {
  columns: string[];
  rows: Record<string, unknown>[];
  queryId?: number; // Optional for server-side export
}

// Threshold for switching to server-side export (10,000 rows)
const SERVER_EXPORT_THRESHOLD = 10000;

export function ExportActions({ columns, rows, queryId }: ExportActionsProps) {
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);

  const isLargeDataset = rows.length >= SERVER_EXPORT_THRESHOLD;
  const canUseServerExport = queryId !== undefined;

  const generateCSV = () => {
    return [
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
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Client-side export (fast, for small datasets)
  const handleClientExportCSV = () => {
    if (isLargeDataset && canUseServerExport) {
      toast({
        title: 'Large Dataset Detected',
        description: 'Use "Export from Server" for better performance with large datasets.',
        variant: 'default',
      });
    }
    downloadFile(generateCSV(), 'results.csv', 'text/csv');
  };

  const handleClientExportJSON = () => {
    if (isLargeDataset && canUseServerExport) {
      toast({
        title: 'Large Dataset Detected',
        description: 'Consider using server export for large datasets.',
        variant: 'default',
      });
    }
    downloadFile(JSON.stringify(rows, null, 2), 'results.json', 'application/json');
  };

  // Server-side export (handles large datasets, supports Excel)
  const handleServerExport = async (format: 'csv' | 'json' | 'excel') => {
    if (!canUseServerExport) {
      toast({
        title: 'Export Not Available',
        description: 'Server export requires a saved query. Save your query first.',
        variant: 'destructive',
      });
      return;
    }

    setExporting(true);
    try {
      const result = await exportQueryResults(queryId!, format);
      
      if (result.download_url) {
        // Open download URL
        window.open(result.download_url, '_blank');
      } else if (result.content) {
        // Fallback: download content directly
        const extension = format === 'excel' ? 'xlsx' : format;
        downloadFile(result.content, `results.${extension}`, result.mime_type || 'application/octet-stream');
      }
      
      toast({
        title: 'Export Successful',
        description: `Downloaded ${result.filename || `results.${format}`}`,
      });
    } catch (error) {
      console.error('Server export failed:', error);
      toast({
        title: 'Export Failed',
        description: error instanceof Error ? error.message : 'Failed to export data',
        variant: 'destructive',
      });
    } finally {
      setExporting(false);
    }
  };

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generateCSV());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast({
        title: 'Copied to Clipboard',
        description: `${rows.length} rows copied as CSV`,
      });
    } catch (error) {
      toast({
        title: 'Copy Failed',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button 
        variant="outline" 
        size="sm" 
        onClick={handleCopyToClipboard}
        disabled={rows.length === 0}
      >
        {copied ? (
          <Check className="w-4 h-4 text-success" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
        <span className="hidden sm:inline">Copy</span>
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="outline" 
            size="sm"
            disabled={rows.length === 0 || exporting}
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">
              {exporting ? 'Exporting...' : 'Export'}
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          {/* Client-side exports (fast, always available) */}
          <DropdownMenuItem onClick={handleClientExportCSV}>
            <Download className="w-4 h-4 mr-2" />
            Export as CSV {isLargeDataset && '(Quick)'}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleClientExportJSON}>
            <Download className="w-4 h-4 mr-2" />
            Export as JSON {isLargeDataset && '(Quick)'}
          </DropdownMenuItem>

          {/* Server-side exports (for large datasets and Excel) */}
          {canUseServerExport && (
            <>
              <DropdownMenuSeparator />
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                <Server className="w-3 h-3 inline mr-1" />
                Server Export {isLargeDataset && '(Recommended)'}
              </div>
              <DropdownMenuItem 
                onClick={() => handleServerExport('csv')}
                disabled={exporting}
              >
                <Server className="w-4 h-4 mr-2" />
                CSV (Server)
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => handleServerExport('json')}
                disabled={exporting}
              >
                <Server className="w-4 h-4 mr-2" />
                JSON (Server)
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => handleServerExport('excel')}
                disabled={exporting}
              >
                <Server className="w-4 h-4 mr-2" />
                Excel (.xlsx)
              </DropdownMenuItem>
            </>
          )}

          {/* Warning for large datasets without server export */}
          {isLargeDataset && !canUseServerExport && (
            <>
              <DropdownMenuSeparator />
              <div className="px-2 py-2 text-xs text-muted-foreground flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>Save query to enable server export for large datasets</span>
              </div>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
