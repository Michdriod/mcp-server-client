"""
Export query results to various formats (CSV, Excel, PDF).
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


# Export directory
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


async def export_to_csv(
    data: list[dict[str, Any]],
    filename: str | None = None,
) -> str:
    """
    Export data to CSV file.
    
    Args:
        data: List of dictionaries containing query results
        filename: Output filename (without extension)
    
    Returns:
        Path to exported file
    """
    if not data:
        raise ValueError("Cannot export empty data")
    
    # Generate filename if not provided
    if filename is None:
        filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = EXPORT_DIR / f"{filename}.csv"
    
    # Write CSV
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        if data:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    return str(filepath)


async def export_to_excel(
    data: list[dict[str, Any]],
    filename: str | None = None,
    title: str | None = None,
) -> str:
    """
    Export data to Excel file with formatting.
    
    Args:
        data: List of dictionaries containing query results
        filename: Output filename (without extension)
        title: Worksheet title
    
    Returns:
        Path to exported file
    """
    if not data:
        raise ValueError("Cannot export empty data")
    
    # Generate filename if not provided
    if filename is None:
        filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = EXPORT_DIR / f"{filename}.xlsx"
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel writer
    with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
        # Write data
        df.to_excel(writer, sheet_name="Data", index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Data"]
        
        # Add formats
        header_format = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#4472C4",
            "font_color": "white",
            "border": 1,
        })
        
        # Format header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Auto-adjust column widths
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.set_column(i, i, min(max_len + 2, 50))
        
        # Add title if provided
        if title:
            title_format = workbook.add_format({
                "bold": True,
                "font_size": 16,
                "align": "center",
            })
            worksheet.write(0, 0, title, title_format)
    
    return str(filepath)


async def export_to_pdf(
    data: list[dict[str, Any]],
    filename: str | None = None,
    title: str | None = None,
) -> str:
    """
    Export data to PDF file with table formatting.
    
    Args:
        data: List of dictionaries containing query results
        filename: Output filename (without extension)
        title: Document title
    
    Returns:
        Path to exported file
    """
    if not data:
        raise ValueError("Cannot export empty data")
    
    # Generate filename if not provided
    if filename is None:
        filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = EXPORT_DIR / f"{filename}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title
    if title:
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#4472C4"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
    
    # Add metadata
    metadata_text = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>Total Rows: {len(data)}"
    elements.append(Paragraph(metadata_text, styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    # Prepare table data
    if data:
        columns = list(data[0].keys())
        table_data = [columns]  # Header row
        
        # Limit to first 100 rows for PDF (too many rows = large file)
        for row in data[:100]:
            table_data.append([str(row.get(col, "")) for col in columns])
        
        if len(data) > 100:
            elements.append(Paragraph(
                f"<i>Note: Showing first 100 of {len(data)} rows</i>",
                styles["Normal"]
            ))
            elements.append(Spacer(1, 12))
        
        # Create table
        table = Table(table_data)
        
        # Style table
        table.setStyle(TableStyle([
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            
            # Data row styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    return str(filepath)


async def export_to_json(
    data: list[dict[str, Any]],
    filename: str | None = None,
) -> str:
    """
    Export data to JSON file.
    
    Args:
        data: List of dictionaries containing query results
        filename: Output filename (without extension)
    
    Returns:
        Path to exported file
    """
    import json
    
    if not data:
        raise ValueError("Cannot export empty data")
    
    # Generate filename if not provided
    if filename is None:
        filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = EXPORT_DIR / f"{filename}.json"
    
    # Write JSON
    with open(filepath, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=2, default=str)
    
    return str(filepath)
