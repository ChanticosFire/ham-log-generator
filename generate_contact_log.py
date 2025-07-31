#!/usr/bin/env python3
"""
Simple generator for an amateur radio contact log static page.

This script reads a CSV file containing contact log entries and a JSON
configuration file describing the station operator.  It then produces a
complete HTML document with a sortable, paginated table.  The goal is
to minimise manual editing of HTML while retaining a familiar look and
feel.  All long entries (e.g. QTH, equipment and antenna fields) are
rendered on a single line with `white‑space: nowrap;` so the table
never wraps awkwardly.

Usage:

    python3 generate_contact_log.py --csv data.csv --config config.json --output index.html

Both the CSV and configuration files must exist.  See the included
`data.csv` and `config.json` examples for the expected field order and
keys.  The script intentionally avoids external dependencies for
portability – it only relies on Python’s standard library.
"""

import argparse
import csv
import html
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an HTML contact log from CSV data.")
    parser.add_argument("--csv", required=True, help="Path to the input CSV file containing log records.")
    parser.add_argument("--config", required=True, help="Path to the JSON configuration file for station details.")
    parser.add_argument("--output", required=True, help="Path to write the generated HTML file.")
    return parser.parse_args()


def load_config(config_path: Path) -> dict:
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as exc:
        raise SystemExit(f"Failed to load configuration from {config_path}: {exc}")
    # Normalise keys to lower case for convenience
    return {k.lower(): v for k, v in config.items()}


def read_csv(csv_path: Path) -> list:
    """Read the CSV file and return a list of ordered dictionaries.

    The script expects the CSV header row to define the order of
    columns.  Whitespace in header names is stripped and used to
    construct table headings.  Rows are returned in the order they
    appear in the file.
    """
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return []
            # Strip whitespace around header names
            headers = [h.strip() for h in headers]
            rows = []
            for row in reader:
                # If row is shorter than headers, pad with empty strings
                if len(row) < len(headers):
                    row += ["" for _ in range(len(headers) - len(row))]
                entry = {headers[i]: row[i].strip() for i in range(len(headers))}
                rows.append(entry)
            return rows
    except FileNotFoundError:
        raise SystemExit(f"CSV file not found: {csv_path}")
    except Exception as exc:
        raise SystemExit(f"Error reading CSV file {csv_path}: {exc}")


def build_html(rows: list, config: dict) -> str:
    """Construct the HTML page as a single string.

    :param rows: A list of dictionaries representing contact log entries.
    :param config: Station configuration with at least 'callsign' and 'license'.
    :return: The complete HTML document.
    """
    callsign = html.escape(str(config.get("callsign", "")).upper())
    license_class = html.escape(str(config.get("license", "")))
    operator = html.escape(str(config.get("operator", "")))
    location = html.escape(str(config.get("location", "")))
    grid = html.escape(str(config.get("grid", "")))
    email = html.escape(str(config.get("email", "")))

    # Derive table headings and display names.  If a header contains
    # English names (e.g. "DATE"), insert a space before the English
    # part.  Otherwise leave as is.  This simple heuristic assumes
    # uppercase letters denote the English abbreviation.
    if rows:
        headers = list(rows[0].keys())
    else:
        headers = []

    def prettify(header: str) -> str:
        """Insert a space between the Chinese portion and the English abbreviation.

        Headers in the CSV use a convention such as "日期DATE" or "模式MODE".
        This function detects the first uppercase sequence and inserts a
        single space before it.  If the header already contains spaces
        (e.g. "Sent RST"), it is returned unchanged.
        """
        header = header.strip()
        # If there's already a space, assume it's formatted correctly
        if ' ' in header:
            return ' '.join(header.split())
        import re
        m = re.search(r'[A-Z]', header)
        if not m:
            return header
        pos = m.start()
        chinese = header[:pos].strip()
        english = header[pos:].strip()
        if chinese:
            return f"{chinese} {english}"
        # If the English part starts at index 0, return as is
        return english

    display_headers = [prettify(h) for h in headers]

    # Build table header HTML
    header_html_parts = []
    for idx, name in enumerate(display_headers):
        header_html_parts.append(f'<th onclick="sortTable({idx})">{html.escape(name)}</th>')
    header_html = "\n                ".join(header_html_parts)

    # Build table body HTML
    row_html_parts = []
    for row in rows:
        cells = []
        for h in headers:
            value = row.get(h, "")
            value = html.escape(value)
            cells.append(f"<td>{value}</td>")
        row_html_parts.append("                <tr>" + "".join(cells) + "</tr>")
    body_html = "\n".join(row_html_parts)

    # Compose the final HTML document
    # Prebuild optional profile lines outside the template to avoid nested f-strings
    operator_line = f"<li><strong>OPR:</strong> {operator}</li>" if operator else ""
    location_line = f"<li><strong>QTH:</strong> {location}</li>" if location else ""
    grid_line = f"<li><strong>GRID:</strong> {grid}</li>" if grid else ""
    email_line = f"<li><strong>EMAIL:</strong> {email}</li>" if email else ""
    # Construct the HTML document using str.format.  Double braces escape literal braces.
    year = datetime.now().year
    template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>业余无线电台{callsign}通联日志</title>
    <style>
        /* Reset and base styles */
        * {{ box-sizing: border-box; }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.5;
            background-color: #f5f7fa;
            color: #333;
        }}
        header {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 1.5rem 0;
            text-align: center;
        }}
        .container {{
            max-width: 80%;
            margin: 0 auto;
            padding: 1rem;
        }}
        .profile {{
            background-color: #ffffff;
            border: 1px solid #e0e6ed;
            border-radius: 6px;
            padding: 1rem 1.25rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .profile h2 {{ margin-top: 0; }}
        .profile ul {{ list-style: none; padding: 0; margin: 0; }}
        .profile li {{ margin-bottom: 0.5rem; }}
        .profile li strong {{ display: inline-block; width: 130px; }}
        .log h2 {{ margin-top: 0; margin-bottom: 0.5rem; }}
        .table-responsive {{ overflow-x: auto; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
        }}
        th, td {{
            padding: 0.625rem 0.75rem;
            border-bottom: 1px solid #e0e6ed;
            text-align: left;
            white-space: nowrap;
        }}
        th {{
            background-color: #3498db;
            color: #ffffff;
            position: sticky;
            top: 0;
            z-index: 2;
            cursor: pointer;
        }}
        tr:nth-child(even) {{ background-color: #f9fcff; }}
        tr:hover {{ background-color: #eef5ff; }}
        .pagination {{
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 2rem;
        }}
        .pagination button {{
            padding: 0.5rem 1rem;
            margin: 0 0.5rem;
            border: none;
            border-radius: 4px;
            background-color: #3498db;
            color: #ffffff;
            cursor: pointer;
        }}
        .pagination button:hover {{ background-color: #2c3e50; }}
        footer {{
            text-align: center;
            padding: 1rem;
            font-size: 0.875rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <header>
        <h1>业余无线电台 {callsign} 通联日志</h1>
    </header>
    <div class="container">
        <section class="profile">
            <h2>个人资料</h2>
            <ul>
                <li><strong>CALL:</strong> {callsign}</li>
                <li><strong>CLASS:</strong> {license_class}</li>
                {operator_line}
                {location_line}
                {grid_line}
                {email_line}
            </ul>
        </section>
        <section class="log">
            <h2>通联日志</h2>
            <div class="table-responsive">
                <table id="logTable">
                    <thead>
                        <tr>
                            {header_html}
                        </tr>
                    </thead>
                    <tbody>
{body_html}
                    </tbody>
                </table>
            </div>
        </section>
        <div class="pagination">
            <button onclick="previousPage()">上页</button>
            <span id="pageInfo"></span>
            <button onclick="nextPage()">下页</button>
        </div>
    </div>
    <footer>
        <p>Copyright © {year} 中国业余无线电台{callsign}</p>
    </footer>
    <script>
        let currentPage = 1;
        const rowsPerPage = 20;
        function displayRows() {{
            const table = document.getElementById('logTable');
            const rows = table.getElementsByTagName('tr');
            const totalRows = rows.length;
            const startRow = (currentPage - 1) * rowsPerPage + 1;
            const endRow = startRow + rowsPerPage - 1;
            for (let i = 1; i < totalRows; i++) {{
                if (i >= startRow && i <= endRow) {{
                    rows[i].style.display = '';
                }} else {{
                    rows[i].style.display = 'none';
                }}
            }}
            document.getElementById('pageInfo').innerText = '显示第 ' + startRow + ' 至 ' + Math.min(endRow, totalRows - 1) + ' 项结果，共 ' + (totalRows - 1) + ' 项';
        }}
        function nextPage() {{
            const table = document.getElementById('logTable');
            const totalRows = table.getElementsByTagName('tr').length;
            if (currentPage * rowsPerPage < totalRows - 1) {{
                currentPage++;
                displayRows();
            }}
        }}
        function previousPage() {{
            if (currentPage > 1) {{
                currentPage--;
                displayRows();
            }}
        }}
        function sortTable(columnIndex) {{
            const table = document.getElementById('logTable');
            let switching = true;
            let dir = 'asc';
            while (switching) {{
                switching = false;
                const rows = table.rows;
                let i;
                for (i = 1; i < rows.length - 1; i++) {{
                    let shouldSwitch = false;
                    const x = rows[i].getElementsByTagName('TD')[columnIndex];
                    const y = rows[i + 1].getElementsByTagName('TD')[columnIndex];
                    if (dir == 'asc') {{
                        if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }} else if (dir == 'desc') {{
                        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }}
                }}
                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                }} else {{
                    if (dir == 'asc') {{
                        dir = 'desc';
                        switching = true;
                    }}
                }}
            }}
            currentPage = 1;
            displayRows();
        }}
        displayRows();
    </script>
</body>
</html>"""
    html_doc = template.format(
        callsign=callsign,
        license_class=license_class,
        operator_line=operator_line,
        location_line=location_line,
        grid_line=grid_line,
        email_line=email_line,
        header_html=header_html,
        body_html=body_html,
        year=year
    )
    return html_doc


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    config_path = Path(args.config)
    output_path = Path(args.output)
    config = load_config(config_path)
    rows = read_csv(csv_path)
    html_content = build_html(rows, config)
    try:
        with output_path.open("w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as exc:
        raise SystemExit(f"Failed to write output file {output_path}: {exc}")
    print(f"Successfully generated {output_path}")


if __name__ == "__main__":
    main()
