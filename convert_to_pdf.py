#!/usr/bin/env python3
"""
Convert Markdown to PDF with support for Persian/Farsi text
"""

import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import sys

def markdown_to_pdf(md_file, pdf_file):
    """Convert markdown file to PDF with proper styling for Persian text"""

    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'tables', 'toc'])
    html_content = md.convert(md_content)

    # Create full HTML document with CSS styling
    full_html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Toyo Ito Structural Analysis</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @bottom-center {{
                    content: counter(page);
                    font-family: sans-serif;
                    font-size: 10pt;
                }}
            }}

            body {{
                font-family: 'DejaVu Sans', 'Arial', 'Tahoma', sans-serif;
                line-height: 1.8;
                color: #333;
                direction: rtl;
                text-align: right;
                font-size: 11pt;
            }}

            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                font-size: 24pt;
                page-break-before: always;
            }}

            h1:first-of-type {{
                page-break-before: avoid;
            }}

            h2 {{
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 8px;
                margin-top: 25px;
                font-size: 20pt;
            }}

            h3 {{
                color: #555;
                margin-top: 20px;
                font-size: 16pt;
            }}

            h4 {{
                color: #666;
                margin-top: 15px;
                font-size: 14pt;
            }}

            pre {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
                overflow-x: auto;
                direction: ltr;
                text-align: left;
                font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
                font-size: 9pt;
                line-height: 1.4;
                white-space: pre;
            }}

            code {{
                background-color: #f8f9fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
                font-size: 10pt;
            }}

            pre code {{
                background-color: transparent;
                padding: 0;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 10pt;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 12px 8px;
                text-align: right;
            }}

            th {{
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }}

            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}

            ul, ol {{
                margin: 10px 0;
                padding-right: 30px;
            }}

            li {{
                margin: 8px 0;
            }}

            p {{
                margin: 12px 0;
                text-align: justify;
            }}

            a {{
                color: #3498db;
                text-decoration: none;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            blockquote {{
                border-right: 4px solid #3498db;
                margin: 20px 0;
                padding: 10px 20px;
                background-color: #f8f9fa;
                font-style: italic;
            }}

            hr {{
                border: none;
                border-top: 2px solid #ddd;
                margin: 30px 0;
            }}

            /* Prevent page breaks inside important elements */
            h1, h2, h3, h4, h5, h6 {{
                page-break-after: avoid;
            }}

            table, pre, blockquote {{
                page-break-inside: avoid;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Configure fonts
    font_config = FontConfiguration()

    # Convert HTML to PDF
    HTML(string=full_html).write_pdf(
        pdf_file,
        font_config=font_config
    )

    print(f"✓ PDF created successfully: {pdf_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        md_file = "toyo-ito-structural-analysis.md"
    else:
        md_file = sys.argv[1]

    # Generate output filename
    pdf_file = md_file.replace('.md', '.pdf')

    markdown_to_pdf(md_file, pdf_file)
