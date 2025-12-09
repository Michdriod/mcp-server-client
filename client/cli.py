"""
CLI Application for Database Query Assistant

A powerful command-line interface for natural language database queries,
with interactive mode and rich formatting.
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import json

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import QueryAssistantClient

# Initialize
app = typer.Typer(
    name="dbquery",
    help="Database Query Assistant CLI - Natural language database queries",
    add_completion=False
)
console = Console()


# Helper function for async operations
def run_async(coro):
    """Run async function"""
    return asyncio.run(coro)


@app.command()
def query(
    question: str = typer.Argument(..., help="Natural language query"),
    user_id: int = typer.Option(1, "--user", "-u", help="User ID (1=admin, 2=sales, 3=finance)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: table, json, csv"),
    save: bool = typer.Option(False, "--save", "-s", help="Save results to file"),
    chart: Optional[str] = typer.Option(None, "--chart", "-c", help="Generate chart: line, bar, pie"),
):
    """
    Execute a natural language database query
    
    Examples:
        dbquery query "Show me the top 5 customers by order value"
        dbquery query "What were last month's sales?" --user 2
        dbquery query "List all products" --output json
        dbquery query "Show revenue trends" --chart line
    """
    output_format = output or "table"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description="Executing query...", total=None)
        
        try:
            # Execute query and optionally generate chart in single session
            async def execute():
                async with QueryAssistantClient() as client:
                    query_result = await client.query_database(question, user_id)
                    
                    # If chart requested, generate it in same session
                    chart_result = None
                    if chart and query_result and ('results' in query_result or 'rows' in query_result):
                        progress.update(task, description="Generating chart...")
                        results = query_result.get('results') or query_result.get('rows', [])
                        if results:
                            chart_result = await client.generate_chart(
                                data=results,
                                chart_type=chart,
                                title=question[:50] + "..." if len(question) > 50 else question
                            )
                    
                    return query_result, chart_result
            
            result, chart_result = run_async(execute())
            progress.remove_task(task)
            
            if not result or ('results' not in result and 'rows' not in result):
                # Check if there's an error message
                if 'error' in result:
                    console.print(f"[red]❌ Error: {result['error']}[/red]")
                else:
                    console.print("[red]❌ No results returned[/red]")
                raise typer.Exit(1)
            
            # Display results  
            results = result.get('results') or result.get('rows', [])
            metadata = result
            
            # Show metadata
            console.print()
            console.print(Panel.fit(
                f"[green]✓[/green] Query executed successfully\n"
                f"Rows: {metadata.get('row_count', 0)} | "
                f"Columns: {metadata.get('column_count', 0)} | "
                f"Time: {metadata.get('execution_time_ms', 0):.0f}ms | "
                f"Cached: {'Yes 🚀' if metadata.get('cached') else 'No'}",
                title="Query Results",
                border_style="green"
            ))
            console.print()
            
            # Display based on format
            if output_format == "json":
                console.print_json(data=results)
            
            elif output_format == "csv":
                if results:
                    # Print CSV
                    keys = results[0].keys()
                    console.print(",".join(keys))
                    for row in results:
                        console.print(",".join(str(row.get(k, "")) for k in keys))
            
            else:  # table format
                if results:
                    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
                    
                    # Add columns
                    keys = list(results[0].keys())
                    for key in keys:
                        table.add_column(key)
                    
                    # Add rows
                    for row in results[:50]:  # Limit to 50 rows for readability
                        table.add_row(*[str(row.get(k, "")) for k in keys])
                    
                    console.print(table)
                    
                    if len(results) > 50:
                        console.print(f"\n[yellow]Showing 50 of {len(results)} rows[/yellow]")
            
            # Save to file
            if save:
                filename = f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                console.print(f"\n[green]✓[/green] Results saved to {filename}")
            
            # Display chart result if generated
            if chart_result:
                # Parse the result if it's a string
                if isinstance(chart_result, str):
                    try:
                        chart_result = json.loads(chart_result)
                    except:
                        pass
                
                if isinstance(chart_result, dict) and 'filepath' in chart_result:
                    console.print(f"\n[green]✓[/green] Chart saved to {chart_result['filepath']}")
                elif isinstance(chart_result, dict):
                    console.print(f"\n[green]✓[/green] Chart generated: {chart_result}")
            elif chart and results:
                console.print("\n[yellow]⚠[/yellow] Chart generation was requested but failed")
            
        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def saved(
    user_id: int = typer.Option(1, "--user", "-u", help="User ID"),
    action: str = typer.Argument("list", help="Action: list, execute, save"),
    query_id: Optional[int] = typer.Option(None, "--id", help="Query ID for execute action"),
):
    """
    Manage saved queries
    
    Examples:
        dbquery saved list
        dbquery saved execute --id 5
    """
    try:
        if action == "list":
            async def list_queries():
                async with QueryAssistantClient() as client:
                    return await client.list_saved_queries(user_id)
            
            queries = run_async(list_queries())
            
            if queries:
                table = Table(title="Saved Queries", box=box.ROUNDED)
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Description")
                table.add_column("Query")
                table.add_column("Created")
                
                for q in queries:
                    table.add_row(
                        str(q['id']),
                        q['name'],
                        q.get('description', '')[:30] + "..." if len(q.get('description', '')) > 30 else q.get('description', ''),
                        q['natural_query'][:40] + "..." if len(q['natural_query']) > 40 else q['natural_query'],
                        str(q.get('created_at', ''))[:19]
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No saved queries found[/yellow]")
        
        elif action == "execute":
            if not query_id:
                console.print("[red]❌ --id is required for execute action[/red]")
                raise typer.Exit(1)
            
            async def load_and_execute():
                async with QueryAssistantClient() as client:
                    query_data = await client.load_saved_query(user_id, query_id)
                    if query_data:
                        return await client.query_database(query_data['natural_query'], user_id)
            
            result = run_async(load_and_execute())
            
            if result and 'results' in result:
                console.print(f"[green]✓[/green] Executed saved query #{query_id}")
                # Display results (simplified)
                console.print_json(data=result['results'][:5])
            else:
                console.print("[red]❌ Failed to execute[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def schedule(
    user_id: int = typer.Option(1, "--user", "-u", help="User ID"),
    action: str = typer.Argument("list", help="Action: list, create, delete, trigger"),
    schedule_id: Optional[int] = typer.Option(None, "--id", help="Schedule ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Report name"),
    query: Optional[str] = typer.Option(None, "--query", help="Natural language query"),
    cron: Optional[str] = typer.Option(None, "--cron", help="Cron expression"),
    email: Optional[str] = typer.Option(None, "--email", help="Email address"),
    format: str = typer.Option("csv", "--format", help="Export format: csv, excel, pdf"),
):
    """
    Manage scheduled reports
    
    Examples:
        dbquery schedule list
        dbquery schedule create --name "Daily Sales" --query "Show today's sales" --cron "0 9 * * *" --email user@example.com
        dbquery schedule trigger --id 5
        dbquery schedule delete --id 5
    """
    try:
        if action == "list":
            async def list_schedules():
                async with QueryAssistantClient() as client:
                    return await client.list_scheduled_reports(user_id)
            
            schedules = run_async(list_schedules())
            
            if schedules:
                table = Table(title="Scheduled Reports", box=box.ROUNDED)
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Query")
                table.add_column("Schedule")
                table.add_column("Email")
                table.add_column("Status")
                
                for s in schedules:
                    status = "✓ Active" if s['is_active'] else "⏸ Paused"
                    table.add_row(
                        str(s['id']),
                        s['name'],
                        s['query'][:30] + "..." if len(s['query']) > 30 else s['query'],
                        s['schedule'],
                        s['email'],
                        status
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No scheduled reports found[/yellow]")
        
        elif action == "create":
            if not all([name, query, cron, email]):
                console.print("[red]❌ --name, --query, --cron, and --email are required[/red]")
                raise typer.Exit(1)
            
            async def create():
                async with QueryAssistantClient() as client:
                    return await client.create_scheduled_report(
                        user_id, name, query, cron, email, format
                    )
            
            result = run_async(create())
            
            if result:
                console.print(Panel.fit(
                    f"[green]✓[/green] Schedule created\n"
                    f"ID: {result.get('schedule_id')}\n"
                    f"Name: {name}\n"
                    f"Schedule: {cron}",
                    title="Success",
                    border_style="green"
                ))
            else:
                console.print("[red]❌ Failed to create schedule[/red]")
        
        elif action == "delete":
            if not schedule_id:
                console.print("[red]❌ --id is required[/red]")
                raise typer.Exit(1)
            
            if Confirm.ask(f"Delete schedule #{schedule_id}?"):
                async def delete():
                    async with QueryAssistantClient() as client:
                        return await client.delete_scheduled_report(user_id, schedule_id)
                
                result = run_async(delete())
                console.print(f"[green]✓[/green] Schedule #{schedule_id} deleted")
        
        elif action == "trigger":
            if not schedule_id:
                console.print("[red]❌ --id is required[/red]")
                raise typer.Exit(1)
            
            async def trigger():
                async with QueryAssistantClient() as client:
                    return await client.trigger_report_now(user_id, schedule_id)
            
            result = run_async(trigger())
            console.print(f"[green]✓[/green] Report #{schedule_id} triggered")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    question: str = typer.Argument(..., help="Natural language query"),
    user_id: int = typer.Option(1, "--user", "-u", help="User ID"),
    format: str = typer.Option("csv", "--format", "-f", help="Format: csv, excel, pdf, json"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename"),
):
    """
    Execute query and export results
    
    Examples:
        dbquery export "Show all customers" --format excel
        dbquery export "Last month's sales" --format pdf --output sales_report.pdf
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description=f"Exporting as {format.upper()}...", total=None)
        
        try:
            async def do_export():
                async with QueryAssistantClient() as client:
                    return await client.export_query_results(user_id, question, format)
            
            result = run_async(do_export())
            progress.remove_task(task)
            
            if result and 'file_path' in result:
                source_path = result['file_path']
                
                # Copy to output path if specified
                if output:
                    import shutil
                    shutil.copy(source_path, output)
                    final_path = output
                else:
                    final_path = source_path
                
                console.print()
                console.print(Panel.fit(
                    f"[green]✓[/green] Export complete\n"
                    f"File: {final_path}\n"
                    f"Size: {os.path.getsize(final_path)} bytes",
                    title="Success",
                    border_style="green"
                ))
            else:
                console.print("[red]❌ Export failed[/red]")
                raise typer.Exit(1)
        
        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def schema(
    table: Optional[str] = typer.Option(None, "--table", "-t", help="Show specific table"),
):
    """
    Display database schema information
    
    Examples:
        dbquery schema
        dbquery schema --table customers
    """
    try:
        async def get_schema():
            async with QueryAssistantClient() as client:
                if table:
                    # Get full schema and filter
                    schema = await client.get_schema_info()
                    return [s for s in schema if s['table_name'] == table]
                else:
                    return await client.get_schema_info()
        
        schema_data = run_async(get_schema())
        
        if schema_data:
            for table_info in schema_data:
                # Table header
                console.print()
                console.print(Panel.fit(
                    f"[bold cyan]Table:[/bold cyan] {table_info['table_name']}",
                    border_style="cyan"
                ))
                
                # Columns
                if 'columns' in table_info:
                    table_display = Table(box=box.SIMPLE)
                    table_display.add_column("Column", style="green")
                    table_display.add_column("Type", style="yellow")
                    table_display.add_column("Nullable", style="cyan")
                    
                    for col in table_info['columns']:
                        table_display.add_row(
                            col['column_name'],
                            col['data_type'],
                            "Yes" if col['is_nullable'] else "No"
                        )
                    
                    console.print(table_display)
                
                # Sample query
                if 'sample_query' in table_info:
                    console.print("\n[bold]Sample Query:[/bold]")
                    syntax = Syntax(table_info['sample_query'], "sql", theme="monokai")
                    console.print(syntax)
        else:
            console.print("[yellow]No schema information available[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def history(
    user_id: int = typer.Option(1, "--user", "-u", help="User ID"),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to show"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of queries to show"),
):
    """
    Show query history
    
    Examples:
        dbquery history
        dbquery history --days 30 --limit 50
    """
    try:
        async def get_history():
            async with QueryAssistantClient() as client:
                return await client.get_query_history(user_id, days)
        
        history_data = run_async(get_history())
        
        if history_data:
            table = Table(title=f"Query History (Last {days} days)", box=box.ROUNDED)
            table.add_column("Time", style="cyan")
            table.add_column("Query", style="green")
            table.add_column("Rows")
            table.add_column("Time (ms)")
            
            for item in history_data[:limit]:
                table.add_row(
                    str(item.get('executed_at', ''))[:19],
                    item['natural_query'][:50] + "..." if len(item['natural_query']) > 50 else item['natural_query'],
                    str(item.get('row_count', 0)),
                    f"{item.get('execution_time_ms', 0):.0f}"
                )
            
            console.print(table)
            
            if len(history_data) > limit:
                console.print(f"\n[yellow]Showing {limit} of {len(history_data)} queries[/yellow]")
        else:
            console.print("[yellow]No query history found[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def stats(
    user_id: int = typer.Option(1, "--user", "-u", help="User ID"),
):
    """
    Show user statistics
    
    Examples:
        dbquery stats
        dbquery stats --user 2
    """
    try:
        async def get_stats():
            async with QueryAssistantClient() as client:
                return await client.get_user_statistics(user_id)
        
        stats_data = run_async(get_stats())
        
        if stats_data:
            console.print()
            console.print(Panel.fit(
                f"[bold cyan]User Statistics[/bold cyan]\n\n"
                f"Total Queries: {stats_data.get('total_queries', 0)}\n"
                f"Saved Queries: {stats_data.get('saved_queries', 0)}\n"
                f"Active Schedules: {stats_data.get('active_schedules', 0)}\n"
                f"Avg Response Time: {stats_data.get('avg_response_time', 0):.0f}ms\n"
                f"Cache Hit Rate: {stats_data.get('cache_hit_rate', 0):.1f}%",
                border_style="cyan"
            ))
        else:
            console.print("[yellow]No statistics available[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive():
    """
    Start interactive query mode
    
    Enter queries one by one and see results immediately.
    Type 'exit' or 'quit' to stop.
    """
    console.print(Panel.fit(
        "[bold cyan]Database Query Assistant - Interactive Mode[/bold cyan]\n\n"
        "Enter natural language queries to search your database.\n"
        "Type [bold]'exit'[/bold] or [bold]'quit'[/bold] to stop.",
        border_style="cyan"
    ))
    
    # Get user ID
    user_id = int(Prompt.ask("\nSelect user", choices=["1", "2", "3"], default="1"))
    
    user_names = {1: "Admin", 2: "Sales Analyst", 3: "Finance Team"}
    console.print(f"\n[green]✓[/green] Logged in as {user_names[user_id]}\n")
    
    while True:
        try:
            # Get query
            query_text = Prompt.ask("\n[bold cyan]Query[/bold cyan]")
            
            if query_text.lower() in ['exit', 'quit', 'q']:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            
            if not query_text.strip():
                continue
            
            # Execute
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(description="Executing...", total=None)
                
                async def execute():
                    async with QueryAssistantClient() as client:
                        return await client.query_database(query_text, user_id)
                
                result = run_async(execute())
                progress.remove_task(task)
            
            if result and 'results' in result:
                results = result['results']
                
                # Show metadata
                console.print(
                    f"\n[green]✓[/green] "
                    f"Rows: {result.get('row_count', 0)} | "
                    f"Time: {result.get('execution_time_ms', 0):.0f}ms"
                )
                
                # Show results (first 10 rows)
                if results:
                    table = Table(box=box.ROUNDED)
                    keys = list(results[0].keys())
                    
                    for key in keys:
                        table.add_column(key)
                    
                    for row in results[:10]:
                        table.add_row(*[str(row.get(k, "")) for k in keys])
                    
                    console.print(table)
                    
                    if len(results) > 10:
                        console.print(f"\n[yellow]Showing 10 of {len(results)} rows[/yellow]")
                else:
                    console.print("[yellow]No results[/yellow]")
            else:
                console.print("[red]❌ Query failed[/red]")
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")


if __name__ == "__main__":
    app()
