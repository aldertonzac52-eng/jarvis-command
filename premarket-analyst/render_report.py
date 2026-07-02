#!/usr/bin/env python3
"""Render REPORT.md to a clean standalone HTML page.
Usage: python3 render_report.py REPORT.md [YYYY-MM-DD]"""
import sys, os
from datetime import date

try:
    import markdown
except ImportError:
    sys.exit("Run: pip install markdown --break-system-packages")

src = sys.argv[1] if len(sys.argv) > 1 else "REPORT.md"
day = sys.argv[2] if len(sys.argv) > 2 else str(date.today())
body = markdown.markdown(open(src).read(), extensions=["tables", "fenced_code", "sane_lists"])

CSS = """
:root{--ink:#1c2733;--mut:#5b6b7c;--line:#dbe3ec;--bg:#f6f8fb;--card:#ffffff;--acc:#0e7490}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 -apple-system,'Segoe UI',Inter,Roboto,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:28px 20px 60px}
header{border-bottom:2px solid var(--acc);padding:10px 0 14px;margin-bottom:18px}
header h1{margin:0;font-size:22px} header .d{color:var(--mut);font-size:13px;margin-top:4px}
h2{font-size:17px;margin:26px 0 8px;padding-top:14px;border-top:1px solid var(--line)}
h3{font-size:14px;color:var(--mut);margin:8px 0}
blockquote{margin:10px 0;padding:8px 14px;background:#eef4f9;border-left:3px solid var(--acc);
color:var(--mut);font-size:13.5px;border-radius:0 8px 8px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card);border-radius:8px;overflow:hidden}
th{background:#e8eef5;text-align:left;padding:8px 10px;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
td{padding:8px 10px;border-top:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#fafcfe}
li{margin:3px 0} code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:13px}
footer{margin-top:34px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
"""
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Premarket Report {day}</title><style>{CSS}</style></head><body><div class="wrap">
<header><h1>AI Premarket Report</h1><div class="d">{day}</div></header>
{body}
<footer>Generated {day} · Built by two independent AI passes · Educational only, not financial advice</footer>
</div></body></html>"""

os.makedirs("reports", exist_ok=True)
out = f"reports/premarket_{day}.html"
open(out, "w").write(html)
print(f"[render] wrote {out}")
