import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, Database, Key, Search, ChevronRight, ArrowLeft, Filter, X } from 'lucide-react';
import { listTables, getTableSchema, TableInfo, TableSchema } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AppLayout } from '@/components/layout/AppLayout';

interface GlobalSearchResult {
  tableName: string;
  columnName?: string;
  columnType?: string;
  matchType: 'table' | 'column' | 'type';
  context?: string;
}

export default function SchemaExplorerPage() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [allSchemas, setAllSchemas] = useState<Map<string, TableSchema>>(new Map());
  const [selectedTable, setSelectedTable] = useState<TableSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [loadingAllSchemas, setLoadingAllSchemas] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'simple' | 'global'>('simple');

  useEffect(() => {
    loadTables();
  }, []);

  // Load all schemas for global search (cached after first load)
  const loadAllSchemas = async () => {
    if (allSchemas.size > 0 || loadingAllSchemas) return; // Already loaded or loading
    
    setLoadingAllSchemas(true);
    try {
      const schemas = new Map<string, TableSchema>();
      // Load schemas in parallel batches of 5 to avoid overwhelming the server
      const batchSize = 5;
      for (let i = 0; i < tables.length; i += batchSize) {
        const batch = tables.slice(i, i + batchSize);
        const results = await Promise.all(
          batch.map(table => getTableSchema(table.name).catch(() => null))
        );
        results.forEach((schema, idx) => {
          if (schema) {
            schemas.set(batch[idx].name, schema);
          }
        });
      }
      setAllSchemas(schemas);
    } catch (err) {
      console.error('Failed to load all schemas:', err);
    } finally {
      setLoadingAllSchemas(false);
    }
  };

  // Trigger schema loading when switching to global search
  useEffect(() => {
    if (searchMode === 'global' && tables.length > 0) {
      loadAllSchemas();
    }
  }, [searchMode, tables.length]);

  const loadTables = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listTables();
      setTables(data.tables);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  const loadTableSchema = async (tableName: string) => {
    try {
      setLoadingSchema(true);
      
      // Check cache first
      if (allSchemas.has(tableName)) {
        setSelectedTable(allSchemas.get(tableName)!);
        setLoadingSchema(false);
        return;
      }
      
      const schema = await getTableSchema(tableName);
      setSelectedTable(schema);
      
      // Add to cache
      setAllSchemas(prev => new Map(prev).set(tableName, schema));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schema');
    } finally {
      setLoadingSchema(false);
    }
  };

  // Simple table name search
  const filteredTables = useMemo(() => {
    if (!searchQuery.trim()) return tables;
    const query = searchQuery.toLowerCase();
    return tables.filter(table =>
      table.name.toLowerCase().includes(query)
    );
  }, [tables, searchQuery]);

  // Global search across tables, columns, and types
  const globalSearchResults = useMemo((): GlobalSearchResult[] => {
    if (!searchQuery.trim() || searchMode !== 'global') return [];
    
    const query = searchQuery.toLowerCase();
    const results: GlobalSearchResult[] = [];
    const seen = new Set<string>(); // Deduplicate

    allSchemas.forEach((schema, tableName) => {
      // Search table name
      if (tableName.toLowerCase().includes(query)) {
        const key = `table:${tableName}`;
        if (!seen.has(key)) {
          results.push({
            tableName,
            matchType: 'table',
            context: `${schema.columns.length} columns, ${schema.rowCount} rows`
          });
          seen.add(key);
        }
      }

      // Search column names and types
      schema.columns.forEach(column => {
        const key = `column:${tableName}.${column.name}`;
        
        if (column.name.toLowerCase().includes(query) && !seen.has(key)) {
          results.push({
            tableName,
            columnName: column.name,
            columnType: column.type,
            matchType: 'column',
            context: `${column.type}${column.primaryKey ? ' (PK)' : ''}${column.foreignKey ? ' (FK)' : ''}`
          });
          seen.add(key);
        } else if (column.type.toLowerCase().includes(query) && !seen.has(key)) {
          results.push({
            tableName,
            columnName: column.name,
            columnType: column.type,
            matchType: 'type',
            context: column.type
          });
          seen.add(key);
        }
      });
    });

    // Sort: tables first, then columns, then types
    return results.sort((a, b) => {
      const order = { table: 0, column: 1, type: 2 };
      return order[a.matchType] - order[b.matchType];
    });
  }, [searchQuery, searchMode, allSchemas]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error && tables.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <button onClick={loadTables} className="btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <AppLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Database Schema</h1>
          <p className="text-muted-foreground">
            Explore your database structure, tables, and relationships
          </p>
        </div>

      {/* Global Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchMode === 'global' ? "Search across all tables, columns, and types..." : "Search tables..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-10"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <Button
              variant={searchMode === 'global' ? 'default' : 'outline'}
              onClick={() => setSearchMode(searchMode === 'simple' ? 'global' : 'simple')}
              className="gap-2"
            >
              <Filter className="h-4 w-4" />
              {searchMode === 'global' ? 'Global Search' : 'Table Search'}
            </Button>
          </div>
          
          {searchMode === 'global' && loadingAllSchemas && (
            <p className="text-sm text-muted-foreground mt-2 flex items-center gap-2">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary"></div>
              Loading schema data for global search...
            </p>
          )}
        </CardContent>
      </Card>

      {/* Global Search Results */}
      {searchMode === 'global' && searchQuery && (
        <Card>
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
            <CardDescription>
              {globalSearchResults.length === 0 
                ? 'No matches found' 
                : `${globalSearchResults.length} matches across tables and columns`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {globalSearchResults.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No tables or columns match "{searchQuery}"
              </p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {globalSearchResults.map((result, index) => (
                  <button
                    key={index}
                    onClick={() => loadTableSchema(result.tableName)}
                    className="w-full text-left p-3 border rounded-lg hover:bg-accent transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {result.matchType === 'table' && (
                            <Table className="h-4 w-4 text-primary flex-shrink-0" />
                          )}
                          {result.matchType === 'column' && (
                            <Database className="h-4 w-4 text-blue-500 flex-shrink-0" />
                          )}
                          {result.matchType === 'type' && (
                            <Key className="h-4 w-4 text-green-500 flex-shrink-0" />
                          )}
                          <span className="font-medium truncate">
                            {result.tableName}
                            {result.columnName && (
                              <span className="text-muted-foreground">
                                .{result.columnName}
                              </span>
                            )}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground truncate">
                          {result.context}
                        </p>
                      </div>
                      <Badge variant={
                        result.matchType === 'table' ? 'default' :
                        result.matchType === 'column' ? 'secondary' : 'outline'
                      } className="flex-shrink-0 capitalize">
                        {result.matchType}
                      </Badge>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Tables List - Show in simple mode or when no search active */}
        {(searchMode === 'simple' || !searchQuery) && (
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Tables ({filteredTables.length}/{tables.length})
              </CardTitle>
              <CardDescription>Click a table to view its schema</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {filteredTables.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8 text-sm">
                    No tables found
                  </p>
                ) : (
                  filteredTables.map((table) => (
                    <button
                      key={table.name}
                      onClick={() => loadTableSchema(table.name)}
                      className={`w-full text-left p-3 border rounded-lg transition-colors hover:bg-accent ${
                        selectedTable?.tableName === table.name ? 'bg-accent border-primary' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <Table className="h-4 w-4 flex-shrink-0 text-primary" />
                          <span className="font-medium truncate">{table.name}</span>
                        </div>
                        <ChevronRight className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                      </div>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span>{table.rowCount.toLocaleString()} rows</span>
                        <span>•</span>
                        <span>{table.columnCount} columns</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Table Schema Details */}
        <Card className={`${(searchMode === 'simple' || !searchQuery) ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {selectedTable ? (
                    <>
                      <Table className="h-5 w-5" />
                      {selectedTable.tableName}
                    </>
                  ) : (
                    'Select a table'
                  )}
                </CardTitle>
                {selectedTable && (
                  <CardDescription className="mt-2">
                    {selectedTable.rowCount.toLocaleString()} rows • {selectedTable.columns.length} columns
                  </CardDescription>
                )}
              </div>
              {selectedTable && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedTable(null)}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loadingSchema ? (
              <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : selectedTable ? (
              <div className="space-y-6">
                {/* Columns */}
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    Columns
                  </h3>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-muted">
                        <tr>
                          <th className="text-left p-3 text-sm font-medium">Name</th>
                          <th className="text-left p-3 text-sm font-medium">Type</th>
                          <th className="text-left p-3 text-sm font-medium">Constraints</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {selectedTable.columns.map((column, index) => (
                          <tr key={index} className="hover:bg-accent transition-colors">
                            <td className="p-3">
                              <div className="flex items-center gap-2">
                                {column.primaryKey && (
                                  <Key className="h-3 w-3 text-yellow-500" />
                                )}
                                <span className="font-mono text-sm">{column.name}</span>
                              </div>
                            </td>
                            <td className="p-3">
                              <Badge variant="secondary" className="font-mono text-xs">
                                {column.type}
                              </Badge>
                            </td>
                            <td className="p-3">
                              <div className="flex flex-wrap gap-1">
                                {column.primaryKey && (
                                  <Badge variant="default" className="text-xs">
                                    Primary Key
                                  </Badge>
                                )}
                                {column.foreignKey && (
                                  <Badge variant="outline" className="text-xs">
                                    FK: {column.foreignKey}
                                  </Badge>
                                )}
                                {!column.nullable && (
                                  <Badge variant="secondary" className="text-xs">
                                    NOT NULL
                                  </Badge>
                                )}
                                {column.defaultValue && (
                                  <Badge variant="secondary" className="text-xs">
                                    Default: {column.defaultValue}
                                  </Badge>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Sample Data */}
                {selectedTable.sampleData && selectedTable.sampleData.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3 flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      Sample Data (First 5 rows)
                    </h3>
                    <div className="border rounded-lg overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-muted">
                          <tr>
                            {Object.keys(selectedTable.sampleData[0]).map((key) => (
                              <th key={key} className="text-left p-3 text-sm font-medium">
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {selectedTable.sampleData.map((row, index) => (
                            <tr key={index} className="hover:bg-accent transition-colors">
                              {Object.values(row).map((value, i) => (
                                <td key={i} className="p-3 text-sm font-mono">
                                  {value === null ? (
                                    <span className="text-muted-foreground italic">null</span>
                                  ) : (
                                    String(value)
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-96 text-center">
                <Database className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Table Selected</h3>
                <p className="text-muted-foreground">
                  {searchMode === 'global' 
                    ? 'Search for tables and columns using the search bar above, then click a result to view details'
                    : 'Select a table from the list to view its schema and sample data'}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      </div>
    </AppLayout>
  );
}
