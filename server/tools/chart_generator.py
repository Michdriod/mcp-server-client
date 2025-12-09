"""
Chart generation tool using matplotlib.
Automatically detects chart type based on data structure.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for faster rendering
import matplotlib.pyplot as plt
import pandas as pd


ChartType = Literal["bar", "line", "pie", "scatter", "table"]


class ChartGenerator:
    """Generate charts from query results."""
    
    def __init__(self, output_dir: str = "charts"):
        """
        Initialize chart generator.
        
        Args:
            output_dir: Directory to save generated charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set matplotlib style - fast style with minimal overhead
        plt.style.use("fast")
    
    def generate_chart(
        self,
        data: list[dict[str, Any]],
        chart_type: ChartType | None = None,
        title: str | None = None,
        x_column: str | None = None,
        y_column: str | None = None,
    ) -> str:
        """
        Generate chart from query results.
        
        Args:
            data: List of dictionaries containing query results
            chart_type: Type of chart to generate (auto-detected if None)
            title: Chart title (auto-generated if None)
            x_column: Column to use for x-axis (auto-detected if None)
            y_column: Column to use for y-axis (auto-detected if None)
        
        Returns:
            Path to generated chart file
        
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Cannot generate chart from empty data")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Auto-detect chart type if not specified
        if chart_type is None:
            chart_type = self._detect_chart_type(df)
        
        # Auto-detect columns if not specified
        if x_column is None or y_column is None:
            x_column, y_column = self._detect_columns(df)
        
        # Generate title if not specified
        if title is None:
            title = f"{chart_type.title()} Chart: {y_column} by {x_column}"
        
        # Create figure with optimized settings
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        
        # Generate chart based on type
        if chart_type == "bar":
            self._create_bar_chart(ax, df, x_column, y_column, title)
        elif chart_type == "line":
            self._create_line_chart(ax, df, x_column, y_column, title)
        elif chart_type == "pie":
            self._create_pie_chart(ax, df, x_column, y_column, title)
        elif chart_type == "scatter":
            self._create_scatter_chart(ax, df, x_column, y_column, title)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Save chart with optimized settings
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{chart_type}_{timestamp}.png"
        filepath = self.output_dir / filename
        
        # Use moderate DPI and optimize flag for faster saving
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close(fig)  # Close specific figure for memory cleanup
        
        return str(filepath)
    
    def _detect_chart_type(self, df: pd.DataFrame) -> ChartType:
        """Auto-detect appropriate chart type based on data structure."""
        num_rows = len(df)
        num_cols = len(df.columns)
        
        # Pie chart: few categories with one numeric value
        if num_rows <= 10 and num_cols == 2:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) == 1:
                return "pie"
        
        # Scatter: two numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) >= 2:
            return "scatter"
        
        # Line chart: time series data
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        if len(date_cols) >= 1 and len(numeric_cols) >= 1:
            return "line"
        
        # Default to bar chart
        return "bar"
    
    def _detect_columns(self, df: pd.DataFrame) -> tuple[str, str]:
        """Auto-detect x and y columns."""
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
        
        # Prefer non-numeric for x-axis, numeric for y-axis
        if non_numeric_cols and numeric_cols:
            return non_numeric_cols[0], numeric_cols[0]
        
        # If all numeric, use first two
        if len(numeric_cols) >= 2:
            return numeric_cols[0], numeric_cols[1]
        
        # Fallback to first two columns
        cols = df.columns.tolist()
        return cols[0], cols[1] if len(cols) > 1 else cols[0]
    
    def _create_bar_chart(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
    ) -> None:
        """Create bar chart."""
        # Sort by y value and limit to top 15 for faster rendering
        df_sorted = df.nlargest(15, y_column)
        
        # Create bars without edges for faster rendering
        ax.bar(df_sorted[x_column].astype(str), df_sorted[y_column], 
               color="steelblue", edgecolor="none")
        ax.set_xlabel(x_column.replace("_", " ").title())
        ax.set_ylabel(y_column.replace("_", " ").title())
        ax.set_title(title, fontsize=13, fontweight="bold")
        
        # Rotate x labels if needed
        if len(df_sorted) > 8:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
        
        # Add value labels on top of bars (only if not too many)
        if len(df_sorted) <= 10:
            for i, v in enumerate(df_sorted[y_column]):
                ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=8)
    
    def _create_line_chart(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
    ) -> None:
        """Create line chart."""
        ax.plot(df[x_column], df[y_column], marker="o", linewidth=2, 
                color="steelblue", markersize=4)
        ax.set_xlabel(x_column.replace("_", " ").title())
        ax.set_ylabel(y_column.replace("_", " ").title())
        ax.set_title(title, fontsize=13, fontweight="bold")
        
        # Rotate x labels if needed
        if len(df) > 8:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
        
        # Add lighter grid
        ax.grid(True, alpha=0.2, linewidth=0.5)
    
    def _create_pie_chart(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
    ) -> None:
        """Create pie chart with smart grouping for small slices."""
        # Sort by value descending
        df_sorted = df.sort_values(y_column, ascending=False).reset_index(drop=True)
        
        # Calculate total and percentages
        total = df_sorted[y_column].sum()
        df_sorted['percentage'] = (df_sorted[y_column] / total) * 100
        
        # Group small slices (< 3%) into "Others" for cleaner visualization
        threshold = 3.0
        main_items = df_sorted[df_sorted['percentage'] >= threshold]
        small_items = df_sorted[df_sorted['percentage'] < threshold]
        
        # If we have small items, add "Others" category
        if len(small_items) > 0:
            others_sum = small_items[y_column].sum()
            others_row = pd.DataFrame({
                x_column: ['Others'],
                y_column: [others_sum],
                'percentage': [(others_sum / total) * 100]
            })
            plot_data = pd.concat([main_items, others_row], ignore_index=True)
        else:
            plot_data = main_items
        
        # Limit to max 8 slices total for clean visualization
        if len(plot_data) > 8:
            top_7 = plot_data.head(7)
            rest = plot_data.tail(len(plot_data) - 7)
            rest_sum = rest[y_column].sum()
            others_row = pd.DataFrame({
                x_column: ['Others'],
                y_column: [rest_sum],
                'percentage': [(rest_sum / total) * 100]
            })
            plot_data = pd.concat([top_7, others_row], ignore_index=True)
        
        # Use high-contrast colors
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Custom function to show percentage only for slices >= 2%
        def autopct_format(pct):
            return f'{pct:.1f}%' if pct >= 2 else ''
        
        # Create pie chart with explode effect for emphasis
        explode = [0.05 if i == 0 else 0 for i in range(len(plot_data))]
        
        wedges, texts, autotexts = ax.pie(
            plot_data[y_column],
            labels=plot_data[x_column].astype(str),
            autopct=autopct_format,
            startangle=90,
            colors=colors[:len(plot_data)],
            explode=explode,
            pctdistance=0.85,
            textprops={'fontsize': 10}
        )
        
        # Make percentage text bold and white for visibility
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(10)
        
        # Improve label positioning - use smart positioning for overlapping labels
        for text in texts:
            text.set_fontsize(9)
        
        ax.set_title(title, fontsize=13, fontweight="bold", pad=20)
    
    def _create_scatter_chart(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
    ) -> None:
        """Create scatter chart."""
        ax.scatter(df[x_column], df[y_column], alpha=0.6, s=40, color="steelblue")
        ax.set_xlabel(x_column.replace("_", " ").title())
        ax.set_ylabel(y_column.replace("_", " ").title())
        ax.set_title(title, fontsize=13, fontweight="bold")
        
        # Add lighter grid
        ax.grid(True, alpha=0.2, linewidth=0.5)
    
    def create_table_image(
        self,
        data: list[dict[str, Any]],
        title: str | None = None,
        max_rows: int = 20,
    ) -> str:
        """
        Create table image from query results.
        
        Args:
            data: List of dictionaries containing query results
            title: Table title
            max_rows: Maximum rows to display (default: 20)
        
        Returns:
            Path to generated table image
        """
        if not data:
            raise ValueError("Cannot generate table from empty data")
        
        # Convert to DataFrame and limit rows
        df = pd.DataFrame(data).head(max_rows)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, len(df) * 0.5 + 2))
        ax.axis("tight")
        ax.axis("off")
        
        # Create table
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc="left",
            loc="center",
            colWidths=[0.15] * len(df.columns),
        )
        
        # Style table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Color header
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor("#4472C4")
            table[(0, i)].set_text_props(weight="bold", color="white")
        
        # Alternate row colors
        for i in range(1, len(df) + 1):
            color = "#F2F2F2" if i % 2 == 0 else "white"
            for j in range(len(df.columns)):
                table[(i, j)].set_facecolor(color)
        
        # Add title
        if title:
            plt.title(title, fontsize=14, fontweight="bold", pad=20)
        
        # Save table
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"table_{timestamp}.png"
        filepath = self.output_dir / filename
        
        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close()
        
        return str(filepath)


# Global chart generator instance
chart_generator = ChartGenerator()
