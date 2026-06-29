#!/usr/bin/env python3
"""Inline data.json into index.html as the FALLBACK constant.
Run after editing data.json:  python3 build.py
"""
import json, re, pathlib

root = pathlib.Path(__file__).parent
data = json.loads((root / "data.json").read_text())
html = (root / "index.html").read_text()

block = "const FALLBACK = " + json.dumps(data, indent=2, ensure_ascii=False) + ";"
# Replace whatever the current FALLBACK assignment is (placeholder or prior inline).
# Use a function repl so backslashes/unicode in the JSON aren't treated as regex templates.
html, n = re.subn(r"const FALLBACK = .*?;\n",
                  lambda m: block + "\n", html, count=1, flags=re.S)
if n == 0:
    raise SystemExit("Could not find FALLBACK assignment in index.html")
(root / "index.html").write_text(html)
print(f"Inlined {len(json.dumps(data))} bytes of data into index.html")
